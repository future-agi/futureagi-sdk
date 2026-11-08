"""Invoke mapped public APIs; a missing wrapper is never replaced by a core call."""
from __future__ import annotations

import copy
import inspect
import re
import typing

UUID = "00000000-0000-4000-8000-000000000001"


def snake(value):
    return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", value).lower()


def public_path(row):
    if row.get("public_wrapper"):
        return row["public_wrapper"]["py"]
    if "wrapper" in row:
        return row["wrapper"]["py"]
    if row["adapter"] == "catalog":
        return "client." + row["catalog"]["public"]
    if row["adapter"] == "platform":
        return row["wrappers"][0]["py"]
    return "client." + ".".join(snake(p) for p in row["name"].split("."))


def unavailable_python_paths(row):
    """Resolve absence candidates, never a callable fallback for offered cases.

    A removed Python twin still has a comparison spelling in the wrapper-map
    contract. Check that spelling so deleting the map entry cannot hide a method
    which is actually registered. Inspect every wrapper, not only the primary.
    """
    wrappers = row.get("wrappers") or ([row["wrapper"]] if "wrapper" in row else [])
    if not wrappers:
        return [public_path(row)]
    paths = []
    for wrapper in wrappers:
        if wrapper.get("py"):
            paths.append(wrapper["py"])
            continue
        absent = wrapper.get("not_offered", {}).get("py", {})
        if absent.get("status") != "NOT-OFFERED" or not absent.get("reason") or not wrapper.get("ts"):
            raise ValueError(f"missing Python path without a valid language declaration: {row['id']}")
        root, *parts = wrapper["ts"].split(".")
        paths.append(".".join([root, *map(snake, parts)]))
    return paths


def absence_candidates(row, inventory):
    """Use real handles, or prove every mapped root factory is absent.

    Missing fixture data alone is never evidence of a missing public API. A
    hidden handle also requires the absence of factories returning its pages.
    """
    if row.get("public_absence"):
        return row["public_absence"]["py"]
    candidates = []
    for path in unavailable_python_paths(row):
        root = path.split(".")[0]
        if root == "client" or row.get("handle_fixtures", {}).get(root, {}).get("py"):
            candidates.append(path)
            continue
        factories = [
            factory
            for candidate in inventory
            for wrapper in candidate.get("wrappers", [])
            if wrapper.get("returns") in (root, f"Page[{root}]")
            for factory in unavailable_python_paths({**candidate, "wrappers": [wrapper]})
            if factory.startswith("client.")
        ]
        if not factories:
            raise ValueError(f"public handle fixture required for {root}; no mapped factory absence proof")
        candidates.extend(factories)
    return candidates


def method_at(client, path, handles=None):
    parts = path.split(".")
    if parts[0] == "client":
        target = client
    else:
        if parts[0] not in (handles or {}):
            raise ValueError(f"public handle fixture required for {path}; no executor fallback")
        target = handles[parts[0]]
    for part in parts[1:]:
        target = getattr(target, part)
    if not callable(target):
        raise TypeError(f"public method is not callable: {path}")
    return target


def value_for(name, row):
    if name in row.get("path_values", {}):
        return row["path_values"][name]
    if name in row.get("query_example", {}):
        return row["query_example"][name]
    if name == "bounds" and row.get("stream"):
        from fi._core.resumable import StreamBounds
        return StreamBounds(max_reconnects=0, max_consecutive_failures=1)
    if name == "rating":
        return "up"
    if name == "body":
        value = copy.deepcopy(row.get("request_example", {}))
        if row["name"] == "prompts.create":
            return {"name": "fixture", "prompt_config": [{"messages": []}]}
        return value
    if name in ("query", "params"):
        return copy.deepcopy(row.get("query_example", {}))
    if name == "file_names":
        return ["fixture.txt"]
    if name == "name" and row["name"] == "knowledgeBases.documents.addText":
        return "fixture.txt"
    if name == "source_type":
        return "trace"
    if name == "id" or name.endswith("_id") or name.endswith("_pk"):
        return UUID
    if name in ("limit", "page", "page_size", "count"):
        return 1
    if name == "wait":
        return False
    if name in ("version", "label"):
        return "v1"
    return "fixture"


def invoke(client, row, handles=None):
    path = public_path(row)
    method = method_at(client, path, handles)
    explicit = row.get("invocation", row.get("wrapper", {}).get("contract", {})).get("py")
    if explicit is not None:
        return method(*copy.deepcopy(explicit["args"]), **copy.deepcopy(explicit.get("kwargs", {})))
    signature = inspect.signature(method)
    try:
        hints = typing.get_type_hints(method)
    except (NameError, TypeError):
        hints = {}
    args, kwargs = [], {}
    for name, param in signature.parameters.items():
        if param.kind == inspect.Parameter.VAR_POSITIONAL:
            raise ValueError(f"explicit public invocation fixture required for {path}")
        if param.kind == inspect.Parameter.VAR_KEYWORD:
            kwargs.update({k: v for k, v in row.get("query_example", {}).items() if k not in signature.parameters})
            continue
        if param.default is not inspect.Parameter.empty and name != "body" and not (name == "bounds" and row.get("stream")):
            if not (row["name"] == "prompts.getByName" and name == "version"):
                continue
        value = value_for(name, row)
        if name == "body":
            annotation = hints.get(name)
            candidates = typing.get_args(annotation) or (annotation,)
            model = next((t for t in candidates if hasattr(t, "from_dict")), None)
            if model is not None:
                value = model.from_dict(value)
        if param.kind == inspect.Parameter.POSITIONAL_ONLY:
            args.append(value)
        else:
            kwargs[name] = value
    return method(*args, **kwargs)
