"""Step 1 smoke test: verify the package imports correctly."""

from __future__ import annotations

import sys
import time


def test_import_agentcc() -> None:
    """import agentcc should succeed without error."""
    import fi.gateway as agentcc
    from fi.gateway._version import futureagi_version

    # D-03: the futureagi version (agentcc 1.0 pinned "0.1.0" here)
    assert agentcc.__version__ == futureagi_version()


def _fresh(code: str) -> str:
    """Run *code* in a new interpreter that imports this tree's fi."""
    import os
    import subprocess
    from pathlib import Path

    import fi

    env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
    env["PYTHONPATH"] = str(Path(fi.__file__).resolve().parents[1])
    return subprocess.run(
        [sys.executable, "-c", code],
        env=env,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()


def test_import_time_under_200ms_in_a_fresh_process() -> None:
    """import fi.gateway should complete in under 200 ms in a fresh process.

    agentcc 1.0 (test_import_time_under_50ms) timed an empty block in-process and
    asserted 1.0's slack bound of 200 ms under a 50 ms name. This times the import in a
    new interpreter, best of three, against that same 200 ms bound, now named for it
    (the target stays 50 ms; a loaded CI host is slower).
    """
    code = (
        "import time; t = time.perf_counter(); import fi.gateway; "
        "print(time.perf_counter() - t)"
    )
    elapsed_ms = min(float(_fresh(code)) for _ in range(3)) * 1000
    assert (
        elapsed_ms < 200
    ), f"import fi.gateway took {elapsed_ms:.1f}ms (target: <50ms in fresh process)"


def test_no_heavy_deps_at_import() -> None:
    """Importing fi.gateway should NOT eagerly load httpx or pydantic.

    In a fresh interpreter: the port's in-process version purged ``agentcc.*`` keys
    that no longer exist, so fi.gateway stayed cached and nothing was checked.
    """
    code = (
        "import sys, fi.gateway as g; "
        "print(sorted(m for m in ('httpx', 'pydantic', 'anyio') if m in sys.modules), "
        "bool(g.__version__))"
    )
    assert _fresh(code) == "[] True"


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
    from fi.gateway import (AgentCCError, APIConnectionError, APIStatusError,
                            APITimeoutError, AuthenticationError,
                            BadGatewayError, BadRequestError,
                            GatewayTimeoutError, GuardrailBlockedError,
                            GuardrailWarning, InternalServerError,
                            NotFoundError, PermissionDeniedError,
                            RateLimitError, ServiceUnavailableError,
                            StreamError, UnprocessableEntityError)

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
        BadRequestError,
        AuthenticationError,
        PermissionDeniedError,
        NotFoundError,
        UnprocessableEntityError,
        RateLimitError,
        InternalServerError,
        BadGatewayError,
        ServiceUnavailableError,
        GatewayTimeoutError,
        GuardrailBlockedError,
        GuardrailWarning,
    ]
    assert len(set(all_exc)) == len(all_exc)
