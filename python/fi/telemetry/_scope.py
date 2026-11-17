"""Explicit agent boundaries, reusable as sync/async managers and decorators."""
from __future__ import annotations

import functools
import inspect
import sys
from time import time_ns

from . import _otel
from ._identity import context_attrs
from ._registry import State


class agent_scope:
    def __init__(self, *, agent=None, context=None):
        self.agent, self.context = agent, context
        self._token = self._carrier_token = None
        self._resume_state = self._resume_context = None

    def __enter__(self):
        self._token = self._carrier_token = None
        if _otel.mode() == "off" or sys.modules.get("opentelemetry.trace") is None:
            return self
        try:
            if self._resume_state is not None:
                self.state = self._resume_state
                self._token = _otel._scope.set(self.state)
                context = sys.modules.get("opentelemetry.context")
                if context is not None and self._resume_context is not None and _otel.mode() == "on":
                    self._carrier_token = context.attach(self._resume_context)
                return self
            parent = _otel._scope.get()
            attrs = dict(parent.attrs) if parent else {}
            otel_context = sys.modules.get("opentelemetry.context")
            value = otel_context.get_value(_otel.CARRIER_KEY) if otel_context else None
            if value and value.get("v") == 1:
                attrs.update(_otel.allowlisted(value.get("attrs", {})))
            if self.context is not None:
                attrs = {k: v for k, v in attrs.items() if not k.startswith(("fi.context.", "fi.skills.", "gen_ai.agent."))}
                attrs.update(context_attrs(self.context))
                attrs["gen_ai.agent.name"] = self.context.identity.name
            if self.agent is not None:
                attrs["gen_ai.agent.name"] = str(self.agent)
            self.state = State(attrs=_otel.allowlisted(attrs))
            self.state.agent_source = "agent_scope" if self.agent is not None else "context" if self.context is not None else getattr(parent, "agent_source", "none")
            self._token = _otel._scope.set(self.state)
            self._carrier_token = _otel.publish(self.state, reset=self.context is not None)
            provider, _ = _otel.select_provider()
            _otel.install(provider)
            current = _otel.current()
            if self.context is not None and current is not None and current.is_recording():
                from ._hooks import load_context
                load_context(self.context, self.state, current, provider, time_ns(), enrich=False)
        except Exception:
            _otel.debug_failure()
        return self

    def __exit__(self, *exc):
        try:
            context = sys.modules.get("opentelemetry.context")
            if self._carrier_token is not None and context is not None:
                context.detach(self._carrier_token)
            if self._token is not None:
                _otel._scope.reset(self._token)
        except Exception:
            _otel.debug_failure()
        return False

    async def __aenter__(self):
        return self.__enter__()

    async def __aexit__(self, *exc):
        return self.__exit__(*exc)

    def __call__(self, function):
        def fresh():
            return type(self)(agent=self.agent, context=self.context)
        if inspect.isasyncgenfunction(function):
            @functools.wraps(function)
            async def generator(*args, **kwargs):
                # Detach before yielding to the caller; its unrelated spans must
                # not inherit this generator's scope. Keep the state across steps.
                iterator = function(*args, **kwargs)
                scope = fresh()
                try:
                    while True:
                        async with scope:
                            try:
                                item = await iterator.__anext__()
                            except StopAsyncIteration:
                                break
                            scope._resume_state = getattr(scope, "state", None)
                            context = sys.modules.get("opentelemetry.context")
                            scope._resume_context = context.get_current() if context else None
                        yield item
                finally:
                    async with scope:
                        await iterator.aclose()
            return generator
        if inspect.iscoroutinefunction(function):
            @functools.wraps(function)
            async def coroutine(*args, **kwargs):
                async with fresh():
                    return await function(*args, **kwargs)
            return coroutine
        if inspect.isgeneratorfunction(function):
            raise TypeError("Wrap the body of a sync generator in agent_scope")
        @functools.wraps(function)
        def wrapped(*args, **kwargs):
            with fresh():
                return function(*args, **kwargs)
        return wrapped
