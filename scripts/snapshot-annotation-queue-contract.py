#!/usr/bin/env python3
"""Write, or check, the server-contract snapshot for creating an annotation queue.

The snapshot is tests/fixtures/server-contracts/annotation-queue-create.json. The SDK's
contract tests (Python and TypeScript) read it, and fail when a queue create() or
get_or_create_default() drifts from what the backend accepts.

The script parses four backend files from git, without importing or running them.
Their content SHA256 digests pin the serializer, model, base model and viewset.

Refresh, from the futureagi-sdk root (stdlib only, any Python 3.10+):

  git -C <future-agi checkout> fetch origin dev
  python3 scripts/snapshot-annotation-queue-contract.py --backend <future-agi checkout> --ref origin/dev

Add --check to compare without writing: exit 0 when the fields match the snapshot (the
backend commit may still have moved), exit 1 when they differ. --check also prints a WARNING
for each of the four files whose git blob changed although the parsed facts did not: the
script parses only what it knows, so read that file's diff (the warning gives the command)
for anything else that reads or applies a scope id on create. Add --strict to exit 2 then.
"""

from __future__ import annotations

import ast
import hashlib
import runpy
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

_METADATA = runpy.run_path(str(Path(__file__).with_name("annotation_contract_metadata.py")))

SNAPSHOT = Path("tests/fixtures/server-contracts/annotation-queue-create.json")
SERIALIZER = (
    "futureagi/model_hub/serializers/annotation_queues.py",
    "AnnotationQueueSerializer",
)
MODEL = ("futureagi/model_hub/models/annotation_queues.py", "AnnotationQueue")
BASE_MODEL = ("futureagi/tfc/utils/base_model.py", "BaseModel")
VIEWS = ("futureagi/model_hub/views/annotation_queues.py", "AnnotationQueueViewSet")
# The queue routes (model_hub/urls.py registers the viewset as "annotation-queues").
CREATE_PATH = "/model-hub/annotation-queues/"
DEFAULT_QUEUE_ACTION = "get-or-create-default"
# DRF serializer fields that are read-only by construction.
READ_ONLY_FIELD_TYPES = {"SerializerMethodField", "ReadOnlyField", "HiddenField"}
FIELD_KWARGS = (
    "read_only",
    "write_only",
    "required",
    "min_length",
    "allow_null",
    "many",
)
MODEL_KWARGS = ("primary_key", "editable", "null", "blank", "auto_now", "auto_now_add")
# The viewset methods a create runs through.
VIEW_CREATE_METHODS = ("create", "perform_create")
# The facts --check compares (the rest of the snapshot says where they came from).
FACT_KEYS = (
    "endpoint",
    "serializer",
    "model_fields",
    "create",
    "view",
    "get_or_create_default",
)


def git(backend: str, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", backend, *args], check=True, capture_output=True
    ).stdout.decode("utf-8")


def find_class(tree: ast.Module, name: str) -> ast.ClassDef:
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == name:
            return node
    raise SystemExit(f"class {name} not found")


def call_name(func: ast.expr) -> str:
    if isinstance(func, ast.Attribute):
        return func.attr
    if isinstance(func, ast.Name):
        return func.id
    raise SystemExit(f"unsupported field constructor: {ast.dump(func)}")


def field_calls(cls: ast.ClassDef) -> dict[str, ast.Call]:
    out: dict[str, ast.Call] = {}
    for node in cls.body:
        if (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and isinstance(node.value, ast.Call)
        ):
            out[node.targets[0].id] = node.value
    return out


def describe(call: ast.Call, names: tuple[str, ...]) -> dict[str, Any]:
    info: dict[str, Any] = {"field": call_name(call.func)}
    for kw in call.keywords:
        if kw.arg in names:
            info[kw.arg] = ast.literal_eval(kw.value)
        elif kw.arg == "default":
            info["has_default"] = True
        elif kw.arg == "child" and isinstance(kw.value, ast.Call):
            info["child"] = call_name(kw.value.func)
    return info


def meta_of(cls: ast.ClassDef) -> dict[str, Any]:
    meta = next(
        (n for n in cls.body if isinstance(n, ast.ClassDef) and n.name == "Meta"), None
    )
    if meta is None:
        raise SystemExit(f"{cls.name} has no Meta")
    out: dict[str, Any] = {}
    for node in meta.body:
        if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name):
            key = node.targets[0].id
            if key in ("fields", "read_only_fields"):
                out[key] = ast.literal_eval(node.value)
            elif key != "model":
                # extra_kwargs, exclude, ...: the derivation below does not model them.
                raise SystemExit(
                    f"{cls.name}.Meta.{key} is not handled; extend this script"
                )
    return out


def base_names(cls: ast.ClassDef) -> list[str]:
    return [call_name(base) for base in cls.bases]


def find_method(cls: ast.ClassDef, name: str) -> ast.FunctionDef:
    for node in cls.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    raise SystemExit(f"{cls.name}.{name} not found")


def class_attribute(cls: ast.ClassDef, name: str) -> str:
    """The name a class attribute is bound to (``serializer_class = X`` gives ``X``)."""
    for node in cls.body:
        if (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and node.targets[0].id == name
        ):
            return call_name(node.value)
    raise SystemExit(f"{cls.name}.{name} not found")


def saved_fields(method: ast.FunctionDef) -> list[str]:
    """The keyword names of the one ``serializer.save(...)`` call in ``method``."""
    saves = [
        node
        for node in ast.walk(method)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "save"
    ]
    if len(saves) != 1:
        raise SystemExit(
            f"{method.name} has {len(saves)} .save() calls, expected 1; extend this script"
        )
    if any(kw.arg is None for kw in saves[0].keywords):
        raise SystemExit(f"{method.name}: save(**...) is not handled; extend this script")
    return [kw.arg for kw in saves[0].keywords]


def decorator_keywords(method: ast.FunctionDef, decorator: str) -> dict[str, ast.expr]:
    for dec in method.decorator_list:
        if isinstance(dec, ast.Call) and call_name(dec.func) == decorator:
            return {kw.arg: kw.value for kw in dec.keywords if kw.arg}
    return {}


def find_action(cls: ast.ClassDef, url_path: str) -> ast.FunctionDef:
    for node in cls.body:
        if isinstance(node, ast.FunctionDef):
            action = decorator_keywords(node, "action")
            if "url_path" in action and ast.literal_eval(action["url_path"]) == url_path:
                return node
    raise SystemExit(f"{cls.name} has no @action(url_path={url_path!r})")


def exactly_one_of(cls: ast.ClassDef) -> list[str] | None:
    """The fields ``validate()`` requires exactly one of, or None when it has no such rule.

    The rule the backend writes: a tuple of the field names, and ``len(selected) != 1``.
    """
    validate = next(
        (n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == "validate"),
        None,
    )
    if validate is None:
        return None
    names = [
        [elt.value for elt in node.elts]
        for node in ast.walk(validate)
        if isinstance(node, (ast.Tuple, ast.List))
        and node.elts
        and all(isinstance(e, ast.Constant) and isinstance(e.value, str) for e in node.elts)
    ]
    not_one = any(
        isinstance(node, ast.Compare)
        and len(node.ops) == 1
        and isinstance(node.ops[0], ast.NotEq)
        and isinstance(node.comparators[0], ast.Constant)
        and node.comparators[0].value == 1
        for node in ast.walk(validate)
    )
    if len(names) != 1 or not not_one:
        raise SystemExit(f"{cls.name}.validate() changed shape; extend this script")
    return names[0]


def names_used(node: ast.AST, names: set[str]) -> list[str]:
    """Which of ``names`` ``node`` uses: as a string (``request.data.get("project_id")``), a
    keyword (``save(project_id=...)``), an attribute (``queue.project_id``) or a variable."""
    found = set()
    for sub in ast.walk(node):
        if isinstance(sub, ast.Constant) and sub.value in names:
            found.add(sub.value)
        elif isinstance(sub, ast.keyword) and sub.arg in names:
            found.add(sub.arg)
        elif isinstance(sub, ast.Attribute) and sub.attr in names:
            found.add(sub.attr)
        elif isinstance(sub, ast.Name) and sub.id in names:
            found.add(sub.id)
    return sorted(found)


def scope_ids_read(
    cls: ast.ClassDef, names: set[str], methods: tuple[str, ...] | None = None
) -> dict[str, list[str]]:
    """Per method of ``cls`` (all, or only ``methods``), the scope ids it uses; methods using
    none are left out. Recorded so that a create path that starts to read or apply a scope id
    (a new ``validate()`` or ``create()`` line, say) shows up as drift."""
    out: dict[str, list[str]] = {}
    for node in cls.body:
        if isinstance(node, ast.FunctionDef) and (methods is None or node.name in methods):
            used = names_used(node, names)
            if used:
                out[node.name] = used
    return out


def changed_facts(old: dict[str, Any], fresh: dict[str, Any]) -> list[str]:
    return [key for key in FACT_KEYS if old.get(key) != fresh[key]]


def changed_blobs(
    old: dict[str, Any], fresh: dict[str, Any]
) -> list[tuple[str, str | None, str | None]]:
    """(path, snapshot blob, backend blob) for each pinned file whose blob differs."""
    before = {f["path"]: f["sha256"] for f in old["source"]["files"]}
    after = {f["path"]: f["sha256"] for f in fresh["source"]["files"]}
    return [
        (path, before.get(path), after.get(path))
        for path in sorted(before.keys() | after.keys())
        if before.get(path) != after.get(path)
    ]


def view_facts(views: ast.Module, serializers: ast.Module) -> tuple[dict, dict]:
    """What the viewset does on create, and its get-or-create-default action."""
    viewset = find_class(views, VIEWS[1])
    view = {
        "class": VIEWS[1],
        "serializer_class": class_attribute(viewset, "serializer_class"),
        # Everything a create saves besides the validated fields.
        "perform_create_saves": saved_fields(find_method(viewset, "perform_create")),
    }
    method = find_action(viewset, DEFAULT_QUEUE_ACTION)
    action = decorator_keywords(method, "action")
    detail = ast.literal_eval(action["detail"])
    if detail:
        raise SystemExit(f"{DEFAULT_QUEUE_ACTION} became a detail route; extend this script")
    validated = decorator_keywords(method, "validated_request")
    if "request_serializer" not in validated:
        raise SystemExit(f"{method.name} has no request_serializer; extend this script")
    request_name = call_name(validated["request_serializer"])
    request_cls = find_class(serializers, request_name)
    default_queue = {
        "view_method": method.name,
        "methods": sorted(m.upper() for m in ast.literal_eval(action["methods"])),
        "path": f"{CREATE_PATH}{DEFAULT_QUEUE_ACTION}/",
        "request_serializer": {
            "class": request_name,
            "bases": base_names(request_cls),
            "declared_fields": {
                name: describe(call, FIELD_KWARGS)
                for name, call in field_calls(request_cls).items()
            },
            "exactly_one_of": exactly_one_of(request_cls),
        },
    }
    # The scope ids any create-path method of the view reads (none: the view never applies
    # them to the queue).
    view["scope_ids_read"] = scope_ids_read(
        viewset,
        set(default_queue["request_serializer"]["declared_fields"]),
        VIEW_CREATE_METHODS,
    )
    return view, default_queue


derive = _METADATA["derive"]


def build(backend: str, ref: str) -> dict[str, Any]:
    commit = git(backend, "rev-parse", f"{ref}^{{commit}}").strip()
    files, trees = [], {}
    for path, _ in (SERIALIZER, MODEL, BASE_MODEL, VIEWS):
        source = git(backend, "show", f"{commit}:{path}")
        files.append({"path": path, "sha256": hashlib.sha256(source.encode()).hexdigest()})
        trees[path] = ast.parse(source)

    ser_cls = find_class(trees[SERIALIZER[0]], SERIALIZER[1])
    meta = meta_of(ser_cls)
    declared = {
        name: describe(call, FIELD_KWARGS)
        for name, call in field_calls(ser_cls).items()
    }
    serializer = {
        "class": SERIALIZER[1],
        # A plain ModelSerializer ignores unknown keys; a Strict* base refuses them.
        "bases": base_names(ser_cls),
        "meta_fields": meta["fields"],
        "read_only_fields": meta.get("read_only_fields", []),
        "declared_fields": {n: declared[n] for n in meta["fields"] if n in declared},
    }
    model_calls = field_calls(find_class(trees[MODEL[0]], MODEL[1]))
    base_calls = field_calls(find_class(trees[BASE_MODEL[0]], BASE_MODEL[1]))
    model_fields: dict[str, Any] = {}
    for name in meta["fields"]:
        if name in declared:
            continue
        if name in model_calls:
            model_fields[name] = describe(model_calls[name], MODEL_KWARGS)
        elif name in base_calls:
            model_fields[name] = {
                **describe(base_calls[name], MODEL_KWARGS),
                "inherited": True,
            }
    view, default_queue = view_facts(trees[VIEWS[0]], trees[SERIALIZER[0]])
    # The serializer methods that read a scope id from the request, and which ones (only to
    # scope the duplicate-name check: nothing saves them on the queue).
    serializer["scope_ids_read"] = scope_ids_read(
        ser_cls, set(default_queue["request_serializer"]["declared_fields"])
    )
    if view["serializer_class"] != SERIALIZER[1]:
        raise SystemExit(
            f"{VIEWS[1]} now uses {view['serializer_class']}, not {SERIALIZER[1]}; "
            "update SERIALIZER in this script"
        )
    return {
        "about": (
            "Fields of POST /model-hub/annotation-queues/ (AnnotationQueueSerializer), what "
            "AnnotationQueueViewSet saves on create, and the request of POST "
            "/model-hub/annotation-queues/get-or-create-default/, parsed from the backend "
            "source. Written by "
            "scripts/snapshot-annotation-queue-contract.py; do not edit by hand."
        ),
        "source": {
            "repository": "https://github.com/future-agi/future-agi",
            "sha256": _METADATA["source_identity"](files),
            "files": files,
        },
        "refresh": (
            "git -C <future-agi checkout> fetch origin dev && python3 "
            "scripts/snapshot-annotation-queue-contract.py --backend <future-agi checkout> "
            "--ref origin/dev"
        ),
        "endpoint": {"method": "POST", "path": CREATE_PATH},
        "serializer": serializer,
        "model_fields": model_fields,
        "create": derive(serializer, model_fields),
        "view": view,
        "get_or_create_default": default_queue,
    }


def main(argv: list[str] | None = None) -> int:
    return _METADATA["main"](globals(), argv)


if __name__ == "__main__":
    sys.exit(main())
