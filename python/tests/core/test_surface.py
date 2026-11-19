"""The rest of the platform core's surface: request building, Page, handles and the one
waiter, with_raw_response, and with_options (a copy that shares the pool)."""

from __future__ import annotations

import asyncio

import pytest

import fi.errors as errors
from fi._core.handles import AsyncHandle, Handle, poll_until
from fi._core.pagination import alist_page, list_page
from fi._core.raw import AsyncNamespace, Namespace
from fi._core.request import BODY_LIMITS, build_path, build_query
from tests.core._support import OPS, Recorder, make_async_core, make_core, respond

# -- requests ---------------------------------------------------------------------------------


def test_path_parameters_are_encoded_and_cannot_climb_out_of_their_segment():
    assert build_path(OPS["runs.get"], {"id": "a/b c"}) == "/workspace/conversations/a%2Fb%20c"
    assert (
        build_path(OPS["files.write"], {"id": "s1", "path": "dir/a b.txt"})
        == "/workspace/sandboxes/s1/files/dir/a%20b.txt"
    )
    for bad in ("", ".", ".."):
        with pytest.raises(errors.ConfigurationError):
            build_path(OPS["runs.get"], {"id": bad})
    with pytest.raises(errors.ConfigurationError):
        build_path(OPS["files.write"], {"id": "s1", "path": "a/../../etc"})
    with pytest.raises(errors.ConfigurationError):
        build_path(OPS["runs.get"], {})


def test_only_declared_query_keys_are_sent():
    assert build_query(OPS["runs.list"], {"limit": 5, "agentId": "a", "cursor": None}) == [
        ("agentId", "a"),
        ("limit", "5"),
    ]
    with pytest.raises(errors.ConfigurationError) as info:
        build_query(OPS["runs.list"], {"api_key": "x"})
    assert info.value.code == "undeclared_query_key"


def test_a_body_past_its_limit_is_refused_before_sending():
    rec = Recorder(respond(201, {}))
    with pytest.raises(errors.PayloadTooLargeError) as info:
        make_core(rec).call("runs.create", body={"x": "a" * BODY_LIMITS["json"]})
    assert info.value.local and info.value.limit_bytes == BODY_LIMITS["json"] and rec.requests == []


def test_human_only_verbs_have_no_sdk_path_and_headers_are_declared_only():
    rec = Recorder(respond(200, {}))
    with pytest.raises(errors.ConfigurationError) as info:
        make_core(rec).call("approvals.decide", path={"id": "a"}, body={})
    assert info.value.code == "human_only_verb" and rec.requests == []
    with pytest.raises(errors.ConfigurationError):
        make_core(rec).call("runs.get", path={"id": "c"}, headers={"X-Api-Key": "other"})


def test_requests_carry_the_credential_user_agent_and_no_redirect_following():
    rec = Recorder(respond(200, {"ok": True}))
    make_core(rec).call("runs.get", path={"id": "c1"})
    req = rec.requests[0]
    assert str(req.url) == "https://api.futureagi.com/omega/api/workspace/conversations/c1"
    assert req.headers["X-Api-Key"] == "k-test-1234" and req.headers["User-Agent"].startswith("futureagi-python/")
    assert "Idempotency-Key" not in req.headers


# -- pages ------------------------------------------------------------------------------------


def test_a_cursor_page_walks_every_item_and_stops_on_a_repeated_cursor():
    pages = {
        None: {"conversations": [1, 2], "nextCursor": "c2"},
        "c2": {"conversations": [3], "nextCursor": "c3"},
        "c3": {"conversations": [4], "nextCursor": "c3"},
    }
    rec = Recorder(lambda r: respond(200, pages[r.url.params.get("cursor")]))
    page = list_page(make_core(rec), "runs.list", query={"agentId": "a"})
    assert page.items == [1, 2] and page.has_more and page.next_cursor == "c2"
    assert list(page) == [1, 2, 3, 4] and len(rec.requests) == 3  # "c3" again ends the walk
    assert all(r.url.params["agentId"] == "a" for r in rec.requests)
    nxt = page.next_page()
    assert nxt is not None and nxt.items == [3]


def test_a_single_page_list_has_the_same_interface():
    rec = Recorder(respond(200, {"sandboxes": [{"id": "s1"}]}))
    page = list_page(make_core(rec), "sandboxes.list", transform=lambda d: d["id"])
    assert page.items == ["s1"] and not page.has_more and page.next_page() is None and list(page) == ["s1"]
    with pytest.raises(ValueError):
        list_page(make_core(rec), "sandboxes.list", cursor="x")


@pytest.mark.anyio
async def test_async_pages():
    pages = {None: {"conversations": [1], "nextCursor": "c2"}, "c2": {"conversations": [2]}}
    rec = Recorder(lambda r: respond(200, pages[r.url.params.get("cursor")]))
    page = await alist_page(make_async_core(rec), "runs.list")
    assert [x async for x in page] == [1, 2]


# -- handles ----------------------------------------------------------------------------------


class Thing(Handle):
    noun = "thing"

    def _get(self):
        return self._ns.read(self.id)

    def _is_done(self):
        return self.status in ("ready", "failed")


class Reader:
    def __init__(self, statuses):
        self.statuses = list(statuses)

    def read(self, thing_id):
        return {"id": thing_id, "status": self.statuses.pop(0), "agentId": "a1"}


def test_a_handle_reads_fields_and_waits_with_one_waiter():
    thing = Thing(Reader(["starting", "ready"]), {"id": "t1", "status": "new", "agentId": "a1"})
    assert thing.id == "t1" and thing.agent_id == "a1" and thing.data["agentId"] == "a1"
    copy = thing.to_dict()
    copy["status"] = "x"
    assert thing.status == "new"
    sleeps = []
    assert thing.wait(timeout=10, sleep=sleeps.append) is thing and thing.status == "ready" and sleeps == [0.5]
    with pytest.raises(AttributeError):
        thing.nope  # noqa: B018
    with pytest.raises(AttributeError):
        thing.status = "x"
    assert repr(thing) == "Thing(id='t1', status='ready')"


def test_wait_times_out_with_api_timeout():
    clock = iter(range(0, 1000, 5))
    with pytest.raises(errors.APITimeoutError) as info:
        poll_until(
            lambda: None, timeout=12, sleep=lambda s: None, clock=lambda: next(clock), label="waiting for thing t1"
        )
    assert "waiting for thing t1 did not finish within 12 s" == str(info.value)


def test_async_handle_waits():
    class AThing(AsyncHandle):
        async def _get(self):
            return {"id": "t", "status": "ready"}

        def _is_done(self):
            return self.status == "ready"

    async def go():
        thing = AThing(None, {"id": "t", "status": "new"})

        async def nosleep(seconds):
            return None

        return (await thing.wait(timeout=5, sleep=nosleep)).status

    assert asyncio.run(go()) == "ready"


# -- raw responses ----------------------------------------------------------------------------


class Runs(Namespace):
    def get(self, run_id):
        return self._core.call("runs.get", path={"id": run_id})

    def create(self, **body):
        return self._core.call("runs.create", body=body)


def test_with_raw_response_returns_the_data_and_the_response_metadata():
    rec = Recorder(
        respond(
            201,
            {"id": "c1"},
            {
                "x-request-id": "req-3",
                "x-ratelimit-remaining": "9",
                "x-omega-idempotent-replayed": "true",
                "set-cookie": "s=secret",
            },
        )
    )
    raw = Runs(make_core(rec)).with_raw_response.create(agentId="a")
    assert raw.data == {"id": "c1"} and raw.parse() == {"id": "c1"} and raw.status_code == 201
    assert raw.request_id == "req-3" and raw.idempotency_key == rec.keys[0] and raw.meta.idempotent_replay
    assert raw.rate_limit == {"x-ratelimit-remaining": "9"} and raw.headers["set-cookie"] == "[redacted]"
    assert Runs(make_core(Recorder(respond(200, {"id": "c2"})))).get("c2") == {"id": "c2"}  # plain results stay plain


def test_with_raw_response_on_async_namespaces():
    class ARuns(AsyncNamespace):
        async def get(self, run_id):
            return await self._core.call("runs.get", path={"id": run_id})

    async def go():
        return await ARuns(
            make_async_core(Recorder(respond(200, {"id": "c1"}, {"x-request-id": "r-a"})))
        ).with_raw_response.get("c1")

    raw = asyncio.run(go())
    assert raw.data == {"id": "c1"} and raw.request_id == "r-a"
