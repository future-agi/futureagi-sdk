"""``sandbox_task(spec)``: the ``async def task(row, ctx)`` that runs one trial in its own sandbox.

A trial takes a slot of the batch's gate, creates the sandbox, writes ``row.json`` and the spec's
files, runs the agent (a command inside, or the caller's function outside) and the verifier, reads
the reward, and deletes the sandbox in ``finally``. The slot is released only after the delete
returns: the engine frees its own slot without waiting for an abandoned task.

Nothing is re-sent. The one call made again is a create refused with 409 ``quota_exceeded``
(nothing was created), within ``quota_wait_s``. A sandbox error the engine would count as transient
is raised as a recorded trial error, so the engine does not run the whole trial (a new sandbox, the
agent again) a second time; any other error (a 429 from the caller's own model) keeps the engine's
own handling. Before the verifier runs, the reward file is removed, so only the verifier's own file
counts. Env values never reach the output or a span.
"""

from __future__ import annotations

import asyncio
import inspect
import sys
import time
import uuid
from contextlib import contextmanager
from typing import Any, Callable, Dict, Iterator, List, Mapping, Optional, Tuple

from fi.experiments.errors import UsageError
from fi.experiments.sandbox._runner import Closer, Sandboxes, quietly
from fi.experiments.sandbox._spec import (
    REFUSED_ENV,
    REWARD_MAX_BYTES,
    ROW_FILE,
    SandboxEval,
    command_record,
    describe,
    fit_name,
    parse_reward,
    positive,
    row_json,
)

#: Sandboxes at once when neither ``max_active`` nor the settings say (the hosted workspace cap).
DEFAULT_MAX_ACTIVE = 2
#: The wait between creates refused with 409 ``quota_exceeded`` when the server sends no hint.
QUOTA_DELAY_S = 5.0

_sleep = asyncio.sleep  # the quota wait's clock; tests replace both
_clock = time.monotonic


class _Phases:
    """``phases_ms`` in the output, and a child span per phase under the trial's root span when the
    trial has one and OpenTelemetry is importable. A span carries the error type, never a message."""

    def __init__(self, parent: Any, out: Dict[str, Any]) -> None:
        self.parent, self.sandbox_id = parent, None
        self.ms: Dict[str, int] = out.setdefault("phases_ms", {})
        self.tracer = _tracer() if parent is not None else None

    @contextmanager
    def phase(self, name: str) -> Iterator[Any]:
        started, span = time.monotonic(), None
        if self.tracer is not None:
            from opentelemetry import trace

            attrs = {"sandbox.id": self.sandbox_id} if self.sandbox_id else {}
            span = self.tracer.start_span("sandbox." + name, context=trace.set_span_in_context(self.parent),
                                          attributes=attrs)
        try:
            yield span
        except BaseException as exc:
            if span is not None:
                from opentelemetry.trace import Status, StatusCode

                span.set_status(Status(StatusCode.ERROR, type(exc).__name__))
            raise
        finally:
            self.ms[name] = int((time.monotonic() - started) * 1000)
            if span is not None:
                span.end()


def _tracer() -> Any:
    try:
        from opentelemetry import trace

        from fi.experiments._tracing.routing import current_delegate
    except ImportError:
        return None
    return (current_delegate() or trace.get_tracer_provider()).get_tracer("fi.experiments.sandbox")


def _traceparent(span: Any) -> Dict[str, str]:
    """``TRACEPARENT`` / ``TRACESTATE`` of ``span`` (no baggage); nothing without a span."""
    try:
        from opentelemetry import propagate, trace
    except ImportError:
        return {}
    carrier: Dict[str, str] = {}
    if span is not None:
        propagate.inject(carrier, context=trace.set_span_in_context(span))
    return {k.upper(): v for k, v in carrier.items() if k in ("traceparent", "tracestate")}


def _stop_if_cancelled(ctx: Any, before: str) -> None:
    if ctx.cancelled.is_set():
        from fi.experiments._log_results import RecordedTrialError

        raise RecordedTrialError("cancelled", f"the trial was cancelled before {before}")


class _Batch:
    """What one ``sandbox_task`` shares across its trials: the limits, the slot gate, the names."""

    def __init__(self, spec: SandboxEval, max_active: Optional[int], quota_wait_s: float,
                 batch_id: Optional[str], factory: Optional[Callable[[], Any]]) -> None:
        if not isinstance(spec, SandboxEval):
            raise UsageError("sandbox_task() takes a SandboxEval(...)")
        if max_active is not None and positive(max_active) is None:
            raise UsageError("max_active must be a whole number, at least 1")
        if isinstance(quota_wait_s, bool) or not isinstance(quota_wait_s, (int, float)) or quota_wait_s < 0:
            raise UsageError("quota_wait_s must be 0 (no wait) or more seconds")
        if factory is not None and not callable(factory):
            raise UsageError("client_factory= takes a function that builds the client inside the running loop")
        batch_id = uuid.uuid4().hex[:8] if batch_id is None else batch_id
        if not isinstance(batch_id, str) or not 1 <= len(batch_id) <= 16 or fit_name(batch_id) != batch_id \
                or batch_id != batch_id.strip():
            raise UsageError("batch_id must be 1 to 16 printable characters")
        self.spec, self.given, self.quota_wait_s = spec, max_active, float(quota_wait_s)
        self.batch_id, self.prefix = batch_id, f"{spec.name_prefix}-{batch_id}-"
        self.sandboxes = Sandboxes(factory)
        self._limits: Optional[Tuple[int, Optional[int]]] = None
        self._loop: Any = None
        self._lock: Optional[asyncio.Lock] = None
        self._gate: Optional[asyncio.Semaphore] = None

    async def limits(self) -> Tuple[int, Optional[int]]:
        """(sandboxes at once, the workspace's longest command in seconds or None), read once."""
        if self._limits is None:
            from fi.sandbox import ConfigurationError, SandboxError

            try:
                raw = await self.sandboxes.settings()
            except ConfigurationError:
                raise
            except SandboxError:  # unreadable settings: the defaults; a create says what is wrong
                raw = None
            caps = raw.get("caps") if isinstance(raw, Mapping) else None
            caps = caps if isinstance(caps, Mapping) else {}
            command = caps.get("exec") if isinstance(caps.get("exec"), Mapping) else {}
            self._limits = (self.given or positive(caps.get("maxActiveSandboxes")) or DEFAULT_MAX_ACTIVE,
                            positive(command.get("maxTimeoutSeconds")))
        longest, spec = self._limits[1], self.spec
        for name, used in (("agent_timeout_s", spec.agent_command is not None),
                           ("verifier_timeout_s", spec.verifier is not None)):
            if used and longest is not None and getattr(spec, name) > longest:
                from fi.sandbox import ConfigurationError

                raise ConfigurationError(
                    f"{name}={getattr(spec, name)} is longer than this workspace lets a command run "
                    f"({longest} s, caps.exec.maxTimeoutSeconds); lower it", code="timeout_above_cap")
        return self._limits

    async def _slot_gate(self) -> asyncio.Semaphore:
        loop = asyncio.get_running_loop()
        if self._loop is not loop:  # one gate per event loop (each run() drives its own)
            self._loop, self._lock, self._gate = loop, asyncio.Lock(), None
        async with self._lock:  # type: ignore[union-attr]
            max_active, _ = await self.limits()
            if self._gate is None:
                self._gate = asyncio.Semaphore(max_active)
        return self._gate

    def name_for(self, ctx: Any) -> str:
        return fit_name(f"{self.prefix}{ctx.example_id}-{ctx.trial}")

    async def trial(self, row: Any, ctx: Any) -> Dict[str, Any]:
        from fi.experiments._engine_pool import transient_info
        from fi.experiments._log_results import RecordedTrialError
        from fi.sandbox import SandboxError

        gate = await self._slot_gate()
        await gate.acquire()
        slot = {"held": True, "deferred": False}

        def release(_: Any = None) -> None:
            if slot["held"]:
                slot["held"] = False
                gate.release()

        out: Dict[str, Any] = {"sandbox_id": None, "deleted": False}
        try:
            await self._run(row, ctx, out, slot, release)
        except Exception as exc:
            # a sandbox error the engine would retry by running the whole trial again; the caller's
            # own errors (its model's 429 or 5xx) keep the engine's backoff and limiter
            if isinstance(exc, SandboxError) and transient_info(exc).transient:
                raise RecordedTrialError(type(exc).__name__, describe(exc)) from exc
            raise
        finally:
            if not slot["deferred"]:
                release()
        return out

    async def _run(self, row: Any, ctx: Any, out: Dict[str, Any], slot: Dict[str, bool],
                   release: Callable[..., None]) -> None:
        phases = _Phases(getattr(ctx, "span", None), out)
        with phases.phase("create"):
            sbx, close = await self._create(ctx)
        out["sandbox_id"] = phases.sandbox_id = sbx.id
        try:
            await self._work(row, ctx, sbx, out, phases)
        finally:
            job = asyncio.ensure_future(self._delete(sbx, close, out, phases))
            try:
                await asyncio.shield(job)
            except asyncio.CancelledError:  # a second cancel: the delete goes on, then frees the slot
                slot["deferred"] = True
                job.add_done_callback(release)
                raise

    async def _create(self, ctx: Any) -> Tuple[Any, Closer]:
        from fi.sandbox import ConnectionError, QuotaExceededError

        spec = self.spec
        body = {k: v for k, v in (("name", self.name_for(ctx)), ("template", spec.template),
                                  ("size", spec.size), ("image", spec.image)) if v is not None}
        deadline: Optional[float] = None
        while True:
            try:
                return await self.sandboxes.create(body)
            except QuotaExceededError as exc:  # a definitive 409: nothing was created
                now = _clock()
                deadline = now + self.quota_wait_s if deadline is None else deadline
                if deadline - now <= 0 or ctx.cancelled.is_set():
                    raise
                hint = exc.retry_after_seconds
                end = now + min(float(hint) if isinstance(hint, (int, float)) and hint > 0 else QUOTA_DELAY_S,
                                deadline - now)
                while not ctx.cancelled.is_set() and _clock() < end:
                    await _sleep(min(1.0, end - _clock()))
                _stop_if_cancelled(ctx, "a sandbox slot was free")
            except ConnectionError as exc:  # never a second create
                sent = getattr(exc, "possibly_applied", True)
                note = ("whether the sandbox was created is unknown: the end-of-run sweep deletes it if "
                        "it was") if sent else "the request was not sent, so no sandbox was created"
                error = type(exc)(f"{exc}; {note}")
                for field in ("base_url", "reason", "kind", "possibly_applied", "idempotency_key"):
                    setattr(error, field, getattr(exc, field, None))
                error.operation = "sandboxes.create"
                raise error from exc

    async def _work(self, row: Any, ctx: Any, sbx: Any, out: Dict[str, Any], phases: _Phases) -> None:
        spec = self.spec
        _stop_if_cancelled(ctx, "setup")
        with phases.phase("setup"):
            await sbx.files.write(ROW_FILE, row_json(row))  # a write creates missing parent folders
            files = spec.files(row) if callable(spec.files) else (spec.files or {})
            for path, data in dict(files).items():
                if not isinstance(path, str) or not path.startswith("/") or not isinstance(data, (str, bytes)):
                    raise UsageError("files= maps an absolute path to text or bytes")
                await sbx.files.write(path, data)
        _stop_if_cancelled(ctx, "the agent")
        ran: Optional[Dict[str, Any]] = None  # the last command's record, for reward_from_exit
        with phases.phase("agent") as span:
            if spec.agent_command is not None:
                command = spec.agent_command(row) if callable(spec.agent_command) else spec.agent_command
                ran = out["agent"] = await self._command(command, row, ctx, sbx, spec.agent_timeout_s, span)
            else:
                value = spec.agent(row, sbx, ctx)  # type: ignore[misc]
                out["agent"] = {"result": await value if inspect.isawaitable(value) else value}
        if spec.verifier is not None:
            _stop_if_cancelled(ctx, "the verifier")
            with phases.phase("verify") as span:
                await self._clear_reward(sbx)
                command = spec.verifier(row) if callable(spec.verifier) else spec.verifier
                ran = out["verifier"] = await self._command(command, row, ctx, sbx, spec.verifier_timeout_s, span)
        out["rewards"], problem = await self._rewards(sbx, ran)
        if problem:
            out["reward_error"] = problem

    async def _command(self, command: str, row: Any, ctx: Any, sbx: Any, timeout_s: int,
                       span: Any) -> Dict[str, Any]:
        result = await sbx.commands.run(command, cwd=self.spec.command_cwd, env=self.env(row, ctx, span),
                                        timeout_seconds=timeout_s)
        record = command_record(result, self.spec.max_output_chars)
        if span is not None:
            span.set_attribute("sandbox.shell_exit_code", record["shell_exit_code"])
        return record

    def env(self, row: Any, ctx: Any, span: Any = None) -> Dict[str, str]:
        """A command's env: the spec's plain variables, then ``EVAL_*`` and the trace context."""
        from fi.sandbox import ConfigurationError

        given = self.spec.env(row, ctx) if callable(self.spec.env) else (self.spec.env or {})
        env: Dict[str, str] = {}
        for name, value in dict(given).items():
            if not isinstance(name, str) or not isinstance(value, str):
                raise ConfigurationError("env= maps variable names to text values", code="invalid_option")
            if name.upper() in REFUSED_ENV:
                raise ConfigurationError(f"env= may not set {name}: a command's env holds plain, non-secret "
                                         "variables only, never credentials", code="secret_in_env")
            env[name] = value
        env.update(EVAL_ROW_FILE=ROW_FILE, EVAL_EXAMPLE_ID=str(ctx.example_id), EVAL_TRIAL=str(ctx.trial),
                   EVAL_RUN_ID=str(ctx.run_id))
        if self.spec.trace_env:
            env.update(_traceparent(span))
        return env

    async def _clear_reward(self, sbx: Any) -> None:
        """Remove a reward file the agent left, so a verifier that writes none scores by its exit.
        Any error other than "no such file" fails the trial: a wrong score is worse."""
        from fi.sandbox import NotFoundError

        try:
            await sbx.files.remove(self.spec.reward_path)
        except NotFoundError:
            pass

    async def _rewards(self, sbx: Any, ran: Optional[Dict[str, Any]]) -> Tuple[Dict[str, float], Optional[str]]:
        from fi.sandbox import NotFoundError

        try:
            return parse_reward(await sbx.files.read(self.spec.reward_path, max_bytes=REWARD_MAX_BYTES))
        except NotFoundError:  # no reward file
            pass
        if self.spec.reward_from_exit and ran is not None:
            return {"reward": 1.0 if ran["shell_exit_code"] == 0 else 0.0}, None
        return {}, None

    async def _delete(self, sbx: Any, close: Closer, out: Dict[str, Any], phases: _Phases) -> None:
        try:
            with phases.phase("delete"):
                await sbx.delete()
            out["deleted"] = True
        except Exception as exc:  # recorded; the id stays for the sweep
            out["deleted"], out["delete_error"] = False, describe(exc)
        finally:
            await quietly(sbx.aclose, close)

    async def sweep(self) -> List[str]:
        """Delete this batch's sandboxes that are still there (one stderr line each); their ids."""
        handles, close = await self.sandboxes.listed()
        gone: List[str] = []
        try:
            for sbx in handles:
                name = str(sbx.info.get("name") or "")
                if not name.startswith(self.prefix) or sbx.state == "destroyed":
                    continue
                # The listed id, read before the delete: the handle takes on the record the delete returns.
                ident = sbx.id
                try:
                    await sbx.delete()
                except Exception as exc:
                    print(f"fi.experiments.sandbox: could not delete leftover sandbox {ident} ({name}): "
                          f"{describe(exc)}", file=sys.stderr)
                    continue
                gone.append(ident)
                print(f"fi.experiments.sandbox: deleted leftover sandbox {ident} ({name})", file=sys.stderr)
        finally:
            await quietly(*(sbx.aclose for sbx in handles), close)
        return gone


def sandbox_task(spec: SandboxEval, *, max_active: Optional[int] = None, quota_wait_s: float = 120.0,
                 batch_id: Optional[str] = None,
                 client_factory: Optional[Callable[[], Any]] = None) -> Callable[[Any, Any], Any]:
    """The ``async def task(row, ctx)`` for ``fi.experiments.run``: one sandbox per (row, trial).

    ``max_active``: sandboxes at once (default ``caps.maxActiveSandboxes`` from the settings, else 2).
    ``quota_wait_s``: how long a create refused with 409 ``quota_exceeded`` waits for a free slot
    (0: no wait). ``client_factory``: builds the client inside the running loop (default: the
    environment). The function also has ``.batch_id`` and ``.sweep()`` (async: deletes what this
    batch left; run it after the run)."""
    batch = _Batch(spec, max_active, quota_wait_s, batch_id, client_factory)

    async def task(row: Any, ctx: Any) -> Dict[str, Any]:
        return await batch.trial(row, ctx)

    task.__name__ = task.__qualname__ = "sandbox_task"
    task.batch_id = batch.batch_id  # type: ignore[attr-defined]
    task.sweep = batch.sweep  # type: ignore[attr-defined]
    task.batch = batch  # type: ignore[attr-defined]
    return task


__all__ = ["sandbox_task", "DEFAULT_MAX_ACTIVE", "QUOTA_DELAY_S"]
