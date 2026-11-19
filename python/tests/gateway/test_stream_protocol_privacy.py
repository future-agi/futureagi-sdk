"""Protocol metadata is not transport diagnostic text."""
import httpx
import pytest

from fi.gateway import StreamError
from fi.gateway._transport._scrub import scrub_error_text


@pytest.mark.parametrize("credential", [b"k", b"blocked", b"stream_blocked"])
def test_protocol_fields_remain_exact_while_the_transport_cause_is_masked(credential):
    body = {"error": {"code": "stream_blocked", "type": "content_blocked", "param": "stream_blocked"}}
    error = StreamError("stream_blocked", code="stream_blocked", type="content_blocked", param="stream_blocked", body=body)
    cause = httpx.ReadError("transport synthetic-private-key")
    error.__cause__ = cause
    scrub_error_text(error, (credential, b"synthetic-private-key"))
    assert error.code == "stream_blocked"
    assert error.type == "content_blocked"
    assert error.param == "stream_blocked"
    assert error.body is body
    assert error.args == ("stream_blocked",)
    assert str(error) == "stream_blocked"
    assert error.__cause__ is cause
    assert str(cause) == "transport [REDACTED]"


@pytest.mark.parametrize("credential", [b"k", b"blocked"])
def test_short_credentials_do_not_substring_redact_diagnostics(credential):
    error = httpx.ReadError("stream_blocked while checking transport")
    scrub_error_text(error, (credential,))
    assert str(error) == "stream_blocked while checking transport"


@pytest.mark.parametrize("first", ["_scrub", "_scrub_diagnostics"])
def test_scrub_modules_can_be_imported_in_either_order(first):
    from pathlib import Path
    import subprocess
    import sys

    root = Path(__file__).resolve().parents[2]
    code = (f"import sys; sys.path.insert(0, {str(root)!r}); "
            f"import fi.gateway._transport.{first}; "
            "from fi.gateway._transport._scrub import scrub_error_text; "
            "from fi.gateway._transport._scrub_diagnostics import bind_stream_scrubber")
    result = subprocess.run([sys.executable, "-I", "-B", "-c", code], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
