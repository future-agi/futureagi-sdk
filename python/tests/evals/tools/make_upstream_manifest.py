"""Write ``fixtures/upstream-ai-evaluation-1.1.0.json`` from the published ai-evaluation 1.1.0 wheel.

    python -I python/tests/evals/tools/make_upstream_manifest.py WHEEL OUT.json

The wheel is read as a zip and never imported. Each file under ``fi/evals`` is hashed, and the hash
is checked against the wheel's own RECORD. The deviations and additions below are this package's
own list: edit them here, then regenerate (the fixture is never edited by hand).
"""

import ast
import base64
import importlib.util
from pathlib import Path
import csv
import hashlib
import io
import json
import sys
import zipfile

DIST_INFO = "ai_evaluation-1.1.0.dist-info"

DEVIATIONS = {
    "fi/evals/core/prompt_generator.py": (
        "route the optional LiteLLM import through the typed dependency guard, "
        "preserving completion arguments and missing transitive dependency errors"
    ),
    "fi/evals/llm/providers/litellm.py": (
        "route the optional LiteLLM import through the shared typed dependency guard, "
        "preserving provider behavior and missing transitive dependency errors"
    ),
    "fi/evals/guardrails/README.md": (
        "a documentation example spelled so it does not look like a credential "
        "(the scanned string is built at run time)"
    ),
    "fi/evals/metrics/code_security/detectors/secrets.py": (
        "a docstring example value replaced by a placeholder; no code changes"
    ),
    "fi/evals/feedback/store.py": "missing dependency guidance installs chromadb directly, not a retired distribution",
    "fi/evals/metrics/hallucination/nli.py": "NLI repair guidance installs transformers and torch directly",
    "fi/evals/core/cloud_registry.py": (
        "the client delegate uses its shared HTTP transport and an isolated registry cache; "
        "registry failure logs use the exception class, not raw exception text; "
        "module and session caches use normalized URLs and SHA-256 digests of length-framed full credentials, "
        "expire after 300 monotonic seconds, and use lock-protected per-cache/key fill tokens; "
        "close, clear, refresh, expiry and non-success atomically clear the cache and revoke all its fills; "
        "reentrant locking permits clear() while the cache lock is already held; "
        "closed sessions never serve cached entries and failures are never cached"
    ),
    "fi/evals/framework/backends/_utils.py": (
        "the missing-dependency message gives only the dependency's own install command, not an "
        "extra of a distribution that does not ship this code"
    ),
    "fi/evals/framework/backends/__init__.py": (
        "the optional-backend install lines name each backend's own dependency, not an extra of a "
        "distribution that does not ship this code"
    ),
    "fi/evals/metrics/__init__.py": (
        "an RL2213 module __getattr__ that raises ImportError with RL2241 fi.alk replacements for "
        "agent-learning-kit-only names listed in _ALK_REPLACEMENTS; no export, alias or behavior "
        "change for any existing SDK name; local metrics require Python 3.11+ before optional imports"
    ),
    "fi/evals/metrics/agents/__init__.py": (
        "an RL2213 module __getattr__ that raises ImportError with RL2241 fi.alk replacements for "
        "agent-learning-kit-only names listed in _ALK_REPLACEMENTS; no export, alias or behavior "
        "change for any existing SDK name"
    ),
    "fi/evals/local/__init__.py": "local evaluation requires Python 3.11+ before optional imports",
    "fi/evals/llm/__init__.py": "LLM judges require Python 3.11+ before optional imports",
    "fi/evals/metrics/heuristics/similarity_metrics.py": (
        "load rouge_score only when constructing ROUGEScore; missing dependency guidance names "
        "Python 3.11+ and futureagi[evals]"
    ),
}

ADDED = {
    "fi/evals/_extras.py": "value-free Python-version guard and installation guidance for optional local evaluations",
    "fi/evals/_cli.py": "the `futureagi-py evals` command group, which replaces the retired `fi` console script",
    "fi/evals/_delegate.py": "FutureAGIClient().evals.evaluate(...), a thin delegate to Evaluator",
    "fi/evals/_client_transport.py": (
        "borrow the root client's HTTP configuration without a second connection pool or retry loop; "
        "closing the borrowed session atomically clears registry entries and revokes pending fills"
    ),
    "fi/evals/_extracted.py": (
        "binds a class in the modules its methods were moved to, so typing.get_type_hints resolves "
        "their annotations as it did in 1.1.0"
    ),
    "fi/evals/metrics/agents/report.py": (
        "an RL2213 stub updated for RL2241 to raise ImportError naming "
        "fi.alk.evals.metrics.agents.report; the module existed only in agent-learning-kit"
    ),
}

# Facades whose moved methods name their own class in annotations (`-> "StreamingEvaluator"`).
BINDS_ITS_CLASS = (
    "fi/evals/autoeval/pipeline.py",
    "fi/evals/framework/evaluator.py",
    "fi/evals/framework/evaluators/non_blocking.py",
    "fi/evals/guardrails/gateway.py",
    "fi/evals/guardrails/scanners/eval_delegate.py",
    "fi/evals/guardrails/scanners/jailbreak.py",
    "fi/evals/guardrails/scanners/topics.py",
    "fi/evals/metrics/code_security/judges/dual_judge.py",
    "fi/evals/metrics/code_security/judges/pattern_judge.py",
    "fi/evals/metrics/code_security/reports/leaderboard.py",
    "fi/evals/streaming/evaluator.py",
)

LAYOUT = json.loads(Path(__file__).with_name("port-layout.json").read_text())
for facade, helpers in LAYOUT.items():
    DEVIATIONS[facade] = "split into focused modules with compatible public exports; every module is at most 400 lines"
    for helper in helpers:
        ADDED[helper] = "implementation extracted from " + facade + "; public names remain available there"
for helper in (
    "fi/evals/_evaluator_evaluator_evaluate.py",
    "fi/evals/_evaluator_evaluator_submit.py",
):
    ADDED[helper] += "; logs retain only operational context and omit evaluated content and raw exception text"
for facade in BINDS_ITS_CLASS:
    DEVIATIONS[facade] += "; after the class statement, the class is bound in its method modules for their annotations"
DEVIATIONS["fi/evals/evaluator.py"] += "; input mapping also borrows the delegate's registry transport"
DEVIATIONS["fi/evals/guardrails/README.md"] += "; installation names futureagi, not the retired package"
DEVIATIONS["fi/evals/otel/enrichment.py"] = (
    "span enrichment logs omit evaluation scores and raw exception text; "
    "span attributes, return values and exception handling are unchanged"
)


def function_contract(wheel):
    spec = importlib.util.spec_from_file_location("ast_contract", Path(__file__).with_name("ast_contract.py"))
    contract = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(contract)
    records, classes, constants = [], [], []
    for path in sorted(LAYOUT):
        tree = ast.parse(wheel.read(path).decode())
        for cls in tree.body:
            if isinstance(cls, ast.ClassDef):
                classes.append({"path": path, "name": cls.name, "ast_sha256": contract.class_digest(cls)})
        for name, node in contract.assignments(tree):
            constants.append({"path": path, "name": name, "ast_sha256": contract.node_digest(node)})
        for owner, function in contract.functions(tree):
            upstream_digest = contract.function_digest(function)
            if (path, owner, function.name) == ("fi/evals/evaluator.py", "Evaluator", "evaluate"):
                # The sole executable change in the split: route registry reads through the client.
                calls = [n for n in ast.walk(function) if isinstance(n, ast.Call)
                         and isinstance(n.func, ast.Name) and n.func.id == "map_inputs_to_backend"]
                assert len(calls) == 1
                calls[0].keywords.append(ast.keyword(arg="session", value=ast.parse(
                    'getattr(self, "_registry_session", None)', mode="eval").body))
            records.append({"path": path, "owner": owner, "name": function.name,
                            "upstream_ast_sha256": upstream_digest,
                            "ast_sha256": contract.function_digest(function)})
    return {"functions": records, "classes": classes, "constants": constants}


def main(argv):
    if len(argv) != 3:
        print(__doc__, file=sys.stderr)
        return 2
    data = open(argv[1], "rb").read()
    wheel = zipfile.ZipFile(io.BytesIO(data))
    record = {}
    for row in csv.reader(io.StringIO(wheel.read(f"{DIST_INFO}/RECORD").decode())):
        if row and row[0].startswith("fi/evals/") and row[1].startswith("sha256="):
            raw = row[1][len("sha256="):]
            record[row[0]] = base64.urlsafe_b64decode(raw + "=" * (-len(raw) % 4)).hex()
    files = {}
    for name in sorted(wheel.namelist()):
        if name.startswith("fi/evals/") and not name.endswith("/"):
            digest = hashlib.sha256(wheel.read(name)).hexdigest()
            if record.get(name) != digest:
                raise SystemExit(f"{name}: the file does not match the wheel's RECORD")
            files[name] = digest
    if set(files) != set(record) or not set(DEVIATIONS) <= set(files):
        raise SystemExit("the RECORD and the files disagree, or a deviation names a file the wheel lacks")
    manifest = {
        "distribution": "ai-evaluation",
        "version": "1.1.0",
        "wheel": "ai_evaluation-1.1.0-py3-none-any.whl",
        "wheel_sha256": hashlib.sha256(data).hexdigest(),
        "license": "Apache-2.0",
        "note": (
            "Every file under fi/evals in that wheel, with the sha256 of its bytes (the digests of "
            "the wheel's RECORD). A file that differs is listed in deviations with the reason; a "
            "file this package adds is listed in added. Generated by tests/evals/tools/make_upstream_manifest.py."
        ),
        "deviations": DEVIATIONS,
        "added": ADDED,
        "files": files,
        "source_contract": function_contract(wheel),
        "function_deviations": {"fi/evals/evaluator.py:Evaluator.evaluate":
                                "input mapping passes the delegate's shared registry session"},
    }
    with open(argv[2], "w") as out:
        json.dump(manifest, out, indent=1)
        out.write("\n")
    print(f"{len(files)} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
