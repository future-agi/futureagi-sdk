"""The public surface: __all__, every module's names, signatures, MRO, error
str/repr/args/pickle, the client's resource tree and model_json_schema()."""

from __future__ import annotations

import importlib
import inspect
import pkgutil
from typing import Any

from .._observe import observe_exception
from .._runner import Case

ERROR_ARGS: dict[str, tuple[tuple[Any, ...], dict[str, Any]]] = {
    "AgentCCError": (("base message",), {}),
    "APIConnectionError": (("connection refused",), {}),
    "APITimeoutError": ((), {}),
    "StreamError": (("stream broke",), {}),
    "GuardrailWarning": (
        (),
        {
            "message": "warned",
            "status_code": 246,
            "completion": {"id": "c"},
            "body": {"id": "c"},
        },
    ),
}


def _sig(obj: Any) -> str:
    try:
        return str(inspect.signature(obj))
    except (TypeError, ValueError) as exc:
        return f"<no signature: {type(exc).__name__}>"


def _modules(ctx) -> list[str]:
    root = ctx.T
    names = [root.__name__]
    for info in pkgutil.walk_packages(root.__path__, prefix=root.__name__ + "."):
        names.append(info.name)
    return sorted(names)


def _rel(ctx, name: str) -> str:
    return name.removeprefix(ctx.root).lstrip(".") or "<root>"


def _module_names(ctx):
    out = {}
    for name in _modules(ctx):
        try:
            module = importlib.import_module(name)
        except Exception as exc:
            out[_rel(ctx, name)] = {"import_error": type(exc).__name__}
            continue
        public = sorted(n for n in vars(module) if not n.startswith("_"))
        defined = sorted(
            n
            for n in public
            if getattr(vars(module)[n], "__module__", None) == name
            and (
                inspect.isclass(vars(module)[n]) or inspect.isfunction(vars(module)[n])
            )
        )
        out[_rel(ctx, name)] = {
            "all": sorted(getattr(module, "__all__", [])) or None,
            "public": public,
            "defined": defined,
        }
    return out


def _all(ctx):
    root = ctx.T
    names = list(root.__all__)
    return {
        "__all__": sorted(names),
        "count": len(names),
        "dir_public": sorted(n for n in dir(root) if not n.startswith("_")),
        "version": getattr(root, "__version__", None),
    }


def _class_surface(cls: type) -> dict[str, Any]:
    members = {}
    for name, value in sorted(vars(cls).items()):
        if name.startswith("_") and name != "__init__":
            continue
        if isinstance(value, property):
            members[name] = "property"
        elif isinstance(value, (staticmethod, classmethod)):
            members[name] = f"{type(value).__name__} {_sig(value.__func__)}"
        elif inspect.isfunction(value):
            members[name] = _sig(value)
        else:
            members[name] = f"attr:{type(value).__qualname__}"
    return {"mro": [c.__qualname__ for c in cls.__mro__], "members": members}


def _signatures(ctx):
    out = {}
    for name in sorted(ctx.T.__all__):
        obj = getattr(ctx.T, name)
        if inspect.isclass(obj):
            out[name] = _class_surface(obj)
        elif callable(obj):
            out[name] = {
                "signature": _sig(obj),
                "coroutine": inspect.iscoroutinefunction(obj),
            }
        else:
            out[name] = {"value_type": type(obj).__qualname__}
    return out


def _resource_tree(obj: Any, depth: int = 0) -> dict[str, Any]:
    tree: dict[str, Any] = {}
    for name in sorted(dir(obj)):
        if name.startswith("_") or depth > 2:
            continue
        try:
            value = getattr(obj, name)
        except Exception as exc:
            tree[name] = {"raises": type(exc).__qualname__}
            continue
        if inspect.ismethod(value):
            tree[name] = {
                "method": _sig(value),
                "coroutine": inspect.iscoroutinefunction(value),
            }
        elif type(value).__module__.split(".")[0] in (
            "agentcc",
            "fi",
        ) and not isinstance(value, (str, int, float, bool)):
            tree[name] = {
                "resource": type(value).__qualname__,
                "members": _resource_tree(value, depth + 1),
            }
        else:
            tree[name] = {"value_type": type(value).__qualname__}
    return tree


def _client_tree(ctx):
    sync = ctx.T.AgentCC(
        api_key="parity-gateway-key", base_url="https://gateway.example.test"
    )
    asyn = ctx.T.AsyncAgentCC(
        api_key="parity-gateway-key", base_url="https://gateway.example.test"
    )
    return {"AgentCC": _resource_tree(sync), "AsyncAgentCC": _resource_tree(asyn)}


def _errors(ctx):
    out = {}
    for name in sorted(ctx.T.__all__):
        cls = getattr(ctx.T, name)
        if not (inspect.isclass(cls) and issubclass(cls, BaseException)):
            continue
        args, kwargs = ERROR_ARGS.get(
            name,
            (
                (),
                {
                    "message": f"{name} message",
                    "status_code": 418,
                    "type": "t",
                    "code": "c",
                    "param": "p",
                    "body": {"error": {"message": "m"}},
                    "request_id": "req-1",
                },
            ),
        )
        try:
            out[name] = observe_exception(cls(*args, **kwargs))
        except Exception as exc:
            out[name] = {"construct_error": type(exc).__qualname__, "message": str(exc)}
    return out


def _schemas(ctx):
    from pydantic import BaseModel

    seen: dict[str, Any] = {}
    for name in _modules(ctx):
        if not (name.startswith(f"{ctx.root}.types") or name == ctx.root):
            continue
        module = importlib.import_module(name)
        for attr, value in sorted(vars(module).items()):
            if (
                inspect.isclass(value)
                and issubclass(value, BaseModel)
                and value is not BaseModel
            ):
                key = value.__qualname__
                if key in seen:
                    continue
                try:
                    seen[key] = value.model_json_schema()
                except Exception as exc:
                    seen[key] = {"schema_error": type(exc).__qualname__}
    return seen


def _not_given(ctx):
    ng = ctx.T.NOT_GIVEN
    return {
        "repr": repr(ng),
        "str": str(ng),
        "bool": bool(ng),
        "singleton": type(ng)() is ng,
    }


def cases() -> list[Case]:
    return [
        Case("surface.all", "surface", _all),
        Case("surface.modules", "surface", _module_names),
        Case("surface.signatures", "surface", _signatures),
        Case("surface.client_tree", "surface", _client_tree),
        Case("surface.errors", "surface", _errors),
        Case("surface.model_json_schema", "surface", _schemas),
        Case("surface.not_given", "surface", _not_given),
    ]
