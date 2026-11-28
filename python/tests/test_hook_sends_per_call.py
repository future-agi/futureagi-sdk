"""Sends through a caller's ``requests`` session while ``HttpClient`` calls on it are in progress, as the 0.8.1 line
judges them: each send takes the opt-in of the call it belongs to (two clients that share one session keep their own
outcome on threads, on two asyncio tasks of one event loop that each send through ``asyncio.to_thread``, and on a
``FuturesSession``), the origin of a send is judged (a query or path the
authentication writes is not a host), an adapter whose ``send`` is a static or class method or a callable object
sends, and a response hook that sends through the adapter a mounted adapter handed the request to is judged.

Listeners run on the loopback interface; ``plain.example.test`` resolves to them through the lookup shim of
``test_plain_http_key_guards`` (its ``net`` fixture applies here too). Each case reads the connections and the marker
bytes at each listener."""

from __future__ import annotations

import asyncio
import threading
from contextlib import ExitStack

import pytest
import requests
from requests.adapters import HTTPAdapter
from requests_futures.sessions import FuturesSession

from fi.api.auth import HttpClient
from fi.api.types import HttpMethod, RequestConfig
from tests.test_keyed_request_paths import KEYED, ok, sites  # noqa: F401
from tests.test_plain_http_key_guards import PLAIN, _attempt, net, refused  # noqa: F401


def _call(client: HttpClient, url: str):
    return client.request(RequestConfig(method=HttpMethod.GET, url=url, retry_attempts=1, retry_delay=0, timeout=5))


def _session(kind: str, *hooks):
    session = FuturesSession() if kind == "futures" else requests.Session()
    session.trust_env = False
    session.hooks["response"].extend(hooks or [lambda r, **kwargs: r])
    return session


class _Held:
    """A route that answers once ``release`` is set, so the call that reached it stays in progress."""

    def __init__(self) -> None:
        self.entered = threading.Event()
        self.release = threading.Event()

    def __call__(self, method, path):
        self.entered.set()
        assert self.release.wait(5), "the second call did not release the held request"
        return ok()


def _overlap(mode: str, held: _Held, first, second):
    """Run ``first`` (a call that reaches ``held``), then ``second`` while ``first`` is in progress; return both errors."""
    def wait_for_first():
        assert held.entered.wait(5), "the first call did not reach the held listener"

    if mode == "threads":
        first_result = []
        worker = threading.Thread(target=lambda: first_result.append(_attempt(first)))
        worker.start()
        try:
            wait_for_first()
            second_result = _attempt(second)
        finally:
            held.release.set()
            worker.join(10)
        assert not worker.is_alive()
        return first_result[0], second_result

    async def main():
        loop = asyncio.get_running_loop()
        thread = threading.get_ident()

        def check_task_location():
            assert asyncio.get_running_loop() is loop
            assert threading.get_ident() == thread

        async def run_first():
            check_task_location()
            return await asyncio.to_thread(_attempt, first)

        async def run_second():
            try:
                check_task_location()
                await asyncio.to_thread(wait_for_first)
                assert not first_task.done(), "the first task finished before the second call"
                return await asyncio.to_thread(_attempt, second)
            finally:
                held.release.set()

        first_task = asyncio.create_task(run_first())
        second_task = asyncio.create_task(run_second())
        first_result, second_result = await asyncio.gather(first_task, second_task)
        return first_result, second_result

    return asyncio.run(main())


@pytest.mark.parametrize("depth", [16, 17])
def test_sending_sessions_returns_at_most_16_outermost_sessions(depth):
    from fi._core.requests_hook_sends import sending_sessions

    with ExitStack() as stack:
        inner_to_outer = [stack.enter_context(requests.Session())]
        for _ in range(depth - 1):
            inner_to_outer.append(stack.enter_context(FuturesSession(session=inner_to_outer[-1])))

        assert sending_sessions(inner_to_outer[-1]) == inner_to_outer[::-1][:16]


MODES = [("threads", "session"), ("asyncio", "session"), ("threads", "futures"), ("asyncio", "futures")]


@pytest.mark.parametrize("mode,kind", MODES)
def test_an_opted_in_client_sends_while_a_client_without_the_opt_in_shares_the_session(net, sites, mode, kind):  # noqa: F811
    held = _Held()
    waiting_site = sites(held)
    session = _session(kind)
    waiting = HttpClient(base_url=waiting_site.base, session=session, default_headers=KEYED)
    opted = HttpClient(base_url=f"http://{PLAIN}:{net.target.port}", session=session, default_headers=KEYED,
                       allow_insecure_http=True)
    first, second = _overlap(mode, held, lambda: _call(waiting, waiting_site.base + "/v1/ping"),
                             lambda: _call(opted, f"http://{PLAIN}:{net.target.port}/v1/ping"))
    assert first is None, repr(first)
    assert second is None, repr(second)
    net.delivered_direct()
    assert waiting_site.marker_bytes() > 0


@pytest.mark.parametrize("mode,kind", MODES)
def test_a_client_without_the_opt_in_is_refused_while_an_opted_in_client_shares_the_session(net, sites, mode, kind):  # noqa: F811
    held = _Held()
    opted_site = sites(held)
    fast = sites(lambda method, path: ok())

    def resend_to_plain(r, **kwargs):
        if f":{fast.port}/" not in r.request.url:
            return r
        prep = r.request.copy()
        prep.url = f"http://{PLAIN}:{net.target.port}/v1/ping"
        return session.send(prep, **kwargs)

    session = _session(kind, resend_to_plain)
    opted = HttpClient(base_url=f"http://{PLAIN}:{opted_site.port}", session=session, default_headers=KEYED,
                       allow_insecure_http=True)
    waiting = HttpClient(base_url=fast.base, session=session, default_headers=KEYED)
    first, second = _overlap(mode, held, lambda: _call(opted, f"http://{PLAIN}:{opted_site.port}/v1/ping"),
                             lambda: _call(waiting, fast.base + "/v1/ping"))
    assert first is None, repr(first)
    assert opted_site.marker_bytes() > 0
    net.nothing_sent()
    refused(second, ValueError)


@pytest.mark.parametrize("mode,kind", MODES)
def test_a_direct_send_without_the_opt_in_is_refused_while_an_opted_in_client_shares_the_session(net, sites, mode, kind):  # noqa: F811
    held = _Held()
    opted_site = sites(held)
    session = _session(kind)
    opted = HttpClient(base_url=f"http://{PLAIN}:{opted_site.port}", session=session, default_headers=KEYED,
                       allow_insecure_http=True)
    waiting = HttpClient(base_url=f"http://{PLAIN}:{net.target.port}", session=session, default_headers=KEYED)
    first, second = _overlap(mode, held, lambda: _call(opted, f"http://{PLAIN}:{opted_site.port}/v1/ping"),
                             lambda: _call(waiting, f"http://{PLAIN}:{net.target.port}/v1/ping"))
    assert first is None, repr(first)
    net.nothing_sent()
    refused(second, ValueError)


class _Rewrite(requests.auth.AuthBase):
    """Authentication that rewrites the URL of the request it signs."""

    def __init__(self, rewrite) -> None:
        self.rewrite = rewrite

    def __call__(self, request):
        request.url = self.rewrite(request.url)
        return request


@pytest.mark.parametrize("rewrite", [
    pytest.param(lambda url: url + "?sig=a@b", id="query"),
    pytest.param(lambda url: url + "?next=http://user@other.example/", id="query-url"),
    pytest.param(lambda url: url.replace("/v1/ping", "/v1/a@b"), id="path"),
])
def test_an_at_sign_the_authentication_writes_after_the_host_of_a_loopback_request_is_sent(sites, rewrite):  # noqa: F811
    site = sites(lambda method, path: ok())
    session = requests.Session()
    session.trust_env = False
    session.auth = _Rewrite(rewrite)
    client = HttpClient(base_url=site.base, session=session, default_headers=KEYED)
    exc = _attempt(lambda: _call(client, site.base + "/v1/ping"))
    assert exc is None, repr(exc)
    assert site.connections == 1 and site.marker_bytes() > 0


@pytest.mark.parametrize("rewrite", [
    pytest.param(lambda url: url.replace("http://", "http://user@", 1), id="user"),
    pytest.param(lambda url: url.replace("http://", "http://user:pass@", 1), id="user-password"),
    pytest.param(lambda url: url.replace("http://", f"http://{PLAIN}@", 1), id="named-user"),
])
def test_user_info_the_authentication_writes_before_the_host_of_a_loopback_request_is_refused(sites, rewrite):  # noqa: F811
    site = sites(lambda method, path: ok())
    session = requests.Session()
    session.trust_env = False
    session.auth = _Rewrite(rewrite)
    client = HttpClient(base_url=site.base, session=session, default_headers=KEYED)
    exc = _attempt(lambda: _call(client, site.base + "/v1/ping"))
    assert exc is not None
    assert (site.connections, site.marker_bytes()) == (0, 0)


_DELEGATE = HTTPAdapter()


class _StaticSend(HTTPAdapter):
    @staticmethod
    def send(request, **kwargs):
        return _DELEGATE.send(request, **kwargs)


class _ClassSend(HTTPAdapter):
    @classmethod
    def send(cls, request, **kwargs):
        return _DELEGATE.send(request, **kwargs)


class _Sender:
    def __call__(self, request, **kwargs):
        return _DELEGATE.send(request, **kwargs)


class _CallableSend(HTTPAdapter):
    send = _Sender()


@pytest.mark.parametrize("adapter", [_StaticSend, _ClassSend, _CallableSend])
@pytest.mark.parametrize("kind", ["session", "futures"])
def test_an_adapter_whose_send_is_not_a_plain_method_sends_a_request_without_keys(sites, adapter, kind):  # noqa: F811
    site = sites(lambda method, path: ok())
    session = _session(kind)
    session.mount("http://", adapter())
    client = HttpClient(base_url=site.base, session=session, default_headers={})
    response = _call(client, site.base + "/v1/ping")
    assert response.status_code == 200
    assert site.connections == 1


@pytest.mark.parametrize("adapter", [_StaticSend, _ClassSend, _CallableSend])
def test_an_adapter_whose_send_is_not_a_plain_method_is_refused_a_keyed_plain_http_request(net, adapter):
    session = _session("session")
    session.mount("http://", adapter())
    client = HttpClient(base_url=f"http://{PLAIN}:{net.target.port}", session=session, default_headers=KEYED,
                        allow_insecure_http=True)
    exc = _attempt(lambda: _call(client, f"http://{PLAIN}:{net.target.port}/v1/ping"))
    net.nothing_sent()
    refused(exc, ValueError)


def _resend_through_the_connection(url: str):
    def hook(r, **kwargs):
        if getattr(r.request, "_resent", False):
            return r
        prep = r.request.copy()
        prep.url = url
        prep._resent = True
        return r.connection.send(prep, **kwargs)

    return hook


def _delegating_session(resend_to: str):
    """A session whose mounted adapter hands each request to another adapter, so a response names that one as its
    connection; its response hook sends the request again through that connection to ``resend_to``."""
    delegate = HTTPAdapter()
    mounted = HTTPAdapter()
    mounted.send = delegate.send
    session = requests.Session()
    session.trust_env = False
    session.mount("http://", mounted)
    session.hooks["response"].append(_resend_through_the_connection(resend_to))
    return session


def test_a_hook_send_through_a_delegate_connection_to_a_named_plain_http_host_is_refused(net, sites):  # noqa: F811
    origin = sites(lambda method, path: ok())
    session = _delegating_session(f"http://{PLAIN}:{net.target.port}/v1/ping")
    client = HttpClient(base_url=origin.base, session=session, default_headers=KEYED)
    exc = _attempt(lambda: _call(client, origin.base + "/v1/ping"))
    net.nothing_sent()
    refused(exc, ValueError)


def test_a_hook_send_through_a_delegate_connection_to_loopback_is_sent(net, sites):  # noqa: F811
    origin = sites(lambda method, path: ok())
    session = _delegating_session(f"http://127.0.0.1:{net.target.port}/v1/ping")
    client = HttpClient(base_url=origin.base, session=session, default_headers=KEYED)
    exc = _attempt(lambda: _call(client, origin.base + "/v1/ping"))
    assert exc is None, repr(exc)
    net.delivered_direct()


@pytest.mark.parametrize("kind", ["session", "futures"])
def test_a_call_a_hook_of_an_opted_in_call_makes_keeps_its_own_opt_in(net, sites, kind):  # noqa: F811
    opted_site = sites(lambda method, path: ok())
    fast = sites(lambda method, path: ok())
    errors: list = []

    def hook(r, **kwargs):
        if f":{opted_site.port}/" in r.request.url:
            errors.append(_attempt(lambda: _call(waiting, fast.base + "/v1/ping")))
        elif f":{fast.port}/" in r.request.url:
            prep = r.request.copy()
            prep.url = f"http://{PLAIN}:{net.target.port}/v1/ping"
            return session.send(prep, **kwargs)
        return r

    session = _session(kind, hook)
    opted = HttpClient(base_url=f"http://{PLAIN}:{opted_site.port}", session=session, default_headers=KEYED,
                       allow_insecure_http=True)
    waiting = HttpClient(base_url=fast.base, session=session, default_headers=KEYED)
    exc = _attempt(lambda: _call(opted, f"http://{PLAIN}:{opted_site.port}/v1/ping"))
    assert exc is None, repr(exc)
    assert opted_site.marker_bytes() > 0
    net.nothing_sent()
    assert len(errors) == 1
    refused(errors[0], ValueError)


def test_query_values_given_as_an_iterator_reach_the_target(sites):  # noqa: F811
    site = sites(lambda method, path: ok())
    session = _session("futures")
    session.auth = requests.auth.HTTPBasicAuth("user", "password")
    client = HttpClient(base_url=site.base, session=session, default_headers=KEYED)
    client.request(RequestConfig(method=HttpMethod.GET, url=site.base + "/v1/items", params={"item": iter(["a", "b"])},
                                 retry_attempts=1, retry_delay=0, timeout=5))
    assert site.requests == [("GET", "/v1/items?item=a&item=b")]


class _SavedContextSession(FuturesSession):
    """A session that runs its next request in a context its response hook saved."""

    saved = None

    def request(self, *args, **kwargs):
        if self.saved is None:
            return super().request(*args, **kwargs)
        context, self.saved = self.saved, None
        return self.executor.submit(context.run, requests.Session.request, self, *args, **kwargs)


def test_a_context_saved_during_a_call_does_not_carry_its_opt_in_to_a_later_call(net, sites):  # noqa: F811
    import contextvars

    first_site = sites(lambda method, path: ok())
    session = _SavedContextSession()
    session.trust_env = False

    def save(r, **kwargs):
        if f":{first_site.port}/" in r.request.url:
            session.saved = contextvars.copy_context()
        return r

    session.hooks["response"].append(save)
    first = HttpClient(base_url=first_site.base, session=session, default_headers=KEYED, allow_insecure_http=False)
    opted = HttpClient(base_url=f"http://{PLAIN}:{net.target.port}", session=session, default_headers=KEYED,
                       allow_insecure_http=True)
    assert _call(first, first_site.base + "/v1/ping") is not None
    assert session.saved is not None
    exc = _attempt(lambda: _call(opted, f"http://{PLAIN}:{net.target.port}/v1/ping"))
    assert exc is None, repr(exc)
    net.delivered_direct()


def test_a_judging_block_left_in_another_context_removes_its_call():
    import contextvars

    from fi._core.requests_hook_sends import judging_sends

    session = requests.Session()
    block = judging_sends([session], False)
    contextvars.Context().run(block.__enter__)
    assert len(session.send.calls) == 1
    block.__exit__(None, None, None)
    assert session.send.calls == []


class _RewriteFor(requests.auth.AuthBase):
    """Authentication that rewrites the URL of a request to ``port`` with ``rewrite``."""

    def __init__(self, port: int, rewrite) -> None:
        self.port, self.rewrite = port, rewrite

    def __call__(self, request):
        if f":{self.port}/" in request.url:
            request.url = self.rewrite(request.url)
        return request


@pytest.mark.parametrize("path", ["/v1/ping", "/v1/other"])
def test_a_futures_session_send_of_a_client_without_the_opt_in_keeps_its_own_opt_in(net, sites, path):  # noqa: F811
    held = _Held()
    opted_site = sites(held)
    fast = sites(lambda method, path: ok())
    session = _session("futures")
    named = f"http://{PLAIN}:{opted_site.port}"
    session.auth = _RewriteFor(fast.port, lambda url: named + path)
    opted = HttpClient(base_url=named, session=session, default_headers=KEYED, allow_insecure_http=True)
    waiting = HttpClient(base_url=fast.base, session=session, default_headers=KEYED)
    first, second = _overlap("threads", held, lambda: _call(opted, named + "/v1/ping"),
                             lambda: _call(waiting, fast.base + "/v1/ping"))
    assert first is None, repr(first)
    refused(second, ValueError)
    assert opted_site.requests == [("GET", "/v1/ping")]
    assert fast.connections == 0


def test_a_connection_a_response_names_keeps_the_opt_in_of_that_response(net, sites):  # noqa: F811
    strict_site = sites(lambda method, path: ok())
    opted_site = sites(lambda method, path: ok())
    saved: list = []

    def hook(r, **kwargs):
        if f":{strict_site.port}/" in r.request.url:
            saved.append(r)
        elif f":{opted_site.port}/" in r.request.url and saved:
            prep = saved[0].request.copy()
            prep.url = f"http://{PLAIN}:{net.target.port}/v1/ping"
            saved[0].connection.send(prep, **kwargs)
        return r

    delegate = HTTPAdapter()
    mounted = HTTPAdapter()
    mounted.send = delegate.send
    session = requests.Session()
    session.trust_env = False
    session.mount("http://", mounted)
    session.hooks["response"].append(hook)
    strict = HttpClient(base_url=strict_site.base, session=session, default_headers=KEYED)
    opted = HttpClient(base_url=f"http://{PLAIN}:{opted_site.port}", session=session, default_headers=KEYED,
                       allow_insecure_http=True)
    assert _attempt(lambda: _call(strict, strict_site.base + "/v1/ping")) is None
    exc = _attempt(lambda: _call(opted, f"http://{PLAIN}:{opted_site.port}/v1/ping"))
    net.nothing_sent()
    refused(exc, ValueError)
