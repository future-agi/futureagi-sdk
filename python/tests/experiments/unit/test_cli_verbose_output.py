"""Wave 2g (e2e CLI-17): ``futureagi-py run --verbose`` logs what the run decided and did at DEBUG on the
``fi.experiments`` logger: the effective settings, each trial, each judge request and each upload batch. Only ids,
counts, statuses and timings: never a key, an output, an input, a URL's credentials or query. No network, no model."""

import json
import logging

import pytest

from fi import experiments
from fi.experiments import _debug
from tests.experiments.unit.cli_helpers import cli
from tests.experiments.unit.contract_server import ContractServer, client_for

SECRET_OUTPUT = "the-output-text-0123456789"


@pytest.fixture(autouse=True)
def fresh_cli_log_handler():
    """The CLI adds its stderr handler to the ``fi`` logger once per process, bound to the sys.stderr of that moment.
    In-process runs of main() (cli_helpers) in one pytest process would write to an earlier test's captured stream, so
    each test here starts with no CLI handler (the real console script is one process, one main())."""
    root = logging.getLogger("fi")
    level = root.level
    for h in [h for h in root.handlers if getattr(h, "_futureagi_cli", False)]:
        root.removeHandler(h)
    yield
    for h in [h for h in root.handlers if getattr(h, "_futureagi_cli", False)]:
        root.removeHandler(h)
    root.setLevel(level)


def _run_file(tmp_path):
    (tmp_path / "run_eval.py").write_text(
        "from fi import experiments\n"
        "def ok(output):\n    return output.startswith('the-output')\n"
        f"experiments.run([{{'q': 1}}, {{'q': 2}}], lambda row: {SECRET_OUTPUT!r}, [ok], name='v', upload=False, "
        "trace=False)\n")


def test_verbose_logs_the_settings_and_each_trial_and_never_an_output(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _run_file(tmp_path)
    code, out, err = cli("run", "run_eval.py", "--verbose", "--no-env-file")
    # a DEBUG line can follow the progress bar's carriage return on the same terminal line: split on both
    debug = [ln[ln.index("DEBUG fi.experiments:"):] for ln in err.replace("\r", "\n").splitlines()
             if "DEBUG fi.experiments:" in ln]
    assert code == 0, err[-500:]
    assert any(" run " in ln and "2 rows x 1 trial(s)" in ln and "error_policy zero" in ln and "upload False" in ln
               for ln in debug), debug
    trials = [ln for ln in debug if ": trial " in ln]
    assert len(trials) == 2 and all("completed in " in ln and "scores: ok=assessed/pass" in ln for ln in trials), trials
    assert SECRET_OUTPUT not in err


def test_without_verbose_or_with_quiet_there_is_no_debug_line(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _run_file(tmp_path)
    for flags in ([], ["--quiet"]):
        code, _, err = cli("run", "run_eval.py", "--no-env-file", *flags)
        assert code == 0 and "DEBUG" not in err, (flags, err[-300:])


def test_a_failed_trial_names_its_error_type_only(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    def boom(row):
        raise ValueError("a message that may hold anything 0123456789")

    with_caplog = logging.getLogger("fi.experiments")
    records = []
    handler = logging.Handler()
    handler.emit = records.append  # type: ignore[method-assign]
    with_caplog.addHandler(handler)
    old = with_caplog.level
    with_caplog.setLevel(logging.DEBUG)
    try:
        experiments.run([{"q": 1}], boom, [], upload=False, progress=False, trace=False)
    finally:
        with_caplog.removeHandler(handler)
        with_caplog.setLevel(old)
    lines = [r.getMessage() for r in records]
    assert any("failed (ValueError)" in ln for ln in lines), lines
    assert not any("0123456789" in ln for ln in lines)


def test_http_lines_drop_credentials_and_query(caplog):
    with caplog.at_level(logging.DEBUG, logger="fi.experiments"):
        _debug.http("judge POST", "https://user:pa55@api.example.test:8443/v1/chat/completions?key=abc", 429, 1)
    [msg] = [r.getMessage() for r in caplog.records]
    assert msg == "judge POST https://api.example.test:8443/v1/chat/completions -> HTTP 429 (retry 1)"


def test_an_upload_batch_is_logged(tmp_path, monkeypatch, caplog):
    monkeypatch.chdir(tmp_path)
    server = ContractServer()
    server.add_dataset("support", [{"id": "T1", "question": "where is order 1?"}])
    with caplog.at_level(logging.DEBUG, logger="fi.experiments"):
        experiments.run(experiments.dataset("support"), lambda row: "shipped", [], client=client_for(server),
                        progress=False, trace=False)
    msgs = [r.getMessage() for r in caplog.records]
    assert any(m.startswith("upload batch of 1 item(s) -> acked") for m in msgs), msgs
    assert not any("shipped" in m for m in msgs) and json.dumps(msgs)
