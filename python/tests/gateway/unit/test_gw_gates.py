"""Static gates on the fi.gateway source.

- every first-party module under ``python/fi/gateway`` (not ``management/``),
  ``python/tests/gateway`` and ``scripts/gateway`` is 400 lines or fewer,
  except eight exact released-test paths with ratcheting ceilings;
- the no-hand-written-URL-path rule of the platform modules finds nothing here, with the
  rule checked against ``scripts/platform/lint/url-path-rule.json``;
- nothing imports ``openai`` (the transport is AgentCC's own), and the only third-party
  imports are the declared base dependencies, plus ImportError-guarded tiktoken
  imports in the released _tokens module only;
- the hosted origin is confined to exact released-wrapper constant definitions;
  AgentCC stays explicit-origin and wrapper/helper uses have a symbol-level gate;
- ``import fi.gateway`` in a fresh interpreter loads no numpy, pandas,
  ``fi.futureagi_client``, ``fi.gateway.management`` or ``openai``.
"""

from __future__ import annotations

import ast
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import fi

REPO = Path(__file__).resolve().parents[4]
GATEWAY = REPO / "python" / "fi" / "gateway"
SCRIPTS = REPO / "scripts" / "gateway"
PYTHON_ROOT = Path(fi.__file__).resolve().parents[1]

# Keep this readable rule copy in sync with scripts/platform/lint/url-path-rule.json.
# The equality test below requires that file and checks every field.
URL_RULE = {
    "pattern": "[\"'`]/(?:(?:workspace|omega-hub|agentcc)(?:/|[\"'`?])|omega/api/)",
    "commentPrefixes": ["*", "/*", "//", "#"],
    "skipDirs": [
        "node_modules",
        "dist",
        "_gen",
        "generated",
        "__pycache__",
        "tests",
        "test",
        "__tests__",
        "__fixtures__",
    ],
    "skipFiles": "\\.test\\.|_test\\.py$|^test_|^conftest\\.py$|\\.d\\.ts$",
    "extensions": [".ts", ".mts", ".mjs", ".js", ".py"],
}
URL_RULE_FILE = REPO / "scripts" / "platform" / "lint" / "url-path-rule.json"

# The data plane imports stdlib, httpx, anyio, pydantic, typing_extensions and
# fi._sdk_exception. jsonschema is a base dependency already, imported lazily by
# validate_json_response only.
ALLOWED_THIRD_PARTY = {"httpx", "anyio", "pydantic", "typing_extensions", "jsonschema"}
ALLOWED_FI = {"fi._sdk_exception"}
FORBIDDEN_AFTER_IMPORT = (
    "numpy",
    "pandas",
    "fi.futureagi_client",
    "fi.gateway.management",
    "openai",
)


def _gateway_sources() -> list[Path]:
    return sorted(
        p
        for p in GATEWAY.rglob("*.py")
        if "management" not in p.relative_to(GATEWAY).parts
        and "__pycache__" not in p.parts
    )


def _imports(path: Path) -> list[tuple[int, str]]:
    """Every absolute module a file imports (``import x.y`` / ``from x.y import z``)."""
    out = []
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            out += [(node.lineno, alias.name) for alias in node.names]
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            out.append((node.lineno, node.module))
    return out


# RL 2251n / RL 2289: append only; never replace or remove earlier entries.
# Every increase needs its own ordered, exact-target ruling in GROWTH_RECORDS.
CEILING_HISTORY = {
    "python/tests/gateway/test_gateway_config.py": [923],
    "python/tests/gateway/test_advanced_features.py": [571],
    "python/tests/gateway/test_exceptions.py": [533],
    "python/tests/gateway/test_new_resources.py": [522],
    "python/tests/gateway/test_batch.py": [482],
    "python/tests/gateway/test_token_model_utils.py": [472],
    "python/tests/gateway/test_responses_files.py": [458],
    "python/tests/gateway/test_security_review_fixes.py": [450],
}
GROWTH_RECORDS = {}
RELEASED_TEST_LINE_CEILINGS = {path: history[-1] for path, history in CEILING_HISTORY.items()}


def _assert_ceiling_history(history, initial, ceiling, count, growth_records):
    """Strict decreases only, except increases consuming explicit growth records."""
    assert isinstance(history, list) and history
    assert all(type(value) is int and value > 0 for value in history)
    assert history[0] == initial, "history must start at the authorized ceiling"
    assert ceiling == history[-1], "active ceiling must equal the history tail"
    assert type(ceiling) is int and type(count) is int and 0 <= count <= ceiling
    assert isinstance(growth_records, list)
    records = growth_records.copy()
    for previous, current in zip(history, history[1:]):
        assert current != previous, "equal history entries are not allowed"
        if current > previous:
            record = records.pop(0) if records else None
            assert isinstance(record, dict), "ceiling increase needs a growth record"
            assert set(record) == {"record", "to"}
            assert isinstance(record["record"], str) and record["record"].strip()
            assert type(record["to"]) is int and record["to"] == current
    assert not records, "unused growth records are not allowed"


def test_every_module_is_at_most_400_lines() -> None:
    tests = REPO / "python" / "tests" / "gateway"
    files = _gateway_sources() + sorted(SCRIPTS.glob("*.py"))
    # The unmodified third-party dependency has its own RECORD-hash check and
    # documented size exception in _vendor/VENDORED.json. Keep its handling separate.
    vendor = tests / "_vendor"
    record = json.loads((vendor / "VENDORED.json").read_text())
    exceptions = record["module_line_limit_exception"]
    assert exceptions["reason"]
    exempt = {vendor / "respx" / name for name in exceptions["files"]}
    for name, count in exceptions["files"].items():
        assert name in record["record_sha256"]
        assert count > 400
        assert len((vendor / "respx" / name).read_text().splitlines()) == count
    files += sorted(p for p in tests.rglob("*.py") if p not in exempt)
    assert len(files) > 50
    over = [
        f"{p.relative_to(REPO)}: {n}"
        for p in files
        if (n := len(p.read_text(encoding="utf-8").splitlines()))
        > RELEASED_TEST_LINE_CEILINGS.get(p.relative_to(REPO).as_posix(), 400)
    ]
    assert over == []


def _url_path_hits(files: list[Path], root: Path, rule: dict) -> list[str]:
    """The same platform URL lint exercised in test_gates_hygiene.py."""
    literal = re.compile(rule["pattern"])
    skip_file = re.compile(rule["skipFiles"])
    comments = tuple(rule["commentPrefixes"])
    hits = []
    for path in files:
        rel = path.relative_to(root)
        if (
            set(rel.parts[:-1]) & set(rule["skipDirs"])
            or skip_file.search(path.name)
            or path.suffix not in rule["extensions"]
        ):
            continue
        for number, line in enumerate(
            path.read_text(encoding="utf-8").splitlines(), start=1
        ):
            if not line.strip().startswith(comments) and literal.search(line):
                hits.append(f"{rel.as_posix()}:{number}")
    return hits


def test_no_hand_written_platform_paths_in_fi_gateway() -> None:
    """The data plane calls only OpenAI-style /v1/* routes and /healthz."""
    sources = _gateway_sources()
    assert sources
    assert _url_path_hits(sources, REPO, URL_RULE) == []


def test_the_rule_copy_still_bites(tmp_path: Path) -> None:
    files = {
        "fi/gateway/a.py": 'PATH = "/agentcc/gateways/"\nP = "/v1/chat/completions"\n',
        "fi/gateway/b.py": "x = '/omega/api/workspace/x'\ny = '/omega/api'\n",
        "fi/gateway/c.py": '# "/workspace/in-a-comment"\nz = "/healthz"\n',
        "fi/gateway/test_d.py": 'PATH = "/agentcc/api-keys"\n',
    }
    for rel, text in files.items():
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / rel).write_text(text)
    hits = _url_path_hits(sorted(tmp_path.rglob("*.py")), tmp_path, URL_RULE)
    assert hits == ["fi/gateway/a.py:1", "fi/gateway/b.py:1"]


def test_the_rule_copy_matches_the_rule_file() -> None:
    """The checked-in rule and the gateway copy must agree."""
    assert URL_RULE_FILE.is_file()
    rule = json.loads(URL_RULE_FILE.read_text(encoding="utf-8"))
    assert {k: rule[k] for k in URL_RULE} == URL_RULE


HOSTED = re.compile(r"gateway\.futureagi\.com", re.IGNORECASE)


# Exact module + symbol definitions only. Comments, other assignments and new
# defaults in these same modules remain forbidden. Uses are checked separately.
HOSTED_DEFINITIONS = {
    ("python/fi/gateway/_constants.py", "AGENTCC_GATEWAY_URL"):
        'AGENTCC_GATEWAY_URL: str = "https://gateway.futureagi.com/v1"',
    ("python/fi/gateway/_fi.py", "DEFAULT_GATEWAY_URL"):
        'DEFAULT_GATEWAY_URL = "https://gateway.futureagi.com"',
}


def _hosted_hits(files: list[Path], root: Path) -> list[str]:
    hits = []
    for path in files:
        rel = path.relative_to(root).as_posix()
        text = path.read_text(encoding="utf-8")
        allowed_lines = set()
        try:
            tree = ast.parse(text)
        except SyntaxError:
            tree = ast.Module(body=[], type_ignores=[])
        for node in tree.body:
            targets = node.targets if isinstance(node, ast.Assign) else (
                [node.target] if isinstance(node, ast.AnnAssign) else []
            )
            if len(targets) == 1 and isinstance(targets[0], ast.Name):
                exact = HOSTED_DEFINITIONS.get((rel, targets[0].id))
                if exact and text.splitlines()[node.lineno - 1] == exact:
                    allowed_lines.add(node.lineno)
        for number, line in enumerate(text.splitlines(), 1):
            if HOSTED.search(line) and number not in allowed_lines:
                hits.append(f"{rel}:{number}")
    return hits


def test_no_hosted_gateway_url_in_fi_gateway() -> None:
    """Only the exact released-wrapper constant definitions may spell the host."""
    assert _hosted_hits(_gateway_sources(), REPO) == []


def test_the_hosted_url_check_bites(tmp_path: Path) -> None:
    files = {
        "a.py": '    base_url: str = "https://gateway.futureagi.com",\n',
        "b.py": "# see HTTPS://Gateway.FutureAGI.com in a comment\n",
        "c.py": 'URL = "https://gateway.example.com"\nDOCS = "https://futureagi.com"\n',
    }
    for name, text in files.items():
        (tmp_path / name).write_text(text)
    hits = _hosted_hits(sorted(tmp_path.glob("*.py")), tmp_path)
    assert hits == ["a.py:1", "b.py:1"]


def test_hosted_definition_allowlist_does_not_exempt_other_symbols(tmp_path: Path) -> None:
    files = []
    for (module, symbol), definition in HOSTED_DEFINITIONS.items():
        path = tmp_path / module
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(definition + '\nOTHER = "https://gateway.futureagi.com"\n')
        files.append(path)
    assert _hosted_hits(files, tmp_path) == [
        "python/fi/gateway/_constants.py:2", "python/fi/gateway/_fi.py:2",
    ]


def test_nothing_imports_openai() -> None:
    hits = [
        f"{p.relative_to(REPO)}:{line}"
        for p in _gateway_sources()
        for line, module in _imports(p)
        if module == "openai" or module.startswith("openai.")
    ]
    assert hits == []
    text_hits = [
        str(p.relative_to(REPO))
        for p in _gateway_sources()
        if re.search(
            r"import_module\(\s*[\"']openai|__import__\(\s*[\"']openai",
            p.read_text(encoding="utf-8"),
        )
    ]
    assert text_hits == []


def _guarded_tiktoken_lines(path: Path) -> set[int]:
    """RL 2251n: only this module's lexically ImportError-guarded imports."""
    if path.relative_to(REPO).as_posix() != "python/fi/gateway/_tokens.py":
        return set()
    lines: set[int] = set()

    def visit(node: ast.AST, guarded: bool = False) -> None:
        # A function body executes later, outside an enclosing definition-time try.
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
            guarded = False
        if isinstance(node, ast.Try):
            catches_import_error = any(
                isinstance(h.type, ast.Name) and h.type.id == "ImportError"
                for h in node.handlers
            )
            for child in node.body:
                visit(child, guarded or catches_import_error)
            for child in [*node.handlers, *node.orelse, *node.finalbody]:
                visit(child, guarded)
            return
        if guarded and isinstance(node, (ast.Import, ast.ImportFrom)):
            lines.add(node.lineno)
        for child in ast.iter_child_nodes(node):
            visit(child, guarded)

    visit(ast.parse(path.read_text(encoding="utf-8")))
    return lines


def test_only_the_planned_dependencies_are_imported() -> None:
    stdlib = set(sys.stdlib_module_names) | {"__future__"}
    bad = []
    for path in _gateway_sources():
        guarded_tiktoken = _guarded_tiktoken_lines(path)
        for line, module in _imports(path):
            if module == "tiktoken" and line in guarded_tiktoken:
                continue
            top = module.split(".")[0]
            if top in stdlib or top in ALLOWED_THIRD_PARTY:
                continue
            if module == "fi.gateway" or module.startswith("fi.gateway."):
                continue
            if module in ALLOWED_FI:
                continue
            bad.append(f"{path.relative_to(REPO)}:{line}: {module}")
    assert bad == []


def _fresh(code: str) -> str:
    env = {
        k: v
        for k, v in os.environ.items()
        if not k.startswith(("FI_", "AGENTCC_", "OPENAI_")) and k != "PYTHONPATH"
    }
    env["PYTHONPATH"] = str(PYTHON_ROOT)
    return subprocess.run(
        [sys.executable, "-c", code],
        env=env,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()


def test_import_fi_gateway_loads_nothing_heavy_in_a_fresh_interpreter() -> None:
    names = json.dumps(list(FORBIDDEN_AFTER_IMPORT))
    out = _fresh(
        "import json, sys; import fi.gateway; "
        f"bad = [m for m in {names} if m in sys.modules or "
        "any(k.startswith(m + '.') for k in sys.modules)]; print(json.dumps(bad))"
    )
    assert json.loads(out) == []


def test_using_the_client_loads_nothing_heavy_either() -> None:
    """Building a client and reading a response goes through the lazy names too."""
    names = json.dumps(list(FORBIDDEN_AFTER_IMPORT))
    out = _fresh(
        "import json, sys, httpx; from fi.gateway import AgentCC; "
        "h = lambda r: httpx.Response(200, json={'id': 'c', 'object': 'chat.completion', "
        "'created': 1, 'model': 'm', 'choices': [{'index': 0, 'message': "
        "{'role': 'assistant', 'content': 'hi'}}]}); "
        "c = AgentCC(api_key='k', base_url='http://127.0.0.1:8090', "
        "http_client=httpx.Client(transport=httpx.MockTransport(h))); "
        "r = c.chat.completions.create(model='m', messages=[]); assert r.agentcc is not None; "
        f"bad = [m for m in {names} if m in sys.modules or "
        "any(k.startswith(m + '.') for k in sys.modules)]; print(json.dumps(bad))"
    )
    assert json.loads(out) == []


def test_dir_lists_the_public_api_and_nothing_imported_for_typing() -> None:
    out = json.loads(_fresh("import json, fi.gateway as g; print(json.dumps(dir(g)))"))
    import fi.gateway as gw

    assert set(gw.__all__) <= set(out)
    assert {"Any", "TYPE_CHECKING", "annotations"}.isdisjoint(out)
    assert [n for n in out if not n.startswith("__")] == sorted(
        n for n in gw.__all__ if not n.startswith("__")
    )


def test_py_typed_ships_with_the_package() -> None:
    assert (GATEWAY / "py.typed").is_file()
