"""Credential header spellings are masked at writing sinks, never in live inputs."""
import copy
import json
import logging
from types import SimpleNamespace

import pytest

from fi.gateway._utils import redact_headers
from fi.gateway.callbacks.base import CallbackRequest, CallbackResponse, redact_credentials

HEADERS = ("authorization", "proxy-authorization", "cookie", "set-cookie",
           "x-api-key", "api-key", "x-goog-api-key", "x-agentcc-config",
           "x-auth-token", "x-access-token", "x-api-token", "x-agentcc-api-key",
           "x-secret-key")


@pytest.mark.parametrize("name", HEADERS)
@pytest.mark.parametrize("casing", ["lower", "upper", "title"])
def test_credential_header_helpers_agree_without_mutating_input(name, casing):
    key = getattr(name, casing)()
    headers = {key: "synthetic-secret", "X-Visible": "yes"}
    expected = {key: "[REDACTED]", "X-Visible": "yes"}
    assert redact_headers(headers) == expected
    assert redact_credentials(headers) == expected
    assert headers == {key: "synthetic-secret", "X-Visible": "yes"}


@pytest.mark.parametrize("sink", ["recorder", "json", "logging", "otel"])
@pytest.mark.filterwarnings("ignore::DeprecationWarning")
def test_writing_sinks_mask_all_header_names_without_editing_live_data(sink, tmp_path):
    output = tmp_path / "sink-output.txt"
    headers = {name.title(): "synthetic-header-" + str(i) for i, name in enumerate(HEADERS)}
    headers["X-Visible"] = "yes"
    body = {"model": "test", "headers": headers,
            "metadata": {"password": "synthetic-password", "api_key": "synthetic-body-key"}}
    files = {"api_key": "synthetic-file"}
    request = CallbackRequest("POST", "/v1/test", headers, body, files=files)
    response = CallbackResponse(200, {}, body={"model": "test"})
    before = copy.deepcopy((body, headers, files))
    if sink == "recorder":
        from fi.gateway.testing.recorder import RequestRecorder
        callback = RequestRecorder(str(output))
        callback.on_request_end(request, response)
        callback.save()
    elif sink == "json":
        from fi.gateway.callbacks.json_logger import JSONLoggingCallbackHandler
        callback = JSONLoggingCallbackHandler(str(output))
        callback.on_request_end(request, response)
        # The public hook omits input headers. Exercise its structured write
        # boundary too, so future fields cannot bypass the shared masking rule.
        callback._write_log({"headers": headers, "body": body, "files": files})
    elif sink == "logging":
        from fi.gateway.callbacks.logging import LoggingCallback
        logger = logging.getLogger("callback-header-output-test")
        handler = logging.FileHandler(output)
        old_level = logger.level
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        try:
            callback = LoggingCallback(logger_name=logger.name)
            callback.on_request_start(request)
            callback.on_request_end(request, response)
        finally:
            logger.setLevel(old_level)
            logger.removeHandler(handler)
            handler.close()
    else:
        from fi.gateway.callbacks.opentelemetry import OpenTelemetryCallback

        class Span:
            def __init__(self):
                self.values = {}

            def set_attribute(self, key, value):
                self.values[key] = value

            def end(self):
                output.write_text(json.dumps(self.values))

        callback = OpenTelemetryCallback(tracer=SimpleNamespace(start_span=lambda name: Span()))
        callback.on_request_start(request)
        callback.on_request_end(request, response)
    text = output.read_text()
    assert text.strip()
    markers = [value for key, value in headers.items() if key != "X-Visible"]
    assert not any(marker in text for marker in markers + ["synthetic-password", "synthetic-body-key", "synthetic-file"])
    assert request.body is body and request.headers is headers and request.files is files
    assert body["headers"] is headers and (body, headers, files) == before
    if sink != "logging":
        assert "[REDACTED]" in text and "yes" in text
