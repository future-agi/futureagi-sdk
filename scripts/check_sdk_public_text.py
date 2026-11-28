#!/usr/bin/env python3
"""Fail on wording the public text of the Python and TypeScript SDKs must not carry.

The rule: every changelog line, README line, shipped docstring and user-visible error message added since a base
commit describes current SDK behaviour and names the setting a user changes.
This script reads `git diff -U0 BASE HEAD`, takes the added lines of

  - the CHANGELOG.md and README.md files of both SDKs,
  - the docstrings, comments and `raise` messages of python/fi/** (the wheel), and
  - the comments and thrown messages of the TypeScript sources (typescript/futureagi/src),

and exits 1 when one of them contains a flagged word, or when an added changelog bullet in the corrections section
mentions an endpoint, proxy, key, redirect or host (those entries belong under "Changed").

    python3 scripts/check_sdk_public_text.py --base b08995afd [--head HEAD]
    python3 scripts/check_sdk_public_text.py --whole-release

Test files are not scanned. `--self-test` runs the scanner on built-in samples and exits 0 when it behaves.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import io
import json
import re
import subprocess
import sys
import tokenize
import warnings
from pathlib import Path

WORDS = (
    r"\bevil\b", r"\battack\w*", r"\bleak\w*", r"forward your keys", r"\bcleartext\b", r"looks? like", r"\bfixed\b", r"\bnow\b",
    r"\bpreviously\b", r"\bvulnerab\w*", r"\bexploit\w*", r"\bnever\b", r"\bjust\b", r"clear[ _]text", r"\bresembles\b",
    r"\bno longer\b", r"\bused to\b", r"\bformerly\b", r"\bstill\b",
)
FLAGGED = re.compile("|".join(WORDS), re.IGNORECASE)
FIXED_TOPICS = re.compile(r"\b(endpoint|proxy|keys?|redirect\w*|hosts?)\b", re.IGNORECASE)

CHANGELOGS = ("python/CHANGELOG.md", "typescript/futureagi/CHANGELOG.md")
READMES = ("python/README.md", "typescript/futureagi/README.md")
README_ROOTS = ("python", "typescript/futureagi")
# Text of the Python distribution that is read as a whole, every section of it: the changelog's shipped sections and the
# files that travel in the wheel and the sdist next to the code.
WHOLE_CHANGELOGS = ("python/CHANGELOG.md",)
WHOLE_TEXT_FILES = ("NOTICE", "python/NOTICE", "python/fi/gateway/VENDORED.md")
TS_ROOTS = ("typescript/futureagi/src/",)


MESSAGE_CALLS = frozenset({"warn", "warning", "error", "info", "debug", "critical", "exception", "print", "write"})
# A call that builds an exception or a warning carries a user-visible message, raised where it is built or somewhere else.
EXCEPTION_SUFFIXES = ("Error", "Exception", "Refused", "Warning", "Exit")


def run(*args: str) -> str:
    return subprocess.run(args, check=True, capture_output=True, text=True).stdout


def added_lines(base: str, head: str) -> dict[str, set[int]]:
    """Path -> line numbers (in the head version) the diff adds."""
    found: dict[str, set[int]] = {}
    path = None
    for line in run("git", "diff", "-U0", "--no-color", base, head).splitlines():
        if line.startswith("+++ "):
            path = line[6:] if line.startswith("+++ b/") else None
            continue
        match = re.match(r"@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@", line)
        if match and path is not None:
            start, count = int(match.group(1)), int(match.group(2) or "1")
            found.setdefault(path, set()).update(range(start, start + count))
    return found


def is_test(path: str) -> bool:
    parts = path.split("/")
    return "tests" in parts or "__tests__" in parts or parts[-1].startswith("test_") or ".test." in parts[-1] or "fixtures" in parts


def python_text_lines(source: str, whole: bool = False, comments: bool = True) -> dict[int, str]:
    """Line number -> text for the comments, docstrings and `raise` message strings of a Python file.

    With `whole`, the string arguments of warn, log and print calls count as messages too, and so do the string arguments
    of a call that builds an exception or a warning (a class whose name ends in Error, Exception, Refused, Warning or Exit),
    wherever it is raised."""
    found: dict[int, str] = {}
    lines = source.splitlines()
    try:
        for token in tokenize.generate_tokens(io.StringIO(source).readline):
            if token.type == tokenize.COMMENT and comments:
                found[token.start[0]] = token.string
    except (tokenize.TokenError, IndentationError):
        pass
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            tree = ast.parse(source)
    except SyntaxError:
        return found
    spans: list[tuple[int, int]] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            body = node.body
            if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) and isinstance(body[0].value.value, str):
                spans.append((body[0].lineno, body[0].end_lineno or body[0].lineno))
        message_call = isinstance(node, ast.Call) and (
            (isinstance(node.func, ast.Attribute) and node.func.attr in MESSAGE_CALLS)
            or (isinstance(node.func, ast.Name) and node.func.id in MESSAGE_CALLS)
        )
        builds_exception = isinstance(node, ast.Call) and (
            (isinstance(node.func, ast.Attribute) and node.func.attr.endswith(EXCEPTION_SUFFIXES))
            or (isinstance(node.func, ast.Name) and node.func.id.endswith(EXCEPTION_SUFFIXES))
        )
        if (isinstance(node, ast.Raise) and node.exc is not None) or ((message_call or builds_exception) and whole):
            for inner in ast.walk(node.exc if isinstance(node, ast.Raise) else node):
                if isinstance(inner, ast.Constant) and isinstance(inner.value, str):
                    spans.append((inner.lineno, inner.end_lineno or inner.lineno))
    for start, end in spans:
        for number in range(start, end + 1):
            if 1 <= number <= len(lines):
                found[number] = lines[number - 1]
    return found


def typescript_text_lines(source: str, comments: bool = True) -> dict[int, str]:
    """Line number -> text for the comment lines and thrown/message lines of a TypeScript file."""
    found: dict[int, str] = {}
    in_block = False
    for number, line in enumerate(source.splitlines(), 1):
        stripped = line.strip()
        if not comments and (stripped.startswith("//") or (not in_block and not stripped.startswith("/**") and stripped.startswith("/*"))):
            continue
        if in_block:
            found[number] = line
            if "*/" in stripped:
                in_block = False
            continue
        if stripped.startswith("/*"):
            found[number] = line
            in_block = "*/" not in stripped
        elif stripped.startswith("//") or stripped.startswith("*"):
            found[number] = line
        elif re.search(r"\bthrow\b|Error\(|\bmessage\b|\bwarn\w*\(|stderr\.write|emitWarning|\bnotice\b", stripped):
            found[number] = line
    return found


# Modules whose subject is detecting security problems: the words that name what they detect are their vocabulary.
DOMAIN_PATHS = ("python/fi/evals/metrics/code_security/", "python/fi/evals/guardrails/")
DOMAIN_WORDS = re.compile(r"\b(attack\w*|vulnerab\w*|exploit\w*|leak\w*)", re.IGNORECASE)


# Literal text a flagged word belongs to and that cannot be reworded: sample jailbreak prompts and the name of the DAN
# prompt family that the scanners detect, the Kubernetes policy that disallows image pulls, the `is_fixed` attribute name, and the
# operation names `sync_now` and the scheduled-task run that the generated clients take from the platform contract.
LITERALS = ("workspace task now", "sync now using", "do anything now", "You are now ", "just make it work", "value Never", "is_fixed")


def exempt(path: str, line: str, word: str) -> bool:
    """True for a flagged word that is scanner vocabulary of a security module or part of a literal that stays as written."""
    if path.startswith(DOMAIN_PATHS) and DOMAIN_WORDS.fullmatch(word):
        return True
    if "/__fixtures__/" in path:
        return True  # test support files are not shipped
    if path.endswith(".ts") and re.search(r"(:|<)\s*never\b|\bnever>|Date\.now", line):
        return True  # the TypeScript bottom type and the clock call are code, not wording
    return any(lit.lower() in line.lower() for lit in LITERALS)


def findings(base: str, head: str) -> list[str]:
    out: list[str] = []
    for path, numbers in sorted(added_lines(base, head).items()):
        if is_test(path):
            continue
        if path in CHANGELOGS or path in READMES:
            source = run("git", "show", f"{head}:{path}")
            heading = ""
            for number, line in enumerate(source.splitlines(), 1):
                if line.startswith("#"):
                    heading = line
                if number not in numbers:
                    continue
                for hit in FLAGGED.finditer(line):
                    out.append(f"{path}:{number}: '{hit.group(0)}' in an added line: {line.strip()[:120]}")
                if path in CHANGELOGS and re.search(r"fixed", heading, re.IGNORECASE) and line.lstrip().startswith("- ") and FIXED_TOPICS.search(line):
                    out.append(f"{path}:{number}: a bullet under a Fixed heading ({heading.strip()}) mentions {FIXED_TOPICS.search(line).group(0)!r}; list it under Changed")
            continue
        if path.startswith("python/fi/") and path.endswith(".py"):
            text = python_text_lines(run("git", "show", f"{head}:{path}"))
        elif path.startswith(TS_ROOTS) and path.endswith((".ts", ".tsx")):
            text = typescript_text_lines(run("git", "show", f"{head}:{path}"))
        else:
            continue
        for number in sorted(numbers):
            line = text.get(number)
            if line is None:
                continue
            for hit in FLAGGED.finditer(line):
                if exempt(path, line, hit.group(0)):
                    continue
                out.append(f"{path}:{number}: '{hit.group(0)}' in an added docstring, comment or message: {line.strip()[:120]}")
    return out


def release_section(source: str) -> tuple[int, list[str]]:
    """The first release section of a changelog: (1-based line of its heading, its lines)."""
    lines = source.splitlines()
    starts = [i for i, line in enumerate(lines) if line.startswith("## ")]
    if not starts:
        return 1, []
    end = next((i for i in starts if i > starts[0]), len(lines))
    return starts[0] + 1, lines[starts[0]:end]


def scan_lines(path: str, text: dict[int, str], what: str) -> list[str]:
    return [
        f"{path}:{number}: '{hit.group(0)}' in {what}: {line.strip()[:120]}"
        for number, line in sorted(text.items())
        for hit in FLAGGED.finditer(line)
        if not exempt(path, line, hit.group(0))
    ]


def whole_release(root: Path) -> list[str]:
    """Findings over the whole current release text under `root` (the repository root)."""
    out: list[str] = []
    for rel in CHANGELOGS:
        path = root / rel
        if path.is_file():
            first, section = release_section(path.read_text(encoding="utf-8"))
            out += scan_lines(rel, {first + i: line for i, line in enumerate(section)}, "the current release section")
            heading = ""
            for i, line in enumerate(section):
                if line.startswith("#"):
                    heading = line
                if re.search(r"fixed", heading, re.IGNORECASE) and line.lstrip().startswith("- ") and FIXED_TOPICS.search(line):
                    out.append(f"{rel}:{first + i}: a bullet under a Fixed heading ({heading.strip()}) mentions {FIXED_TOPICS.search(line).group(0)!r}; list it under Changed")
    for rel in WHOLE_CHANGELOGS:
        path = root / rel
        if path.is_file():
            lines = path.read_text(encoding="utf-8").splitlines()
            first, section = release_section("\n".join(lines))
            out += scan_lines(rel, {number: line for number, line in enumerate(lines, 1) if number >= first + len(section)},
                              "a shipped release section")
    for rel in WHOLE_TEXT_FILES:
        path = root / rel
        if path.is_file():
            out += scan_lines(rel, dict(enumerate(path.read_text(encoding="utf-8").splitlines(), 1)), "a text file of the distribution")
    skip = {"node_modules", ".venv", "dist", "build", "tests", "test", "__tests__", "fixtures", "examples", "consumer"}
    readmes: set[Path] = set()
    for rel in README_ROOTS:
        base = root / rel
        if base.is_dir():
            readmes.update(p for p in (base.glob("README*.md") if rel != "python" else base.rglob("README*.md")) if not skip & set(p.relative_to(base).parts[:-1]))
    for path in sorted(readmes):
        out += scan_lines(str(path.relative_to(root)), dict(enumerate(path.read_text(encoding="utf-8").splitlines(), 1)), "a README line")
    manifest = root / "python" / "tests" / "evals" / "fixtures" / "upstream-ai-evaluation-1.1.0.json"
    upstream = json.loads(manifest.read_text()).get("files", {}) if manifest.is_file() else {}
    for path in sorted((root / "python" / "fi").rglob("*.py")):
        if "generated" in path.parts:
            continue
        rel = str(path.relative_to(root))
        if upstream.get(rel[len("python/"):]) == hashlib.sha256(path.read_bytes()).hexdigest():
            continue  # ported ai-evaluation 1.1.0 text, kept byte-identical to the published wheel
        out += scan_lines(rel, python_text_lines(path.read_text(encoding="utf-8"), whole=True), "a docstring, comment or message")
    for ts_root in TS_ROOTS:
        for path in sorted((root / ts_root).rglob("*")) if (root / ts_root).is_dir() else []:
            if path.suffix in (".ts", ".tsx") and "generated" not in path.parts and not is_test(str(path.relative_to(root))) and "node_modules" not in path.parts:
                out += scan_lines(str(path.relative_to(root)), typescript_text_lines(path.read_text(encoding="utf-8"), comments=False), "a docstring or message")
    return out


PLANTED = (
    "evil", "attacker", "attack", "leak", "forward your keys", "cleartext", "clear text", "clear_text", "look like", "looks like",
    "resembles", "fixed", "now", "previously", "vulnerable", "exploit", "never", "just", "no longer", "used to", "formerly", "still",
)


def self_test() -> int:
    clean = ["The gateway answered with a redirect. Set the base URL to the final address.", "Requests to localhost go direct.", "Set FI_ALLOW_INSECURE_HTTP=1."]
    missed = [word for word in PLANTED if not FLAGGED.search(f"The client sends a {word} request.")]
    ok = not missed and not any(FLAGGED.search(text) for text in clean)
    every = [hit.group(0) for hit in FLAGGED.finditer("never just clear text clear_text resembles")]
    ok = ok and len(every) == 5
    doc = 'def f():\n    """Sends a call.\n\n    It was fixed.\n    """\n    value = "fixed in code"  # a comment now\n    raise ValueError("this is evil")\n'
    lines = python_text_lines(doc)
    ok = ok and {2, 4, 6, 7} <= set(lines) and 1 not in lines
    ts = "const x = 'now';\n// a leak\nthrow new Error('attack');\n/**\n * cleartext\n */\nconsole.warn('never');\nprocess.stderr.write('just');\n"
    tl = typescript_text_lines(ts)
    ok = ok and 1 not in tl and {2, 3, 4, 5, 6, 7, 8} <= set(tl)
    whole_doc = 'import warnings\nwarnings.warn("this is now off")\nlog.error("never again")\nprint("clean")\n'
    ok = ok and {2, 3} <= set(python_text_lines(whole_doc, whole=True)) and not {2, 3} & set(python_text_lines(whole_doc))
    ok = ok and release_section("# C\n\n## [2] - x\n- a\n## [1]\n- b\n") == (3, ["## [2] - x", "- a"])
    if missed:
        print("self-test missed: " + ", ".join(missed))
    print("self-test " + ("ok" if ok else "FAILED") + f" ({len(PLANTED)} words planted)")
    return 0 if ok else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--base", help="the commit the added lines are counted from")
    parser.add_argument("--head", default="HEAD")
    parser.add_argument("--whole-release", action="store_true", help="scan the whole current release text instead of a diff")
    parser.add_argument("--root", default=str(Path(__file__).resolve().parents[1]), help="repository root for --whole-release")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        return self_test()
    if args.whole_release:
        found = whole_release(Path(args.root))
        for line in found:
            print(line)
        print(f"public-text check: {len(found)} finding(s) in the whole current release text")
        return 1 if found else 0
    if not args.base:
        parser.error("--base is required")
    found = findings(args.base, args.head)
    for line in found:
        print(line)
    print(f"public-text check: {len(found)} finding(s) in the lines added since {args.base}")
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
