"""Keyless gates that run in the existing CI jobs as tests.

This module holds the shared gates; each platform package adds itself to the lists here. The code
generator's gates (the scoped-spec sha, the policy table, the wrapper map, hygiene and the lints) are
in the sibling test_gates_*.py modules."""

from __future__ import annotations

import ast
import inspect
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

from ._gates_support import load

PYTHON = Path(__file__).resolve().parents[2]
REPO = PYTHON.parent
FI = PYTHON / "fi"
#: Platform-owned Python files. Each platform package appends itself.
PLATFORM_FILES = sorted([FI / "errors.py", *(FI / "_core").glob("*.py"),
                         *(p for p in (FI / "agents" / "runs").rglob("*.py") if p.name != "_cli.py")])
PLATFORM_TESTS = sorted([*(PYTHON / "tests" / "core").glob("*.py"), *(PYTHON / "tests" / "platform").glob("*.py")])
CORE_MODULES = sorted(f"fi._core.{p.stem}" for p in (FI / "_core").glob("*.py") if p.stem != "__init__")
FORBIDDEN_PREFIXES = ("fi.utils", "fi.api", "fi.experiments")
HYGIENE = [
    (re.compile(r"/Volumes/|/Users/|/home/[a-z]"), "a local path"),
    (
        re.compile(r"\b(sk-[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9]{30,}|xox[bp]-[A-Za-z0-9-]{10,})"),
        "a secret",
    ),
    (re.compile(r"\bevidence\b\s*[:=]"), "an evidence field"),
]
#: The hashed-name rules of the shared hygiene rules that this gate applies to the files above.
INTERNAL_NAME_RULES = {"gcp-project", "placeholder-host", "ee-only-marker", "rig"}


def _run(code: str) -> str:
    code = f"import sys; sys.path.insert(0, {str(PYTHON)!r})\n" + code
    out = subprocess.run([sys.executable, "-I", "-B", "-c", code], capture_output=True, text=True, timeout=120, cwd=str(PYTHON))
    assert out.returncode == 0, out.stderr
    return out.stdout.strip()


def test_platform_modules_load_nothing_from_alk_or_experiments():
    """Another distribution overwrites fi/utils and fi/api; fi.experiments is not part of the platform core."""
    code = (
        "import sys; import " + ", ".join(CORE_MODULES) + "; "
        f"print(sorted(m for m in sys.modules if m == 'fi.utils' or m.startswith({FORBIDDEN_PREFIXES!r})))"
    )
    assert _run(code) == "[]"


def test_import_fi_and_fi_errors_load_no_platform_module():
    bootstrap = json.loads(_run(
        "import json, sys; from pathlib import Path\n"
        "before = set(sys.modules); import fi\n"
        "owned = {'fi': 'fi/__init__.py', 'fi._alk_moved': 'fi/_alk_moved.py', "
        "'_futureagi_namespace_guard': '_futureagi_namespace_guard.py'}\n"
        f"root = Path({str(PYTHON)!r})\n"
        "for name, relative in owned.items():\n"
        "    module = sys.modules[name]\n"
        "    assert Path(module.__file__).resolve() == (root / relative).resolve()\n"
        "    assert Path(module.__spec__.origin).resolve() == (root / relative).resolve()\n"
        "third = sorted(m for m in set(sys.modules) - before "
        "if m not in owned and m.split('.')[0] not in sys.stdlib_module_names)\n"
        "print(json.dumps({'fi_modules': sorted(m for m in sys.modules if m.startswith('fi.')), "
        "'third_party': third}))"
    ))
    assert bootstrap == {"fi_modules": ["fi._alk_moved"], "third_party": []}
    for relative in ("fi/_alk_moved.py", "_futureagi_namespace_guard.py"):
        for node in ast.walk(ast.parse((PYTHON / relative).read_text())):
            if isinstance(node, ast.Import):
                assert all(alias.name.split('.')[0] in sys.stdlib_module_names for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                assert node.level == 0 and node.module.split('.')[0] in sys.stdlib_module_names
    assert _run("import sys, fi.errors; print(sorted(m for m in sys.modules if m.startswith('fi._core')))") == "[]"
    # the clients load the platform executor only on the first platform call
    loaded = _run("import sys, fi.futureagi_client; print(sorted(m for m in sys.modules if m.startswith('fi._core')))")
    assert "fi._core.platform_base" not in loaded and "fi._core.origins" not in loaded


def test_platform_modules_are_at_most_400_lines():
    long = {
        str(p.relative_to(PYTHON)): n
        for p in PLATFORM_FILES + PLATFORM_TESTS
        if (n := len(p.read_text().splitlines())) > 400
    }
    assert not long, f"split these modules (at most 400 lines each): {long}"


def test_platform_modules_import_only_what_the_rules_allow():
    allowed = ("fi._sdk_exception", "fi._credentials", "fi._http", "fi.errors", "fi._core", "fi.generated.platform")
    for path in PLATFORM_FILES:
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            names = []
            if isinstance(node, ast.ImportFrom) and node.module and node.module.startswith("fi"):
                names = [node.module]
            elif isinstance(node, ast.Import):
                names = [a.name for a in node.names if a.name.startswith("fi")]
            for name in names:
                if (
                    name == "fi"
                    and isinstance(node, ast.ImportFrom)
                    and all(a.name in ("errors", "__version__") for a in node.names)
                ):
                    continue
                assert name.startswith(allowed), f"{path.name} imports {name} (not an allowed import)"


def test_no_unset_in_public_signatures():
    import importlib

    for name in ["fi.errors", *CORE_MODULES]:
        module = importlib.import_module(name)
        for attr, value in vars(module).items():
            if attr.startswith("_") or not (inspect.isfunction(value) or inspect.isclass(value)):
                continue
            targets = [value] + (
                [m for _, m in inspect.getmembers(value, inspect.isfunction)] if inspect.isclass(value) else []
            )
            for target in targets:
                try:
                    text = str(inspect.signature(target))
                except (TypeError, ValueError):
                    continue
                assert "Unset" not in text, f"{name}.{attr}: {text}"


def test_hygiene_scan_of_committed_platform_files():
    # Internal project, host and rig names are matched by hash, so this file spells none of them.
    scan = load("platform_hygiene", "scripts/platform/hygiene_scan.py")
    names = scan.load_rules()["names"]
    hits = []
    for path in PLATFORM_FILES + PLATFORM_TESTS + [REPO / "CONVENTIONS.md"]:
        if not path.exists():
            continue
        for lineno, line in enumerate(path.read_text().splitlines(), 1):
            for pattern, what in HYGIENE:
                if pattern.search(line) and path != Path(__file__).resolve():  # this file holds the patterns
                    hits.append(f"{path.relative_to(REPO)}:{lineno}: {what}")
            for hit in scan.name_hits(line, names):
                if hit["rule"] in INTERNAL_NAME_RULES:
                    hits.append(f"{path.relative_to(REPO)}:{lineno}: an internal name ({hit['rule']})")
    assert not hits, hits


def test_every_platform_error_is_an_sdk_exception_and_exported():
    import fi.errors as errors
    from fi._sdk_exception import SDKException

    for name in errors.__all__:
        value = getattr(errors, name)
        if isinstance(value, type):
            assert issubclass(value, SDKException), name


def test_sync_and_async_clients_have_the_same_public_surface():
    """The parity test, with the known gaps listed (async core namespaces are a
    later layer; each name leaves this list when its async twin lands)."""
    from fi import AsyncFutureAGIClient, FutureAGIClient

    sync = {n for n in dir(FutureAGIClient) if not n.startswith("_")}
    sync |= {
        "annotation_queues",
        "datasets",
        "evals",
        "experiments_v2",
        "experiment_runs",
        "simulations",
        "tracing",
        "users",
        "alerts",
    }
    aio = {n for n in dir(AsyncFutureAGIClient) if not n.startswith("_")} | {"experiment_runs"}
    only_sync = {
        "annotation_queues",
        "datasets",
        "evals",
        "experiments",
        "experiments_v2",
        "simulations",
        "tracing",
        "users",
        "alerts",
        "api_key",
        "secret_key",
        "close",
    }
    only_async = {"request", "aclose"}
    assert sync - aio == only_sync, sorted(sync - aio)
    assert aio - sync == only_async, sorted(aio - sync)


def test_the_anyio_plugin_is_loaded(request):
    """Async tests use @pytest.mark.anyio; CI installs only `pip install -e ./python pytest`."""
    assert request.config.pluginmanager.hasplugin("anyio")


def test_policy_table_counts_when_the_generated_table_exists():
    """The code generator emits fi/generated/platform/policy.py; without it this gate has nothing to count."""
    policy = FI / "generated" / "platform" / "policy.py"
    if not policy.exists():
        pytest.skip("fi.generated.platform is not on this base")
    from fi._core.policy import counts

    from fi.generated.platform.policy import OPERATIONS  # type: ignore[import-not-found]  # isort: skip

    table = counts(OPERATIONS)
    source = REPO / "openapi" / "platform" / "source.json"
    assert all(
        op.human_only is False for op in OPERATIONS.values()
    ), "human-only operations are never in the scoped table"
    if source.exists() and "counts" in json.loads(source.read_text()):
        assert table == json.loads(source.read_text())["counts"]
