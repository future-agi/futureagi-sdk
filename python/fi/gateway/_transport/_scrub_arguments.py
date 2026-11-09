"""Mask only the SDK-owned header mapping retained by a completed send."""
from collections.abc import MutableMapping

from fi.gateway._constants import CREDENTIAL_HEADER_NAMES
from fi.gateway.callbacks.base import REDACTED


def scrub_argument_headers(
    headers: MutableMapping[str, str], composed_names: frozenset[str],
) -> None:
    """Scrub the SDK-owned header copy retained in a completed send's locals.

    HTTPX copies headers when building a request; scrubbing that request alone
    leaves this earlier mapping intact. Never pass caller-owned defaults here.
    """
    names = CREDENTIAL_HEADER_NAMES | composed_names
    for name in list(headers):
        if name.lower() in names:
            headers[name] = REDACTED
