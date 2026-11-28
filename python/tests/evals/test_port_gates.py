"""The complete port is subject to the same installation and source hygiene rules."""
import builtins
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import warnings

import pytest

ROOT = Path(__file__).resolve().parents[3]
EVALS = ROOT / "python/fi/evals"


def test_feedback_dependency_guidance(monkeypatch):
    from fi.evals.feedback.store import ChromaFeedbackStore
    original = builtins.__import__

    def importing(name, *args, **kwargs):
        if name == "chromadb":
            raise ModuleNotFoundError("chromadb is not installed", name=name)
        return original(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", importing)
    with pytest.raises(ImportError) as error:
        ChromaFeedbackStore()
    assert "pip install chromadb" in str(error.value)
    assert "ai-evaluation" not in str(error.value)


def test_nli_dependency_guidance(monkeypatch):
    from fi.evals.metrics.hallucination import nli
    monkeypatch.setattr(nli, "_heuristic_warning_issued", False)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        nli._warn_heuristic_fallback()
    assert len(caught) == 1
    assert "pip install transformers torch" in str(caught[0].message)
    assert "ai-evaluation" not in str(caught[0].message)


# Third-party distributions the evaluation code tells users to install for an optional feature.
# Anything else after `pip install` (a retired package, a name no index serves for this code, an
# extra futureagi does not define) is wrong guidance.
THIRD_PARTY_INSTALLS = {
    "accelerate", "azure-ai-contentsafety", "celery", "chromadb", "cloudpickle", "httpx",
    "kubernetes", "openai", "opentelemetry-exporter-otlp", "opentelemetry-sdk", "pyyaml", "ray",
    "sentence-transformers", "temporalio", "torch", "transformers",
}
OWNED = ("python/fi/evals", "python/fi/api", "python/fi/utils", "python/fi/__init__.py")
_PIP = re.compile(r"\bpip3?\s+install\b")
_REQUIREMENT = re.compile(r"([A-Za-z0-9][A-Za-z0-9._-]*)(?:\[([^\]]*)\])?(?:[<>=!~].*)?")


def _futureagi_extras():
    text = (ROOT / "python/pyproject.toml").read_text()
    table = text.split("[tool.poetry.extras]", 1)[1].split("\n[", 1)[0]
    return {line.split("=", 1)[0].strip() for line in table.splitlines() if "=" in line}


def install_targets(line):
    """(distribution, extras) named after each `pip install` on a line. Flags are skipped; a
    placeholder (`{name}`, `<name>`) or prose (a word in parentheses) ends the list."""
    found = []
    for match in _PIP.finditer(line):
        for token in line[match.end():].split():
            token = token.strip("'\"`").rstrip(",.;:)'\"`")
            if token.startswith("-"):
                continue
            if not token or token[0] in "{<($":
                break
            requirement = _REQUIREMENT.fullmatch(token)
            if requirement is None:
                break
            found.append((requirement.group(1), requirement.group(2)))
    return found


def test_install_guidance_names_only_futureagi_or_a_third_party_dependency():
    extras, wrong = _futureagi_extras(), []
    paths = [p for root in OWNED for p in ([ROOT / root] if root.endswith(".py") else (ROOT / root).rglob("*"))]
    for path in sorted(p for p in paths if p.is_file() and "__pycache__" not in p.parts):
        for number, line in enumerate(path.read_text(errors="replace").splitlines(), 1):
            for name, extra in install_targets(line):
                normal = re.sub(r"[-_.]+", "-", name).lower()
                if normal == "futureagi" and (extra is None or extra in extras):
                    continue
                if normal in THIRD_PARTY_INSTALLS:
                    continue
                wrong.append(f"{path.relative_to(ROOT)}:{number}: {name}" + (f"[{extra}]" if extra else ""))
    assert wrong == []


def test_the_install_guidance_check_rejects_other_distributions():
    assert install_targets("Or install the extra: pip install fi-evals[{self.extra_name}]") == [
        ("fi-evals", "{self.extra_name}")]
    assert install_targets("pip install ai-evaluation") == [("ai-evaluation", None)]
    assert install_targets("Requires: pip install 'celery[redis]'  # workers") == [("celery", "redis")]
    assert install_targets('INSTALL_HINT = \'pip install "futureagi[evals]"\'') == [("futureagi", "evals")]
    assert install_targets("RUN pip install --no-cache-dir cloudpickle>=3.0") == [("cloudpickle", None)]
    assert install_targets("extra name for pip install (e.g., 'temporal')") == []
    assert install_targets('hint = f\'pip install "{distribution}[{extra}]"\'') == []


def test_port_authored_files_have_no_trailing_whitespace():
    """Files this package added or changed; files kept byte-identical to 1.1.0 stay as published."""
    manifest = json.loads((Path(__file__).parent / "fixtures/upstream-ai-evaluation-1.1.0.json").read_text())
    untidy = []
    for rel in sorted(set(manifest["added"]) | set(manifest["deviations"])):
        text = (ROOT / "python" / rel).read_text()
        untidy += [f"{rel}:{n}" for n, line in enumerate(text.split("\n"), 1) if line != line.rstrip()]
        if text.endswith("\n\n"):
            untidy.append(f"{rel}: blank line at end of file")
    assert untidy == []


def test_every_evals_module_obeys_size_limit():
    oversized = {str(p.relative_to(ROOT)): len(p.read_text().splitlines())
                 for p in EVALS.rglob("*.py") if len(p.read_text().splitlines()) > 400}
    assert oversized == {}


def test_public_census_has_no_consumer_revision_identifiers():
    census = json.loads((Path(__file__).parent / "fixtures/census-fi-evals.json").read_text())
    for source in census["sources"].values():
        assert set(source) == {"repository", "files_with_hits", "cli_lines"}
    assert re.search(r"\b[0-9a-f]{40}\b", json.dumps(census)) is None


def test_census_covers_the_docs_the_site_and_the_app_snippets():
    census = json.loads((Path(__file__).parent / "fixtures/census-fi-evals.json").read_text())
    assert {label: s["repository"] for label, s in census["sources"].items()} == {
        "docs": "future-agi/unified-docs", "site": "future-agi/landing-page", "app": "future-agi/future-agi"}
    assert census["sources"]["app"]["files_with_hits"] >= 1
    assert census["symbols"]["fi.evals:Evaluator"]["app"] >= 1
    assert all(set(counts) == {"docs", "site", "app"} for counts in census["symbols"].values())


def test_census_generator_omits_private_provenance(monkeypatch, tmp_path):
    from tests.evals.tools import census
    monkeypatch.setattr(census, "scan", lambda *_: {"files_with_hits": 1, "cli": {}, "symbols": {}})
    monkeypatch.setattr(census, "_git", lambda *_: "https://github.com/example/docs.git")
    output = tmp_path / "census.json"
    assert census.main(["census", str(output), "docs=repo@" + "a" * 40]) == 0
    assert set(json.loads(output.read_text())["sources"]["docs"]) == {"repository", "files_with_hits", "cli_lines"}


def test_complete_evals_tree_passes_hygiene():
    result = subprocess.run(["python3", str(ROOT / "scripts/platform/hygiene_scan.py"),
                             "python/fi/evals", "python/tests/evals"], cwd=ROOT,
                            text=True, capture_output=True)
    assert result.returncode == 0, result.stdout + result.stderr
