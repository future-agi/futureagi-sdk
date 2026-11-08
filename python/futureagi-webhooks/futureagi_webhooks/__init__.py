"""Verify Future AGI webhook requests (Standard Webhooks v1), with nothing but the Python standard library.

    from futureagi_webhooks import verify, WebhookVerificationError
    event = verify(body=request.body, headers=request.headers, secret=os.environ["FI_WEBHOOK_SECRET"])

The same code as ``fi.webhooks.verify`` in the ``futureagi`` SDK (``_verify.py`` is a byte-identical copy, checked by
the SDK's tests), for receivers that do not want the whole SDK.
"""

from futureagi_webhooks._verify import (
    SECRET_PREFIX,
    TOLERANCE_S,
    VERIFY_RESULTS,
    WebhookSecretError,
    WebhookVerificationError,
    secret_key,
    sign,
    signature_header,
    verify,
    verify_result,
)

__all__ = [
    "SECRET_PREFIX",
    "TOLERANCE_S",
    "VERIFY_RESULTS",
    "WebhookSecretError",
    "WebhookVerificationError",
    "secret_key",
    "sign",
    "signature_header",
    "verify",
    "verify_result",
]
