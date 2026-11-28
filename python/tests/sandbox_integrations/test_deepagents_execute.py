"""FutureAGISandbox.execute over the frozen-OpenAPI mock, with Deep Agents faked: the exit-code rule
(124 timed out, 128+N signal, 130 cancelled, 1 could not start), stderr tagged, a failure of the
call itself as a result (None when whether the command finished is unknown), one request per call,
the time limit read from the workspace's caps, the python3 check, the working folder sent relative
to /workspace (the mock's exec route refuses an absolute one, as the service does), and the import
guards (Python 3.10, a missing Deep Agents). Fake credentials only."""

from __future__ import annotations

import importlib
import inspect
import sys

import httpx
import pytest

from fi.errors import MissingExtraError
from fi.sandbox import ConfigurationError
from fi.sandbox.errors import ValidationError
from tests.platform._sandbox_mock import (
    EXEC,
    EXIT0,
    SBX,
    Chunks,
    MockServer,
    api,
    error,
    example,
    sse,
    stream_response,
)

from . import _fake_deepagents as fake

STARTED = ("started", {"execId": EXEC, "sandboxId": SBX})


@pytest.fixture(name="adapter")
def adapter_fixture(monkeypatch):
    fake.install(monkeypatch)
    return importlib.import_module(fake.ADAPTER)


def settings(server: MockServer, max_timeout: int = 900):
    """The workspace's sandbox settings with this exec maximum (a fresh response each time)."""
    body = example(server.spec, server.routes["sandboxes.settings.get"].schema)
    body["caps"]["exec"].update(maxTimeoutSeconds=max_timeout, defaultTimeoutSeconds=60)
    return lambda request: httpx.Response(200, json=body)


def make(adapter, server: MockServer, max_timeout: int = 900, **options):
    """A backend on a connected handle; the requests made to build it are forgotten."""
    server.on("sandboxes.settings.get", settings(server, max_timeout))
    sbx = api(server, "sync").connect(SBX)
    backend = adapter.FutureAGISandbox(sandbox=sbx, **options)
    server.seen.clear()
    return backend, sbx


def ending(server: MockServer, *frames, **exit_fields) -> None:
    body = sse(STARTED, *frames, ("exit", {**EXIT0, **exit_fields}))
    server.on("sandboxes.commands.run", lambda request: stream_response(body))


def runs(server: MockServer) -> list:
    return [seen for seen in server.seen if seen.name == "sandboxes.commands.run"]


def test_execute_declares_timeout_by_name(adapter):
    assert fake.execute_accepts_timeout(adapter.FutureAGISandbox) is True
    parameter = inspect.signature(adapter.FutureAGISandbox.execute).parameters["timeout"]
    assert parameter.kind is inspect.Parameter.KEYWORD_ONLY and parameter.default is None
    assert issubclass(adapter.FutureAGISandbox, fake.BaseSandbox)
    assert "grep" not in vars(adapter.FutureAGISandbox)  # the base class's grep is kept


def test_building_reads_the_exec_limit_and_checks_python3(adapter):
    server = MockServer()
    server.on("sandboxes.settings.get", settings(server))
    sbx = api(server, "sync").connect(SBX)
    backend = adapter.FutureAGISandbox(sandbox=sbx)
    assert [seen.name for seen in server.seen] == [
        "sandboxes.getInfo", "sandboxes.settings.get", "sandboxes.commands.run"]
    assert server.last.json() == {"command": "command -v python3", "timeoutSeconds": 30}  # no cwd: /workspace
    assert backend.id == SBX and backend.sandbox is sbx and backend.max_timeout == 900


def test_the_mock_exec_route_refuses_an_absolute_cwd_as_the_service_does():
    server = MockServer()
    sbx = api(server, "sync").connect(SBX)
    with pytest.raises(ValidationError):
        sbx.commands.run("pwd", cwd="/workspace")
    with pytest.raises(ValidationError):
        sbx.commands.run("pwd", cwd="src/../lib")
    assert sbx.commands.run("pwd", cwd="src").exit_code == 0
    assert sbx.commands.run("pwd").exit_code == 0


def test_the_python3_check_sends_no_cwd_whatever_the_workdir(adapter):
    """The PATH check detects python3 even when the working directory does not exist."""
    server = MockServer()
    server.on("sandboxes.settings.get", settings(server))
    sbx = api(server, "sync").connect(SBX)
    backend = adapter.FutureAGISandbox(sandbox=sbx, workdir="/workspace/not/made/yet")
    assert runs(server)[0].json() == {"command": "command -v python3", "timeoutSeconds": 30}
    server.seen.clear()
    backend.execute("pwd")
    assert runs(server)[0].json()["cwd"] == "not/made/yet"


def test_max_timeout_given_skips_the_settings_read(adapter):
    server = MockServer()
    sbx = api(server, "sync").connect(SBX)
    backend = adapter.FutureAGISandbox(sandbox=sbx, max_timeout=600)
    assert [seen.name for seen in server.seen] == ["sandboxes.getInfo", "sandboxes.commands.run"]
    assert backend.max_timeout == 600 and backend.timeout == 600
    server.seen.clear()
    backend.execute("x", timeout=0)
    backend.execute("x", timeout=45)
    assert [run.json()["timeoutSeconds"] for run in runs(server)] == [600, 45]


@pytest.mark.parametrize("given", [0, -1, True, 1.5, "900"])
def test_max_timeout_must_be_whole_seconds(adapter, given):
    server = MockServer()
    sbx = api(server, "sync").connect(SBX)
    with pytest.raises(ValueError, match="max_timeout"):
        adapter.FutureAGISandbox(sandbox=sbx, max_timeout=given)
    assert [seen.name for seen in server.seen] == ["sandboxes.getInfo"]


def test_a_sandbox_without_python3_is_refused(adapter):
    server = MockServer()
    server.on("sandboxes.settings.get", settings(server))
    sbx = api(server, "sync").connect(SBX)
    ending(server, exitCode=1)
    with pytest.raises(ConfigurationError) as caught:
        adapter.FutureAGISandbox(sandbox=sbx)
    assert caught.value.code == "python3_missing"
    assert "python3" in str(caught.value) and SBX in str(caught.value)


def test_exit_zero_stdout_only(adapter):
    server = MockServer()
    backend, _ = make(adapter, server)
    ending(server, ("stdout", {"data": "hello\n"}), stdoutBytes=6)
    response = backend.execute("echo hello")
    assert response == fake.ExecuteResponse(output="hello\n", exit_code=0, truncated=False)
    assert len(runs(server)) == 1


def test_nonzero_exit_passthrough(adapter):
    server = MockServer()
    backend, _ = make(adapter, server)
    ending(server, ("stdout", {"data": "partial"}), exitCode=3)
    response = backend.execute("false")
    assert response.exit_code == 3 and response.output == "partial" and response.truncated is False


def test_stderr_is_tagged(adapter):
    server = MockServer()
    backend, _ = make(adapter, server)
    ending(server, ("stdout", {"data": "out\n"}), ("stderr", {"data": "warn\n"}), exitCode=1)
    response = backend.execute("x")
    assert response.output == "out\n\n<stderr>warn\n</stderr>"
    assert response.output.endswith("\n<stderr>warn\n</stderr>") and response.exit_code == 1


def test_timed_out_maps_to_124_with_note_and_truncated_flag(adapter):
    server = MockServer()
    backend, _ = make(adapter, server)
    ending(server, ("stdout", {"data": "so far\n"}),
           exitCode=None, signal="SIGKILL", timedOut=True, truncated=True)
    response = backend.execute("sleep 99", timeout=30)
    assert response.exit_code == 124 and response.truncated is True
    assert response.output == "so far\nCommand timed out after 30 seconds"
    assert runs(server)[0].json()["timeoutSeconds"] == 30


def test_signal_kill_maps_to_137(adapter):
    server = MockServer()
    backend, _ = make(adapter, server)
    ending(server, exitCode=None, signal="SIGKILL")
    response = backend.execute("x")
    assert response.exit_code == 137 and response.output == "Command was ended by signal SIGKILL"


def test_cancelled_maps_to_130(adapter):
    server = MockServer()
    backend, _ = make(adapter, server)
    ending(server, exitCode=None, signal="SIGTERM", cancelled=True)
    response = backend.execute("x")
    assert response.exit_code == 130 and response.output == "Command was cancelled"


def test_spawn_error_maps_to_1(adapter):
    server = MockServer()
    backend, _ = make(adapter, server)
    ending(server, exitCode=None, error="spawn /bin/nope ENOENT")
    response = backend.execute("x")
    assert response.exit_code == 1
    assert response.output == "The command could not start: spawn /bin/nope ENOENT"


def test_unknown_signal_gives_none(adapter):
    server = MockServer()
    backend, _ = make(adapter, server)
    ending(server, exitCode=None, signal="SIGWEIRD")
    response = backend.execute("x")
    assert response.exit_code is None
    assert response.output == "Command ended without an exit code (SIGWEIRD)"


def test_missing_exit_frame_gives_none_exit_code_and_one_request(adapter):
    server = MockServer()
    backend, _ = make(adapter, server)
    body = sse(STARTED, ("stdout", {"data": "partial"}))
    server.on("sandboxes.commands.run",
              lambda request: stream_response(Chunks([body, b"event: exit\ndata: {"])))
    response = backend.execute("long")
    assert response.exit_code is None
    assert response.output.startswith("partial\nError: the connection ended before the command finished")
    assert "whether it finished is unknown" in response.output
    assert [seen.name for seen in server.seen] == ["sandboxes.commands.run"]  # a single execution attempt


def test_dropped_stream_is_not_retried(adapter):
    server = MockServer()
    backend, _ = make(adapter, server)
    server.on("sandboxes.commands.run",
              lambda request: stream_response(Chunks([sse(STARTED)], fail=httpx.ReadError("reset"))))
    response = backend.execute("long")
    assert response.exit_code is None and "unknown" in response.output
    assert len(server.seen) == 1


def test_error_frame_maps_to_1(adapter):
    server = MockServer()
    backend, _ = make(adapter, server)
    body = sse(STARTED, ("stdout", {"data": "a"}), ("error", {"message": "runtime died"}))
    server.on("sandboxes.commands.run", lambda request: stream_response(body))
    response = backend.execute("x")
    assert response.exit_code == 1
    assert response.output.startswith("a\nError executing command (CommandFailedError): ")
    assert "runtime died" in response.output and len(server.seen) == 1


def test_hibernated_409_message_names_resume(adapter):
    server = MockServer()
    backend, _ = make(adapter, server)
    server.on("sandboxes.commands.run",
              lambda request: error(409, "conflict", detail={"state": "hibernated"}))
    response = backend.execute("x")
    assert response.exit_code == 1
    assert response.output == (
        f"Error: sandbox {SBX} is hibernated; resume it (sbx.resume()) before running commands")
    assert [seen.name for seen in server.seen] == ["sandboxes.commands.run"]  # no resume, no retry


@pytest.mark.parametrize("status", [403, 429, 502, 503])
def test_other_refusals_are_results_and_never_retried(adapter, status):
    server = MockServer()
    backend, _ = make(adapter, server)
    server.on("sandboxes.commands.run", lambda request: error(status, "refused_here"))
    response = backend.execute("x")
    assert response.exit_code == 1
    assert response.output.startswith("Error executing command (")
    assert "refused_here" in response.output and len(server.seen) == 1


@pytest.mark.parametrize(("cap", "timeout", "sent"), [
    (900, 0, 900), (900, 5000, 900), (900, None, 900), (900, 45, 45),
    (3600, 0, 3600), (3600, 5000, 3600), (3600, None, 1800),
])
def test_timeout_zero_and_large_clamp_to_900(adapter, cap, timeout, sent):
    """0 and anything above the workspace's exec maximum (900 here, then 3600: it is read from the
    settings, not assumed) become that maximum; no timeout uses min(30 minutes, maximum)."""
    server = MockServer()
    backend, _ = make(adapter, server, max_timeout=cap)
    backend.execute("x", timeout=timeout)
    assert runs(server)[0].json()["timeoutSeconds"] == sent


def test_constructor_timeout_is_clamped_too(adapter):
    server = MockServer()
    backend, _ = make(adapter, server, timeout=0)
    assert backend.timeout == 900
    backend.execute("x")
    assert runs(server)[0].json()["timeoutSeconds"] == 900


def test_default_workdir_is_the_workspace_sent_as_no_cwd(adapter):
    server = MockServer()
    backend, _ = make(adapter, server)
    assert backend.execute("pwd").exit_code == 0
    assert runs(server)[0].json() == {"command": "pwd", "timeoutSeconds": 900}
    assert backend.workdir == "/workspace"


@pytest.mark.parametrize(("workdir", "folder", "cwd"), [
    ("/workspace/", "/workspace", None),
    (".", "/workspace", None),
    ("", "/workspace", None),
    ("/workspace/src", "/workspace/src", "src"),
    ("/workspace/./my proj/", "/workspace/my proj", "my proj"),
    ("/workspace/a/../b", "/workspace/b", "b"),
    ("//workspace/src", "/workspace/src", "src"),
    ("src", "/workspace/src", "src"),
    ("./src/lib/", "/workspace/src/lib", "src/lib"),
])
def test_workdir_is_sent_relative_to_the_workspace(adapter, workdir, folder, cwd):
    server = MockServer()
    backend, _ = make(adapter, server, workdir=workdir)
    assert backend.workdir == folder
    assert backend.execute("pwd").exit_code == 0
    body = runs(server)[0].json()
    assert body.get("cwd") == cwd and ("cwd" in body) == (cwd is not None)


@pytest.mark.parametrize("workdir", [
    "/tmp/job", "/", "/workspacex", "/workspace/..", "/workspace/../etc", "..", "../x", "src/../../x", None,
])
def test_workdir_outside_the_workspace_is_refused_before_any_request(adapter, workdir):
    server = MockServer()
    sbx = api(server, "sync").connect(SBX)
    with pytest.raises(ValueError, match="workdir"):
        adapter.FutureAGISandbox(sandbox=sbx, workdir=workdir)
    assert [seen.name for seen in server.seen] == ["sandboxes.getInfo"]  # the connect only


def test_configuration_error_propagates(adapter, monkeypatch):
    server = MockServer()
    backend, sbx = make(adapter, server)

    def refuse(*args, **kwargs):
        raise ConfigurationError("OMEGA_BASE_URL is not set", code="missing_base_url")

    monkeypatch.setattr(sbx.commands, "run", refuse)
    monkeypatch.setattr(sbx.files, "upload", refuse)
    monkeypatch.setattr(sbx.files, "make_dir", refuse)
    monkeypatch.setattr(sbx.files, "download", refuse)
    with pytest.raises(ConfigurationError):
        backend.execute("x")
    with pytest.raises(ConfigurationError):
        backend.upload_files([("/workspace/a.txt", b"a")])
    with pytest.raises(ConfigurationError):
        backend.download_files(["/workspace/a.txt"])
    assert server.seen == []


def test_exec_env_is_never_sent(adapter):
    server = MockServer()
    backend, _ = make(adapter, server)
    backend.execute("env")
    assert "env" not in runs(server)[0].json()


def test_missing_deepagents_raises_missing_extra(monkeypatch):
    fake.forget_adapter(monkeypatch)
    for name in fake.FAKE_MODULES:
        fake.forget_on_teardown(monkeypatch, name)
    monkeypatch.setattr(sys, "version_info", (3, 12, 0))
    monkeypatch.setitem(sys.modules, "deepagents", None)  # "not installed", even where it is
    with pytest.raises(MissingExtraError) as caught:
        importlib.import_module(fake.ADAPTER)
    assert caught.value.extra == "sandbox-deepagents"
    assert 'pip install "futureagi[sandbox-deepagents]"' in str(caught.value)


class _Watch:
    """A finder placed first on ``sys.meta_path`` that records any attempt to import Deep Agents."""

    def __init__(self) -> None:
        self.asked: list = []

    def find_spec(self, name, path=None, target=None):
        if name == "deepagents" or name.startswith("deepagents."):
            self.asked.append(name)
        return None


def test_python_310_raises_needs_python_311_not_install_hint(monkeypatch):
    fake.forget_adapter(monkeypatch)
    for name in fake.FAKE_MODULES:
        fake.forget_on_teardown(monkeypatch, name)
    watch = _Watch()
    monkeypatch.setattr(sys, "meta_path", [watch, *sys.meta_path])
    monkeypatch.setattr(sys, "version_info", (3, 10, 14))
    with pytest.raises(ImportError) as caught:
        importlib.import_module(fake.ADAPTER)
    text = str(caught.value)
    assert "needs Python 3.11+" in text
    assert "pip install" not in text and "sandbox-deepagents" not in text
    assert not isinstance(caught.value, MissingExtraError)
    assert watch.asked == [] and "deepagents" not in sys.modules
