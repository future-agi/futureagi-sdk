"""The 0.9.0 changelog describes the traces-to-Future-AGI behaviour in plain product language.

The notes sit under a Changed heading and name the settings and error codes a user needs.
"""

import pathlib
import re

import pytest

CHANGELOG = pathlib.Path(__file__).resolve().parents[3] / "CHANGELOG.md"
HEADING = "### Changed: traces to Future AGI"
BANNED = [
    r"evil", r"attacker", r"attack", r"\bleak", r"forward your keys", r"cleartext", r"look like",
    r"\bfixed\b", r"\bnow\b", r"previously", r"vulnerab", r"exploit", r"\bnever\b", r"\bjust\b", r"clear_?text", r"resembles", r"no longer",
]
REQUIRED = [
    "unsupported_otlp_exporter", "insecure_http_origin", "INSECURE_HTTP_REFUSED", "unreadable_tls_file",
    ">=1.39.1,<1.46", "HTTP_PROXY", "HTTPS_PROXY", "NO_PROXY", "TLS", "white space",
    "FI_ALLOW_INSECURE_HTTP",
]


def release_section():
    text = CHANGELOG.read_text(encoding="utf-8")
    start = text.index("\n## 0.9.0\n") + 1
    end = text.find("\n## ", start + 1)
    return text[start:end if end != -1 else None]


def section(title_prefix):
    body = release_section()
    lines = body.split("\n")
    out, inside = [], False
    for line in lines:
        if line.startswith("### "):
            inside = line.startswith(title_prefix)
            continue
        if inside:
            out.append(line)
    return "\n".join(out)


def test_the_traces_notes_are_under_a_changed_heading():
    assert HEADING in release_section()
    assert "### Fixed: traces to Future AGI" not in release_section()


@pytest.mark.parametrize("pattern", BANNED)
def test_the_traces_notes_hold_no_banned_word(pattern):
    found = re.findall(pattern, section(HEADING), flags=re.IGNORECASE)
    assert found == []


@pytest.mark.parametrize("needed", REQUIRED)
def test_the_traces_notes_keep_what_a_user_needs(needed):
    assert needed in section(HEADING)


def bullets():
    return [item for item in re.split(r"\n(?=- )", section(HEADING)) if item.startswith("- ")]


@pytest.mark.parametrize("code", ["KeyedProxyRefusedError", "otel_env_key_headers"])
def test_a_break_names_its_error_code_inside_its_breaking_clause(code):
    clauses = [item.split("Breaking:", 1)[1] for item in bullets() if "Breaking:" in item]
    assert any(f"`{code}`" in clause for clause in clauses)


def test_every_break_gives_the_action_to_take():
    for item in bullets():
        for clause in item.split("Breaking:")[1:]:
            text = " ".join(clause.split())
            assert re.search(r"\b(use|remove|set|write|put|point|let|unset|pass|send)\b", text, re.IGNORECASE), text[:80]
