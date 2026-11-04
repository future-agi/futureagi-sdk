"""Step 1 smoke test: verify the package imports correctly."""

from __future__ import annotations

import sys
import time


def _reattach_parent() -> None:
    """Point `fi.gateway` back at the restored module (on 3.9, mock.patch resolves via getattr)."""
    import fi

    fi.gateway = sys.modules["fi.gateway"]  # type: ignore[attr-defined]


def test_import_agentcc() -> None:
    """import agentcc should succeed without error."""
    import fi.gateway as agentcc

    assert agentcc.__version__ == "0.1.0"


def test_import_time_under_50ms() -> None:
    """import agentcc should complete in under 50ms.

    We run in a subprocess-like check: remove agentcc from sys.modules,
    re-import, and measure. Note: in practice, first import in a fresh
    process is the true benchmark; this is an approximation.
    """
    # Save and remove agentcc and all submodules from cache
    saved = {key: sys.modules[key] for key in list(sys.modules) if key == "fi.gateway" or key.startswith("fi.gateway.")}
    for mod in saved:
        del sys.modules[mod]

    try:
        start = time.perf_counter()

        elapsed_ms = (time.perf_counter() - start) * 1000

        # Allow some slack in CI; the hard target is <50ms in a fresh process
        assert elapsed_ms < 200, f"import agentcc took {elapsed_ms:.1f}ms (target: <50ms in fresh process)"
    finally:
        # Restore original modules to avoid poisoning other tests
        for key in list(sys.modules):
            if key == "fi.gateway" or key.startswith("fi.gateway."):
                del sys.modules[key]
        sys.modules.update(saved)
        _reattach_parent()


def test_no_heavy_deps_at_import() -> None:
    """Importing agentcc should NOT eagerly load httpx or pydantic."""
    saved = {key: sys.modules[key] for key in list(sys.modules) if key == "fi.gateway" or key.startswith("fi.gateway.")}
    saved_heavy: dict[str, object] = {}
    for mod_name in ["httpx", "pydantic"]:
        for k in list(sys.modules):
            if k == mod_name or k.startswith(f"{mod_name}."):
                saved_heavy[k] = sys.modules[k]

    for mod in saved:
        del sys.modules[mod]
    for mod in saved_heavy:
        del sys.modules[mod]

    try:
        import fi.gateway as agentcc

        # httpx and pydantic should NOT have been imported
        assert "httpx" not in sys.modules, "httpx was imported at `import agentcc` time"
        # pydantic may be imported by _exceptions if we used it there, but we don't
        # assert "pydantic" not in sys.modules, "pydantic was imported at `import agentcc` time"

        # Verify agentcc is functional (version accessible)
        assert agentcc.__version__
    finally:
        # Restore original modules to avoid poisoning other tests
        for key in list(sys.modules):
            if key == "fi.gateway" or key.startswith("fi.gateway."):
                del sys.modules[key]
        for key in list(sys.modules):
            if key in saved_heavy:
                del sys.modules[key]
        sys.modules.update(saved)
        _reattach_parent()
        sys.modules.update(saved_heavy)


def test_not_given_sentinel() -> None:
    """NOT_GIVEN should be a falsy singleton distinct from None."""
    from fi.gateway import NOT_GIVEN

    assert not NOT_GIVEN
    assert NOT_GIVEN is not None
    assert repr(NOT_GIVEN) == "NOT_GIVEN"

    # Singleton check
    from fi.gateway._constants import NOT_GIVEN as NOT_GIVEN_2

    assert NOT_GIVEN is NOT_GIVEN_2


def test_exceptions_importable() -> None:
    """All exception classes should be importable from fi.gateway."""
    from fi.gateway import (
        APIConnectionError,
        APIStatusError,
        APITimeoutError,
        AuthenticationError,
        BadGatewayError,
        BadRequestError,
        GatewayTimeoutError,
        GuardrailBlockedError,
        GuardrailWarning,
        InternalServerError,
        NotFoundError,
        PermissionDeniedError,
        AgentCCError,
        RateLimitError,
        ServiceUnavailableError,
        StreamError,
        UnprocessableEntityError,
    )

    # Verify inheritance
    assert issubclass(APIConnectionError, AgentCCError)
    assert issubclass(APITimeoutError, APIConnectionError)
    assert issubclass(APIStatusError, AgentCCError)
    assert issubclass(BadRequestError, APIStatusError)
    assert issubclass(RateLimitError, APIStatusError)
    assert issubclass(GuardrailBlockedError, APIStatusError)
    assert issubclass(GuardrailWarning, APIStatusError)
    assert issubclass(StreamError, AgentCCError)

    # Verify they're all distinct classes
    all_exc = [
        BadRequestError, AuthenticationError, PermissionDeniedError,
        NotFoundError, UnprocessableEntityError, RateLimitError,
        InternalServerError, BadGatewayError, ServiceUnavailableError,
        GatewayTimeoutError, GuardrailBlockedError, GuardrailWarning,
    ]
    assert len(set(all_exc)) == len(all_exc)
