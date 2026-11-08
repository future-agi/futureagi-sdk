"""HTTP 402 errors, lazily exported by :mod:`fi.errors`."""

from fi.errors import FutureAGIAPIError


class PaymentRequiredError(FutureAGIAPIError):
    """402: the server requires payment, entitlement or a licence.

    A generic 402 does not by itself mean that an Enterprise licence is missing.
    Inspect ``code`` and ``payload`` for the server's reason.
    """

    def get_error_code(self) -> str:
        return "PAYMENT_REQUIRED"


class LicenseRequiredError(PaymentRequiredError):
    """402 ``LICENSE_MISSING``: this server needs an Enterprise licence.

    Ask its administrator to configure a licence that includes the feature.
    Mapped messages name the feature when the server supplies it.
    This error makes no claim about availability on hosted deployments.
    """

    def get_error_code(self) -> str:
        return "LICENSE_REQUIRED"
