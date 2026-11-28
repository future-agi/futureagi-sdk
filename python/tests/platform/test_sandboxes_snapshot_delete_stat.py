"""Snapshot deletion and file metadata through the real sync and async transports.

The recording server handles these requests without changing the operation table
used by ordinary sandbox calls.
"""

from __future__ import annotations

import re
from pathlib import PurePosixPath

import httpx
import pytest
from fi.sandbox import (
    AsyncSandbox,
    AuthenticationError,
    ConfigurationError,
    ConnectionError,
    NotFoundError,
    PermissionDeniedError,
    ProviderError,
    RateLimitError,
    Sandbox,
    SandboxAPIError,
    SandboxHibernatedError,
    UnavailableError,
    ValidationError,
)
from fi.sandbox._connection import OriginRule

from ._sandbox_mock import (
    FAKE_KEY,
    FAKE_SECRET,
    FAKE_TOKEN,
    HOSTED,
    MODES,
    ORIGIN,
    SBX,
    SNAP,
    MockServer,
    Route,
    api,
    resolve,
    run,
)

V1 = "omega-workspace-sandboxes/v1"
DELETE = "sandboxes.snapshots.delete"
READ = "sandboxes.files.read"
PREFIX = f"/omega/api/workspace/sandboxes/{SBX}"
ACK = {"schemaVersion": V1, "deleted": True, "request_id": "req-delete"}
STAT = {
    "path": "dir/report.txt",
    "type": "file",
    "size": 17,
    "mode": "640",
    "modifiedAt": "2026-11-14T00:00:00.000Z",
}


def server():
    mock = MockServer()
    # Direct-only snapshot deletion returns the v1 deleted acknowledgement.
    template = "/workspace/sandboxes/{id}/snapshots/{snapshotId}"
    mock.routes[DELETE] = Route(
        DELETE, "DELETE", template,
        re.compile(r"^/workspace/sandboxes/[^/]+/snapshots/[^/]+$"),
        200, None,
    )
    mock.on(DELETE, httpx.Response(200, json=ACK))
    # Metadata is nested under `file`, not `stat`.
    mock.on(READ, httpx.Response(200, json={"schemaVersion": V1, "file": STAT}))
    return mock


def handle(mock, mode, **options):
    cls = AsyncSandbox if mode == "async" else Sandbox
    return cls(api(mock, mode, **options), {"id": SBX, "state": "active"})


def required_method(part, name):
    method = getattr(part, name, None)
    assert callable(method), f"required sandbox method {name} must be callable"
    return method


def invoke(sbx, verb):
    if verb == "delete":
        return required_method(sbx.snapshots, "delete")(SNAP)
    return required_method(sbx.files, "stat")(STAT["path"])


def refusal(status, code, detail=None):
    error = {"code": code, "message": "fixture refusal"}
    if detail is not None:
        error["detail"] = detail
    return httpx.Response(
        status, json={"schemaVersion": V1, "error": error},
        headers={"x-request-id": "req-refused", "retry-after": "0"},
    )


@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("auth", ["keys", "bearer"])
def test_snapshot_delete_returns_the_v1_ack_on_the_same_connection(mode, auth):
    mock = server()
    sbx = handle(mock, mode, auth=auth)
    before = dict(sbx.info)
    assert run(resolve(required_method(sbx.snapshots, "delete")(SNAP))) == ACK
    assert sbx.info == before
    assert [seen.name for seen in mock.seen] == [DELETE]
    request = mock.last.request
    assert request.method == "DELETE"
    assert str(request.url) == ORIGIN + f"/workspace/sandboxes/{SBX}/snapshots/{SNAP}"
    assert request.content == b"" and not request.url.query
    assert request.headers["accept"] == "application/json"
    assert request.extensions["fi.retry"]["retries"] == 0
    if auth == "keys":
        assert request.headers["x-api-key"] == FAKE_KEY
        assert request.headers["x-secret-key"] == FAKE_SECRET
        assert "authorization" not in request.headers
    else:
        assert request.headers["authorization"] == f"Bearer {FAKE_TOKEN}"
        assert "x-api-key" not in request.headers and "x-secret-key" not in request.headers


@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("snapshot_id,encoded", [
    ("snap space", "snap%20space"),
    ("snap_雪", "snap_%E9%9B%AA"),
    ("snap/a?#", "snap%2Fa%3F%23"),
    ("snap%2Fid", "snap%252Fid"),
])
def test_snapshot_delete_encodes_one_segment_and_preserves_server_not_found(mode, snapshot_id, encoded):
    mock = server()
    mock.on(DELETE, refusal(404, "not_found"))
    with pytest.raises(NotFoundError):
        run(resolve(required_method(handle(mock, mode).snapshots, "delete")(snapshot_id)))
    assert len(mock.seen) == 1
    assert mock.last.request.url.raw_path == f"{PREFIX}/snapshots/{encoded}".encode()


@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("snapshot_id", ["", ".", "..", None])
def test_snapshot_delete_keeps_existing_path_parameter_refusals(mode, snapshot_id):
    mock = server()
    with pytest.raises(ConfigurationError):
        run(resolve(required_method(handle(mock, mode).snapshots, "delete")(snapshot_id)))
    assert mock.seen == []


@pytest.mark.parametrize("mode", MODES)
def test_snapshot_delete_hosted_unsupported_is_not_retargeted_or_hidden(mode):
    mock = server()
    mock.on(DELETE, refusal(404, "unsupported_operation"))
    with pytest.raises(NotFoundError) as caught:
        run(resolve(required_method(handle(mock, mode, base=HOSTED).snapshots, "delete")(SNAP)))
    assert caught.value.code == "unsupported_operation"
    assert len(mock.seen) == 1
    assert str(mock.last.request.url) == HOSTED + f"/workspace/sandboxes/{SBX}/snapshots/{SNAP}"
    assert mock.last.request.headers["x-api-key"] == FAKE_KEY
    assert "authorization" not in mock.last.request.headers


@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("kind", ["file", "directory", "symlink", "other"])
def test_file_stat_extracts_metadata_without_content_or_listing(mode, kind):
    mock = server()
    metadata = {**STAT, "type": kind, "size": 0, "mode": "0"}
    mock.on(READ, httpx.Response(200, json={"schemaVersion": V1, "file": metadata}))
    assert run(resolve(required_method(handle(mock, mode).files, "stat")(STAT["path"]))) == metadata
    assert [seen.name for seen in mock.seen] == [READ]
    request = mock.last.request
    assert request.method == "GET"
    assert request.url.raw_path == f"{PREFIX}/files/dir/report.txt?stat=1".encode()
    assert request.content == b""
    assert request.headers["accept"] == "application/json"
    assert "retries" not in request.extensions["fi.retry"]


@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("path,encoded", [
    ("dir/a b.txt", "dir/a%20b.txt"),
    ("/workspace/dir/雪.txt", "dir/%E9%9B%AA.txt"),
    ("//workspace/dir//a?#.txt", "dir/a%3F%23.txt"),
    ("dir/%2e%2e.txt", "dir/%252e%252e.txt"),
    (PurePosixPath("/workspace/dir/report.txt"), "dir/report.txt"),
])
def test_file_stat_reuses_path_normalization_and_encodes_once(mode, path, encoded):
    mock = server()
    run(resolve(required_method(handle(mock, mode).files, "stat")(path)))
    assert len(mock.seen) == 1
    assert mock.last.request.url.raw_path == f"{PREFIX}/files/{encoded}?stat=1".encode()


@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("path", [
    "", ".", "/workspace", "/tmp/a", "../a", "a/../b", "a/./b",
    "/workspace/../b", "a\\b", "a\x00b", "a\nb", "a\x7fb", None, 7,
])
def test_file_stat_refuses_invalid_paths_before_transport(mode, path):
    mock = server()
    with pytest.raises(ConfigurationError) as caught:
        run(resolve(required_method(handle(mock, mode).files, "stat")(path)))
    assert caught.value.code == "invalid_path"
    assert mock.seen == []


@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("verb", ["delete", "stat"])
@pytest.mark.parametrize("status,code,error_type,detail", [
    (400, "validation", ValidationError, None),
    (401, "unauthorized", AuthenticationError, None),
    (403, "forbidden", PermissionDeniedError, None),
    (404, "not_found", NotFoundError, None),
    (409, "conflict", SandboxHibernatedError, {"state": "hibernated"}),
    (429, "rate_limited", RateLimitError, None),
    (502, "provider_error", ProviderError, None),
    (503, "unavailable", UnavailableError, None),
    (501, "unsupported", SandboxAPIError, None),
])
def test_conveniences_preserve_server_errors(mode, verb, status, code, error_type, detail):
    mock = server()
    mock.on(DELETE if verb == "delete" else READ, refusal(status, code, detail))
    sbx = handle(mock, mode, retries=3 if verb == "delete" else 0)
    with pytest.raises(error_type) as caught:
        run(resolve(invoke(sbx, verb)))
    assert caught.value.status == status and caught.value.code == code
    assert caught.value.request_id == "req-refused"
    if detail is not None:
        assert caught.value.detail["state"] == "hibernated"
    assert len(mock.seen) == 1


@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("verb", ["delete", "stat"])
def test_conveniences_propagate_connection_failures(mode, verb):
    mock = server()

    def dropped(request):
        raise httpx.ReadError("fixture reset", request=request)

    mock.on(DELETE if verb == "delete" else READ, dropped)
    sbx = handle(mock, mode, retries=3 if verb == "delete" else 0)
    with pytest.raises(ConnectionError) as caught:
        run(resolve(invoke(sbx, verb)))
    # The transport records a post-send failure for both; only a mutation warns
    # that completion is unknown. Stat retains the existing read error semantics.
    assert caught.value.possibly_applied is True
    assert ("completion is unknown" in str(caught.value)) is (verb == "delete")
    assert len(mock.seen) == 1


@pytest.mark.parametrize("mode", MODES)
def test_stat_keeps_the_existing_read_retry_policy(mode):
    mock = server()
    responses = iter([
        refusal(503, "unavailable"),
        httpx.Response(200, json={"schemaVersion": V1, "file": STAT}),
    ])
    mock.on(READ, lambda request: next(responses))
    assert run(resolve(required_method(handle(mock, mode).files, "stat")(STAT["path"]))) == STAT
    assert [seen.name for seen in mock.seen] == [READ, READ]
    assert all(dict(seen.request.url.params) == {"stat": "1"} for seen in mock.seen)


@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("verb", ["delete", "stat"])
@pytest.mark.parametrize("base,auth,code", [
    ("http://sbx.example.test", "keys", "insecure_sandbox_origin"),
    (ORIGIN, "bearer", "custom_base_url_not_allowed"),
])
def test_conveniences_keep_origin_refusals(mode, verb, base, auth, code):
    mock = server()
    sbx = handle(mock, mode, base=base, auth=auth, rule=OriginRule())
    with pytest.raises(ConfigurationError) as caught:
        run(resolve(invoke(sbx, verb)))
    assert caught.value.code == code
    assert mock.seen == []


@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("encoding,content,expected", [
    ("utf8", "héllo", "héllo"),
    ("base64", "AP8=", b"\x00\xff"),
])
def test_stat_leaves_ordinary_read_and_the_generated_table_unchanged(mode, encoding, content, expected):
    from fi.generated.platform.policy import OPERATIONS

    before = dict(OPERATIONS)
    mock = server()
    sbx = handle(mock, mode)
    assert run(resolve(required_method(sbx.files, "stat")(STAT["path"]))) == STAT
    assert run(resolve(required_method(sbx.snapshots, "delete")(SNAP))) == ACK
    mock.on(READ, httpx.Response(200, json={"schemaVersion": V1, "file": {
        "path": STAT["path"], "encoding": encoding, "content": content,
    }}))
    assert run(resolve(sbx.files.read(STAT["path"], max_bytes=17))) == expected
    assert dict(mock.last.request.url.params) == {"maxBytes": "17"}
    assert len(mock.seen) == 3
    assert OPERATIONS == before
    assert DELETE not in OPERATIONS
    assert OPERATIONS[READ].query == ("maxBytes",)


@pytest.mark.parametrize("mode", MODES)
def test_low_level_resources_return_the_full_envelopes(mode):
    mock = server()
    resource = api(mock, mode)
    assert run(resolve(required_method(resource.snapshots, "delete")(SBX, SNAP))) == ACK
    assert run(resolve(required_method(resource.files, "stat")(SBX, STAT["path"]))) == {
        "schemaVersion": V1, "file": STAT,
    }
    assert [seen.name for seen in mock.seen] == [DELETE, READ]
