"""Docstrings and refusal messages in the modules of the plain-transport rule use plain product wording.

The scan covers every docstring of these modules, the constants and variables that hold a message or a notice, the
text of every ``ConfigurationError``, ``HostNotAllowedError`` or redirect error they raise, and the text of every
warning they emit (``warnings.warn``, ``sys.stderr.write`` and the ``warning``/``error`` calls of a logger). The
scan checks that this text describes SDK behavior in plain product wording.
"""

import ast
import pathlib
import re

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[3]
MODULES = [
    "fi/_otlp_headers.py",
    "fi/api/auth.py",
    "fi/evals/otel/_tracer_factories.py",
    "fi/experiments/_tracing/export_status.py",
    "fi/experiments/_tracing/export.py",
    "fi/_core/http_security.py",
    "fi/kb/client.py",
]
BANNED = [
    r"evil", r"attacker", r"attack", r"\bleak", r"forward your keys", r"cleartext", r"clear text", r"clear_?text",
    r"look like", r"resembles", r"\bfixed\b", r"\bnow\b", r"previously", r"vulnerab", r"exploit", r"\bnever\b",
    r"\bjust\b", r"no longer",
]
WARNERS = {"warn", "write", "warning", "error"}
RAISERS = {"ConfigurationError", "HostNotAllowedError", "RequestException", "RedirectNotFollowed"}


def strings(node):
    return [n.value for n in ast.walk(node) if isinstance(n, ast.Constant) and isinstance(n.value, str)]


def public_text(path):
    tree = ast.parse((ROOT / path).read_text(encoding="utf-8"))
    found = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            doc = ast.get_docstring(node, clean=False)
            if doc:
                found.append(("docstring", doc))
        if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name):
            name = node.targets[0].id
            if re.search(r"MESSAGE|REFUSAL|NOTICE", name, flags=re.IGNORECASE):
                found.extend((name, text) for text in strings(node.value))
        if isinstance(node, ast.Call):
            func = node.func
            called = func.id if isinstance(func, ast.Name) else func.attr if isinstance(func, ast.Attribute) else ""
            if called in RAISERS or (isinstance(func, ast.Call) and getattr(func.func, "id", "") in RAISERS):
                found.extend(("message", text) for arg in node.args[:1] for text in strings(arg))
            elif called in WARNERS and node.args:
                found.extend(("warning", text) for text in strings(node.args[0]))
    return found


@pytest.mark.parametrize("path", MODULES)
@pytest.mark.parametrize("pattern", BANNED)
def test_the_public_text_holds_no_banned_word(path, pattern):
    hits = [(kind, match.group(0)) for kind, text in public_text(path)
            for match in re.finditer(pattern, text, flags=re.IGNORECASE)]
    assert hits == []


def test_the_scan_reads_the_stderr_notice_and_the_log_warnings():
    kinds = {kind for kind, _text in public_text("fi/_core/http_security.py")}
    assert "warning" in kinds
    assert any(kind == "warning" and "plain" in text for kind, text in public_text("fi/_otlp_headers.py"))
