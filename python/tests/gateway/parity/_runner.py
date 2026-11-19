"""Run one catalog case in one mode and return its observation.

A case is a plain function ``fn(ctx)``. The same body serves the sync and the
async client: ``ctx.call`` runs a coroutine on the case's own event loop and
``ctx.drain`` consumes a sync or async iterator until it ends or raises.
"""

from __future__ import annotations

import asyncio
import importlib
import inspect
import logging
import os
import warnings
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from ._determinism import Determinism
from ._observe import clean, observe
from ._wire import Wire

KEY = (
    "parity-gateway-key"  # never a credential shape: gitleaks and the pull scan pass it
)
BASE_URL = "https://gateway.example.test"
ENV_PREFIXES = ("AGENTCC_", "FI_", "OPENAI_")


@dataclass
class Case:
    id: str
    area: str
    fn: Callable[[Ctx], Any]
    modes: tuple[str, ...] = ("sync",)
    env: dict[str, str] = field(default_factory=dict)
    replies: list[dict[str, Any]] = field(default_factory=list)


def exercises(
    *paths: str,
) -> Callable[[Callable[[Ctx], Any]], Callable[[Ctx], Any]]:
    """Mark a case function with the client methods it calls (dotted paths from
    the client, such as ``batches.create_and_wait`` or ``aclose``), so the catalog
    test can prove every method of the recorded client tree has a case."""

    def mark(fn: Callable[[Ctx], Any]) -> Callable[[Ctx], Any]:
        fn.exercises = paths  # type: ignore[attr-defined]
        return fn

    return mark


class Ctx:
    def __init__(
        self, root: str, mode: str, wire: Wire, loop: asyncio.AbstractEventLoop | None
    ) -> None:
        self.root = root
        self.mode = mode
        self.wire = wire
        self._loop = loop
        self.T = importlib.import_module(root)

    # -- target access ---------------------------------------------------------
    def mod(self, name: str = "") -> Any:
        return importlib.import_module(f"{self.root}.{name}" if name else self.root)

    def client(self, **opts: Any) -> Any:
        opts.setdefault("api_key", KEY)
        opts.setdefault("base_url", BASE_URL)
        for k in [k for k, v in opts.items() if v is _OMIT]:
            del opts[k]
        cls = self.T.AsyncAgentCC if self.mode == "async" else self.T.AgentCC
        return cls(**opts)

    def script(self, *replies: dict[str, Any]) -> None:
        self.wire.script(*replies)

    # -- execution -------------------------------------------------------------
    def run(self, value: Any) -> Any:
        if inspect.isawaitable(value):
            assert self._loop is not None, "awaitable in sync mode"
            return self._loop.run_until_complete(_await(value))
        return value

    def call(self, target: Any, path: str = "", *args: Any, **kwargs: Any) -> Any:
        fn = target
        for part in [p for p in path.split(".") if p]:
            fn = getattr(fn, part)
        return self.run(fn(*args, **kwargs))

    def enter(self, cm: Any) -> Any:
        if hasattr(cm, "__aenter__") and self.mode == "async":
            return self.run(cm.__aenter__())
        return cm.__enter__()

    def exit(self, cm: Any) -> None:
        if hasattr(cm, "__aexit__") and self.mode == "async":
            self.run(cm.__aexit__(None, None, None))
        else:
            cm.__exit__(None, None, None)

    def drain(self, it: Any, limit: int = 200) -> dict[str, Any]:
        items: list[Any] = []
        error = None
        try:
            if hasattr(it, "__aiter__"):

                async def collect() -> None:
                    async for item in it:
                        items.append(observe(item))
                        if len(items) >= limit:
                            break

                self.run(collect())
            else:
                for item in it:
                    items.append(observe(item))
                    if len(items) >= limit:
                        break
        except Exception as exc:  # the stream's failure is part of the observation
            error = observe(exc)
        return {"items": items, "error": error}

    def attempt(self, fn: Callable[[], Any]) -> dict[str, Any]:
        try:
            return {"ok": observe(fn())}
        except Exception as exc:
            return {"raised": observe(exc)}


_OMIT = object()


def omit() -> Any:
    """Use as an option value to leave api_key/base_url out of the constructor."""
    return _OMIT


async def _await(value: Any) -> Any:
    return await value


class _LogCapture(logging.Handler):
    def __init__(self) -> None:
        super().__init__(logging.DEBUG)
        self.records: list[list[str]] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append([record.name, record.levelname, clean(record.getMessage())])


def _isolated_env(extra: dict[str, str]) -> dict[str, str]:
    saved = dict(os.environ)
    for key in list(os.environ):
        if key.startswith(ENV_PREFIXES):
            del os.environ[key]
    os.environ.update(extra)
    return saved


def run_case(case: Case, root: str, mode: str) -> dict[str, Any]:
    import httpx

    saved_env = _isolated_env(case.env)
    wire = Wire(httpx)
    wire.script(*case.replies)
    det = Determinism(sync_clock=mode == "sync")
    loop = asyncio.new_event_loop() if mode == "async" else None
    logs = _LogCapture()
    loggers = [logging.getLogger("agentcc"), logging.getLogger("fi")]
    levels = [lg.level for lg in loggers]
    for lg in loggers:
        lg.addHandler(logs)
        lg.setLevel(logging.DEBUG)
    out: dict[str, Any] = {}
    try:
        wire.install()
        det.install()
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            ctx = Ctx(root, mode, wire, loop)
            try:
                out["result"] = observe(case.fn(ctx))
            except Exception as exc:
                out["raised"] = observe(exc)
        out["warnings"] = [
            [w.category.__qualname__, clean(str(w.message))] for w in caught
        ]
    finally:
        det.remove()
        wire.remove()
        for lg, level in zip(loggers, levels):
            lg.removeHandler(logs)
            lg.setLevel(level)
        if loop is not None:
            loop.run_until_complete(loop.shutdown_asyncgens())
            loop.close()
        os.environ.clear()
        os.environ.update(saved_env)
    out["requests"] = wire.requests
    out.update(det.report())
    if logs.records:
        out["logs"] = [
            r
            for r in logs.records
            if not r[0].startswith(("httpx", "httpcore", "asyncio"))
        ]
    if wire.replies:
        out["unused_replies"] = len(wire.replies)
    if not out["warnings"]:
        del out["warnings"]
    return out
