"""``ExperimentResult.url`` uses the run page URL in the server's ``app_url`` field.
Without that URL, the result explains why rather than constructing a link.
These tests use a contract stand-in, without network or model calls."""

import json
import webbrowser

import pytest

from fi import experiments
from fi.experiments._engine_summary import run_page
from fi.experiments.errors import NoRunPageError
from fi.experiments.results import ExperimentResult
from tests.experiments.unit.cli_helpers import cli
from tests.experiments.unit.contract_server import ContractServer, client_for

ROWS = [{"id": "T0", "question": "where is order 1?"}, {"id": "T1", "question": "where is order 2?"}]


def _run(server, **kw):
    return experiments.run(experiments.dataset(ROWS, name="support-cases"), lambda row: "shipped", [],
                           client=client_for(server), trace=False, **kw)


def test_url_is_the_servers_app_url_and_open_opens_it(monkeypatch, capsys):
    server = ContractServer()
    server.app_url_base = "http://app.example.test:3031"
    result = _run(server)
    [ds] = server.datasets.values()
    assert result.url == f"http://app.example.test:3031/dashboard/develop/{ds['id']}?tab=experiments&run={result.run_id}"
    assert result.url_note is None
    assert f"App      {result.url}" in capsys.readouterr().err
    opened = []
    monkeypatch.setattr(webbrowser, "open", lambda url: opened.append(url) or True)
    assert result.open() == result.url and opened == [result.url]


def test_no_frontend_url_on_the_server_means_no_url_and_open_says_why(monkeypatch, capsys):
    server = ContractServer()  # app_url is null: the deployment sets no frontend URL
    result = _run(server)
    assert result.url is None and "sets no frontend URL (FRONTEND_URL or APP_URL)" in result.url_note
    assert "App      no link: the server knows no app URL" in capsys.readouterr().err
    monkeypatch.setattr(webbrowser, "open", lambda url: pytest.fail("no link to open"))
    with pytest.raises(NoRunPageError) as info:
        result.open()
    assert f"run {result.run_id} has no page to open" in str(info.value) and "FRONTEND_URL" in str(info.value)
    assert info.value.get_error_code() == "NO_RUN_PAGE"


def test_a_local_run_has_no_page():
    result = experiments.run(ROWS, lambda row: "x", [], upload=False, trace=False, progress=False)
    assert result.url is None and "was not uploaded" in result.url_note
    with pytest.raises(NoRunPageError, match="was not uploaded"):
        result.open()


def test_no_browser_is_said_with_the_link(monkeypatch):
    result = ExperimentResult(run_id="r", name="n", url="http://app.example.test/x", status="completed", items=[])
    monkeypatch.setattr(webbrowser, "open", lambda url: False)
    with pytest.raises(NoRunPageError, match="no browser is available here; open http://app.example.test/x"):
        result.open()


@pytest.mark.parametrize("header, uploaded, url, note", [
    ({"app_url": "https://app.example.test/d/1?run=2"}, True, "https://app.example.test/d/1?run=2", None),
    ({"app_url": None}, True, None, "the server knows no app URL"),
    ({"status": "completed"}, True, None, "did not include the run page URL (app_url)"),
    ({}, True, None, "never confirmed the run"),
    ({"app_url": "javascript:alert(1)"}, True, None, "not an http(s) link"),
    ({"app_url": "https://x"}, False, None, "was not uploaded"),
])
def test_run_page_never_makes_a_link_up(header, uploaded, url, note):
    got_url, got_note = run_page(header, uploaded)
    assert got_url == url and (note is None and got_note is None or note in got_note)


def test_the_cli_json_carries_url_and_its_note(tmp_path):
    (tmp_path / "agent.py").write_text("def task(row):\n    return 'ok'\n")
    (tmp_path / "rows.jsonl").write_text("\n".join(json.dumps(r) for r in ROWS) + "\n")
    # The CLI refuses traced runs on Python 3.14 (exit 3); --no-trace isolates url / url_note.
    code, out, err = cli("run", "agent.py:task", "--dataset", "rows.jsonl", "--no-upload", "--no-trace", "--json")
    assert code == 0, err
    [run] = json.loads(out)["runs"]
    assert run["url"] is None and "was not uploaded" in run["url_note"]
