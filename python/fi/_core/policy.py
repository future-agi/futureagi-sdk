"""The shape of one platform operation, and the retry class it gets.

The contract generator writes the table (``fi/generated/platform/policy.py``) from the pinned customer
contract::

    from fi._core.policy import OperationSpec as Op, PaginationSpec as Page, StreamSpec as Stream
    OPERATIONS: dict[str, Op] = {"runs.get": Op(name="runs.get", family="runs", method="GET", ...)}

Namespaces call operations by SDK name only (``runs.events``); no URL path string exists outside
the generated table. Every field comes from the contract's ``x-omega-*`` keys:

=====================================  =========================================================
``x-omega-sdk`` ``{family, method}``   ``name`` (``<family>.<method>``) and ``family``
``x-omega-idempotent``                 ``idempotent``: the call takes an ``Idempotency-Key``
``x-omega-idempotency.durable``        ``durable``: a restarted server still remembers the key
``x-omega-idempotency.keyRequired``    ``idempotency_key_required``
``x-omega-not-found-on-retry-...``     ``not_found_means_applied`` (``sandboxes.kill``)
``x-omega-stream``                     ``stream`` (:class:`StreamSpec`)
``x-omega-pagination``                 ``pagination`` (:class:`PaginationSpec`)
``x-omega-{body,timeout,rate}-class``  ``body``, ``timeout``, ``rate``
``x-omega-min-role``                   ``role``
=====================================  =========================================================

The four retry classes (the transport's ``request.extensions["fi.retry"]``, ``fi._http``):

====================  ==================================================  ======================
Class                 Which operations                                    Retried on
====================  ==================================================  ======================
``keyed``             idempotent and durable                              429, 502-504, network
``keyed-not-durable`` idempotent, ``durable: false``                      429, pre-send errors
``http-idempotent``   not idempotent; GET, HEAD, OPTIONS, PUT, DELETE     429, 502-504, network
``unsafe``            not idempotent; POST, PATCH                         429, pre-send errors
====================  ==================================================  ======================

On top of the transport, the executor (``fi._core.platform_base``) waits out a 409
``idempotency_key_in_progress`` on a keyed call (``Retry-After``, else 1 s) and resends with the
same key, and counts a 404 on a retry of a ``not_found_means_applied`` call as success.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Mapping, Optional

from fi.errors import PlatformNotConfiguredError

HttpMethod = Literal["GET", "HEAD", "OPTIONS", "POST", "PUT", "PATCH", "DELETE"]
RetryClass = Literal["keyed", "keyed-not-durable", "http-idempotent", "unsafe"]
#: The gateway's body classes: no body, JSON (1 MiB), or a bundle (64 MiB).
BodyClass = Literal["none", "json", "bundle"]
TimeoutClass = Literal["read", "write", "model", "stream"]
RateClass = Literal["read", "write", "model-start"]

HTTP_IDEMPOTENT_METHODS = frozenset({"GET", "HEAD", "OPTIONS", "PUT", "DELETE"})
RETRY_CLASS_DOCS: dict[str, str] = {
    "keyed": (
        "Takes an idempotency key (minted for you unless you pass idempotency_key=; the same key on "
        "every attempt). Retried on 429, 502, 503, 504 and network errors; a 409 in progress waits."
    ),
    "keyed-not-durable": (
        "Takes an idempotency key, but a restarted server forgets it, so it is retried only on 429 "
        "and on errors before anything was sent."
    ),
    "http-idempotent": "Idempotent by method. Retried on 429, 502, 503, 504 and network errors.",
    "unsafe": (
        "Not idempotent and takes no key: retried only on 429 and on errors before anything was "
        "sent, never after a 5xx (the request may have run)."
    ),
}


@dataclass(frozen=True)
class StreamSpec:
    """How a streaming operation streams (``x-omega-stream``)."""

    #: ``sse-get`` (a resumable read) or ``sse-post`` (exec: the stream is the command).
    kind: Literal["sse-get", "sse-post"]
    #: ``last-event-id`` when a reconnect resumes after the last durable ``id:``.
    resume: Literal["last-event-id", "none"] = "none"
    #: The contract title of the frame union (``OmegaRunEventFrame``).
    events: str = ""
    #: The event types this SDK knows; any other type is yielded as an unknown event.
    known_events: tuple[str, ...] = ()
    keepalive_seconds: Optional[int] = None
    #: True when closing the stream cancels the work (exec).
    cancel_on_disconnect: bool = False
    #: The long-poll fallback (``?transport=poll&wait=25000``), when there is one.
    poll_param: Optional[str] = None
    poll_value: Optional[str] = None
    poll_wait_param: Optional[str] = None
    poll_max_wait_ms: Optional[int] = None


@dataclass(frozen=True)
class PaginationSpec:
    """How a list operation pages (``x-omega-pagination``). Cursors are opaque: never parsed or built."""

    #: ``cursor`` (server-paged), ``single-page`` or ``window`` (one page bounded by ``limit``).
    style: Literal["cursor", "single-page", "window"]
    #: The field holding the items (dotted for nested fields).
    items_field: str
    cursor_param: Optional[str] = None
    limit_param: Optional[str] = None
    #: The field holding the next cursor (dotted, e.g. ``page.nextCursor``).
    next_cursor_field: Optional[str] = None
    has_more_field: Optional[str] = None
    truncated_field: Optional[str] = None


@dataclass(frozen=True)
class OperationSpec:
    """One in-scope operation of the pinned customer contract."""

    #: ``<family>.<method>`` from ``x-omega-sdk``.
    name: str
    family: str
    method: HttpMethod
    #: The path template under the platform origin, with ``{name}`` placeholders.
    path: str
    #: Placeholder names, in path order.
    path_params: tuple[str, ...] = ()
    #: The query keys the contract declares; no other key is ever sent.
    query: tuple[str, ...] = ()
    body: BodyClass = "none"
    timeout: TimeoutClass = "read"
    rate: Optional[RateClass] = None
    role: Optional[str] = None
    #: The request headers the contract declares (lower case), beyond the SDK's own.
    headers: tuple[str, ...] = ()
    #: The request body's media type, when it has one.
    content_type: Optional[str] = None
    idempotent: bool = False
    durable: bool = True
    idempotency_key_required: bool = False
    not_found_means_applied: bool = False
    #: Only a person may do this (approvals, settings writes): never wrapped.
    human_only: bool = False
    #: Path parameters that may span several segments (each segment encoded on its own).
    multi_segment: tuple[str, ...] = ()
    stream: Optional[StreamSpec] = None
    pagination: Optional[PaginationSpec] = None
    #: Fields the contract marks secret: ``request.<path>`` or ``response.<path>``; ``*`` is any key.
    secret_fields: tuple[str, ...] = ()
    #: EE's operationId, for cross-reference only.
    operation_id: Optional[str] = None

    @property
    def retry_class(self) -> RetryClass:
        """The operation's retry class (the table in this module's docstring)."""
        return retry_class_of(self)


def retry_class_of(op: OperationSpec) -> RetryClass:
    """``keyed`` / ``keyed-not-durable`` from the contract's idempotency flags, else by method."""
    if op.idempotent:
        return "keyed" if op.durable else "keyed-not-durable"
    if op.method.upper() in HTTP_IDEMPOTENT_METHODS:
        return "http-idempotent"
    return "unsafe"


def lookup(table: Mapping[str, OperationSpec], name: str) -> OperationSpec:
    """The operation named ``name``; a name the table lacks raises ``PlatformNotConfiguredError``."""
    op = table.get(name)
    if op is None:
        raise PlatformNotConfiguredError(
            f"no platform operation is named {name!r} in this SDK's contract", code="unknown_operation", operation=name
        )
    return op


def counts(table: Mapping[str, OperationSpec]) -> dict[str, int]:
    """Operations per retry class, plus streams and paginated lists (``check.sh`` and the gates)."""
    out: dict[str, int] = {"keyed": 0, "keyed-not-durable": 0, "http-idempotent": 0, "unsafe": 0}
    for op in table.values():
        out[op.retry_class] += 1
    out["stream"] = sum(1 for op in table.values() if op.stream is not None)
    out["paginated"] = sum(1 for op in table.values() if op.pagination is not None)
    return out
