"""Ask ``typing.get_type_hints`` for every function the ``fi.evals`` modules expose.

``test_type_hints.py`` imports this module, and it runs unchanged where only ai-evaluation 1.1.0 is
installed, so both environments record the same keys:

- ``module:Name`` for each public class or function a module defines or re-exports;
- ``module:Class.attr`` for each function a public class reaches through ``dir()`` (its own, inherited
  or moved into a ``_*Methods`` base), looked up on the class, so a moved method keeps its key.

Only the standard library is imported here.

    python -I type_hints.py MANIFEST.json OUT.json
"""

import importlib
import inspect
import json
import sys
import typing
import warnings


def module_name(path):
    """``fi/evals/x/__init__.py`` -> ``fi.evals.x``."""
    name = path[:-3].replace("/", ".")
    return name[: -len(".__init__")] if name.endswith(".__init__") else name


def upstream_modules(manifest):
    """Every module of the published wheel, from the manifest's file list."""
    return sorted({module_name(p) for p in manifest["files"] if p.endswith(".py")})


def functions_of(value):
    """(suffix, function) for each plain function behind a class attribute."""
    if isinstance(value, (classmethod, staticmethod)):
        value = value.__func__
    if isinstance(value, property):
        return [("." + part, fn) for part, fn in (("fget", value.fget), ("fset", value.fset),
                                                  ("fdel", value.fdel)) if fn is not None]
    wrapped = getattr(value, "func", None)  # functools.cached_property and partialmethod
    if wrapped is not None and inspect.isfunction(wrapped):
        value = wrapped
    return [("", value)] if inspect.isfunction(value) else []


def _ours(obj):
    return (getattr(obj, "__module__", None) or "").startswith("fi.evals")


def public_targets(name, module):
    """The keyed targets of one imported module (see the module docstring)."""
    for attr, obj in sorted(vars(module).items()):
        if attr.startswith("_") or not (inspect.isclass(obj) or inspect.isfunction(obj)) or not _ours(obj):
            continue
        key = f"{name}:{attr}"
        yield key, obj
        if inspect.isclass(obj):
            for member in sorted(dir(obj)):
                try:
                    raw = inspect.getattr_static(obj, member)
                except AttributeError:
                    continue
                for suffix, fn in functions_of(raw):
                    if _ours(fn):
                        yield f"{key}.{member}{suffix}", fn


def defined_targets(module):
    """Every function whose code lives in ``module`` (its globals are the module's namespace), the
    private ones and the methods of its classes included. ``__module__`` is not used: a facade
    re-labels the classes and functions it re-exports with its own name."""
    namespace = vars(module)
    for attr, obj in sorted(namespace.items()):
        if inspect.isfunction(obj) and obj.__globals__ is namespace:
            yield f"{module.__name__}:{attr}", obj
        elif inspect.isclass(obj):
            for member, raw in sorted(vars(obj).items()):
                for suffix, fn in functions_of(raw):
                    if fn.__globals__ is namespace:
                        yield f"{module.__name__}:{attr}.{member}{suffix}", fn


def outcome(target):
    try:
        typing.get_type_hints(target)
        return "ok"
    except Exception as exc:  # noqa: BLE001 - every failure is reported, not raised
        return f"{type(exc).__name__}: {exc}"


def sweep(modules):
    """{key: "ok" or "ExceptionType: message"} for each target of each module that imports."""
    out = {}
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        for name in modules:
            try:
                module = importlib.import_module(name)
            except Exception:  # noqa: BLE001 - a module that cannot import has no hints to ask for
                continue
            for key, target in public_targets(name, module):
                out[key] = outcome(target)
    return out


def main(argv):
    manifest = json.loads(open(argv[1]).read())
    result = sweep(upstream_modules(manifest))
    with open(argv[2], "w") as fh:
        json.dump(result, fh, indent=1, sort_keys=True)
        fh.write("\n")
    failing = {k: v for k, v in result.items() if v != "ok"}
    print(f"{len(result)} targets, {len(failing)} failing")
    for key, value in sorted(failing.items()):
        print(f"  {key} -> {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
