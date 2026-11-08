"""Runtime introspection resolves the public annotations of fi.gateway.

``typing.get_type_hints`` (what pydantic's ``validate_call``, sphinx autodoc and DI
frameworks call) evaluates a function's annotations in its module. A name imported only
under ``TYPE_CHECKING`` is missing there, so it raised ``NameError``: on
``AgentCC.session`` and ``AsyncAgentCC.session`` (``SessionContext``),
``chat.completions.stream`` (``StreamManager`` / ``AsyncStreamManager``), and the
callback hooks and ``RequestRecorder`` (``RequestOptions``). Those names are now real
imports. The sweep covers every public function and method of every public module, so
a new typing-only name fails here.

One exception is kept, with its reason: ``SessionContext.__init__`` names the two client
classes, whose modules import the session module, so it cannot import them back.
``client.session()`` builds it; the clients' own ``session`` hints resolve.
"""

from __future__ import annotations

import importlib
import inspect
import pkgutil
import subprocess
import sys
import typing
from pathlib import Path

import pytest

import fi.gateway

PYTHON_ROOT = Path(fi.gateway.__file__).resolve().parents[2]
CYCLE_EXCEPTIONS = {"fi.gateway._session.SessionContext.__init__"}


def _public_modules() -> list[str]:
    names = []
    for info in pkgutil.walk_packages(fi.gateway.__path__, "fi.gateway."):
        if ".management" in info.name:
            continue
        names.append(info.name)
    return sorted(names)


def _callables() -> dict[str, object]:
    found: dict[str, object] = {}
    for module_name in _public_modules():
        module = importlib.import_module(module_name)
        for name, obj in vars(module).items():
            if name.startswith("_") or getattr(obj, "__module__", None) != module_name:
                continue
            if inspect.isfunction(obj):
                found[f"{module_name}.{name}"] = obj
            elif inspect.isclass(obj):
                for attr, value in vars(obj).items():
                    if attr.startswith("_") and attr != "__init__":
                        continue
                    func = value.fget if isinstance(value, property) else value
                    if inspect.isfunction(func):
                        found[f"{module_name}.{name}.{attr}"] = func
    return found


def test_every_public_annotation_resolves_at_runtime() -> None:
    callables = _callables()
    assert len(callables) > 200
    failures = {}
    for label, func in callables.items():
        try:
            typing.get_type_hints(func)
        except Exception as exc:  # noqa: BLE001 - the sweep reports every kind
            failures[label] = f"{type(exc).__name__}: {exc}"
    assert set(failures) == CYCLE_EXCEPTIONS, failures


def test_the_named_returns_resolve_to_their_classes() -> None:
    from fi.gateway import AgentCC, AsyncAgentCC, SessionContext
    from fi.gateway._streaming import AsyncStreamManager, StreamManager
    from fi.gateway._transport._base import RequestOptions
    from fi.gateway.callbacks.base import CallbackHandler
    from fi.gateway.resources.chat import AsyncChatCompletions, ChatCompletions
    from fi.gateway.testing import RequestRecorder

    assert typing.get_type_hints(AgentCC.session)["return"] is SessionContext
    assert typing.get_type_hints(AsyncAgentCC.session)["return"] is SessionContext
    assert typing.get_type_hints(ChatCompletions.stream)["return"] is StreamManager
    hints = typing.get_type_hints(AsyncChatCompletions.stream)
    assert hints["return"] is AsyncStreamManager
    for hook in (CallbackHandler.on_request_start, RequestRecorder.on_request_end):
        assert typing.get_type_hints(hook)["request"] is RequestOptions


@pytest.mark.parametrize(
    "first",
    [
        "fi.gateway._session",
        "fi.gateway._client",
        "fi.gateway._async_client",
        "fi.gateway.callbacks",
        "fi.gateway.testing",
        "fi.gateway.resources.chat",
        "fi.gateway._streaming",
    ],
)
def test_every_import_order_works_in_a_fresh_interpreter(first: str) -> None:
    code = (
        f"import {first}; import fi.gateway as g; "
        "import fi.gateway.callbacks, fi.gateway.testing, fi.gateway.resources.chat; "
        "assert g.AgentCC and g.AsyncAgentCC and g.SessionContext; print('ok')"
    )
    out = subprocess.run(
        [
            sys.executable,
            "-I",
            "-c",
            f"import sys; sys.path.insert(0, {str(PYTHON_ROOT)!r}); {code}",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert out.returncode == 0 and out.stdout.strip() == "ok", out.stderr[-2000:]
