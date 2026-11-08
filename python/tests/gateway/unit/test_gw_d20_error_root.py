"""D-20: every gateway error is an ``SDKException``; str, repr, args and pickling are 1.0's.

The comparison is against the agentcc 1.0.0 golden itself
(``tests/fixtures/gateway/golden/py-agentcc-1.0.0/surface.json``, case ``surface.errors``),
observed with the parity recorder's own observer and the same constructor arguments, so
the only allowed difference is ``SDKException`` in the MRO.
"""

from __future__ import annotations

import inspect
import json
import pickle
from pathlib import Path

import pytest

import fi.gateway as gw
from fi._sdk_exception import SDKException
from fi.errors import FutureAGIError

GOLDEN = (
    Path(__file__).resolve().parents[4] / "tests" / "fixtures" / "gateway" / "golden"
)
SURFACE = json.loads((GOLDEN / "py-agentcc-1.0.0" / "surface.json").read_text())
GOLDEN_ERRORS = SURFACE["cases"]["surface.errors[sync]"]["result"]

D02_FIELDS = {
    "type": None,
    "code": None,
    "param": None,
    "body": None,
    "request_id": None,
}
# The gateway's error classes. AgentCCDeprecationWarning is a FutureWarning the agentcc
# 2.0 package emits on import, not a gateway error.
NOT_ERRORS = {"AgentCCDeprecationWarning"}
# Billing and budget refusals added after agentcc 1.0.0 (one-key credits); no golden entry.
BILLING_ERRORS = {
    "InsufficientCreditsError", "AgentBudgetExhaustedError", "BudgetExceededError",
    "FutureAGICreditsOffError",
}
ALL_ERROR_NAMES = sorted(
    n
    for n in gw.__all__
    if n not in NOT_ERRORS
    and inspect.isclass(getattr(gw, n))
    and issubclass(getattr(gw, n), BaseException)
)
# The 17 errors that agentcc 1.0.0 shipped; golden comparisons apply to these only.
ERROR_NAMES = [n for n in ALL_ERROR_NAMES if n not in BILLING_ERRORS]


def _construct(name: str) -> BaseException:
    from parity.cases.surface import ERROR_ARGS

    args, kwargs = ERROR_ARGS.get(
        name,
        (
            (),
            {
                "message": f"{name} message",
                "status_code": 418,
                "type": "t",
                "code": "c",
                "param": "p",
                "body": {"error": {"message": "m"}},
                "request_id": "req-1",
            },
        ),
    )
    return getattr(gw, name)(*args, **kwargs)


def test_the_seventeen_errors_are_all_here() -> None:
    assert len(ERROR_NAMES) == 17
    assert set(ERROR_NAMES) == set(GOLDEN_ERRORS)
    assert set(ALL_ERROR_NAMES) == set(GOLDEN_ERRORS) | BILLING_ERRORS
    assert len(ALL_ERROR_NAMES) == 21
    exceptions = {
        n
        for n in gw.__all__
        if inspect.isclass(getattr(gw, n)) and issubclass(getattr(gw, n), BaseException)
    }
    assert exceptions - set(ALL_ERROR_NAMES) == NOT_ERRORS
    assert not issubclass(gw.AgentCCDeprecationWarning, gw.AgentCCError)


@pytest.mark.parametrize("name", ALL_ERROR_NAMES)
def test_each_error_is_an_sdk_exception(name: str) -> None:
    cls = getattr(gw, name)
    assert issubclass(cls, SDKException)
    assert issubclass(cls, FutureAGIError)
    assert issubclass(cls, gw.AgentCCError)


@pytest.mark.parametrize("name", ERROR_NAMES)
def test_mro_is_1_0_with_sdk_exception_under_agentcc_error(name: str) -> None:
    expected = list(GOLDEN_ERRORS[name]["mro"])
    expected.insert(expected.index("AgentCCError") + 1, "SDKException")
    assert [c.__qualname__ for c in getattr(gw, name).__mro__] == expected


@pytest.mark.parametrize("name", ERROR_NAMES)
def test_str_repr_args_attrs_and_pickle_equal_the_golden(name: str) -> None:
    from parity._observe import observe_exception

    observed = observe_exception(_construct(name))
    golden = dict(GOLDEN_ERRORS[name])
    if name == "StreamError":
        # D-02 adds the gateway frame's fields, None when a StreamError is built bare
        golden["attrs"] = {**golden["attrs"], **D02_FIELDS}
    for key in ("str", "repr", "args", "attrs", "pickle", "__exception__"):
        assert observed[key] == golden[key], key


def test_an_empty_message_stays_empty() -> None:
    """SDKException.__init__ would put its default text in args; AgentCCError does not."""
    err = gw.AgentCCError("")
    assert err.args == ("",)
    assert str(err) == ""
    assert err.get_message() == ""


def test_get_message_is_the_message() -> None:
    assert gw.AgentCCError("boom").get_message() == "boom"
    err = gw.BadRequestError(message="bad", status_code=400)
    assert err.get_message() == "bad"
    assert str(err) == "Error code: 400 - bad"


def test_implicit_exception_context_is_kept() -> None:
    """Assigning __cause__ (as SDKException.__init__ does) would suppress the context."""
    with pytest.raises(gw.APIConnectionError) as info:
        try:
            raise OSError("socket closed")
        except OSError:
            raise gw.APIConnectionError("Connection error")
    assert isinstance(info.value.__context__, OSError)
    assert info.value.__suppress_context__ is False
    assert info.value.__cause__ is None


def test_explicit_cause_still_works() -> None:
    root = TimeoutError("read")
    try:
        raise gw.APITimeoutError("Request timed out") from root
    except gw.APITimeoutError as err:
        assert err.__cause__ is root


def test_a_simple_error_round_trips_through_pickle() -> None:
    back = pickle.loads(pickle.dumps(gw.StreamError("stream broke")))
    assert type(back) is gw.StreamError and str(back) == "stream broke"
