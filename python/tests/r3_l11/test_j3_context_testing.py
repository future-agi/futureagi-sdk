"""Transport-bound regressions for explicit, digest-bound context test admission."""

import json
from uuid import uuid4

import httpx
import pytest

from fi.context import testing
from fi.platform import Client

CONTEXT = str(uuid4())
RUN = str(uuid4())
FINGERPRINT = "sha256:" + "a" * 64


@pytest.fixture
def configured():
    seen = []

    def handle(request):
        seen.append(request)
        return httpx.Response(200, json={"result": {"id": RUN}}, request=request)

    with Client(api_key="test-key", secret_key="test-secret",
                base_url="https://example.invalid", workspace_id=str(uuid4()),
                http_client=httpx.Client(transport=httpx.MockTransport(handle))) as client:
        yield testing.ContextTestingClient(client), seen


def payload():
    return dict(configuration={"candidate": {"kind": "draft", "revision": 4,
                                             "digest": FINGERPRINT}},
                expected_fingerprint=FINGERPRINT,
                inventory_review={"fingerprint": FINGERPRINT, "reviewed_all_files": True},
                acknowledge_provider_processing=True, idempotency_key=str(uuid4()))


def test_exact_review_and_original_operation_are_forwarded(configured):
    client, seen = configured
    request = payload()
    assert client.create(CONTEXT, **request) == {"id": RUN}
    assert client.create(CONTEXT, **request) == {"id": RUN}
    assert len(seen) == 2
    assert all(r.headers["Idempotency-Key"] == request["idempotency_key"] for r in seen)
    assert seen[0].content == seen[1].content
    assert json.loads(seen[0].content) == {k: v for k, v in request.items() if k != "idempotency_key"}
    assert seen[0].url.path == f"/model-hub/skills/contexts/{CONTEXT}/test-runs/"


@pytest.mark.parametrize("change", [
    {"acknowledge_provider_processing": False}, {"acknowledge_provider_processing": 1},
    {"expected_fingerprint": "newest"}, {"idempotency_key": "not-a-uuid"},
])
def test_no_implicit_consent_or_identity_reconstruction(configured, change):
    client, seen = configured
    with pytest.raises(ValueError):
        client.create(CONTEXT, **{**payload(), **change})
    assert seen == []


def test_lifecycle_paths_and_pagination(configured):
    client, seen = configured
    client.preview(CONTEXT, {"candidate": {"kind": "version", "version": 2}})
    client.list(CONTEXT, page=2, page_size=3)
    client.get(CONTEXT, RUN)
    client.results(CONTEXT, RUN, page=4, page_size=5)
    attempt = str(uuid4())
    client.attempt(CONTEXT, RUN, attempt)
    client.cancel(CONTEXT, RUN)
    assert [(r.method, r.url.path.rsplit("/", 2)[-2]) for r in seen] == [
        ("POST", "preview"), ("GET", "test-runs"), ("GET", RUN),
        ("GET", "results"), ("GET", attempt), ("POST", "cancel"),
    ]
    assert dict(seen[3].url.params) == {"page": "4", "page_size": "5"}
    assert json.loads(seen[-1].content) == {}


def test_uncertain_paid_request_is_not_retried():
    seen = []
    def handle(request):
        seen.append(request)
        raise httpx.ReadTimeout("private fixture data", request=request)
    with Client(api_key="test-key", secret_key="test-secret", base_url="https://example.invalid",
                http_client=httpx.Client(transport=httpx.MockTransport(handle))) as client:
        with pytest.raises(testing.APIConnectionError):
            testing.ContextTestingClient(client).create(CONTEXT, **payload())
    assert len(seen) == 1


def test_cli_requires_separate_consent_before_client_creation(tmp_path, monkeypatch, capsys):
    document = tmp_path / "request.json"
    document.write_text(json.dumps({k: v for k, v in payload().items()
                                  if k not in {"idempotency_key", "acknowledge_provider_processing"}}))
    monkeypatch.setattr(testing, "Client", lambda **kwargs: pytest.fail("No client before consent"))
    assert testing.main(["create", CONTEXT, "--input", str(document),
                         "--idempotency-key", str(uuid4())]) == 2
    assert "Invalid context test" in capsys.readouterr().err


def test_cli_retains_preview_request_and_scoped_transport(tmp_path, monkeypatch, capsys):
    document = tmp_path / "config.json"
    document.write_text(json.dumps({"candidate": {"kind": "version", "version": 1}}))
    org, workspace = str(uuid4()), str(uuid4())
    monkeypatch.setenv("FI_ORGANIZATION_ID", org)
    monkeypatch.setenv("FI_WORKSPACE_ID", workspace)
    seen = []
    class Transport:
        def __init__(self, **kwargs):
            assert kwargs == {"workspace_id": workspace, "default_headers": {"X-Organization-Id": org}}
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def request(self, method, path, **kwargs):
            seen.append((method, path, kwargs))
            return {"fingerprint": FINGERPRINT}
    monkeypatch.setattr(testing, "Client", Transport)
    assert testing.main(["preview", CONTEXT, "--input", str(document)]) == 0
    assert json.loads(capsys.readouterr().out) == {"fingerprint": FINGERPRINT}
    assert seen[0][2]["body"] == {"candidate": {"kind": "version", "version": 1}}


def test_cli_reports_only_status_and_machine_code_of_a_rejected_request(tmp_path, monkeypatch, capsys):
    document = tmp_path / "config.json"
    document.write_text(json.dumps({"candidate": {"kind": "version", "version": 1}}))
    monkeypatch.setenv("FI_ORGANIZATION_ID", str(uuid4()))
    monkeypatch.setenv("FI_WORKSPACE_ID", str(uuid4()))

    def handle(request):
        return httpx.Response(400, json={"status": False, "type": "validation", "code": "model_not_configured",
                                         "message": "private fixture prompt", "detail": {"prompt": "secret case text"}},
                              request=request)

    real = testing.Client
    monkeypatch.setattr(testing, "Client", lambda **kwargs: real(
        api_key="k", secret_key="s", base_url="https://example.invalid", max_retries=0,
        http_client=httpx.Client(transport=httpx.MockTransport(handle)), **kwargs))
    assert testing.main(["preview", CONTEXT, "--input", str(document)]) == 1
    err = capsys.readouterr().err
    assert "HTTP 400, model_not_configured" in err
    assert "private fixture prompt" not in err and "secret case text" not in err
