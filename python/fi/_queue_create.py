"""What creating an annotation queue (POST model-hub/annotation-queues/) needs, and what
getting a default queue (POST model-hub/annotation-queues/get-or-create-default/) needs.

Shared by ``fi.queues.AnnotationQueue`` and ``FutureAGIClient.annotation_queues``. The backend
facts (``AnnotationQueueSerializer``, ``AnnotationQueueViewSet`` and the get-or-create-default
request) are pinned in ``tests/fixtures/server-contracts/annotation-queue-create.json``; the
contract tests fail when either client drifts from that snapshot. Standard library only.
"""

from __future__ import annotations

import warnings
from collections.abc import Iterable, Mapping
from typing import Any, Callable
from uuid import UUID

# The fields the server requires on create (the snapshot's create.required; the contract tests
# fail when the two differ). Both create() methods require them on the final POST, an
# explicit None included: FutureAGIClient.annotation_queues.create (create_body) and
# AnnotationQueue.create (require_on_create), as both TypeScript create() methods do.
REQUIRED_ON_CREATE = ("name", "label_ids")

# Read-only on the server: never sent on create. Retained for published callers; when
# label_ids is omitted, exactly one can identify the default queue used for labels.
IGNORED_ON_CREATE = ("project", "dataset", "agent_definition")

# The get-or-create-default field for each of them. Exactly one is given per call.
DEFAULT_QUEUE_SCOPE_IDS = {
    "project": "project_id",
    "dataset": "dataset_id",
    "agent_definition": "agent_definition_id",
}

# The facade's get-or-create-default method, as a scope-id refusal names it.
FACADE_DEFAULT_QUEUE_METHOD = "annotation_queues.get_or_create_default"

# What each client's create() points at instead of the ignored fields.
FACADE_DEFAULT_QUEUE_CALL = (
    "annotation_queues.get_or_create_default(project_id=...), or dataset_id= or "
    "agent_definition_id="
)
QUEUE_CLIENT_DEFAULT_QUEUE_CALL = (
    "AnnotationQueue.get_or_create_default(project_id=...), or dataset_id= or "
    "agent_definition_id="
)


class _OmittedLabelIds:
    """Readable signature default, distinct from an explicit invalid None."""

    def __repr__(self) -> str:
        return "OMITTED_LABEL_IDS"


OMITTED_LABEL_IDS: Any = _OmittedLabelIds()


class DefaultQueueLabelError(ValueError):
    """No truthful default labels can be derived for a legacy queue create.

    Exactly one scope is needed, and its default queue must already carry labels.
    The server's get-or-create-default endpoint does not manufacture labels.
    """


def default_label_ids(
    scopes: Mapping[str, Any],
    *,
    get_default: Callable[..., Any],
    caller: str,
    stacklevel: int,
) -> list[str]:
    """Reuse get_or_create_default, never invent a label or select an unrelated org label."""
    warnings.warn(
        f"{caller}: label_ids will be required; pass them explicitly. For compatibility, "
        "the given scope is used only to obtain its default queue's labels; the new queue "
        "is not scoped to that entity.",
        DeprecationWarning,
        stacklevel=stacklevel + 1,
    )
    scope_ids = {
        DEFAULT_QUEUE_SCOPE_IDS[key]: value
        for key, value in scopes.items()
        if key in DEFAULT_QUEUE_SCOPE_IDS and value is not None
    }
    if len(scope_ids) != 1:
        raise DefaultQueueLabelError(
            f"{caller}: needs label_ids or exactly one of project, dataset or "
            "agent_definition to resolve a default queue's labels"
        )
    result = get_default(**scope_ids)
    if isinstance(result, Mapping):
        result = result.get("result", result)
        labels = result.get("labels", [])
    else:
        labels = result.labels
    if not labels:
        raise DefaultQueueLabelError(
            f"{caller}: the default queue has no labels; pass label_ids explicitly"
        )
    try:
        return label_id_list([label["id"] for label in labels], caller=caller)
    except (KeyError, TypeError, ValueError) as exc:
        raise DefaultQueueLabelError(
            f"{caller}: the default queue returned invalid label ids; pass label_ids explicitly"
        ) from exc


def ignored_on_create_message(caller: str, instead: str) -> str:
    return (
        f"{caller}: project, dataset and agent_definition are ignored by the server (they are "
        "read-only when a queue is created), so they are not sent. They remain accepted for "
        "compatibility. A create never scopes a queue; for the default queue of a "
        f"project, dataset or agent definition, call {instead}."
    )


def check_uuid(value: str, *, caller: str, what: str) -> None:
    """Raise ``ValueError`` naming ``caller`` unless ``value`` is a UUID.

    ``what`` says what must be one, for example ``"project_id must be a UUID"``. The generated
    models parse ids with ``uuid.UUID`` and would otherwise raise a bare "badly formed
    hexadecimal UUID string" that names no call.
    """
    try:
        UUID(value)
    except ValueError:
        raise ValueError(f"{caller}: {what}, not {value!r}") from None


def default_queue_body(
    *, caller: str, uuid_ids: bool = False, **scope_ids: Any
) -> dict[str, str]:
    """The get-or-create-default request body: exactly one of the scope ids, as a string.

    With ``uuid_ids`` the id must be a UUID (the server's field is a ``UUIDField``); the facade,
    whose generated request model parses it, asks for that check.
    """
    given = {name: value for name, value in scope_ids.items() if value is not None}
    if len(given) != 1:
        raise ValueError(
            f"{caller}: give exactly one of project_id, dataset_id or agent_definition_id "
            f"(got {', '.join(sorted(given)) or 'none'})"
        )
    ((name, value),) = given.items()
    if isinstance(value, UUID):
        value = str(value)
    if not isinstance(value, str) or not value:
        raise TypeError(
            f"{caller}: {name} must be a non-empty id string or UUID, not {value!r}"
        )
    if uuid_ids:
        check_uuid(value, caller=caller, what=f"{name} must be a UUID")
    return {name: value}


def id_list(value: Any, *, caller: str, argument: str) -> list[str]:
    """Return ``value`` (an iterable of id strings or UUIDs) as a list of strings."""
    if isinstance(value, (str, bytes)) or not isinstance(value, Iterable):
        raise TypeError(
            f"{caller}: {argument} must be a list of id strings, not {type(value).__name__}"
        )
    ids: list[str] = []
    for item in value:
        if isinstance(item, UUID):
            item = str(item)
        if not isinstance(item, str) or not item:
            raise TypeError(
                f"{caller}: {argument} must hold non-empty id strings, got {item!r}"
            )
        ids.append(item)
    return ids


def require_on_create(values: Mapping[str, Any], *, caller: str) -> None:
    """Raise ``ValueError`` naming each ``REQUIRED_ON_CREATE`` field that ``values`` lacks
    (absent or ``None``), worded as TypeScript's ``requireKeys``."""
    missing = [key for key in REQUIRED_ON_CREATE if values.get(key) is None]
    if not missing:
        return
    one = len(missing) == 1
    raise ValueError(
        f"{caller}: {' and '.join(missing)} {'is' if one else 'are'} required; the server "
        f"refuses a queue without {'it' if one else 'them'}"
    )


def label_id_list(value: Any, *, caller: str) -> list[str]:
    """``id_list`` for ``label_ids``, which needs at least one id."""
    ids = id_list(value, caller=caller, argument="label_ids")
    if not ids:
        raise ValueError(
            f"{caller}: label_ids needs at least one annotation label id; the server refuses "
            "a queue without labels"
        )
    return ids


def drop_ignored_on_create(
    body: dict[str, Any], *, caller: str, instead: str, stacklevel: int
) -> None:
    """Remove the read-only scope fields from ``body``; warn when one carried a value.

    ``instead`` is the call the warning points at. ``stacklevel`` counts from the caller of
    this function, as in ``warnings.warn``.
    """
    passed = [key for key in IGNORED_ON_CREATE if body.pop(key, None) is not None]
    if passed:
        warnings.warn(
            ignored_on_create_message(caller, instead),
            DeprecationWarning,
            stacklevel=stacklevel + 1,
        )


def refuse_scope_ids(body: dict[str, Any], *, caller: str, default_call: str) -> None:
    """Refuse ``project_id`` / ``dataset_id`` / ``agent_definition_id`` in a create body.

    They are not create fields, and the server never applies them to the queue it creates: its
    serializer reads them only to scope its duplicate-name check (``validate_name``), and the
    view saves none of them (the snapshot pins both). So the queue would be created unscoped
    while the caller believes it is scoped, and its name checked against the wrong queues.
    ``default_call`` names the get-or-create-default call to use instead (for example
    ``"annotation_queues.get_or_create_default"``). Keys holding ``None`` are dropped.
    """
    passed = {
        field: body[field]
        for field in DEFAULT_QUEUE_SCOPE_IDS.values()
        if body.get(field) is not None
    }
    if not passed:
        for field in DEFAULT_QUEUE_SCOPE_IDS.values():
            body.pop(field, None)
        return
    if len(passed) == 1:
        ((field, value),) = passed.items()
        call = f"{default_call}({field}={str(value)!r})"
    else:
        call = f"{default_call}() with one of them"
    it = "it" if len(passed) == 1 else "them"
    raise ValueError(
        f"{caller}: {' and '.join(passed)} cannot be set on a new queue: a create has no such "
        f"field, and the server never applies {it} to the queue (it only uses {it} to scope "
        "its duplicate-name check), so the queue would belong to no project, dataset or agent "
        "definition. For the default queue of a project, dataset or agent definition, call "
        f"{call}."
    )


def create_body(
    body: Mapping[str, Any],
    *,
    caller: str,
    instead: str,
    default_call: str,
    stacklevel: int,
    uuid_ids: bool = False,
    get_default: Callable[..., Any] | None = None,
) -> dict[str, Any]:
    """A request body for the queue create: scope ids refused, required fields present, label
    ids checked, ignored fields dropped.

    With ``uuid_ids`` every label and annotator id must be a UUID (the server's fields are
    lists of ``UUIDField``); the facade, whose generated body model parses them, asks for it.
    """
    out = dict(body)
    refuse_scope_ids(out, caller=caller, default_call=default_call)
    if "label_ids" not in out and out.get("name") is not None and get_default is not None:
        out["label_ids"] = default_label_ids(
            out, get_default=get_default, caller=caller, stacklevel=stacklevel + 1
        )
        # The single omission warning also explains that these never scope the new queue.
        for key in IGNORED_ON_CREATE:
            out.pop(key, None)
    missing = [key for key in REQUIRED_ON_CREATE if out.get(key) is None]
    if missing:
        needs = ", ".join(
            "label_ids (at least one annotation label id; the server refuses a queue "
            "without labels)"
            if key == "label_ids"
            else key
            for key in missing
        )
        raise ValueError(f"{caller}: the body needs {needs}")
    out["label_ids"] = label_id_list(out["label_ids"], caller=caller)
    if out.get("annotator_ids") is not None:
        out["annotator_ids"] = id_list(
            out["annotator_ids"], caller=caller, argument="annotator_ids"
        )
    if uuid_ids:
        for argument in ("label_ids", "annotator_ids"):
            for value in out.get(argument) or ():
                check_uuid(value, caller=caller, what=f"{argument} must hold UUIDs")
    drop_ignored_on_create(
        out, caller=caller, instead=instead, stacklevel=stacklevel + 1
    )
    return out
