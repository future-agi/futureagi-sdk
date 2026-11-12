"""The Sandbox / AsyncSandbox handle (contract section 3): construction, lifecycle, the context
manager, idempotent delete, files, snapshots (restore is a NEW sandbox), the network policy with
its ETag (v2 item 5), and the read-only settings (v2.1 item 7)."""

from __future__ import annotations

import base64
import io

import httpx
import pytest
from fi.sandbox import (
    AsyncSandbox,
    ConflictError,
    NetworkPolicyInfo,
    NotFoundError,
    Sandbox,
    SandboxList,
    UnavailableError,
)
from fi.sandbox import ConnectionError as SandboxConnectionError

from ._sandbox_mock import ETAG, MODES, SBX, SNAP, MockServer, api, error, resolve, run

OTHER = "sbx_" + "c" * 24


def handle(server, mode, state="active"):
    cls = AsyncSandbox if mode == "async" else Sandbox
    return cls(api(server, mode), {"id": SBX, "state": state})


def from_env(monkeypatch, server):
    from fi.sandbox import _connection

    for name in ("FI_API_KEY", "FI_SECRET_KEY", "FI_WORKSPACE_ID", "FI_ORGANIZATION_ID"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("OMEGA_BASE_URL", "http://127.0.0.1:8787")
    monkeypatch.setenv("FUTUREAGI_OMEGA_API_KEY", "fake-token-0007")
    monkeypatch.setattr(_connection, "default_transport", server.transport)


def record(state="active", ident=SBX):
    return {"schemaVersion": "omega-workspace-sandboxes/v1", "sandbox": {"id": ident, "state": state, "name": "n"}}


async def enter_exit(sbx, mode, body=None):
    if mode == "async":
        async with sbx as inside:
            assert inside is sbx
            if body:
                raise body
    else:
        with sbx as inside:
            assert inside is sbx
            if body:
                raise body


@pytest.mark.parametrize("mode", MODES)
def test_lifecycle_methods_update_info(mode):
    server = MockServer()
    sbx = handle(server, mode)
    server.on("sandboxes.hibernate", httpx.Response(200, json=record("hibernated")))
    assert run(resolve(sbx.hibernate()))["state"] == "hibernated" and sbx.state == "hibernated"
    server.on("sandboxes.resume", httpx.Response(200, json=record("active")))
    assert run(resolve(sbx.resume()))["state"] == "active"
    server.on("sandboxes.update", httpx.Response(200, json=record()))
    run(resolve(sbx.update(name="n", idle_ttl_seconds=60)))
    assert server.last.json() == {"name": "n", "idleTtlSeconds": 60}
    server.on("sandboxes.getInfo", httpx.Response(200, json=record("recovery_required")))
    assert run(resolve(sbx.refresh()))["state"] == "recovery_required" and sbx.info["name"] == "n"
    assert [s.name for s in server.seen] == ["sandboxes.hibernate", "sandboxes.resume", "sandboxes.update",
                                            "sandboxes.getInfo"]


@pytest.mark.parametrize("mode", MODES)
def test_delete_is_idempotent_from_the_callers_view(mode):
    server = MockServer()
    sbx = handle(server, mode)
    server.on("sandboxes.kill", httpx.Response(200, json=record("destroyed")))
    assert run(resolve(sbx.delete()))["state"] == "destroyed"
    server.on("sandboxes.kill", error(404, "not_found"))
    assert run(resolve(sbx.delete()))["state"] == "destroyed"
    assert len(server.seen) == 2


@pytest.mark.parametrize("mode", MODES)
def test_the_context_manager_deletes_on_exit(mode):
    server = MockServer()
    run(enter_exit(handle(server, mode), mode))
    assert [s.name for s in server.seen] == ["sandboxes.kill"]


@pytest.mark.parametrize("mode", MODES)
def test_a_failed_delete_never_hides_the_bodys_exception(mode):
    server = MockServer()
    server.on("sandboxes.kill", error(503, "unavailable"))
    with pytest.raises(KeyError) as caught:
        run(enter_exit(handle(server, mode), mode, KeyError("body")))
    assert server.seen and all(seen.name == "sandboxes.kill" for seen in server.seen)
    if hasattr(caught.value, "add_note"):  # Python 3.11+: the failed delete is noted on it
        assert any("deleting sandbox" in note for note in caught.value.__notes__)


@pytest.mark.parametrize("mode", MODES)
def test_a_failed_delete_after_a_clean_body_raises(mode):
    server = MockServer()
    server.on("sandboxes.kill", error(503, "unavailable"))
    with pytest.raises(UnavailableError):
        run(enter_exit(handle(server, mode), mode))


@pytest.mark.parametrize("mode", MODES)
def test_list_returns_handles_and_caps(mode, monkeypatch):
    server = MockServer()
    body = {"schemaVersion": "omega-workspace-sandboxes/v1", "caps": {"maxActiveSandboxes": 3},
            "sandboxes": [{"id": SBX, "state": "active"}, {"id": OTHER, "state": "hibernated"}]}
    server.on("sandboxes.list", httpx.Response(200, json=body))
    from_env(monkeypatch, server)
    cls = AsyncSandbox if mode == "async" else Sandbox
    found = run(resolve(cls.list()))
    assert isinstance(found, SandboxList) and found.caps == {"maxActiveSandboxes": 3}
    assert [(s.id, s.state, type(s)) for s in found.sandboxes] == [(SBX, "active", cls), (OTHER, "hibernated", cls)]
    settings = run(resolve(cls.settings()))
    assert "caps" in settings and server.last.name == "sandboxes.settings.get"
    assert "Console" in cls.settings.__doc__ and "signed-in session" in cls.settings.__doc__


@pytest.mark.parametrize("mode", MODES)
def test_create_maps_every_field(mode, monkeypatch):
    server = MockServer()
    from_env(monkeypatch, server)
    cls = AsyncSandbox if mode == "async" else Sandbox
    run(resolve(cls.create(
        name="n", template="python", size="small", image="img", environment_id="env_1",
        limits={"cpus": 1}, network="none", network_policy={"mode": "off"}, idle_ttl_seconds=300,
    )))
    assert server.last.json() == {
        "name": "n", "template": "python", "size": "small", "image": "img", "environmentId": "env_1",
        "limits": {"cpus": 1}, "network": "none", "networkPolicy": {"mode": "off"}, "idleTtlSeconds": 300,
    }


@pytest.mark.parametrize("mode", MODES)
def test_restore_returns_a_new_sandbox_and_leaves_the_source(mode):
    server = MockServer()
    sbx = handle(server, mode)
    server.on("sandboxes.snapshots.restore", httpx.Response(201, json=record(ident=OTHER)))
    restored = run(resolve(sbx.snapshots.restore(SNAP, name="copy")))
    assert restored is not sbx and restored.id == OTHER and sbx.id == SBX and sbx.state == "active"
    assert server.last.json() == {"name": "copy"}
    snap = {"id": SNAP, "sandboxId": SBX}
    server.on("sandboxes.snapshots.create", httpx.Response(201, json={"snapshot": snap}))
    assert run(resolve(sbx.snapshots.create())) == snap
    server.on("sandboxes.snapshots.list", httpx.Response(200, json={"snapshots": [snap]}))
    assert run(resolve(sbx.snapshots.list())) == [snap]


@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("encoding,content,expected", [
    ("utf8", "héllo", "héllo"),
    ("base64", base64.b64encode(b"\x00\xff").decode(), b"\x00\xff"),
])
def test_files_read_returns_str_or_bytes(mode, encoding, content, expected):
    server = MockServer()
    file = {"outcome": "content", "path": "a", "encoding": encoding, "content": content, "bytes": 2, "truncated": False}
    server.on("sandboxes.files.read", httpx.Response(200, json={"file": file}))
    assert run(resolve(handle(server, mode).files.read("a", max_bytes=2))) == expected


@pytest.mark.parametrize("mode", MODES)
def test_files_write_upload_and_the_path_helpers(mode, tmp_path):
    server = MockServer()
    files = handle(server, mode).files
    run(resolve(files.write("a.txt", "hi")))
    assert server.last.json() == {"content": "hi", "encoding": "utf8"}
    run(resolve(files.write("a.bin", b"\x00")))
    assert server.last.json() == {"content": "AA==", "encoding": "base64"}
    local = tmp_path / "in.bin"
    local.write_bytes(b"from-path")
    for data, sent in ((b"raw", b"raw"), (local, b"from-path"), (io.BytesIO(b"from-file"), b"from-file")):
        run(resolve(files.upload("dir/x.bin", data)))
        assert server.last.name == "sandboxes.files.upload" and server.last.body == sent
    server.on("sandboxes.files.list", httpx.Response(200, json={"path": ".", "entries": [{"name": "x"}]}))
    assert run(resolve(files.list())) == [{"name": "x"}]
    assert dict(server.last.request.url.params) == {}  # the root: no path (the route refuses ".")
    run(resolve(files.remove("old")))
    assert "recursive" not in server.last.request.url.params
    run(resolve(files.remove("tree", recursive=True)))
    assert server.last.request.url.params["recursive"] == "true"
    run(resolve(files.move("a", "b")))
    assert server.last.json() == {"from": "a", "to": "b"}
    run(resolve(files.make_dir("d")))
    assert server.last.name == "sandboxes.files.makeDir"


@pytest.mark.parametrize("mode", MODES)
def test_download_to_renames_only_a_complete_file(mode, tmp_path):
    server = MockServer()
    files = handle(server, mode).files
    target = tmp_path / "out.bin"
    server.on("sandboxes.files.download", httpx.Response(200, content=b"complete"))
    assert run(resolve(files.download_to("a.bin", target))) == str(target)
    assert target.read_bytes() == b"complete"
    assert run(resolve(files.download("a.bin"))) == b"complete"

    from ._sandbox_mock import Chunks

    broken = Chunks([b"half"], fail=httpx.ReadError("reset"))
    server.on("sandboxes.files.download", lambda r: httpx.Response(200, stream=broken))
    with pytest.raises(SandboxConnectionError):
        run(resolve(files.download_to("a.bin", tmp_path / "partial.bin")))
    assert sorted(p.name for p in tmp_path.iterdir()) == ["out.bin"]  # no partial, no temp file
    server.on("sandboxes.files.download", error(404, "not_found"))
    with pytest.raises(NotFoundError):
        run(resolve(files.download_to("gone.bin", tmp_path / "gone.bin")))
    assert not (tmp_path / "gone.bin").exists()


POLICY = {"policy": {"desired": {"mode": "off"}, "desiredRevision": 4, "appliedRevision": 4, "applyStatus": "applied"}}


@pytest.mark.parametrize("mode", MODES)
def test_network_policy_get_returns_the_policy_with_its_etag_header(mode):
    server = MockServer()
    server.on("sandboxes.networkPolicy.get", httpx.Response(200, json=POLICY, headers={"ETag": '"9"'}))
    info = run(resolve(handle(server, mode).network_policy.get()))
    assert isinstance(info, NetworkPolicyInfo) and info.etag == '"9"'  # the header, not the body
    assert info.policy["desiredRevision"] == 4 and info.raw == POLICY
    server.on("sandboxes.networkPolicy.get", httpx.Response(200, json=POLICY))
    assert run(resolve(handle(server, mode).network_policy.get())).etag == '"4"'  # no header: the revision


@pytest.mark.parametrize("mode", MODES)
def test_network_policy_set_reads_the_etag_first_unless_given(mode):
    server = MockServer()
    policy = handle(server, mode).network_policy
    server.on("sandboxes.networkPolicy.get", httpx.Response(200, json=POLICY, headers={"ETag": '"4"'}))
    info = run(resolve(policy.set({"mode": "allow-all-public"})))
    assert [s.name for s in server.seen] == ["sandboxes.networkPolicy.get", "sandboxes.networkPolicy.update"]
    assert server.last.request.headers["if-match"] == '"4"'
    assert server.last.json() == {"mode": "allow-all-public"}
    assert isinstance(info, NetworkPolicyInfo) and info.etag == ETAG  # the PUT's own ETag
    run(resolve(policy.set({"mode": "off"}, if_match='"5"')))
    assert server.last.request.headers["if-match"] == '"5"' and len(server.seen) == 3
    run(resolve(policy.set({"mode": "off"}, if_match=6)))
    assert server.last.request.headers["if-match"] == '"6"' and len(server.seen) == 4


@pytest.mark.parametrize("mode", MODES)
def test_a_stale_etag_is_a_conflict_and_is_never_retried(mode):
    server = MockServer()
    stale = httpx.Response(412, json={"code": "network_policy_revision_mismatch", "message": "stale revision"})
    server.on("sandboxes.networkPolicy.update", stale)
    with pytest.raises(ConflictError) as caught:
        run(resolve(handle(server, mode).network_policy.set({"mode": "off"})))
    assert caught.value.code == "network_policy_revision_mismatch" and caught.value.status == 412
    assert [s.name for s in server.seen] == ["sandboxes.networkPolicy.get", "sandboxes.networkPolicy.update"]


@pytest.mark.parametrize("mode", MODES)
def test_activity_returns_the_entries(mode):
    server = MockServer()
    entries = [{"at": "2", "verb": "exec"}, {"at": "1", "verb": "create"}]
    server.on("sandboxes.activity.list", httpx.Response(200, json={"activity": entries}))
    assert run(resolve(handle(server, mode).activity())) == entries
