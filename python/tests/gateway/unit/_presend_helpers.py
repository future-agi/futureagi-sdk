"""Shared pre-send assertions; test cases keep their original module identities."""
from __future__ import annotations

import inspect

import pytest

from fi.gateway._gateway_config import GatewayConfig, LoadBalanceConfig, LoadBalanceTarget

ORIGIN = "https://gateway.example.test"
KEY = "synthetic-presend-api-value"
HEADER = "synthetic-presend-header-value"
VIRTUAL = "synthetic-presend-virtual-value"


async def resolve(value):
    return await value if inspect.isawaitable(value) else value


def config_with_key():
    with pytest.warns(DeprecationWarning):
        target = LoadBalanceTarget(model="test", virtual_key=VIRTUAL)
        config = GatewayConfig(load_balance=LoadBalanceConfig(targets=[target]))
    return config


def assert_safe_sdk_locals(error):
    pending, seen, leaks, count = [error], set(), [], 0
    while pending:
        exc = pending.pop()
        if exc is None or id(exc) in seen:
            continue
        seen.add(id(exc))
        pending.extend((exc.__cause__, exc.__context__))
        pending.extend(getattr(exc, "exceptions", ()))
        tb = exc.__traceback__
        while tb is not None:
            frame = tb.tb_frame
            if frame.f_globals.get("__name__", "").startswith("fi.gateway."):
                count += 1
                for name, value in frame.f_locals.items():
                    for render in (repr, str):
                        try:
                            text = render(value)
                        except Exception:
                            # Partially constructed clients have no released repr yet.
                            continue
                        if any(key in text for key in (KEY, HEADER, VIRTUAL)):
                            leaks.append((frame.f_code.co_name, name, render.__name__))
            tb = tb.tb_next
    assert count, "The original SDK traceback must remain available"
    assert not leaks, f"Secrets retained in SDK locals: {leaks}"


def caller_failure(call):
    caller_key = KEY
    caller_headers = {"X-Api-Key": HEADER}
    try:
        call()
    except BaseException as error:
        return error
    raise AssertionError("Expected a pre-send failure")


def assert_caller_untouched(error):
    tb = error.__traceback__
    while tb is not None and tb.tb_frame.f_code is not caller_failure.__code__:
        tb = tb.tb_next
    assert tb is not None
    assert tb.tb_frame.f_locals["caller_key"] == KEY
    assert tb.tb_frame.f_locals["caller_headers"] == {"X-Api-Key": HEADER}
