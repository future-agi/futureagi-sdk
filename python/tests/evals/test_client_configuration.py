"""Evaluation and management calls share client HTTP settings and resource ownership."""
import httpx
import pytest
import requests

from fi import FutureAGIClient
from tests.evals import _mock_http


@pytest.fixture
def captures(monkeypatch):
    calls = []
    backend = _mock_http.FakeBackend()

    def send_requests(adapter, request, **kwargs):
        calls.append((request, kwargs.get("timeout")))
        return backend.send(request)

    def send_httpx(transport, request):
        calls.append((request, request.extensions["timeout"]))
        prepared = requests.Request(request.method, str(request.url),
                                    headers=dict(request.headers), data=request.content).prepare()
        response = backend.send(prepared)
        return httpx.Response(response.status_code, content=response.content,
                              headers=response.headers, request=request)

    monkeypatch.setattr(requests.adapters.HTTPAdapter, "send", send_requests)
    monkeypatch.setattr(httpx.HTTPTransport, "handle_request", send_httpx)
    return calls


def client(**kwargs):
    return FutureAGIClient(api_key="key-A", secret_key="secret-A",
                          base_url="http://127.0.0.1:9", **kwargs)


def timeouts(calls):
    return [t if isinstance(t, dict) else dict.fromkeys(("connect", "read", "write", "pool"), t)
            for _, t in calls]


def test_headers_and_origin_match_across_namespaces(captures):
    with client(headers={"X-Proxy-Auth": "test-proxy", "X-Workspace": "test-workspace"}) as c:
        c.evals.list_templates({})
        result = c.evals.evaluate("toxicity", {"output": "hi"})
        assert result.eval_results[0].output == "Passed"
        assert len(captures) == 3
        for request, _ in captures:
            assert request.headers["X-Proxy-Auth"] == "test-proxy"
            assert request.headers["X-Workspace"] == "test-workspace"
            assert request.headers["X-Api-Key"] == "key-A"
            assert str(request.url).startswith(c.base_url)


def test_timeouts_and_copies(captures):
    with client(timeout=1.25, retries=0) as c:
        with c.with_options(timeout=2.5) as clone:
            c.evals.evaluate("toxicity", {"output": "a"})
            assert timeouts(captures) == [dict.fromkeys(("connect", "read", "write", "pool"), 1.25)] * 2
            captures.clear()
            clone.evals.evaluate("tone", {"output": "b"})
            assert timeouts(captures) == [dict.fromkeys(("connect", "read", "write", "pool"), 2.5)] * 2
        captures.clear()
        c.evals.evaluate("toxicity", {"output": "still open"})
        assert len(captures) == 1


def test_structured_timeout_and_per_evaluation_override(captures):
    timeout = httpx.Timeout(connect=1, read=2, write=3, pool=4)
    with client(timeout=timeout) as c:
        c.evals.evaluate("toxicity", {"output": "a"})
        assert timeouts(captures) == [timeout.as_dict()] * 2
        captures.clear()
        c.evals.evaluate("toxicity", {"output": "b"}, timeout=0.75)
        assert timeouts(captures) == [dict.fromkeys(("connect", "read", "write", "pool"), 0.75)]
        captures.clear()
        c.evals.evaluate("toxicity", {"output": "c"}, timeout=2)
        assert timeouts(captures) == [dict.fromkeys(("connect", "read", "write", "pool"), 2)]


@pytest.mark.parametrize("context_exit", [False, True])
def test_client_disposes_its_retained_evaluator_once(captures, monkeypatch, context_exit):
    c = client()
    c.__enter__()
    c.evals.evaluate("toxicity", {"output": "x"})
    evaluator = c.evals._delegate.evaluator()
    closed = []
    original = evaluator.close

    def close():
        closed.append(True)
        original()

    monkeypatch.setattr(evaluator, "close", close)
    if context_exit:
        c.__exit__(None, None, None)
    else:
        c.close()
    c.close()
    assert closed == [True]


def test_close_copy_does_not_dispose_parent_evaluator(captures, monkeypatch):
    with client() as c:
        c.evals.evaluate("toxicity", {"output": "x"})
        parent = c.evals._delegate.evaluator()
        parent_closed = []
        monkeypatch.setattr(parent, "close", lambda: parent_closed.append(True))
        with c.with_options() as clone:
            clone.evals.evaluate("tone", {"output": "x"})
            assert clone.evals._delegate.evaluator() is not parent
        assert parent_closed == []
        assert c.evals.evaluate("toxicity", {"output": "x"}).eval_results[0].output == "Passed"
    assert parent_closed == [True]


def test_retry_policy_is_shared_without_an_extra_legacy_retry_loop(monkeypatch):
    attempts = []
    backend = _mock_http.FakeBackend()

    def send(transport, request):
        attempts.append(request)
        if len(attempts) == 1:
            raise httpx.ConnectError("synthetic connection failure", request=request)
        prepared = requests.Request(request.method, str(request.url),
                                    headers=dict(request.headers), data=request.content).prepare()
        response = backend.send(prepared)
        return httpx.Response(response.status_code, content=response.content, request=request)

    monkeypatch.setattr(httpx.HTTPTransport, "handle_request", send)
    with client(retries=0) as c:
        result = c.evals.evaluate("toxicity", {"output": "x"}, skip_input_mapping=True)
        assert len(attempts) == 1
        assert result.eval_results[0].output is None
        attempts.clear()
        with c.with_options(retries=1) as clone:
            result = clone.evals.evaluate("toxicity", {"output": "x"}, skip_input_mapping=True)
            assert len(attempts) == 2
            assert result.eval_results[0].output == "Passed"


def test_only_the_parent_closes_the_shared_connection_pool(captures, monkeypatch):
    closed = []
    monkeypatch.setattr(httpx.HTTPTransport, "close", lambda transport: closed.append(transport))
    c = client()
    with c.with_options() as clone:
        clone.evals.evaluate("toxicity", {"output": "x"})
    assert closed == []
    c.evals.evaluate("toxicity", {"output": "x"})
    c.close()
    assert len(closed) == 1


def test_replaced_evaluators_are_all_disposed(captures):
    from fi._credentials import Credentials
    from fi.evals._delegate import EvaluatorDelegate

    with client() as c:
        credentials = [c.auth]
        delegate = EvaluatorDelegate(lambda: credentials[0], c.generated_client.get_httpx_client)
        first = delegate.evaluator()
        from dataclasses import replace
        credentials[0] = replace(credentials[0], api_key="key-B")
        second = delegate.evaluator()
        assert second is not first
        delegate.close()
        assert first._session.closed and second._session.closed
        with pytest.raises(RuntimeError, match="closed"):
            delegate.evaluator()
