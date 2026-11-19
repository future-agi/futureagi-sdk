"""Idempotency keys (ported from the Omega runtime).

- One UUID4 per logical call, minted with ``uuid.uuid4`` and reused on every attempt of that call:
  the transport's retries resend the same request, and the 409 "in progress" wait resends the
  same key.
- Sent only to operations the contract marks idempotent. A caller's own key on any other
  operation is refused, so nobody believes a repeat is safe when the server would ignore the key.
- The caller may pass its own (``idempotency_key="ci-" + GITHUB_SHA``); it is on errors and on
  ``with_raw_response`` results, never on plain results.
- A replay is flagged when the server says so (``x-omega-idempotent-replayed: true``).
"""

from __future__ import annotations

import re
import uuid
from typing import Mapping, Optional

from fi._core.policy import OperationSpec
from fi.errors import ConfigurationError

IDEMPOTENCY_HEADER = "Idempotency-Key"
REPLAYED_HEADER = "x-omega-idempotent-replayed"
IN_PROGRESS_CODE = "idempotency_key_in_progress"
#: The wait for ``idempotency_key_in_progress`` when the server names none (1 s).
IN_PROGRESS_DEFAULT_S = 1.0
#: A longer ``Retry-After`` than this is not waited out: the error is raised with it set.
IN_PROGRESS_MAX_WAIT_S = 60.0
_KEY = re.compile(r"^[\x21-\x7e]{1,255}$")


def resolve_idempotency_key(op: OperationSpec, supplied: Optional[str]) -> Optional[str]:
    """The caller's key (validated), else a new UUID4, else none for an operation that takes none."""
    if supplied is not None:
        if not op.idempotent:
            raise ConfigurationError(
                f"{op.name} does not accept an idempotency key, so a repeat could apply twice",
                code="idempotency_not_supported",
                operation=op.name,
            )
        if not _KEY.match(supplied):
            raise ConfigurationError(
                "idempotency_key must be 1 to 255 visible ASCII characters with no spaces",
                code="invalid_idempotency_key",
                operation=op.name,
            )
        return supplied
    return str(uuid.uuid4()) if op.idempotent else None


def is_replay(headers: Mapping[str, str]) -> bool:
    """True when the response is the server's replay of an earlier request with the same key."""
    return str(headers.get(REPLAYED_HEADER, "")).lower() == "true"


def in_progress_wait(
    op: OperationSpec, status: int, code: Optional[str], retry_after: Optional[float]
) -> Optional[float]:
    """Seconds to wait before resending a keyed call the server reports as still running
    (``retry_after`` is the parsed hint), or None when this answer is not that, or the hint is too
    long to wait out."""
    if not op.idempotent or status != 409 or code != IN_PROGRESS_CODE:
        return None
    seconds = retry_after
    if seconds is None:
        seconds = IN_PROGRESS_DEFAULT_S
    return None if seconds > IN_PROGRESS_MAX_WAIT_S else seconds
