"""Every extracted executable method matches the published source, not just the import census."""
import ast
import builtins
import json
from pathlib import Path
import symtable

from tests.evals.tools.ast_contract import (
    class_digest, function_digest, node_digest, resolve_definition, resolve_method,
)

PYTHON = Path(__file__).resolve().parents[2]
MANIFEST = json.loads((Path(__file__).parent / "fixtures/upstream-ai-evaluation-1.1.0.json").read_text())


def test_extracted_functions_keep_the_published_signature_and_body():
    # Keep the upstream recording immutable; intentional executable changes have
    # their own reviewed hashes and migration reason, rather than skipping them.
    differences = json.loads((Path(__file__).parent / "fixtures/differences-ai-evaluation-1.1.0.json").read_text())
    expected = {identity: record for entry in differences["differences"]
                for identity, record in entry.get("source_contract", {}).items()}
    seen = set()
    failures = []
    for record in MANIFEST["source_contract"]["functions"]:
        path, owner, name = record["path"], record["owner"], record["name"]
        identity = path + ":" + ((owner + ".") if owner else "") + name
        if owner:
            node = resolve_method(PYTHON, path, owner, name)
        else:
            _, node = resolve_definition(PYTHON, path, name)
        facade = path[:-3].replace("/", ".")
        approved = expected.get(identity, record)
        if identity in expected:
            seen.add(identity)
            assert approved["upstream_ast_sha256"] == record["upstream_ast_sha256"]
            assert approved["ast_sha256"] != record["ast_sha256"]
        if function_digest(node, facade) != approved["ast_sha256"]:
            failures.append(identity)
    assert seen == set(expected), "a source-contract exception must name an upstream function"
    assert failures == []


def test_class_fields_decorators_and_constants_are_preserved():
    failures = []
    for kind, digest in (("classes", class_digest), ("constants", node_digest)):
        for record in MANIFEST["source_contract"][kind]:
            _, node = resolve_definition(PYTHON, record["path"], record["name"])
            if digest(node) != record["ast_sha256"]:
                failures.append(record["path"] + ":" + record["name"])
    assert failures == []


def test_extracted_methods_have_no_unresolved_global_names():
    failures = []
    for path in MANIFEST["added"]:
        if not path.endswith(".py"):
            continue
        table = symtable.symtable((PYTHON / path).read_text(), path, "exec")
        bound = {s.get_name() for s in table.get_symbols()
                 if s.is_imported() or s.is_assigned() or s.is_namespace()}
        pending = list(table.get_children())
        while pending:
            scope = pending.pop()
            pending.extend(scope.get_children())
            missing = {s.get_name() for s in scope.get_symbols() if s.is_global() and s.is_referenced()}
            missing -= bound | set(dir(builtins))
            if missing:
                failures.append((path, scope.get_name(), sorted(missing)))
    assert failures == []


def test_the_size_gate_includes_the_entire_evaluation_port():
    root = PYTHON.parent
    roots = (root / "scripts/platform/lint/roots.mjs").read_text()
    assert '"python/fi/evals"' in roots.split("export const SIZE_ROOTS", 1)[1]
    assert '"python/tests/evals"' in roots.split("export const SIZE_ROOTS", 1)[1]


def test_hygiene_rules_reject_revision_fields():
    import re
    rules = json.loads((PYTHON.parent / "scripts/platform/hygiene-rules.json").read_text())
    rule = next(rule for rule in rules["patterns"] if rule["id"] == "consumer-revision")
    for key in ("commit", "revision", "consumer_head"):
        assert re.search(rule["regex"], json.dumps({key: "a" * 40}))
