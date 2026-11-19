"""Answers that are not the API's JSON: a gateway, proxy, load balancer or web app answered for the server.

- e2e SDK-34 on dsx-e2e-1, behind the stack's nginx router (run 20261023T101220Z-vm): a restarting server's HTML 502 /
  503 / 504 page stopped the upload ("a batch upload failed (JSONDecodeError)"). Both calls are replays (same run id
  and body; same receipts), so a 429 or 5xx page is retried like any 5xx.
- The review of that fix (probe test_probe_4xx_html.py): every other non-JSON answer was retried too, because the
  generated parser reads the body before anyone sees the status. An nginx 413 (its default body limit is 1 MiB; a
  batch is up to 2 MiB) stalled for GIVE_UP_S, then printed a resume line that hit the same 413. Now the status is
  read first: any non-JSON answer other than a 429 or a 5xx stops the run at once, naming the status and the page.

No network, no model: every request goes to the contract stand-in (contract_server.py) over httpx.MockTransport.
"""

import httpx
import pytest

from fi import experiments
from fi.experiments import _upload
from fi.experiments._upload import NonJSONAnswerError, UploadRefusedError, UploadStalledError
from tests.experiments.unit.contract_server import ContractServer, client_for

ROWS = experiments.dataset([{"question": "where is order 1?", "expected": "shipped"},
                            {"question": "where is order 2?", "expected": "lost"}], name="gateway-rows")
INGEST = r"/model-hub/experiment-runs/[^/]+/results/"
CREATE = r"/model-hub/experiment-runs/$"


def task(row):
    return "shipped"


def _run(server, **kw):
    return experiments.run(ROWS, task, client=client_for(server), trace=False, progress=False, **kw)


# ---- a 429 or 5xx page: the server behind the gateway is down or restarting; retried ----------------------------


def test_ingest_retries_through_a_gateways_html_pages_and_stores_every_item(monkeypatch):
    monkeypatch.setattr(_upload, "BACKOFF_S", (0.01,))
    server = ContractServer()
    server.gateway_ingest = [502, 503, 504]
    result = _run(server)
    [run] = server.runs.values()
    assert result.status == "completed" and len(run["items"]) == 2
    assert result.metadata["upload"]["retries"] == 3
    assert server.count("POST", INGEST) == 4  # 3 gateway pages, then the ack


def test_run_create_retries_through_a_gateways_html_page(monkeypatch):
    monkeypatch.setattr(_upload, "CREATE_RETRY_S", (0.01, 0.01, 0.01))
    server = ContractServer()
    server.gateway_create = [502, 503]
    result = _run(server)
    [run] = server.runs.values()
    assert result.status == "completed" and len(run["items"]) == 2
    assert server.count("POST", CREATE) == 3  # two gateway pages, then the create


def test_a_gateway_that_never_recovers_stalls_with_exit_3_naming_the_status_and_the_page(monkeypatch):
    monkeypatch.setattr(_upload, "BACKOFF_S", (0.01,))
    monkeypatch.setattr(_upload, "GIVE_UP_S", 0.0)
    server = ContractServer()
    server.gateway_ingest = [502]
    with pytest.raises(UploadStalledError) as info:
        _run(server)
    text = str(info.value)
    assert info.value.exit_code == 3 and "HTTP 502" in text and "'502 Bad Gateway'" in text
    assert "gateway or proxy" in text and "Expecting value" not in text  # the page, not the parser's complaint
    assert "resume=" in text


def test_a_run_create_gateway_that_never_recovers_is_refused_naming_the_status(monkeypatch):
    monkeypatch.setattr(_upload, "CREATE_RETRY_S", (0.01, 0.01, 0.01))
    server = ContractServer()
    server.gateway_create = [503] * 4
    with pytest.raises(UploadRefusedError) as info:
        _run(server)
    assert "HTTP 503" in str(info.value) and "'503 Service Temporarily Unavailable'" in str(info.value)
    assert server.count("POST", CREATE) == 4  # the first try and 3 retries


# ---- any other status: refused at once, the status and the page named ------------------------------------------


@pytest.mark.parametrize(("status", "says"), [
    (413, "raise its request body limit to at least 2 MiB"),
    (404, "check FI_BASE_URL"),
    (403, "refused the request before the API saw it"),
])
def test_ingest_answered_by_a_proxys_4xx_page_stops_at_once(monkeypatch, status, says):
    monkeypatch.setattr(_upload, "BACKOFF_S", (0.01,))
    server = ContractServer()
    server.gateway_ingest = [status] * 50  # every ingest gets the page: a retry would get it again
    with pytest.raises(UploadRefusedError) as info:
        _run(server)
    text = str(info.value)
    assert server.count("POST", INGEST) == 1  # one POST: no retry loop, no 300 s stall
    assert info.value.exit_code == 3
    assert f"a batch upload failed (HTTP {status})" in text and f"'{status} " in text and says in text
    assert "Expecting value" not in text and "JSONDecodeError" not in text


def test_run_create_answered_by_a_404_page_is_refused_naming_the_status(monkeypatch):
    monkeypatch.setattr(_upload, "CREATE_RETRY_S", (0.01, 0.01, 0.01))
    server = ContractServer()
    server.gateway_create = [404] * 10
    with pytest.raises(UploadRefusedError) as info:
        _run(server)
    assert server.count("POST", CREATE) == 1
    assert "the run was not created (HTTP 404)" in str(info.value) and "'404 Not Found'" in str(info.value)
    assert server.runs == {}


def test_run_create_answered_by_a_web_apps_200_page_is_refused():
    server = ContractServer()
    server.gateway_create = [httpx.Response(200, text="<!doctype html><html><head><title>Future AGI</title></head>"
                                                      "<body><div id=root></div></body></html>",
                                            headers={"content-type": "text/html; charset=utf-8"})]
    with pytest.raises(UploadRefusedError) as info:
        _run(server)
    assert server.count("POST", CREATE) == 1
    assert "(HTTP 200)" in str(info.value) and "'Future AGI'" in str(info.value) and "FI_BASE_URL" in str(info.value)


def test_a_redirect_is_refused_naming_where_it_points():
    server = ContractServer()
    server.gateway_create = [301]
    with pytest.raises(UploadRefusedError) as info:
        _run(server)
    assert "(HTTP 301)" in str(info.value) and "redirects to https://srv.test/" in str(info.value)


def test_a_json_speaking_proxys_413_is_refused_at_once_with_its_message(monkeypatch):
    monkeypatch.setattr(_upload, "BACKOFF_S", (0.01,))
    server = ContractServer()
    server.gateway_ingest = [httpx.Response(413, json={"message": "Request size limit exceeded"})] * 5
    with pytest.raises(UploadRefusedError) as info:
        _run(server)
    assert server.count("POST", INGEST) == 1
    assert "a batch upload failed (HTTP 413): Request size limit exceeded" in str(info.value)


# ---- the answer's reading -----------------------------------------------------------------------------------------


def test_only_429_and_5xx_pages_are_retried():
    for status in (429, 500, 502, 503, 504):
        assert _upload._transient(NonJSONAnswerError(status, "x")) is True, status
    for status in (200, 301, 400, 401, 403, 404, 405, 407, 413):
        assert _upload._transient(NonJSONAnswerError(status, "x")) is False, status
    assert _upload._transient(ValueError("x")) is False


def test_the_title_is_one_printable_line_and_an_empty_page_names_its_status():
    from fi.experiments._api_answer import _page_title

    page = httpx.Response(502, text="<HTML><HEAD><TITLE>\n  Bad\tGateway &amp; \x1b[31mred </TITLE></HEAD></HTML>")
    assert _page_title(page) == "Bad Gateway & [31mred"
    assert _page_title(httpx.Response(504, content=b"")) == "504 Gateway Timeout"
    assert NonJSONAnswerError.from_response(httpx.Response(504, content=b"")).status_code == 504
