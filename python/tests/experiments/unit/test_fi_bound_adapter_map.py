# ruff: noqa: F811
"""The adapters of a Future AGI-bound session stay the SDK's own, changed in place or copied.

``session.adapters`` is the dict ``requests`` looks transports up in. A transport that is not the
SDK's plain HTTP adapter can follow a redirect inside its own ``send``, so the dict refuses such a
value whichever way it is written, keeps its default adapters in place, and a copy of the session
keeps the same guard. A plain adapter mounted the normal way still works.
"""

import contextlib
import copy

import pytest
import requests
from requests.adapters import HTTPAdapter

from tests.experiments.unit.test_fi_bound_exporter_headers import sink  # noqa: F401
from tests.experiments.unit.test_fi_bound_session_paths import (  # noqa: F401
    FollowingAdapter,
    clean_futureagi_session,
    first,
    nothing_reached,
    second,
)


def refused(action):
    from fi.errors import ConfigurationError

    with pytest.raises(ConfigurationError) as raised:
        action()
    assert raised.value.code == "unsupported_session_adapter"


def untouched(session):
    assert list(session.adapters) == ["https://", "http://"]
    assert all(type(a) is HTTPAdapter for a in session.adapters.values())


def test_setting_an_adapter_the_sdk_did_not_build_in_place_is_refused():
    session = clean_futureagi_session()
    refused(lambda: session.adapters.__setitem__("http://", FollowingAdapter()))
    refused(lambda: session.adapters.__setitem__("ftp://", FollowingAdapter()))
    untouched(session)


def test_update_and_setdefault_with_such_an_adapter_are_refused():
    session = clean_futureagi_session()
    refused(lambda: session.adapters.update({"http://": FollowingAdapter()}))
    refused(lambda: session.adapters.update(a=FollowingAdapter()))
    refused(lambda: session.adapters.setdefault("ftp://", FollowingAdapter()))
    untouched(session)


def test_merging_such_an_adapter_with_the_union_operator_is_refused():
    session = clean_futureagi_session()

    def merge():
        session.adapters |= {"http://": FollowingAdapter()}

    refused(merge)
    untouched(session)


def test_the_default_adapters_cannot_be_removed():
    session = clean_futureagi_session()
    refused(session.adapters.clear)
    refused(lambda: session.adapters.pop("http://"))
    refused(session.adapters.popitem)
    refused(lambda: session.adapters.__delitem__("https://"))
    untouched(session)


def test_a_plain_adapter_can_be_mounted_and_set(sink):
    session = clean_futureagi_session()
    plain = HTTPAdapter(pool_maxsize=3)
    session.mount("http://", plain)
    assert session.adapters["http://"] is plain
    session.mount("http://127.0.0.1", HTTPAdapter())
    assert next(iter(session.adapters)) == "http://127.0.0.1"
    session.adapters["https://"] = HTTPAdapter()
    assert session.post(sink.base + "/tracer/v1/traces", data=b"x").status_code == 200


@pytest.mark.parametrize("make", [copy.copy, copy.deepcopy])
def test_a_copy_of_the_session_refuses_other_adapters(make):
    session = clean_futureagi_session()
    duplicate = make(session)
    refused(lambda: duplicate.mount("http://", FollowingAdapter()))
    refused(lambda: setattr(duplicate, "adapters", {"http://": FollowingAdapter()}))
    refused(lambda: duplicate.adapters.__setitem__("http://", FollowingAdapter()))
    refused(duplicate.adapters.clear)


@pytest.mark.parametrize("make", [copy.copy, copy.deepcopy])
def test_a_copy_of_the_session_mounts_plain_adapters_and_sends(make, sink):
    duplicate = make(clean_futureagi_session())
    duplicate.mount("http://", HTTPAdapter())
    assert duplicate.post(sink.base + "/tracer/v1/traces", data=b"x").status_code == 200


def test_a_307_reaches_nothing_when_a_following_adapter_is_set_in_place(
    first, second
):
    from fi.errors import ConfigurationError

    session = clean_futureagi_session()
    for write in (
        lambda: session.adapters.__setitem__("http://", FollowingAdapter()),
        lambda: session.adapters.update({"http://": FollowingAdapter()}),
        lambda: copy.copy(session).adapters.__setitem__("http://", FollowingAdapter()),
    ):
        with contextlib.suppress(ConfigurationError):
            write()
    try:
        session.post(first.base + "/tracer/v1/traces", data=b"x")
    except requests.RequestException:
        pass
    assert first.requests
    nothing_reached(second)
