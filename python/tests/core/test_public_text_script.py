"""scripts/check_sdk_public_text.py reports every flagged occurrence on each added line.
Its --whole-release mode scans the current release section and the shipped strings
without a diff."""

from __future__ import annotations

import importlib.util
import os
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[3] / "scripts" / "check_sdk_public_text.py"

WORDS = [
    "evil", "attacker", "attack", "leak", "forward your keys", "cleartext", "clear text", "clear_text", "look like",
    "looks like", "resembles", "fixed", "now", "previously", "vulnerable", "exploit", "never", "just",
    "no longer", "used to", "formerly", "still",
]


def _load():
    spec = importlib.util.spec_from_file_location("check_sdk_public_text", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _git(repo: Path, *args: str) -> str:
    env = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.test",
           "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@example.test"}
    return subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True, env=env).stdout.strip()


@pytest.fixture
def repo(tmp_path, monkeypatch):
    _git(tmp_path, "init", "-q")
    (tmp_path / "python").mkdir()
    (tmp_path / "python" / "CHANGELOG.md").write_text("# Changelog\n\n### Changed\n\n- Base entry.\n")
    (tmp_path / "python" / "fi").mkdir()
    (tmp_path / "python" / "fi" / "mod.py").write_text('"""Base."""\n')
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-q", "-m", "base")
    monkeypatch.chdir(tmp_path)
    return tmp_path


def _plant(repo: Path, line: str) -> list[str]:
    base = _git(repo, "rev-parse", "HEAD")
    with open(repo / "python" / "CHANGELOG.md", "a") as handle:
        handle.write(f"- {line}\n")
    with open(repo / "python" / "fi" / "mod.py", "a") as handle:
        handle.write(f'# {line}\n')
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "planted")
    return _load().findings(base, "HEAD")


@pytest.mark.parametrize("word", WORDS)
def test_each_word_is_reported(repo, word):
    found = _plant(repo, f"The client sends the {word} request.")
    assert len(found) == 2, found
    assert all(word.split()[0].lower() in hit.lower() for hit in found), found


def test_every_hit_of_a_line_is_reported(repo):
    found = _plant(repo, "It never forwards a key, just resembles clear text, clear_text and cleartext.")
    changelog = [hit for hit in found if hit.startswith("python/CHANGELOG.md")]
    reported = " ".join(changelog).lower()
    for word in ("never", "just", "resembles", "clear text", "clear_text", "cleartext"):
        assert word in reported, (word, changelog)
    assert len(changelog) >= 6


def test_a_clean_line_is_not_reported(repo):
    assert _plant(repo, "Set FI_ALLOW_INSECURE_HTTP=1 to send plain HTTP to a self-hosted host.") == []


def test_the_self_test_passes():
    result = subprocess.run(["python3", str(SCRIPT), "--self-test"], capture_output=True, text=True)
    assert result.returncode == 0 and "self-test ok" in result.stdout


def _whole_repo(root: Path, changelog: str) -> Path:
    (root / "python" / "fi").mkdir(parents=True)
    (root / "python" / "CHANGELOG.md").write_text(changelog)
    (root / "python" / "README.md").write_text("# SDK\n\nSet FI_BASE_URL to your gateway.\n")
    (root / "python" / "fi" / "mod.py").write_text(
        '"""Sends a call."""\nimport warnings\n\n\ndef f():\n    """Reads a value."""\n    warnings.warn("set the base URL")\n'
    )
    return root


def test_whole_release_reports_the_current_release_section_and_the_shipped_ones(tmp_path):
    root = _whole_repo(
        tmp_path,
        "# Changelog\n\n## [2.0.0] - pending release\n\n### Changed\n- The client does not follow a redirect.\n"
        "- The proxy is no longer read.\n\n## [1.0.0] (2020-01-01)\n\n### Changed\n- It never leaked.\n",
    )
    found = _load().whole_release(root)
    assert [hit.split(": ")[0] for hit in found] == ["python/CHANGELOG.md:7", "python/CHANGELOG.md:12", "python/CHANGELOG.md:12"], found
    assert "no longer" in found[0] and "never" in found[1] and "leak" in found[2]


def test_whole_release_reads_the_notice_and_vendored_text_files(tmp_path):
    root = _whole_repo(tmp_path, "# Changelog\n\n## [2.0.0] - pending release\n\n- Clean entry.\n")
    (root / "python" / "fi" / "gateway").mkdir()
    (root / "python" / "NOTICE").write_text("Portions are copied from a project.\n")
    (root / "NOTICE").write_text("This product is clean.\n")
    (root / "python" / "fi" / "gateway" / "VENDORED.md").write_text("# Vendored\n\n- the stream now closes.\n")
    assert [hit.split(": ")[0] for hit in _load().whole_release(root)] == ["python/fi/gateway/VENDORED.md:3"]
    (root / "python" / "fi" / "gateway" / "VENDORED.md").write_text("# Vendored\n\n- the stream closes.\n")
    (root / "python" / "NOTICE").write_text("It was never a copy.\n")
    (root / "NOTICE").write_text("Just a notice.\n")
    assert [hit.split(": ")[0] for hit in _load().whole_release(root)] == ["NOTICE:1", "python/NOTICE:1"]


def test_whole_release_reads_the_message_of_every_exception_that_is_built(tmp_path):
    root = _whole_repo(tmp_path, "# Changelog\n\n## [2.0.0] - pending release\n\n- Clean entry.\n")
    (root / "python" / "fi" / "mod.py").write_text(
        'class RedirectError(Exception):\n    pass\n\n\ndef refuse(host):\n'
        '    error = RedirectError(f"{host}: calls never follow a redirect")\n    return error\n\n\n'
        'def other(errors):\n    return errors.UnexpectedRedirectError("a call that is just refused", status_code=302)\n\n\n'
        'def clean():\n    return RedirectError("a call that is refused")\n'
    )
    found = _load().whole_release(root)
    assert [hit.split(": ")[0] for hit in found] == ["python/fi/mod.py:6", "python/fi/mod.py:11"], found


def test_whole_release_reads_readme_docstring_and_message_strings(tmp_path):
    root = _whole_repo(tmp_path, "# Changelog\n\n## [2.0.0] - pending release\n\n- Clean entry.\n")
    assert _load().whole_release(root) == []
    (root / "python" / "README.md").write_text("# SDK\n\nJust set it.\n")
    (root / "python" / "fi" / "mod.py").write_text(
        '"""It used to work."""\nimport warnings\n\n\ndef f():\n    warnings.warn("this is now off")\n    return "a never string"\n'
    )
    found = _load().whole_release(root)
    assert [hit.split(":")[0] + ":" + hit.split(":")[1] for hit in found] == [
        "python/README.md:3", "python/fi/mod.py:1", "python/fi/mod.py:6",
    ], found


def test_whole_release_command_exits_one_on_a_finding_and_zero_when_clean(tmp_path):
    root = _whole_repo(tmp_path, "# Changelog\n\n## [2.0.0] - pending release\n\n- It formerly refused.\n")
    run = lambda: subprocess.run(["python3", str(SCRIPT), "--whole-release", "--root", str(root)], capture_output=True, text=True)
    dirty = run()
    assert dirty.returncode == 1 and "python/CHANGELOG.md:5:" in dirty.stdout and "1 finding(s)" in dirty.stdout
    (root / "python" / "CHANGELOG.md").write_text("# Changelog\n\n## [2.0.0] - pending release\n\n- It refuses.\n")
    clean = run()
    assert clean.returncode == 0 and "0 finding(s)" in clean.stdout
