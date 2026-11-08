"""Record what the published ai-evaluation 1.1.0 does, as the golden file the compatibility tests read.

Run it in a virtual environment where ai-evaluation 1.1.0 is installed and this package is not,
from a directory that has no ``fi`` folder, so ``import fi`` is the published package::

    python -I python/tests/evals/record_upstream.py OUT.json

It writes one JSON object:

- ``installed``: the version, and whether every installed ``fi/evals`` file has the sha256 the
  provenance manifest lists (so the recording is of exactly those bytes);
- ``examples``: for each example in ``_examples.py``, the requests it sent to the fake API in
  ``_mock_http.py`` and the result it returned or the exception it raised;
- ``census``: for each name in ``fixtures/census-fi-evals.json``, whether
  ``from <module> import <name>`` works in 1.1.0, or the error it raises;
- ``shared``: the public names of ai-evaluation's own copies of the modules both packages ship
  (``fi.api.*``, ``fi.utils.*``), and its ``Routes`` members with their paths.

No network: the fake answers every HTTP request, and any other socket is refused.
"""

from __future__ import annotations

import hashlib
import importlib
import inspect
import json
import os
import socket
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import _examples  # noqa: E402
import _mock_http  # noqa: E402

SHARED_MODULES = (
    "fi.api", "fi.api.auth", "fi.api.types", "fi.utils", "fi.utils.constants", "fi.utils.errors",
    "fi.utils.executor", "fi.utils.routes", "fi.utils.utils",
)


def _refuse_sockets() -> None:
    def refuse(*args, **kwargs):
        raise ConnectionRefusedError("recording: no network")

    socket.socket.connect = refuse  # type: ignore[method-assign]
    socket.getaddrinfo = refuse  # type: ignore[assignment]


def _installed(manifest: dict) -> dict:
    import fi.evals

    root = Path(fi.evals.__file__).resolve().parent.parent.parent
    mismatched = []
    for rel, digest in manifest["files"].items():
        data = (root / rel).read_bytes() if (root / rel).exists() else b""
        if hashlib.sha256(data).hexdigest() != digest:
            mismatched.append(rel)
    from importlib.metadata import version

    return {"version": version("ai-evaluation"), "files": len(manifest["files"]), "mismatched": mismatched}


def _environment(env: dict) -> dict:
    saved = {k: os.environ.get(k) for k in env}
    for key, value in env.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value
    return saved


def _restore(saved: dict) -> None:
    for key, value in saved.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value


def record_examples() -> dict:
    out = {}
    for name, fn in _examples.EXAMPLES.items():
        env, overrides = _examples.SPECIAL.get(name, ({}, {}))
        saved = _environment(env)
        _mock_http.reset_caches()
        try:
            out[name] = _mock_http.run_example(fn, _mock_http.FakeBackend(overrides))
        finally:
            _restore(saved)
    return out


def record_census(census: dict) -> dict:
    out = {}
    for key in census["symbols"]:
        module, _, name = key.partition(":")
        try:
            mod = importlib.import_module(module)
            if name != "*":
                getattr(mod, name)
            out[key] = {"ok": True}
        except BaseException as exc:  # noqa: BLE001 - every failure is the record
            if isinstance(exc, (KeyboardInterrupt, SystemExit)):
                raise
            out[key] = {"ok": False, "error": f"{type(exc).__name__}: {str(exc)[:200]}",
                        "missing_module": getattr(exc, "name", None) if isinstance(exc, ImportError) else None}
    return out


def _kind(module: str, value: object) -> str:
    if inspect.ismodule(value):
        return "module"
    if getattr(value, "__module__", None) == module and (inspect.isclass(value) or inspect.isfunction(value)):
        return "defined"
    if inspect.isclass(value) or inspect.isroutine(value):
        return "imported"
    return "constant"


def _signature(value: object):
    try:
        return [[p.name, p.kind.name, p.default is inspect.Parameter.empty] for p in inspect.signature(value).parameters.values()]
    except (TypeError, ValueError):
        return None


def record_shared() -> dict:
    """For each shared module: every public name, its kind, and the call signature of each class or
    function the module defines (parameter name, kind, and whether it is required)."""
    out = {}
    for module in SHARED_MODULES:
        mod = importlib.import_module(module)
        names = {}
        for name, value in sorted(vars(mod).items()):
            if name.startswith("_"):
                continue
            kind = _kind(module, value)
            names[name] = {"kind": kind, "signature": _signature(value) if kind == "defined" else None}
        out[module] = names
    from fi.utils.routes import Routes

    out["Routes"] = {member: Routes[member].value for member in Routes.__members__}
    return out


def record_surface() -> dict:
    import fi.evals as evals

    return {
        "all": sorted(evals.__all__),
        "evaluator_available": bool(evals._evaluator_available),
        "framework_available": bool(evals._framework_available),
        "template_names": sorted(evals.evaluation_template_names),
    }


def main(argv: list) -> int:
    if len(argv) != 2:
        print(__doc__, file=sys.stderr)
        return 2
    os.environ.update({
        "FI_API_KEY": _mock_http.KEY,
        "FI_SECRET_KEY": _mock_http.SECRET,
        "FI_BASE_URL": _mock_http.BASE_URL,
        "FI_LOGIN_FILE": "/nonexistent/futureagi-login.json",
        "LITELLM_LOCAL_MODEL_COST_MAP": "True",
    })
    _refuse_sockets()
    manifest = json.loads((HERE / "fixtures" / "upstream-ai-evaluation-1.1.0.json").read_text())
    census = json.loads((HERE / "fixtures" / "census-fi-evals.json").read_text())
    import fi

    if Path(fi.__path__[0]).resolve().is_relative_to(HERE.parent.parent):
        print("record_upstream: `import fi` found this source tree, not the published package", file=sys.stderr)
        return 2
    record = {
        "installed": _installed(manifest),
        "python": sys.version.split()[0],
        "examples": record_examples(),
        "census": record_census(census),
        "shared": record_shared(),
        "surface": record_surface(),
    }
    Path(argv[1]).write_text(json.dumps(record, indent=1, sort_keys=True, default=str) + "\n")
    bad = record["installed"]["mismatched"]
    print(f"recorded {len(record['examples'])} examples, {len(record['census'])} names; "
          f"{len(bad)} installed files differ from the manifest")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
