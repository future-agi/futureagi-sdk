"""fi.errors: the minimal public error tree."""

import asyncio
import subprocess
import sys

import httpx
import pytest

import fi.errors as errors
from fi._sdk_exception import SDKException


def test_root_is_sdk_exception_and_old_names_are_the_same_classes():
    from fi._credentials import CredentialsMissingError, MissingAuthError
    from fi.futureagi_client import FutureAGIAPIError
    from fi.utils.errors import MissingAuthError as LegacyMissingAuthError

    assert errors.FutureAGIError is SDKException
    assert errors.SDKException is SDKException
    assert errors.FutureAGIAPIError is FutureAGIAPIError
    assert errors.CredentialsMissingError is CredentialsMissingError
    # one class under both names only because this distribution's fi/utils is the one on disk;
    # agent-learning-kit / ai-evaluation ship their own fi/utils/errors.py
    assert errors.MissingAuthError is MissingAuthError is LegacyMissingAuthError
    assert issubclass(CredentialsMissingError, errors.AuthError)
    for name in errors.__all__:
        value = getattr(errors, name)
        if isinstance(value, type):
            assert issubclass(value, SDKException), name


@pytest.mark.parametrize(
    "status, cls, code",
    [
        (401, "AuthenticationError", "AUTHENTICATION_FAILED"),
        (403, "PermissionDeniedError", "PERMISSION_DENIED"),
        (404, "NotFoundError", "NOT_FOUND"),
        (429, "RateLimitError", "RATE_LIMITED"),
        (500, "ServerError", "SERVER_ERROR"),
        (503, "ServerError", "SERVER_ERROR"),
        # every status has a class; an unclassed 4xx stays the base class
        (400, "BadRequestError", "BAD_REQUEST"),
        (409, "ConflictError", "CONFLICT"),
        (418, "FutureAGIAPIError", "FUTURE_AGI_API_ERROR"),
    ],
)
def test_api_error_picks_the_subclass(status, cls, code):
    err = errors.api_error(status, {"detail": "x"}, {"Retry-After": "2", "X-Request-Id": "req-1"})
    assert type(err) is getattr(errors, cls)
    assert isinstance(err, errors.FutureAGIAPIError)
    assert err.status_code == status and err.payload == {"detail": "x"}
    assert err.get_error_code() == code
    assert err.retry_after == 2.0 and err.request_id == "req-1"
    assert f"status {status}" in str(err)


def test_configuration_value_error_preserves_both_catch_contracts():
    err = errors.ConfigurationValueError("invalid setup", operation="ground_truth_setup")
    assert isinstance(err, errors.ConfigurationError)
    assert isinstance(err, ValueError)
    assert "ConfigurationValueError" in errors.__all__
    assert err.get_error_code() == "CONFIGURATION_ERROR"
    assert err.code == "invalid_option"
    assert err.operation == "ground_truth_setup"
    assert str(err) == "invalid setup"
    with pytest.raises(ValueError):
        raise err
    with pytest.raises(errors.ConfigurationError):
        raise err


def test_auth_status_errors_are_auth_errors():
    assert isinstance(errors.api_error(401, None), errors.AuthError)
    assert isinstance(errors.api_error(403, None), errors.AuthError)
    assert not isinstance(errors.api_error(404, None), errors.AuthError)


def test_transport_error_from_an_httpx_error_names_the_origin():
    exc = httpx.ConnectError("[Errno 61] Connection refused", request=httpx.Request("GET", "http://srv.test:8000/x"))
    err = errors.TransportError.from_exception(exc)
    assert err.base_url == "http://srv.test:8000" and "Connection refused" in err.reason
    assert str(err) == "cannot reach http://srv.test:8000 ([Errno 61] Connection refused); check FI_BASE_URL"
    assert err.get_error_code() == "SERVER_UNREACHABLE" and err.__cause__ is exc
    assert errors.TransportError.from_exception(RuntimeError(""), "http://b.test/").base_url == "http://b.test"


def test_transport_error_words_timeouts_resets_and_the_platform_origin():
    """A read timeout or a reset reached the server; a platform request names its variable."""
    req = httpx.Request("GET", "http://srv.test:8000/x")
    timeout = errors.TransportError.from_exception(httpx.ReadTimeout("read timed out", request=req))
    assert timeout.kind == "timeout"
    assert str(timeout) == "http://srv.test:8000 did not answer in time (read timed out); the server may be busy, retry later"
    reset = errors.TransportError.from_exception(httpx.ReadError("connection reset", request=req))
    assert reset.kind == "connection" and "broke before a response" in str(reset) and "FI_BASE_URL" not in str(reset)
    closed = errors.TransportError.from_exception(httpx.RemoteProtocolError("closed", request=req))
    assert closed.kind == "connection"
    connect_timeout = errors.TransportError.from_exception(httpx.ConnectTimeout("timed out", request=req))
    assert connect_timeout.kind == "connect" and str(connect_timeout).endswith("check FI_BASE_URL")
    plat = httpx.Request("GET", "http://srv.test:8000/omega/api/v1/runs")
    err = errors.TransportError.from_exception(httpx.ConnectError("refused", request=plat))
    assert str(err).endswith("check FI_PLATFORM_BASE_URL (or FI_BASE_URL, which it derives from)")
    err = errors.TransportError.from_exception(httpx.ConnectError("refused", request=req), setting="--base-url")
    assert str(err).endswith("check --base-url")
    for exc, kind in ((ConnectionRefusedError("x"), "connect"), (ConnectionResetError("x"), "connection"),
                      (TimeoutError("x"), "timeout")):
        assert errors.transport_failure_kind(exc) == kind


def test_missing_extra_error_carries_its_install_hint():
    err = errors.MissingExtraError(extra="langgraph", module="traceai_langchain")
    assert err.install_hint == 'pip install "futureagi[langgraph]"'
    assert str(err) == 'traceai_langchain is not installed. Run: pip install "futureagi[langgraph]"'
    assert errors.MissingExtraError("custom").install_hint is None and str(errors.MissingExtraError("custom")) == "custom"


@pytest.mark.parametrize("module", ["yaml", "cv2", "PIL.Image", "livekit.api"])
def test_missing_extra_with_a_module_only_guesses_no_distribution(module):
    """An import name is not a distribution name (yaml is PyYAML, cv2 opencv-python)."""
    err = errors.MissingExtraError(module=module)
    assert err.install_hint is None and "pip install" not in str(err)
    top = module.split(".")[0]
    assert str(err) == f"{module} is not installed. Install the package that provides the {top!r} module."


def test_credentials_missing_names_no_cli_flag_and_takes_a_hint():
    """The shared message names no group's flag; a group adds its own sentence."""
    from fi._credentials import CredentialsMissingError, MissingAuthError

    err = CredentialsMissingError("http://x.test", ("FI_API_KEY",))
    # `futureagi-py login` is a core command (shared/cli-auth), not a group's flag
    assert str(err) == "No FI_API_KEY for http://x.test. Set FI_API_KEY and FI_SECRET_KEY, or run `futureagi-py login`."
    assert "--" not in str(err)
    hinted = CredentialsMissingError("http://x.test", ("FI_SECRET_KEY",), "login skipped", hint="Or add --local.")
    assert str(hinted) == ("No FI_SECRET_KEY for http://x.test. Set FI_API_KEY and FI_SECRET_KEY, or run "
                           "`futureagi-py login`. Or add --local. (login skipped)")
    assert "--no-upload" not in str(MissingAuthError(None, None, cause=err, base_url="http://x.test"))


def test_async_request_raises_the_typed_subclass(monkeypatch):
    from fi import AsyncFutureAGIClient

    for var in ("FI_API_KEY", "FI_SECRET_KEY", "FI_BASE_URL"):
        monkeypatch.delenv(var, raising=False)

    def handler(request):
        return httpx.Response(404, json={"detail": "no such run"}, headers={"X-Request-Id": "r-9"})

    client = AsyncFutureAGIClient(api_key="k-test-1234", secret_key="s-test-1234", base_url="http://api.test")
    client.generated_client._httpx_args["transport"]._wrapped_async = httpx.MockTransport(handler)

    async def go():
        try:
            await client.request("GET", "/x")
        finally:
            await client.aclose()

    with pytest.raises(errors.NotFoundError) as info:
        asyncio.run(go())
    assert info.value.request_id == "r-9" and info.value.payload == {"detail": "no such run"}


def test_fi_errors_imports_nothing_heavy():
    code = (
        "import sys; import fi.errors; "
        "print(sorted(m for m in sys.modules if m.startswith(('fi.utils', 'fi.api', 'fi.generated', 'httpx'))))"
    )
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=60)
    assert out.returncode == 0, out.stderr
    assert out.stdout.strip() == "[]"
