"""Process-level behaviour: Ctrl-C flushes the journal and raises RunInterrupted; a timed-out sync
task's thread never holds the interpreter at exit."""

import json
import os
import signal
import subprocess
import sys
import textwrap
import time
from pathlib import Path

import pytest

pytestmark = pytest.mark.skipif(sys.platform == "win32", reason="POSIX signals")


def _child_env(tmp_path):
    env = {k: v for k, v in os.environ.items() if not k.startswith("FI_")}
    env.update(FI_BASE_URL="http://127.0.0.1:9", FI_RUN_DIR=str(tmp_path / "runs"), PYTHONUNBUFFERED="1")
    return env


def test_ctrl_c_flushes_journal_and_raises_run_interrupted(tmp_path):
    script = textwrap.dedent(
        """
        import signal, sys, time
        signal.signal(signal.SIGINT, signal.default_int_handler)  # a job started by memcap.sh ignores SIGINT
        from fi import experiments
        from fi.experiments.errors import RunInterrupted
        rows = [{"id": f"T{i}", "q": i} for i in range(40)]
        def task(row):
            if row["q"] == 3:
                print("READY", flush=True)
            time.sleep(0.2)
            return row["q"]
        try:
            experiments.run(rows, task, upload=False, progress=False, concurrency=1)
        except RunInterrupted as exc:
            print(f"INTERRUPTED {exc.run_id} {exc.done} {exc.total}", flush=True)
            sys.exit(4)
        print("NOT INTERRUPTED", flush=True)
        """
    )
    proc = subprocess.Popen([sys.executable, "-c", script], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            text=True, env=_child_env(tmp_path), cwd=tmp_path)
    for line in proc.stdout:
        if line.startswith("READY"):
            break
    time.sleep(0.1)
    proc.send_signal(signal.SIGINT)
    out, err = proc.communicate(timeout=30)
    assert proc.returncode == 4, (out, err)
    _, run_id, done, total = out.strip().splitlines()[-1].split()
    assert int(total) == 40 and 3 <= int(done) < 40
    lines = (tmp_path / "runs" / run_id / "journal.jsonl").read_text().splitlines()
    assert len(lines) == int(done)  # every finished trial was flushed before the raise
    assert all(json.loads(l)["status"] == "completed" for l in lines)
    assert not (tmp_path / "runs" / run_id / "lock").exists()


def test_timed_out_sync_thread_does_not_hold_exit(tmp_path):
    script = textwrap.dedent(
        """
        import time
        from fi import experiments
        def task(row):
            time.sleep(60)
        r = experiments.run([{"q": 1}], task, upload=False, progress=False, timeout_s=0.3)
        print(r.items[0].error.type, r.metadata["abandoned_threads"], flush=True)
        """
    )
    started = time.monotonic()
    out = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True, timeout=30,
                         env=_child_env(tmp_path), cwd=tmp_path)
    elapsed = time.monotonic() - started
    assert out.returncode == 0, out.stderr
    assert out.stdout.split() == ["timeout", "1"]
    assert elapsed < 5.0


def test_cli_interrupt_prints_a_resume_line_that_resumes(tmp_path):
    """The interrupt message is the real command (no literal `...`), selects the interrupted declared
    run with --filter, and running it finishes that run."""
    import shlex

    (tmp_path / "two_eval.py").write_text(textwrap.dedent(
        """
        import signal, time
        signal.signal(signal.SIGINT, signal.default_int_handler)  # a job started by memcap.sh ignores SIGINT
        from fi import experiments
        def slow(row):
            if row["q"] == 3:
                print("READY", flush=True)
            time.sleep(0.2)
            return row["q"]
        experiments.run([{"q": 0}], lambda row: 0, upload=False, name="first")
        experiments.run([{"id": f"T{i}", "q": i} for i in range(20)], slow, upload=False, name="second",
                        concurrency=1)
        """
    ))
    argv = ["run", "two_eval.py", "--no-trace", "--quiet"]
    proc = subprocess.Popen([sys.executable, "-m", "fi._cli.main", *argv], stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, text=True, env=_child_env(tmp_path), cwd=tmp_path)
    for line in proc.stdout:
        if line.startswith("READY"):
            break
    time.sleep(0.1)
    proc.send_signal(signal.SIGINT)
    out, err = proc.communicate(timeout=30)
    assert proc.returncode == 4, (out, err)
    line = err.strip().splitlines()[-1].strip()
    words = shlex.split(line)
    assert words[:5] == ["futureagi-py", "run", "two_eval.py", "--no-trace", "--quiet"] and "..." not in line
    assert words[5:7] == ["--filter", "second"] and words[7] == "--resume"
    resumed = subprocess.run([sys.executable, "-m", "fi._cli.main", *words[1:], "--json"], capture_output=True,
                             text=True, timeout=60, env=_child_env(tmp_path), cwd=tmp_path)
    assert resumed.returncode == 0, resumed.stderr
    doc = json.loads(resumed.stdout.strip().splitlines()[-1])  # the task may print READY again
    assert [r["label"] for r in doc["runs"]] == ["second"] and doc["runs"][0]["run_id"] == words[8]
    assert doc["runs"][0]["summary"]["completed"] == 20
