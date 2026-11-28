"""``fi.experiments.sandbox.sandbox_task``: one trial over the frozen-OpenAPI mock sandbox server.

Handles are built from the environment (a self-managed EE on loopback, Bearer), with the mock as the
transport, and the task closure is called directly with a real ``TaskContext``. The mock's exec route
refuses an absolute ``cwd`` with a 400, and its files routes an absolute or dotted path, as the sandbox
service does. The quota wait runs on a fake clock. Fake credentials only.
"""

from __future__ import annotations

import asyncio
import json
from urllib.parse import unquote

import httpx
import pytest

from fi.experiments._context import TaskContext
from fi.experiments._log_results import RecordedTrialError
from fi.experiments.errors import UsageError
from fi.experiments.sandbox import EVAL_DIR, SandboxEval, sandbox_task
from fi.experiments.sandbox import _task
from fi.sandbox import _connection
from fi.sandbox.errors import CommandIncompleteError, ConfigurationError, ConnectionError, QuotaExceededError
from fi.sandbox.errors import ValidationError
from tests.platform._sandbox_mock import EXEC, EXIT0, FAKE_KEY, FAKE_SECRET, FAKE_TOKEN, SBX, MockServer, error, example
from tests.platform._sandbox_mock import sse, stream_response
from tests.sandbox_integrations._strict_exec import strict

LOCAL = "http://127.0.0.1:8787"
ENV = ("OMEGA_BASE_URL", "FI_API_KEY", "FI_SECRET_KEY", "FUTUREAGI_OMEGA_API_KEY", "OMEGA_OS_API_KEY",
       "FI_WORKSPACE_ID", "FI_ORGANIZATION_ID", "FI_ALLOW_INSECURE_HTTP", "FI_BASE_URL",
       "FI_PLATFORM_BASE_URL", "FI_PLATFORM_TOKEN", "FI_ALLOW_CUSTOM_PLATFORM_URL", "FI_EXTRA_HEADERS")
STARTED = ("started", {"execId": EXEC, "sandboxId": SBX})


# ---- shared with test_sandbox_runner.py --------------------------------------------------------


@pytest.fixture(name="sandbox_env")
def sandbox_env_fixture(monkeypatch):
    """A self-managed EE on loopback (Bearer) with the mock as its transport; settings allow 2 sandboxes
    and an hour per command; the reward file is missing unless a test answers it; an absolute cwd or
    files path gets the service's 400."""
    mock = strict(MockServer())
    for name in ENV:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("OMEGA_BASE_URL", LOCAL)
    monkeypatch.setenv("FUTUREAGI_OMEGA_API_KEY", FAKE_TOKEN)
    monkeypatch.setattr(_connection, "default_transport", mock.transport)
    mock.on("sandboxes.settings.get", settings_answer(mock))
    mock.on("sandboxes.files.read", lambda request: error(404, "not_found"))
    return mock


def settings_answer(server, max_active=2, longest=3600):
    body = example(server.spec, server.routes["sandboxes.settings.get"].schema)
    body["caps"]["maxActiveSandboxes"] = max_active
    body["caps"]["exec"]["maxTimeoutSeconds"] = longest
    return lambda request: httpx.Response(200, json=body)


def exit_frame(code=0, **extra):
    return ("exit", {**EXIT0, "exitCode": code, **extra})


def exec_answer(rule):
    """``rule(body) -> frames`` decides each command's stream from its request body."""
    return lambda request: stream_response(sse(STARTED, *rule(json.loads(request.read()))))


def file_answer(content):
    return lambda request: httpx.Response(200, json={"schemaVersion": "omega-workspace-sandboxes/v1", "file": {
        "outcome": "content", "path": "reward", "encoding": "utf8", "content": content,
        "bytes": len(content), "truncated": False}})


def sequence(*answers):
    """Answer each request with the next one; the last one repeats."""
    left = list(answers)
    return lambda request: (left.pop(0) if len(left) > 1 else left[0])(request)


def names(server):
    return [seen.name for seen in server.seen]


def bodies(server, name):
    return [seen.json() for seen in server.seen if seen.name == name]


def file_path(seen):
    """The path a files request carried in its URL, as the service reads it (relative to /workspace)."""
    raw = seen.request.url.raw_path.decode("ascii").split("?", 1)[0]
    return unquote(raw.split(f"/{SBX}/", 1)[1].split("/", 1)[1])


def file_paths(server, prefix="sandboxes.files."):
    return [(seen.name, file_path(seen)) for seen in server.seen if seen.name.startswith(prefix)]


def context(example_id="ex-1", trial=1):
    return TaskContext("run-1", example_id, trial, {})


def call(task, row=None, ctx=None):
    return asyncio.run(task(row if row is not None else {"q": 1}, ctx or context()))


class FakeClock:
    def __init__(self):
        self.now, self.slept = 1000.0, []

    def __call__(self):
        return self.now

    async def sleep(self, seconds):
        self.slept.append(seconds)
        self.now += seconds


@pytest.fixture(name="clock")
def clock_fixture(monkeypatch):
    clock = FakeClock()
    monkeypatch.setattr(_task, "_clock", clock)
    monkeypatch.setattr(_task, "_sleep", clock.sleep)
    return clock


QUOTA = lambda after: lambda request: httpx.Response(  # noqa: E731
    409, json={"code": "quota_exceeded", "message": "workspace limit"}, headers={"Retry-After": str(after)})
COMMAND = SandboxEval(agent_command="python3 /workspace/solve.py", verifier="bash /workspace/test.sh")


# ---- tests -------------------------------------------------------------------------------------


def test_create_name_and_body(sandbox_env):
    spec = SandboxEval(agent_command="true", template="python-data", size="small", image="img:1")
    task = sandbox_task(spec, batch_id="b1")
    call(task, ctx=context("x" * 100, 2))
    call(task, ctx=context("\U0001F600" * 60, 1))
    first, second = bodies(sandbox_env, "sandboxes.create")
    assert first == {"name": ("fi-eval-b1-" + "x" * 100)[:63], "template": "python-data", "size": "small",
                     "image": "img:1"}
    assert len(first["name"]) == 63 and second["name"].startswith("fi-eval-b1-")
    assert len(second["name"].encode("utf-8")) <= 120
    assert task.batch_id == "b1"


def test_row_file_and_files_written_before_agent(sandbox_env):
    spec = SandboxEval(agent_command="python3 /workspace/solve.py",
                       files=lambda row: {"/workspace/task.md": f"solve {row['q']}",
                                          "/workspace/data.bin": b"\x00\x01"})
    call(sandbox_task(spec), row={"q": 7})
    order = names(sandbox_env)
    writes = [s for s in sandbox_env.seen if s.name == "sandboxes.files.write"]
    assert order.index("sandboxes.commands.run") > max(i for i, n in enumerate(order) if n == "sandboxes.files.write")
    # the files routes take paths relative to /workspace: /workspace/task.md is sent as task.md
    assert [file_path(w) for w in writes] == [".fi-eval/row.json", "task.md", "data.bin"]
    assert EVAL_DIR == "/workspace/.fi-eval"
    assert json.loads(writes[0].json()["content"]) == {"data": {"q": 7}}
    assert writes[1].json() == {"content": "solve 7", "encoding": "utf8"}
    assert writes[2].json()["encoding"] == "base64"


@pytest.mark.parametrize("reward_path,sent", [
    (None, ".fi-eval/reward"),
    ("/workspace/out/score.json", "out/score.json"),
])
def test_reward_file_is_removed_and_read_relative_to_the_workspace(sandbox_env, reward_path, sent):
    given = {} if reward_path is None else {"reward_path": reward_path}
    out = call(sandbox_task(SandboxEval(agent_command="true", verifier="true", **given)))
    assert file_paths(sandbox_env) == [("sandboxes.files.write", ".fi-eval/row.json"),
                                       ("sandboxes.files.remove", sent), ("sandboxes.files.read", sent)]
    assert out["rewards"] == {"reward": 1.0} and out["deleted"] is True


NOT_UNDER_WORKSPACE = ["/tmp/task.md", "/workspace/../etc/task.md", "/workspace/a/./b.md", "/workspace/a\\b.md",
                       "/workspace/a\x00b.md", "/workspace", "/workspace/", "/workspacex/a.md", "task.md", 7]


@pytest.mark.parametrize("path", NOT_UNDER_WORKSPACE)
def test_a_files_key_outside_the_workspace_is_refused_when_the_spec_is_made(sandbox_env, path):
    with pytest.raises(UsageError) as info:
        SandboxEval(agent_command="true", files={"/workspace/ok.md": "ok", path: "x"})
    assert str(info.value).startswith(f"files= key {path!r} is not a file under /workspace: ")
    assert sandbox_env.seen == []  # no spec, so no trial: nothing was created or written


@pytest.mark.parametrize("path", NOT_UNDER_WORKSPACE)
def test_a_reward_path_outside_the_workspace_is_refused_when_the_spec_is_made(sandbox_env, path):
    with pytest.raises(UsageError) as info:
        SandboxEval(agent_command="true", verifier="true", reward_path=path)
    assert str(info.value).startswith(f"reward_path {path!r} is not a file under /workspace: ")
    assert sandbox_env.seen == []


def test_a_static_files_value_that_is_not_text_or_bytes_is_refused_when_the_spec_is_made():
    with pytest.raises(UsageError) as info:
        SandboxEval(agent_command="true", files={"/workspace/n.txt": 7})
    assert str(info.value) == "files= maps each path to text or bytes, not int (for '/workspace/n.txt')"


@pytest.mark.parametrize("path", ["/tmp/task.md", "/workspace/../etc/task.md", "/workspace/a\\b.md", "task.md"])
def test_a_files_key_from_a_function_is_refused_before_any_file_is_written(sandbox_env, path):
    spec = SandboxEval(agent_command="true", files=lambda row: {"/workspace/ok.md": "ok", path: "x"})
    with pytest.raises(UsageError) as info:
        call(sandbox_task(spec))
    assert str(info.value).startswith(f"files= key {path!r} is not a file under /workspace: ")
    assert file_paths(sandbox_env) == []  # not row.json, not ok.md
    assert "sandboxes.commands.run" not in names(sandbox_env)
    assert names(sandbox_env).count("sandboxes.kill") == 1


def test_agent_env_has_eval_names_and_no_fi_names(sandbox_env):
    spec = SandboxEval(agent_command="python3 /workspace/solve.py", env={"MODEL": "small-model"})
    call(sandbox_task(spec), ctx=context("ex-9", 3))
    (run,) = bodies(sandbox_env, "sandboxes.commands.run")
    assert run["env"] == {"MODEL": "small-model", "EVAL_ROW_FILE": EVAL_DIR + "/row.json", "EVAL_EXAMPLE_ID": "ex-9",
                          "EVAL_TRIAL": "3", "EVAL_RUN_ID": "run-1"}
    assert not any(name.startswith("FI_") for name in run["env"])
    assert "cwd" not in run and run["timeoutSeconds"] == 900  # /workspace itself: no cwd


@pytest.mark.parametrize("cwd,sent", [
    ("/workspace", None),
    ("/workspace/", None),
    (".", None),
    ("/workspace/app", "app"),
    ("/workspace/a/../b", "b"),
    ("app/", "app"),
    ("./app/src", "app/src"),
])
def test_agent_command_and_verifier_get_the_folder_relative_to_the_workspace(sandbox_env, cwd, sent):
    spec = SandboxEval(agent_command="python3 solve.py", verifier="bash test.sh", cwd=cwd)
    assert spec.command_cwd == sent
    out = call(sandbox_task(spec))
    agent, verifier = bodies(sandbox_env, "sandboxes.commands.run")
    assert agent["command"] == "python3 solve.py" and verifier["command"] == "bash test.sh"
    for body in (agent, verifier):
        assert body.get("cwd") == sent and ("cwd" in body) == (sent is not None)
    assert out["agent"]["shell_exit_code"] == 0 and out["verifier"]["shell_exit_code"] == 0
    assert out["rewards"] == {"reward": 1.0} and out["deleted"] is True


@pytest.mark.parametrize("cwd", ["/tmp", "/", "/workspacex", "/workspace/../etc", "..", "../x", "app/../../x", 7])
def test_a_folder_outside_the_workspace_is_refused_when_the_spec_is_made(cwd):
    with pytest.raises(UsageError, match="cwd"):
        SandboxEval(agent_command="true", cwd=cwd)


def test_the_mock_refuses_an_absolute_cwd_as_the_service_does(sandbox_env):
    async def agent(row, sbx, ctx):
        with pytest.raises(ValidationError):
            await sbx.commands.run("pwd", cwd="/workspace")
        return (await sbx.commands.run("pwd", cwd="app")).exit_code

    out = call(sandbox_task(SandboxEval(agent=agent)))
    assert out["agent"] == {"result": 0}
    assert [b.get("cwd") for b in bodies(sandbox_env, "sandboxes.commands.run")] == ["/workspace", "app"]


def test_refused_env_name_raises_and_deletes(sandbox_env):
    spec = SandboxEval(agent_command="true", env=lambda row, ctx: {"FI_API_KEY": FAKE_KEY})
    with pytest.raises(ConfigurationError) as info:
        call(sandbox_task(spec))
    assert info.value.code == "secret_in_env" and FAKE_KEY not in str(info.value)
    assert "sandboxes.commands.run" not in names(sandbox_env)
    assert names(sandbox_env).count("sandboxes.kill") == 1


def test_verifier_runs_after_agent(sandbox_env):
    sandbox_env.on("sandboxes.commands.run", exec_answer(
        lambda body: [("stdout", {"data": "solved\n"}), exit_frame(0)] if "solve" in body["command"]
        else [exit_frame(None, signal="SIGKILL")]))
    out = call(sandbox_task(COMMAND))
    agent, verifier = bodies(sandbox_env, "sandboxes.commands.run")
    assert agent["command"] == "python3 /workspace/solve.py" and verifier["command"] == "bash /workspace/test.sh"
    assert verifier["timeoutSeconds"] == 300
    assert out["agent"]["stdout_tail"] == "solved\n" and out["agent"]["shell_exit_code"] == 0
    assert out["verifier"]["exit_code"] is None and out["verifier"]["shell_exit_code"] == 137
    assert out["rewards"] == {"reward": 0.0} and out["deleted"] is True and out["sandbox_id"] == SBX


@pytest.mark.parametrize("content, verifier_code, rewards", [
    ('{"reward": 0.5, "style": 1}', 0, {"reward": 0.5, "style": 1.0}),
    ("1\n", 1, {"reward": 1.0}),
    (None, 0, {"reward": 1.0}),
    (None, 3, {"reward": 0.0}),
])
def test_reward_from_json_from_number_and_from_exit_code(sandbox_env, content, verifier_code, rewards):
    if content is not None:
        sandbox_env.on("sandboxes.files.read", file_answer(content))
    sandbox_env.on("sandboxes.commands.run", exec_answer(
        lambda body: [exit_frame(verifier_code if "test.sh" in body["command"] else 0)]))
    out = call(sandbox_task(COMMAND))
    assert out["rewards"] == rewards and "reward_error" not in out
    read = [s for s in sandbox_env.seen if s.name == "sandboxes.files.read"][0]
    assert "reward" in str(read.request.url)


def test_reward_file_left_by_the_agent_is_removed_before_the_verifier(sandbox_env):
    stored = {}

    def write(request):  # None: the mock's default answer
        if "reward" in str(request.url):
            stored["reward"] = json.loads(request.read())["content"]

    def remove(request):
        if "reward" in str(request.url) and stored.pop("reward", None) is None:
            return error(404, "not_found")
        return None

    def read(request):
        return file_answer(stored["reward"])(request) if "reward" in stored else error(404, "not_found")

    sandbox_env.on("sandboxes.files.write", write)
    sandbox_env.on("sandboxes.files.remove", remove)
    sandbox_env.on("sandboxes.files.read", read)
    sandbox_env.on("sandboxes.commands.run", exec_answer(lambda body: [exit_frame(1)]))

    async def cheats(row, sbx, ctx):
        await sbx.files.write(EVAL_DIR + "/reward", "1")

    out = call(sandbox_task(SandboxEval(agent=cheats, verifier="bash /workspace/test.sh")))
    assert out["rewards"] == {"reward": 0.0} and "reward_error" not in out and out["deleted"] is True
    seen = sandbox_env.seen
    planted = max(i for i, s in enumerate(seen) if s.name == "sandboxes.files.write" and "reward" in str(s.request.url))
    removed = [i for i, s in enumerate(seen) if s.name == "sandboxes.files.remove"]
    verifier = [i for i, s in enumerate(seen) if s.name == "sandboxes.commands.run"]
    assert len(removed) == 1 and len(verifier) == 1 and planted < removed[0] < verifier[0]
    assert "reward" in str(seen[removed[0]].request.url)

    async def honest(row, sbx, ctx):  # nothing to remove: the 404 is ignored
        return None

    out = call(sandbox_task(SandboxEval(agent=honest, verifier="bash /workspace/test.sh")))
    assert out["rewards"] == {"reward": 0.0} and out["deleted"] is True


def test_reward_file_that_is_not_a_number_is_reported(sandbox_env):
    sandbox_env.on("sandboxes.files.read", file_answer('{"reward": "high"}'))
    out = call(sandbox_task(COMMAND))
    assert out["rewards"] == {} and "neither a number" in out["reward_error"]


def test_agent_callable_mode_gets_sandbox_and_ctx(sandbox_env):
    got = {}

    async def agent(row, sbx, ctx):
        got.update(row=row, sbx=sbx.id, ctx=ctx)
        await sbx.files.write("/workspace/answer.txt", "42")
        return {"answer": 42}

    ctx = context()
    out = asyncio.run(sandbox_task(SandboxEval(agent=agent, verifier="python3 check.py"))({"q": 1}, ctx))
    assert got == {"row": {"q": 1}, "sbx": SBX, "ctx": ctx}
    assert out["agent"] == {"result": {"answer": 42}}
    assert [b["command"] for b in bodies(sandbox_env, "sandboxes.commands.run")] == ["python3 check.py"]
    assert set(out["phases_ms"]) == {"create", "setup", "agent", "verify", "delete"}


def test_delete_on_agent_raise_incomplete_stream_and_cancel(sandbox_env):
    async def boom(row, sbx, ctx):
        raise ValueError("agent failed")

    with pytest.raises(ValueError):
        call(sandbox_task(SandboxEval(agent=boom)))
    assert names(sandbox_env).count("sandboxes.kill") == 1

    sandbox_env.on("sandboxes.commands.run", exec_answer(lambda body: [("stdout", {"data": "part"})]))
    with pytest.raises(CommandIncompleteError):
        call(sandbox_task(SandboxEval(agent_command="true", verifier="true")))
    assert names(sandbox_env).count("sandboxes.kill") == 2
    assert names(sandbox_env).count("sandboxes.commands.run") == 1  # no retry or verifier command

    async def stops(row, sbx, ctx):
        ctx.cancelled.set()  # what the engine sets on a timeout or Ctrl-C

    with pytest.raises(RecordedTrialError) as info:
        call(sandbox_task(SandboxEval(agent=stops, verifier="true")))
    assert info.value.error_type == "cancelled" and names(sandbox_env).count("sandboxes.kill") == 3
    assert names(sandbox_env).count("sandboxes.commands.run") == 1

    async def cancel_it():
        started = asyncio.Event()

        async def hangs(row, sbx, ctx):
            started.set()
            await asyncio.Event().wait()

        trial = asyncio.ensure_future(sandbox_task(SandboxEval(agent=hangs))({"q": 1}, context()))
        await asyncio.wait_for(started.wait(), timeout=5)
        trial.cancel()  # an engine timeout or Ctrl-C
        with pytest.raises(asyncio.CancelledError):
            await trial

    asyncio.run(cancel_it())
    assert names(sandbox_env).count("sandboxes.kill") == 4


def test_quota_409_waits_then_creates_once_more(sandbox_env, clock):
    sandbox_env.on("sandboxes.create", sequence(QUOTA(7), lambda request: httpx.Response(
        201, json=example(sandbox_env.spec, sandbox_env.routes["sandboxes.create"].schema))))
    out = call(sandbox_task(SandboxEval(agent_command="true")))
    assert names(sandbox_env).count("sandboxes.create") == 2 and out["deleted"] is True
    assert sum(clock.slept) == pytest.approx(7.0)


def test_quota_wait_exhausted_raises_without_more_creates(sandbox_env, clock):
    sandbox_env.on("sandboxes.create", QUOTA(4))
    with pytest.raises(QuotaExceededError):
        call(sandbox_task(SandboxEval(agent_command="true"), quota_wait_s=10))
    assert names(sandbox_env).count("sandboxes.create") == 4  # at 0, 4, 8 and 10 seconds
    assert sum(clock.slept) == pytest.approx(10.0) and "sandboxes.kill" not in names(sandbox_env)
    with pytest.raises(QuotaExceededError):
        call(sandbox_task(SandboxEval(agent_command="true"), quota_wait_s=0))
    assert names(sandbox_env).count("sandboxes.create") == 5


def test_connection_error_on_create_no_second_create(sandbox_env):
    def drop(request):
        raise httpx.ReadError("connection dropped")

    sandbox_env.on("sandboxes.create", drop)
    with pytest.raises(ConnectionError) as info:
        call(sandbox_task(SandboxEval(agent_command="true")))
    assert "sweep deletes it" in str(info.value)
    assert names(sandbox_env).count("sandboxes.create") == 1 and "sandboxes.kill" not in names(sandbox_env)


def test_transient_server_error_is_recorded_so_the_engine_does_not_rerun_it(sandbox_env):
    sandbox_env.on("sandboxes.create", lambda request: error(503, "unavailable"))
    with pytest.raises(RecordedTrialError) as info:
        call(sandbox_task(SandboxEval(agent_command="true")))
    assert info.value.error_type == "UnavailableError"
    assert names(sandbox_env).count("sandboxes.create") == 1


def test_agent_own_transient_error_keeps_the_engine_handling(sandbox_env):
    class Throttled(Exception):  # what a model client's 429 looks like to the engine
        status_code = 429

    async def agent(row, sbx, ctx):
        raise Throttled("model rate limit")

    with pytest.raises(Throttled):  # not a RecordedTrialError: the engine's backoff and limiter apply
        call(sandbox_task(SandboxEval(agent=agent)))
    assert names(sandbox_env).count("sandboxes.kill") == 1


def test_slot_gate_never_exceeds_max_active(sandbox_env):
    async def agent(row, sbx, ctx):
        await asyncio.sleep(0.01)

    task = sandbox_task(SandboxEval(agent=agent), max_active=2)

    async def many():
        await asyncio.gather(*(task({"q": i}, context(f"ex-{i}")) for i in range(6)))

    asyncio.run(many())
    alive, peak = 0, 0
    for name in names(sandbox_env):
        alive += {"sandboxes.create": 1, "sandboxes.kill": -1}.get(name, 0)
        peak = max(peak, alive)
    assert peak == 2 and alive == 0 and names(sandbox_env).count("sandboxes.create") == 6


def test_max_active_from_settings_caps_else_2(sandbox_env):
    sandbox_env.on("sandboxes.settings.get", settings_answer(sandbox_env, max_active=3, longest=1200))
    assert asyncio.run(sandbox_task(COMMAND).batch.limits()) == (3, 1200)
    assert asyncio.run(sandbox_task(COMMAND, max_active=5).batch.limits()) == (5, 1200)
    sandbox_env.on("sandboxes.settings.get", lambda request: error(404, "not_found"))
    assert asyncio.run(sandbox_task(COMMAND).batch.limits()) == (2, None)
    reads = names(sandbox_env).count("sandboxes.settings.get")
    task = sandbox_task(SandboxEval(agent_command="true"))
    call(task)
    call(task)
    assert names(sandbox_env).count("sandboxes.settings.get") == reads + 1  # read once per task


def test_timeout_above_the_workspace_maximum_is_refused_before_create(sandbox_env):
    sandbox_env.on("sandboxes.settings.get", settings_answer(sandbox_env, longest=600))
    with pytest.raises(ConfigurationError) as info:
        call(sandbox_task(SandboxEval(agent_command="true", agent_timeout_s=900)))
    assert info.value.code == "timeout_above_cap" and "sandboxes.create" not in names(sandbox_env)


def test_sweep_deletes_only_this_batch(sandbox_env, capsys):
    record = example(sandbox_env.spec, sandbox_env.routes["sandboxes.list"].schema)
    template = record["sandboxes"][0]
    ids = ["sbx_" + c * 24 for c in "1234"]
    record["sandboxes"] = [
        {**template, "id": ids[0], "name": "fi-eval-b1-ex-1-1", "state": "active"},
        {**template, "id": ids[1], "name": "fi-eval-b1-ex-2-1", "state": "destroyed"},
        {**template, "id": ids[2], "name": "fi-eval-b2-ex-1-1", "state": "active"},
        {**template, "id": ids[3], "name": "mine", "state": "active"},
    ]
    sandbox_env.on("sandboxes.list", lambda request: httpx.Response(200, json=record))
    task = sandbox_task(SandboxEval(agent_command="true"), batch_id="b1")
    assert asyncio.run(task.sweep()) == [ids[0]]
    kills = [str(s.request.url) for s in sandbox_env.seen if s.name == "sandboxes.kill"]
    assert len(kills) == 1 and ids[0] in kills[0]
    assert capsys.readouterr().err.count("deleted leftover sandbox") == 1


def test_output_has_no_secret_and_no_env_values(sandbox_env):
    spec = SandboxEval(agent_command="python3 solve.py", verifier="true", env={"MY_SETTING": "plain-value-xyz"})
    out = call(sandbox_task(spec))
    text = json.dumps(out)
    for secret in (FAKE_KEY, FAKE_SECRET, FAKE_TOKEN, "plain-value-xyz"):
        assert secret not in text
    assert all(b["env"]["MY_SETTING"] == "plain-value-xyz" for b in bodies(sandbox_env, "sandboxes.commands.run"))


def test_spec_refuses_two_agents_and_bad_timeouts():
    for kwargs in ({}, {"agent_command": "a", "agent": lambda r, s, c: None},
                   {"agent_command": "a", "agent_timeout_s": 0}, {"agent_command": "a", "cwd": "/tmp"},
                   {"agent_command": "a", "reward_path": "reward"}, {"agent_command": "a", "name_prefix": ""}):
        with pytest.raises(UsageError):
            SandboxEval(**kwargs)
    assert SandboxEval(agent_command="a", agent_timeout_s=3600).mode == "command"
