"""This package's ``fi/api`` and ``fi/utils`` serve everything ai-evaluation 1.1.0's copies did.

Both distributions ship the same ten files (``fi/__init__.py``, ``fi/api/*``, ``fi/utils/*``); this
package owns them, so its copies must offer every class, function and constant ai-evaluation's
copies defined, with calls that still bind, and every ``Routes`` member with the same path.
"""

from __future__ import annotations

import enum
import importlib
import inspect

from tests.evals._golden import golden


def _params(value: object) -> dict:
    return {p.name: p for p in inspect.signature(value).parameters.values()}


def test_every_name_ai_evaluation_defined_or_set_is_here() -> None:
    missing = []
    for module, names in golden()["shared"].items():
        if module == "Routes":
            continue
        mod = importlib.import_module(module)
        for name, info in names.items():
            if info["kind"] in ("defined", "constant") and not hasattr(mod, name):
                missing.append(f"{module}.{name}")
    assert missing == []


def test_every_call_that_bound_in_1_1_0_still_binds() -> None:
    """Each upstream parameter exists here with the same kind, a parameter upstream did not
    require is not required here, and any parameter added here has a default."""
    broken = []
    for module, names in golden()["shared"].items():
        if module == "Routes":
            continue
        mod = importlib.import_module(module)
        for name, info in names.items():
            if not info["signature"] or not hasattr(mod, name):
                continue
            value = getattr(mod, name)
            if inspect.isclass(value) and issubclass(value, enum.Enum):
                continue  # an Enum class's call signature is the interpreter's, and differs by version
            ours = _params(value)
            upstream = {p[0]: p for p in info["signature"]}
            for pname, kind, required in info["signature"]:
                mine = ours.get(pname)
                var = any(p.kind in (p.VAR_KEYWORD,) for p in ours.values())
                if mine is None and not (var and kind == "KEYWORD_ONLY"):
                    broken.append(f"{module}.{name}({pname}) is gone")
                elif mine is not None and mine.kind.name != kind:
                    broken.append(f"{module}.{name}({pname}) is {mine.kind.name}, was {kind}")
                elif mine is not None and not required and mine.default is inspect.Parameter.empty:
                    broken.append(f"{module}.{name}({pname}) is now required")
            for pname, p in ours.items():
                extra = pname not in upstream and p.kind not in (p.VAR_POSITIONAL, p.VAR_KEYWORD)
                if extra and p.default is inspect.Parameter.empty:
                    broken.append(f"{module}.{name}({pname}) is new and required")
    assert broken == []


def test_every_route_ai_evaluation_had_is_here_with_the_same_path() -> None:
    from fi.utils.routes import Routes

    upstream = golden()["shared"]["Routes"]
    assert len(upstream) > 50
    different = {
        name: (path, Routes[name].value if name in Routes.__members__ else None)
        for name, path in upstream.items()
        if name not in Routes.__members__ or Routes[name].value != path
    }
    assert different == {}


def test_every_route_fi_evals_reads_exists() -> None:
    import re
    from pathlib import Path

    from fi.utils.routes import Routes

    root = Path(__file__).resolve().parents[2] / "fi" / "evals"
    used = set()
    for path in root.rglob("*.py"):
        used |= set(re.findall(r"Routes\.([a-z_0-9]+)", path.read_text(encoding="utf-8")))
    assert used and sorted(used - set(Routes.__members__)) == []
