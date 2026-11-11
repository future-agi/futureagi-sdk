"""Fresh/resumed runtime sessions never substitute a server-chosen session."""

import json
from uuid import uuid4

import httpx
import pytest

from fi.context.sessions import ContextSessionClient
from fi.context.snapshot import SnapshotIntegrityError
from fi.platform import Client

CONTEXT = str(uuid4())
BINDING = str(uuid4())
SESSION = str(uuid4())


def make(response):
    seen = []

    def handle(request):
        seen.append(request)
        return httpx.Response(200, json={"result": response(request)}, request=request)

    client = Client(api_key="test-key", secret_key="test-secret",
                    base_url="https://example.invalid", workspace_id=str(uuid4()),
                    http_client=httpx.Client(transport=httpx.MockTransport(handle)))
    return ContextSessionClient(client, context_id=CONTEXT, binding_id=BINDING), seen


def request(resume=None):
    return {"client_session_key": str(uuid4()), "incarnation_id": str(uuid4()),
            "resume_session_id": resume, "adapter_version": "a", "runtime_version": "r",
            "runtime_config_digest": "sha256:" + "0" * 64}


def mapped(mode, session=SESSION):
    return {"session_id": session, "resolution_id": str(uuid4()), "history_mode": mode,
            "version": 1, "version_id": str(uuid4()), "digest": "sha256:" + "1" * 64}


def test_resume_is_forwarded_once_with_original_key():
    client, seen = make(lambda _: mapped("resumed"))
    key = str(uuid4())
    assert client.open(request(SESSION), idempotency_key=key)["session_id"] == SESSION
    assert len(seen) == 1
    assert seen[0].headers["Idempotency-Key"] == key
    assert json.loads(seen[0].content)["resume_session_id"] == SESSION
    assert seen[0].url.path == f"/model-hub/skills/contexts/bindings/{BINDING}/sessions/"


@pytest.mark.parametrize("asked,returned", [
    (SESSION, mapped("fresh")),                 # resume silently became a fresh thread
    (SESSION, mapped("resumed", str(uuid4()))),  # a different session was resumed
    (None, mapped("resumed")),                  # fresh request mapped onto history
])
def test_substituted_session_is_rejected(asked, returned):
    client, _ = make(lambda _: returned)
    with pytest.raises(SnapshotIntegrityError):
        client.open(request(asked), idempotency_key=str(uuid4()))


def test_invalid_identity_is_rejected():
    client, _ = make(lambda _: {**mapped("fresh"), "resolution_id": "latest"})
    with pytest.raises(SnapshotIntegrityError):
        client.open(request(), idempotency_key=str(uuid4()))


def test_snapshot_never_reads_a_different_manifest_identity():
    session = {**mapped("fresh"), "requested": {"version": 1}, "resolution_expires_at": "2099-01-01T00:00:00Z"}
    other = {"version_id": str(uuid4()), "digest": session["digest"], "resource_id": CONTEXT}
    client, seen = make(lambda _: other)
    with pytest.raises(SnapshotIntegrityError):
        client.snapshot(session)
    assert len(seen) == 1
    assert seen[0].url.path == f"/model-hub/skills/contexts/{CONTEXT}/versions/1/manifest/"
