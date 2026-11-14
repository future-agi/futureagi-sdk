"""A sandbox's state in an error body, kept past the shared redactor (``fi.sandbox.errors``).

The shared redactor hides every field named ``state``, but a 409's ``detail.state`` (a sandbox
state such as ``hibernated``) is what picks the error class. :func:`keep_state` copies a sandbox
state to ``detail.sandboxState`` before the redactor runs (sandbox calls scrub their error bodies
with it), and :func:`put_back` returns it to ``detail.state`` when the error is built. Any other
field named ``state`` stays hidden. Standard library only: nothing here imports ``fi``.
"""

from __future__ import annotations

from typing import Any, Callable, Mapping

#: The states a sandbox can be in, as an error's ``detail.state`` names them.
SANDBOX_STATES = frozenset({"active", "hibernated", "recovery_required", "destroyed"})
#: Where a sandbox state rides past the shared redactor, which hides every field named
#: ``state``; :func:`fi.sandbox.errors.translate` puts it back.
STATE_KEY = "sandboxState"


def _lift(detail: Any) -> Any:
    state = detail.get("state") if isinstance(detail, Mapping) else None
    if isinstance(state, str) and state in SANDBOX_STATES:
        return {**detail, STATE_KEY: state}
    return detail


def put_back(detail: Any) -> Any:
    """``detail`` with a kept sandbox state back under ``state`` (and no ``sandboxState``)."""
    state = detail.get(STATE_KEY) if isinstance(detail, Mapping) else None
    if not isinstance(state, str) or state not in SANDBOX_STATES:
        return detail
    out = {key: value for key, value in detail.items() if key != STATE_KEY}
    out["state"] = state
    return out


def each_detail(body: Any, change: Callable[[Any], Any]) -> Any:
    """``body`` with ``change`` applied to its ``detail`` and to its ``error.detail``."""
    if not isinstance(body, Mapping):
        return body
    out = dict(body)
    if "detail" in out:
        out["detail"] = change(out["detail"])
    nested = out.get("error")
    if isinstance(nested, Mapping) and "detail" in nested:
        out["error"] = {**nested, "detail": change(nested["detail"])}
    return out


def keep_state(body: Any) -> Any:
    """An error body whose sandbox state survives the shared redactor: a ``detail.state``
    that names a sandbox state is also copied to ``detail.sandboxState`` (any other field
    named ``state`` stays hidden). Sandbox calls scrub their error bodies with this."""
    return each_detail(body, _lift)


__all__ = ["SANDBOX_STATES", "STATE_KEY", "each_detail", "keep_state", "put_back"]
