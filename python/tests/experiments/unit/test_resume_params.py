"""A resume runs the rest of a run with the params it started with.

M2: since the recorded revision the printed resume line shows a credential param as ``api_key=[redacted]``; running the
line as printed resumed with exit 0 and handed the remaining trials the literal placeholder (probe
test_review_resume.py). A resume now refuses a placeholder (UsageError, exit 2) and names the param;
the interrupt message names the params to give again. S4: a resume with a changed param (another
model) mixed two configs in one run; it is refused too. No network, no model, no server."""

import json
import os
import shlex
import signal
import subprocess
import sys
import textwrap
import time
from pathlib import Path

import pytest

from fi import experiments
from fi.experiments._redact import REDACTED
from fi.experiments.errors import UsageError

FAKE = "plain-fake-value-no-shape-0042"  # a credential-named param with no known shape, in no env var
ROWS = [{"id": "a", "q": 1}, {"id": "b", "q": 2}]


def _run(params, **kw):
    return experiments.run(ROWS, lambda row: "ok", upload=False, progress=False, trace=False, params=params, **kw)


def test_a_resume_with_the_placeholder_is_refused_and_names_the_param():
    first = _run({"model": "m", "api_key": FAKE})
    with pytest.raises(UsageError) as info:
        _run({"model": "m", "api_key": REDACTED}, resume=first.run_id)
    msg = str(info.value)
    assert "param api_key is '[redacted]'" in msg and "Give the real value again" in msg
    assert "--param-str api_key=VALUE" in msg and info.value.exit_code == 2
    nested = _run({"cfg": {"azure_key": FAKE, "n": 2}})
    with pytest.raises(UsageError, match="param cfg is"):
        _run({"cfg": {"azure_key": REDACTED, "n": 2}}, resume=nested.run_id)


def test_a_resume_with_the_real_credential_resumes():
    first = _run({"model": "m", "api_key": FAKE, "max_tokens": 256})
    again = _run({"model": "m", "api_key": FAKE, "max_tokens": 256}, resume=first.run_id)
    assert again.run_id == first.run_id and [i.status for i in again.items] == ["completed", "completed"]


def test_a_value_redacted_by_shape_cannot_come_back_as_its_placeholder():
    """A param the run specification journaled redacted (here a bearer header) is refused when it comes back holding the
    placeholder, even inside a longer string; a literal "[redacted]" in prose that was never redacted is not."""
    header = "Bearer 9f8e7d6c5b4a39281706f5e4d3c2b1a0"
    first = _run({"header": header, "prompt": "mask names as [redacted]"})
    plan = json.loads((Path(first.journal_dir) / "plan.json").read_text())
    assert plan["redacted_params"] == ["header"] and plan["params"]["header"] == REDACTED
    with pytest.raises(UsageError, match="param header is"):
        _run({"header": f"x {REDACTED}", "prompt": "mask names as [redacted]"}, resume=first.run_id)
    again = _run({"header": header, "prompt": "mask names as [redacted]"}, resume=first.run_id)
    assert again.run_id == first.run_id


@pytest.mark.parametrize("changed, said", [
    ({"model": "other", "max_tokens": 256}, 'model is "other", the run has "m"'),
    ({"model": "m"}, "max_tokens is missing (the run has 256)"),
    ({"model": "m", "max_tokens": 256, "seed": 7}, "seed=7 is not in the run"),
])
def test_a_resume_with_changed_params_is_refused(changed, said):
    """S4: one run never mixes two configs."""
    first = _run({"model": "m", "max_tokens": 256})
    with pytest.raises(UsageError) as info:
        _run(changed, resume=first.run_id)
    assert "the params differ from the journaled run" in str(info.value) and said in str(info.value)


def test_a_value_the_journal_holds_redacted_is_not_compared():
    """A journal from wave 0 holds max_tokens as "[redacted]" (the substring rule); it still resumes."""
    first = _run({"model": "m", "max_tokens": 256})
    plan_path = Path(first.journal_dir) / "plan.json"
    plan = json.loads(plan_path.read_text())
    plan["params"]["max_tokens"] = REDACTED
    plan.pop("redacted_params", None)  # a wave-0 plan has no such key
    plan_path.write_text(json.dumps(plan))
    again = _run({"model": "m", "max_tokens": 256}, resume=first.run_id)
    assert again.run_id == first.run_id


def test_the_resume_line_names_the_values_it_hides():
    from fi.experiments._cli.commands import hidden_note, hidden_values

    argv = ["run", "a.py", "--param-str", f"api_key={FAKE}", "--param", "max_tokens=256", f"--token={FAKE}"]
    assert hidden_values(argv) == ["api_key", "token"]
    assert hidden_note(argv).startswith("The line below shows api_key, token as [redacted]")
    assert hidden_note(["run", "a.py", "--param", "max_tokens=256"]) == ""


def _child_env(tmp_path):
    env = {k: v for k, v in os.environ.items() if not k.startswith("FI_")}
    env.update(FI_BASE_URL="http://127.0.0.1:9", FI_RUN_DIR=str(tmp_path / "runs"), PYTHONUNBUFFERED="1",
               PROBE_OUT=str(tmp_path / "seen.jsonl"))
    return env


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX signals")
def test_the_printed_resume_line_refuses_the_placeholder_and_resumes_with_the_real_value(tmp_path):
    """The review's probe (test_review_resume.py): Ctrl-C a CLI run with --param-str api_key=VALUE, run the
    printed line as is (exit 2, names api_key, no trial runs), then with the real value (exit 0, one key)."""
    (tmp_path / "agent.py").write_text(textwrap.dedent(
        """
        import json, os, signal, time
        signal.signal(signal.SIGINT, signal.default_int_handler)  # a job started by memcap.sh ignores SIGINT
        from fi import experiments
        def task(row):
            with open(os.environ["PROBE_OUT"], "a") as f:
                f.write(json.dumps({"q": row["q"], "api_key": experiments.param("api_key")}) + "\\n")
            if row["q"] == 3:
                print("READY", flush=True)
            time.sleep(0.2)
            return row["q"]
        experiments.run([{"id": f"T{i}", "q": i} for i in range(12)], task, upload=False, name="probe",
                        concurrency=1)
        """
    ))
    argv = ["run", "agent.py", "--no-trace", "--quiet", "--param-str", f"api_key={FAKE}"]
    proc = subprocess.Popen([sys.executable, "-m", "fi._cli.main", *argv], stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, text=True, env=_child_env(tmp_path), cwd=tmp_path)
    for line in proc.stdout:
        if line.startswith("READY"):
            break
    time.sleep(0.1)
    proc.send_signal(signal.SIGINT)
    out, err = proc.communicate(timeout=30)
    assert proc.returncode == 4, (out, err)
    assert "The line below shows api_key as [redacted]: put the real value(s) back" in err
    line = err.strip().splitlines()[-1].strip()
    assert FAKE not in err and f"api_key={REDACTED}" in line
    words = shlex.split(line)
    seen_file = tmp_path / "seen.jsonl"
    before = len(seen_file.read_text().splitlines())
    as_printed = subprocess.run([sys.executable, "-m", "fi._cli.main", *words[1:], "--json"], capture_output=True,
                                text=True, timeout=60, env=_child_env(tmp_path), cwd=tmp_path)
    said = as_printed.stdout + as_printed.stderr  # --json: the error is the JSON document on stdout
    assert as_printed.returncode == 2, said
    assert "param api_key is '[redacted]'" in said and "Give the real value again" in said
    assert len(seen_file.read_text().splitlines()) == before  # no trial ran with the placeholder
    real = [w.replace(f"api_key={REDACTED}", f"api_key={FAKE}") for w in words[1:]]
    resumed = subprocess.run([sys.executable, "-m", "fi._cli.main", *real, "--json"], capture_output=True,
                             text=True, timeout=60, env=_child_env(tmp_path), cwd=tmp_path)
    assert resumed.returncode == 0, resumed.stderr
    doc = json.loads(resumed.stdout.strip().splitlines()[-1])
    assert doc["runs"][0]["run_id"] == words[-1] and doc["runs"][0]["summary"]["completed"] == 12
    seen = [json.loads(x) for x in seen_file.read_text().splitlines()]
    assert {s["api_key"] for s in seen} == {FAKE}  # one api_key throughout the run
