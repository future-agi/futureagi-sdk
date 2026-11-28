"""A partial Langfuse key pair stops only the Langfuse configuration call.

The environment holds tenant A's Future AGI key pair, ``FI_BASE_URL`` names loopback listener FI,
and ``LANGFUSE_HOST`` names loopback listener LF. ``LANGFUSE_PUBLIC_KEY`` or ``LANGFUSE_SECRET_KEY``
is set without the other. ``Evaluator``, ``Protect`` and ``Guardrails`` with a turing model build
and evaluate: FI receives A's keys and 0 bytes of the Langfuse key, LF receives no connection.
``Evaluator.evaluate(platform="langfuse", ...)`` raises :class:`fi.errors.AuthError` before any
request, so FI and LF receive nothing.

``Guardrails`` passes an :class:`fi.errors.AuthError` raised while it builds a backend to the caller
as it is; any other failure to build a backend raises ``RuntimeError``.

Every key is built at run time with ``secrets.token_hex``, one distinct marker per tenant.
"""

from __future__ import annotations

import secrets
from typing import Callable, Dict, Iterator

import pytest

import fi.errors
from fi.evals import Evaluator
from fi.evals.guardrails.base import Guardrails
from fi.evals.guardrails.config import GuardrailModel, GuardrailsConfig
from fi.evals.protect import Protect
from tests.core.redirect_sinks import _Listener

TRACE_ID = "0af7651916cd43dd8448eb211c80319c"
SPAN_ID = "b7ad6b7169203331"
LANGFUSE_NAMES = ("LANGFUSE_PUBLIC_KEY", "LANGFUSE_SECRET_KEY")


def _marker(tag: str) -> str:
    return "mk" + f"-{tag}-" + secrets.token_hex(8)


def _marker_bytes(listener: _Listener, markers) -> int:
    return sum(raw.count(m.encode()) * len(m.encode()) for _, raw in list(listener.records) for m in markers)


@pytest.fixture
def world(monkeypatch: pytest.MonkeyPatch) -> Iterator[Dict[str, object]]:
    fi_sink, lf_sink = _Listener("127.0.0.1"), _Listener("127.0.0.1")
    keys = {"api": _marker("A"), "secret": _marker("A")}
    langfuse = {name: _marker("LF") for name in LANGFUSE_NAMES}
    for name in (*LANGFUSE_NAMES, "LANGFUSE_HOST"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("FI_API_KEY", keys["api"])
    monkeypatch.setenv("FI_SECRET_KEY", keys["secret"])
    monkeypatch.setenv("FI_BASE_URL", f"http://127.0.0.1:{fi_sink.port}")
    monkeypatch.setenv("LANGFUSE_HOST", f"http://127.0.0.1:{lf_sink.port}")
    try:
        yield {"fi": fi_sink, "lf": lf_sink, "keys": keys, "langfuse": langfuse, "monkeypatch": monkeypatch}
    finally:
        fi_sink.close()
        lf_sink.close()


def _evaluate(_: Dict[str, object]) -> None:
    try:
        Evaluator().evaluate("toxicity", {"output": "x"}, model_name="turing_flash")
    except fi.errors.AuthError:
        raise
    except Exception:  # the listener answers {}; the bytes each listener read are what this file checks
        pass


def _protect(_: Dict[str, object]) -> None:
    client = Protect()
    try:
        client.protect("some text to screen", use_flash=True, timeout=5000)
    except fi.errors.AuthError:
        raise
    except Exception:  # as above
        pass


def _guardrails(model: GuardrailModel) -> Callable[[Dict[str, object]], None]:
    def run(_: Dict[str, object]) -> None:
        guardrails = Guardrails(config=GuardrailsConfig(models=[model]))
        try:
            guardrails.screen_input("a short message")
        except fi.errors.AuthError:
            raise
        except Exception:  # as above
            pass

    return run


CLIENTS: Dict[str, Callable[[Dict[str, object]], None]] = {
    "evaluator": _evaluate,
    "protect": _protect,
    "guardrails-turing_flash": _guardrails(GuardrailModel.TURING_FLASH),
    "guardrails-turing_safety": _guardrails(GuardrailModel.TURING_SAFETY),
}


@pytest.mark.parametrize("present", LANGFUSE_NAMES)
@pytest.mark.parametrize("client", sorted(CLIENTS))
def test_one_langfuse_key_in_the_environment_leaves_other_evaluations_working(world, client: str, present: str) -> None:
    world["monkeypatch"].setenv(present, world["langfuse"][present])
    raised = None
    try:
        CLIENTS[client](world)
    except Exception as exc:  # the type is checked after the listeners are read
        raised = exc
    fi_sink, lf_sink, keys = world["fi"], world["lf"], world["keys"]
    counts = {
        "fi_requests": len(fi_sink.records),
        "fi_requests_with_both_keys": sum(1 for _, raw in fi_sink.records
                                          if all(k.encode() in raw for k in keys.values())),
        "langfuse_bytes_at_fi": _marker_bytes(fi_sink, world["langfuse"].values()),
        "lf_requests": len(lf_sink.records),
    }
    assert raised is None, (repr(raised), counts)
    assert counts["fi_requests"] >= 1, counts
    assert counts["fi_requests_with_both_keys"] == counts["fi_requests"], counts
    assert counts["langfuse_bytes_at_fi"] == 0, counts
    assert counts["lf_requests"] == 0, counts


PARTIAL_PAIRS = {
    "env-public-only": ({"LANGFUSE_PUBLIC_KEY": "LANGFUSE_PUBLIC_KEY"}, {}, "LANGFUSE_SECRET_KEY"),
    "env-secret-only": ({"LANGFUSE_SECRET_KEY": "LANGFUSE_SECRET_KEY"}, {}, "LANGFUSE_PUBLIC_KEY"),
    "argument-public-with-env-pair": (
        {"LANGFUSE_PUBLIC_KEY": "LANGFUSE_PUBLIC_KEY", "LANGFUSE_SECRET_KEY": "LANGFUSE_SECRET_KEY"},
        {"langfuse_public_key": "argument"}, "langfuse_secret_key"),
}


@pytest.mark.parametrize("case", sorted(PARTIAL_PAIRS))
def test_the_langfuse_configuration_call_refuses_a_partial_pair_before_any_request(world, case: str) -> None:
    pytest.importorskip("opentelemetry.trace")
    env, arguments, missing = PARTIAL_PAIRS[case]
    for name, source in env.items():
        world["monkeypatch"].setenv(name, world["langfuse"][source])
    argument_markers = {name: _marker("LFA") for name in arguments}

    evaluator = Evaluator(**argument_markers)
    with pytest.raises(fi.errors.AuthError) as raised:
        evaluator.evaluate(
            "toxicity", {"output": "x"}, model_name="turing_flash", platform="langfuse",
            custom_eval_name="answer-check", trace_id=TRACE_ID, span_id=SPAN_ID,
        )

    message = str(raised.value)
    assert message.endswith(f"Missing: {missing}")
    planted = [*world["langfuse"].values(), *argument_markers.values()]
    assert not any(m in message for m in planted)
    assert (len(world["fi"].records), len(world["lf"].records)) == (0, 0)


class _PlantedAuthError(fi.errors.AuthError):
    pass


def test_guardrails_passes_an_auth_error_from_a_backend_through_as_it_is(world) -> None:
    import fi.evals.guardrails.registry as registry

    planted = _PlantedAuthError("backend refused its keys")

    class RefusingBackend:
        def __init__(self, **_: object) -> None:
            raise planted

    class BrokenBackend:
        def __init__(self, **_: object) -> None:
            raise ValueError("backend could not start")

    monkeypatch = world["monkeypatch"]
    monkeypatch.setattr(registry, "get_backend_class", lambda model: RefusingBackend)
    with pytest.raises(fi.errors.AuthError) as raised:
        Guardrails(config=GuardrailsConfig(models=[GuardrailModel.TURING_FLASH]))
    assert raised.value is planted

    monkeypatch.setattr(registry, "get_backend_class", lambda model: BrokenBackend)
    with pytest.raises(RuntimeError, match="^Failed to create backend for turing_flash: backend could not start$"):
        Guardrails(config=GuardrailsConfig(models=[GuardrailModel.TURING_FLASH]))
    assert (len(world["fi"].records), len(world["lf"].records)) == (0, 0)
