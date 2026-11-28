"""The gateway's refusal of a 3xx answer."""

from __future__ import annotations

from fi._keyed_errors import KeyedRedirectRefusedError
from fi.gateway._exceptions import APIConnectionError
from fi.gateway._gateway_evidence import GatewayEvidence


class GatewayRedirectRefusedError(APIConnectionError, KeyedRedirectRefusedError):
    """A gateway answered a request with a 3xx. It is an ``APIConnectionError`` (the gateway family) and a
    ``KeyedRedirectRefusedError`` (code ``KEYED_REDIRECT_REFUSED``): the redirect was not followed and is not retried."""

    def __init__(self, message: str, *, status_code: int | None = None, gateway_evidence: GatewayEvidence | None = None) -> None:
        APIConnectionError.__init__(self, message, gateway_evidence=gateway_evidence)
        self.status_code = status_code
        self.target_host = None
        self.request_id = None
        self.operation = None

    def get_error_code(self) -> str:
        return "KEYED_REDIRECT_REFUSED"
