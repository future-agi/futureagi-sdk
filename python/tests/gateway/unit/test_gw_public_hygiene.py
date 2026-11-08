"""Public hygiene: fi.gateway, its tests and its scripts name no local path, no
internal design document and none of the build process's own words.

futureagi-sdk is a public repository. Every text file under ``python/fi/gateway``
(not ``management/``), ``python/tests/gateway`` (not ``parity/``, which has its own
scan), ``scripts/gateway`` and the shared parity data ``tests/fixtures/gateway`` (the
goldens, the case catalog and the intended-differences list with its reviewer records)
is scanned for:

- local paths: a home directory under the macOS users root, a mounted volume, or the
  developers' local notes directory;
- the names of internal design documents, inventories, integration notes and
  operational logs, together with their section references,
  which readers of the public repository cannot open. The names are held as truncated
  SHA-256 digests of their words, so this public file does not spell them;
- the build process's own words, which mean nothing to those readers either: work-stream
  ids (an ``L`` and one digit), the work-stream word itself, the checking agent, fix-round
  numbers, cloud job ids, workflow ids and the build machines' instance kind.

The other patterns are assembled from pieces at run time, so this file passes its own
scan; every bite sample below is synthetic.
The transport also has no hosted base URL default: ``BaseClient.__init__`` requires
``base_url``.
"""

from __future__ import annotations

import hashlib
import importlib.util
import inspect
import json
import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[4]
_spec = importlib.util.spec_from_file_location(
    "review_metadata", REPO / "python/tests/gateway/parity/_review.py"
)
assert _spec and _spec.loader
_review = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_review)
ROOTS = (
    (REPO / "python" / "fi" / "gateway", {"management"}),
    (REPO / "python" / "tests" / "gateway", {"parity"}),
    (REPO / "scripts" / "gateway", set()),
    (REPO / "tests" / "fixtures" / "gateway", set()),
)
SKIP_PARTS = {"__pycache__", ".pytest_cache"}


def _j(*parts: str) -> str:
    return "".join(parts)


LOCAL_PATHS = (
    re.escape(_j(".", "futureagi", "-local")),
    re.escape(_j("/", "Volumes", "/")),
    re.escape(_j("/", "Users", "/")),
)
# The internal document names: sha256(name)[:16] of each name, its words joined by "-"
# (a two-word name in prose, by one space). Case matters, as in the names.
DOC_NAME_DIGESTS = frozenset(
    {
        "097221ffff991fad",
        "0ff15403106fefda",
        "12e3252fd56e0b75",
        "1a1f87e00f7dac4e",
        "204248500a1c2294",
        "27cd9caa843dcbf9",
        "293b90888520644a",
        "2ed983d9c5692ffd",
        "3699e7b636f6fd65",
        "379aed35e171560b",
        "3d23ac7958c6f16d",
        "517de0dbef59405f",
        "530cdbed8b7a85b2",
        "6cfbdd08634c3af7",
        "7c92b36e594239fa",
        "83a76f29e2fcca1a",
        "ad0a04f1643769e3",
        "bc7f4a15879f6527",
        "ccb85a77ad5fc31e",
        "d5ae7c5bd05aaabe",
        "e3dc6940f073fe34",
        "f9e3ef06849bcbf0",
    }
)
DOC_REFERENCES = (
    _j(r"\bC", r"R [ABS][0-9]"),
    _j(r"\bI", r"NV-[ACFP]\b"),
    _j(r"\bD", r"[AB] §"),
    _j("[Rr]ul", r"ing [0-9]"),
)
PROCESS_WORDS = (
    _j(r"(?<![A-Za-z0-9])L[1-9]", r"(?![0-9])"),
    _j(r"(?<![A-Za-z])[Ll]a", r"nes?(?![A-Za-z])"),
    _j(r"\bverif", r"(ier|y agent)"),
    _j(r"\b[Rr]ou", r"nd [0-9]+\b"),
    _j(r"\bj-20[0-9]{6}", r"t[0-9]{4}-[0-9a-f]{6}\b"),
    _j(r"\bwf", r"_[0-9a-f]{8}"),
    _j(r"\b[Ss]p", r"ot (VM|instance)s?\b"),
)
FORBIDDEN = re.compile("|".join(LOCAL_PATHS + DOC_REFERENCES + PROCESS_WORDS))
# A name-like token: words joined by "-", "_", "." or "/" (so a file name, a path or a
# hyphenated name is one token); its runs of up to 3 words are what the digests name.
TOKEN = re.compile(r"[A-Za-z0-9]+(?:[-_./][A-Za-z0-9]+)*")
WORD = re.compile(r"[A-Za-z]+")


def _digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def _doc_name(text: str, digests: frozenset[str] = DOC_NAME_DIGESTS) -> str | None:
    """The first internal document name in *text*, or ``None``."""
    for match in TOKEN.finditer(text):
        parts = re.split(r"[-_./]", match.group(0))
        for i in range(len(parts)):
            for j in range(i + 1, min(len(parts), i + 3) + 1):
                if _digest("-".join(parts[i:j])) in digests:
                    return match.group(0)
    words = WORD.findall(text)
    for first, second in zip(words, words[1:]):
        if _digest(f"{first} {second}") in digests:
            return f"{first} {second}"
    return None


def _forbidden(text: str, digests: frozenset[str] = DOC_NAME_DIGESTS) -> str | None:
    match = FORBIDDEN.search(text)
    return match.group(0) if match else _doc_name(text, digests)


def _files(root: Path, skip_dirs: set[str]) -> list[Path]:
    out = []
    for path in sorted(root.rglob("*")):
        rel = path.relative_to(root).parts
        if not path.is_file() or SKIP_PARTS & set(rel):
            continue
        if rel[0] in skip_dirs:
            continue
        out.append(path)
    return out


def _hits(
    files: list[Path], base: Path, digests: frozenset[str] = DOC_NAME_DIGESTS
) -> list[str]:
    hits = []
    for path in files:
        rel = path.relative_to(base).as_posix()
        if _forbidden(rel, digests):
            hits.append(f"{rel}: (file name)")
        data = path.read_bytes()
        if b"\x00" in data:
            continue
        text = data.decode("utf-8", errors="replace")
        if path.suffix == ".json":
            try:
                metadata = json.loads(text)
            except ValueError:
                metadata = None
            for entry_id in _review.review_metadata_hits(metadata):
                hits.append(f"{rel}: {entry_id}: review metadata contains a revision")
        for number, line in enumerate(text.splitlines(), start=1):
            found = _forbidden(line, digests)
            if found:
                hits.append(f"{rel}:{number}: {found!r}")
    return hits


def test_no_local_path_or_internal_document_name_in_the_public_tree() -> None:
    files = [f for root, skip in ROOTS for f in _files(root, skip)]
    assert len(files) > 100
    assert _hits(files, REPO) == []


def test_the_scan_covers_the_source_tests_scripts_and_data_files() -> None:
    names = {f.relative_to(REPO).as_posix() for r, s in ROOTS for f in _files(r, s)}
    for expected in (
        "python/fi/gateway/_transport/_base.py",
        "python/fi/gateway/py.typed",
        "python/tests/gateway/port_manifest.json",
        "python/tests/gateway/intended-differences-py.json",
        "python/tests/gateway/_vendor/VENDORED.json",
        "python/tests/gateway/unit/test_gw_public_hygiene.py",
        "scripts/gateway/compare_enew.py",
        "python/tests/gateway/live/test_live_core.py",
        "python/tests/gateway/live/stack/gateway.yaml",
        "tests/fixtures/gateway/intended-differences.json",
        "tests/fixtures/gateway/catalog.json",
        "tests/fixtures/gateway/README.md",
        "tests/fixtures/gateway/golden/py-agentcc-1.0.0/index.json",
    ):
        assert expected in names
    assert not any(n.startswith("python/tests/gateway/parity/") for n in names)


BITES = {
    "home.py": _j("ROOT = '", "/", "Users", "/someone/repo'\n"),
    "volume.json": _j('{"dir": "', "/", "Volumes", '/disk/x"}\n'),
    "notes.md": _j("see ~/", ".", "futureagi", "-local/notes\n"),
    "critique.txt": _j("finding ", "C", "R B2\n"),
    "inventory.txt": _j("I", "NV-A section 6\n"),
    "decision.txt": _j("per ", "rul", "ing 7\n"),
    "stream-id.py": _j("# as ", "L", "1's comparator does\n"),
    "stream-id2.py": _j("SHARED = ", "L", "1_FILE\n"),
    "stream-word.py": _j("def test_every_delta_this_", "la", "ne_owns():\n"),
    "stream-word2.txt": _j("this ", "la", "ne owns it\n"),
    "checker-note.py": _j('"""The ', "verif", 'ier\'s note."""\n'),
    "signer.json": _j('{"by": "', "verif", 'y agent"}\n'),
    "fix-round.txt": _j("overlay for ", "rou", "nd 3\n"),
    "job-id.json": _j('{"run": "', "j-2000", '0101t0000-abcdef"}\n'),
    "workflow.txt": _j("see ", "wf", "_0123abcd-000\n"),
    "machine.ts": _j("// no latency claim from a S", "pot VM\n"),
    "machine2.md": _j("ran on s", "pot instances\n"),
}
# Synthetic document names for the digest check: what the real ones look like in text.
SAMPLE_NAMES = ("SAMPLE-NOTES", "sample-notes", "SAMPLE", "Demo plan", "demo plan")
SAMPLE_DIGESTS = frozenset(_digest(name) for name in SAMPLE_NAMES)
NAME_BITES = {
    "upper.py": '"""See SAMPLE-NOTES section 3."""\n',
    "snake.py": "from sample_notes import x\n",
    "dotted.txt": "SAMPLE-NOTES.md:171\n",
    "path.txt": "kept in docs/SAMPLE-NOTES/ here\n",
    "single.py": "# as the SAMPLE says (5.1)\n",
    "prose.py": "# (the demo plan 2.2)\n",
    "prose2.py": "# Demo plan, row 4\n",
}
NAME_CLEAN = (
    "SAMPLES = 'SAMPLED'; sample = 1; notes = 2\n"
    "the sample notes, a demo, planned, a plan\n"
    "sample-note and notes-sample and SAMPLER_NOTES\n"
)
CLEAN = (
    "url = 'https://gateway.example.test/v1/users/42'\n"
    "planned = 'PLANNED'  # a plan, the explanation\n"
    "path = 'users/x' and '/volumes/y' and the readiness probe /readyz\n"
    "elapsed = round(1.25, 1)  # verify the model works on the data plane\n"
    "L10 = 'L0'; LLM = 'planes'; laneway = SL1; j-2026 = 'x'; wf = 1\n"
    "a spot check of the cache on a VM, and the hot spot\n"
)


def test_the_scan_bites(tmp_path: Path) -> None:
    for name, text in BITES.items():
        (tmp_path / name).write_text(text, encoding="utf-8")
    (tmp_path / "clean.py").write_text(CLEAN, encoding="utf-8")
    hits = _hits(sorted(tmp_path.iterdir()), tmp_path)
    flagged = {h.split(":", 1)[0] for h in hits}
    assert flagged == set(BITES)
    assert not [h for h in hits if h.startswith("clean.py")]


def test_the_document_name_check_bites(tmp_path: Path) -> None:
    for name, text in NAME_BITES.items():
        (tmp_path / name).write_text(text, encoding="utf-8")
    (tmp_path / "clean.py").write_text(NAME_CLEAN, encoding="utf-8")
    (tmp_path / "test_sample_notes.py").write_text("x = 1\n")
    hits = _hits(sorted(tmp_path.iterdir()), tmp_path, SAMPLE_DIGESTS)
    flagged = {h.split(":", 1)[0] for h in hits}
    assert flagged == set(NAME_BITES) | {"test_sample_notes.py"}
    assert not [h for h in hits if h.startswith("clean.py")]
    # the same files with the real digests: none of the samples is a real name
    assert _hits(sorted(tmp_path.iterdir()), tmp_path) == []


def test_the_digest_list_is_whole() -> None:
    assert len(DOC_NAME_DIGESTS) == 22
    assert all(re.fullmatch(r"[0-9a-f]{16}", d) for d in DOC_NAME_DIGESTS)


def test_the_transport_has_no_hosted_base_url_default() -> None:
    from fi.gateway._transport._async import AsyncBaseClient
    from fi.gateway._transport._base import BaseClient
    from fi.gateway._transport._sync import SyncBaseClient

    for cls in (BaseClient, SyncBaseClient, AsyncBaseClient):
        param = inspect.signature(cls.__init__).parameters["base_url"]
        assert param.default is inspect.Parameter.empty, cls
        assert param.kind is inspect.Parameter.KEYWORD_ONLY
    with pytest.raises(TypeError, match="base_url"):
        SyncBaseClient(api_key="k")  # type: ignore[call-arg]


def test_the_clients_resolve_a_base_url_or_raise(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from fi.gateway import AgentCC, AgentCCError, AsyncAgentCC

    for name in ("FI_GATEWAY_BASE_URL", "FI_GATEWAY_URL", "AGENTCC_BASE_URL"):
        monkeypatch.delenv(name, raising=False)
    for cls in (AgentCC, AsyncAgentCC):
        assert inspect.signature(cls.__init__).parameters["base_url"].default is None
        with pytest.raises(AgentCCError, match="FI_GATEWAY_BASE_URL"):
            cls(api_key="gw-key")
