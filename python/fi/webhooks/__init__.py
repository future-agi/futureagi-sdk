"""Future AGI webhooks: verify signed requests, and manage endpoints from code.

Receivers::

    from fi.webhooks import verify, WebhookVerificationError
    event = verify(body=request.body, headers=request.headers, secret=os.environ["FI_WEBHOOK_SECRET"])

Management (the same keys as the rest of the SDK: arguments, ``FI_API_KEY`` / ``FI_SECRET_KEY``, or the saved
``futureagi-py login``)::

    from fi.webhooks import Webhooks
    wh = Webhooks()
    ep = wh.endpoints.create(url="https://hooks.acme.ai/fi", events=["prompt.label.changed"])
    ep.secret            # shown once; store it where the receiver reads it

``verify`` and the errors load eagerly and need only the standard library. The clients (:class:`Webhooks`,
:class:`AsyncWebhooks`) load on first use (PEP 562), so ``from fi.webhooks import verify`` stays light.
"""

from __future__ import annotations

from typing import Any

from fi.webhooks.verify import (
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

_LAZY = {
    "Webhooks": "fi.webhooks._client",
    "AsyncWebhooks": "fi.webhooks._client",
    "Endpoint": "fi.webhooks.types",
    "Rotation": "fi.webhooks.types",
    "TestResult": "fi.webhooks.types",
    "Page": "fi.webhooks.types",
    "Record": "fi.webhooks.types",
}

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
    *_LAZY,
]


def __getattr__(name: str) -> Any:
    module_name = _LAZY.get(name)
    if module_name is None:
        raise AttributeError(f"module 'fi.webhooks' has no attribute {name!r}")
    import importlib

    value = getattr(importlib.import_module(module_name), name)
    globals()[name] = value
    return value


def __dir__() -> list:
    return sorted(set(globals()) | set(_LAZY))
