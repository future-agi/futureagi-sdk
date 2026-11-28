"""Without the experiments extra, `futureagi-py run` prints the install line and exits 3 (no traceback)."""

import subprocess
import sys
import textwrap


def test_missing_otel_prints_install_line_and_exits_3(tmp_path):
    (tmp_path / "agent.py").write_text("def task(row):\n    return 1\n")
    (tmp_path / "rows.jsonl").write_text('{"q": 1}\n')
    blocker = tmp_path / "block"
    blocker.mkdir()
    (blocker / "sitecustomize.py").write_text(textwrap.dedent(
        """
        import sys
        class _Block:
            def find_spec(self, name, path=None, target=None):
                if name == "opentelemetry" or name.startswith("opentelemetry.") or name.startswith("fi_instrumentation"):
                    raise ImportError(f"blocked {name}")
                return None
        sys.meta_path.insert(0, _Block())
        """))
    env = {"PATH": "/usr/bin:/bin", "PYTHONPATH": str(blocker), "FI_BASE_URL": "http://127.0.0.1:9",
           "FI_RUN_DIR": str(tmp_path / "runs"), "HOME": str(tmp_path)}
    out = subprocess.run([sys.executable, "-m", "fi.experiments", "run", "agent.py:task", "--dataset", "rows.jsonl",
                          "--no-upload"], capture_output=True, text=True, cwd=tmp_path, env=env, timeout=60)
    assert out.returncode == 3, out.stderr
    assert 'pip install "futureagi[experiments]"' in out.stderr
    assert "Traceback" not in out.stderr
    ok = subprocess.run([sys.executable, "-m", "fi.experiments", "run", "agent.py:task", "--dataset", "rows.jsonl",
                         "--no-upload", "--no-trace", "--quiet"], capture_output=True, text=True, cwd=tmp_path,
                        env=env, timeout=60)
    assert ok.returncode == 0, ok.stderr
