"""Contract: ``futureagi-py login`` never writes a judge model into the shared login file (the platform
reads that file too). The judge model lives in the run config (``judge_model=`` / ``--judge-model``),
``FI_JUDGE_MODEL`` (the environment, or the project's ``.env`` that ``futureagi-py run`` / ``upload``
load), never the login. No network: every login here is ``--no-verify``."""

import json

import pytest

from fi.experiments._cli.run import doctor_lines
from tests.experiments.unit.cli_helpers import cli

LOGIN_KEYS = {"base_url", "platform_base_url", "platform_base_url_derived", "api_key", "secret_key"}


@pytest.fixture
def login_file(monkeypatch, tmp_path):
    path = tmp_path / "cfg" / "login.json"
    monkeypatch.setenv("FI_LOGIN_FILE", str(path))
    monkeypatch.setenv("FI_API_KEY", "a" * 32)
    monkeypatch.setenv("FI_SECRET_KEY", "b" * 32)
    monkeypatch.setenv("FI_BASE_URL", "http://127.0.0.1:9")
    return path


def test_login_has_no_judge_model_option_and_saves_nothing_with_it(login_file):
    code, out, err = cli("login", "--from-env", "--no-verify", "--judge-model", "gpt-4.1-nano")
    assert code == 2 and "--judge-model" in err  # argparse: unrecognized arguments
    assert not login_file.exists()


def test_login_never_writes_the_judge_model_even_when_one_is_set(login_file, monkeypatch):
    monkeypatch.setenv("FI_JUDGE_MODEL", "gpt-4.1-nano")
    code, out, err = cli("login", "--from-env", "--no-verify")
    assert code == 0, err
    saved = json.loads(login_file.read_text())
    assert set(saved) == LOGIN_KEYS
    assert "judge" not in login_file.read_text().lower() and "gpt-4.1-nano" not in login_file.read_text()


class _Args:
    judge_model = None
    target = None
    dataset = None
    offline = True


def test_a_judge_model_in_a_login_file_is_never_used(login_file, monkeypatch):
    login_file.parent.mkdir(parents=True)
    login_file.write_text(json.dumps({"base_url": "http://127.0.0.1:9", "api_key": "a" * 32,
                                      "secret_key": "b" * 32, "judge_model": "from-the-login-file"}))
    monkeypatch.delenv("FI_JUDGE_MODEL", raising=False)
    assert any(line.startswith("Judge      not set") for line in doctor_lines(_Args()))
    monkeypatch.setenv("FI_JUDGE_MODEL", "from-the-env")
    assert ("Judge      from-the-env (for LLM-judge templates; judge() takes its own model=, default gpt-4.1-mini)"
            in doctor_lines(_Args()))
