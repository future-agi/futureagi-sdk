"""Per-exception-type retry policy configuration."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RetryPolicy:
    """Per-exception-type retry configuration.

    Instead of a flat ``max_retries`` for all error types, this allows
    fine-grained control over how many retries each error category gets.

    Usage::

        from fi.gateway import RetryPolicy

        policy = RetryPolicy(RateLimitErrorRetries=5, TimeoutRetries=3)
        client = AgentCC(retry_policy=policy, api_key="sk-...", base_url="...")
    """

    RateLimitErrorRetries: int = 2
    TimeoutRetries: int = 2
    ConnectionErrorRetries: int = 2
    InternalServerErrorRetries: int = 1
    BadGatewayRetries: int = 1
    ServiceUnavailableRetries: int = 1
    GatewayTimeoutRetries: int = 1

    def get_retries_for_status(self, status_code: int) -> int:
        """Return the max retries for a given HTTP status code."""
        mapping = {
            429: self.RateLimitErrorRetries,
            500: self.InternalServerErrorRetries,
            502: self.BadGatewayRetries,
            503: self.ServiceUnavailableRetries,
            504: self.GatewayTimeoutRetries,
        }
        return mapping.get(status_code, 0)

    def get_retries_for_connection_error(self) -> int:
        """Return the max retries for connection errors."""
        return self.ConnectionErrorRetries

    def get_retries_for_timeout(self) -> int:
        """Return the max retries for timeout errors."""
        return self.TimeoutRetries
