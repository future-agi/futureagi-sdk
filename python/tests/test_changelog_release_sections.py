"""Check release order, distinguish new behavior from 0.7.1, and keep proxy guidance consistent.

Check the Python release text against the published history and shared generator wording.
"""

from __future__ import annotations

import hashlib
import importlib.util
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CHANGELOG = (ROOT / "python" / "CHANGELOG.md").read_text(encoding="utf-8")

RELEASED_0_7_1_NOTES = (
    (
        "A request that carries `X-Api-Key` and `X-Secret-Key` is sent with redirects off, in `HttpClient` "
        "(and every client built on it) and in the `fi.kb` file uploads. A 3xx answer raises "
        "`KeyedRedirectRefusedError` (code `KEYED_REDIRECT_REFUSED`) and the redirect target is not contacted."
    ),
    (
        "`HttpClient` raises `KeyedProxyRefusedError` (code `KEYED_PROXY_REFUSED`) before sending when a "
        "caller-supplied session would route a key-carrying request through a proxy: a proxy set on the session, "
        "an adapter other than requests' own `HTTPAdapter`, or a proxy from `HTTP_PROXY`, `http_proxy` or `ALL_PROXY` "
        "that a session with `trust_env` on picks up and `NO_PROXY` does not bypass."
    ),
    (
        "A session the SDK builds sends direct: `trust_env=False` and `proxies={}`, so it reads no proxy variable, "
        "`.netrc` or `REQUESTS_CA_BUNDLE`. The `fi.kb` uploads use such a session."
    ),
)


def _sections() -> dict[str, str]:
    parts = re.split(r"(?m)^(?=## )", CHANGELOG)
    return {part.splitlines()[0]: part for part in parts if part.startswith("## ")}


def _bullets(section: str) -> list[str]:
    """The bullets of a section, each with its continuation lines."""
    found: list[str] = []
    for line in section.splitlines():
        if line.startswith("- "):
            found.append(line)
        elif found and line.startswith("  ") and line.strip():
            found[-1] += " " + line.strip()
    return found


def test_the_sections_run_from_0_9_0_through_0_8_1_and_0_8_0_to_0_7_0():
    headings = [line for line in CHANGELOG.splitlines() if line.startswith("## ")]
    if headings and headings[0].startswith("## [0.9.0]("):
        headings = headings[1:]
    assert len(headings) == 5, headings
    assert headings[0] == "## 0.9.0"
    assert headings[1].startswith("## [0.8.1](")
    assert headings[2] == "## 0.8.1"
    assert headings[3].startswith("## [0.8.0](")
    assert headings[3].endswith(" (2026-11-21)")
    assert headings[4].startswith("## [0.7.0](")


def test_the_0_9_0_notes_do_not_republish_the_0_7_1_entries():
    section = " ".join(_sections()["## 0.9.0"].split())
    for note in RELEASED_0_7_1_NOTES:
        assert note not in section, note


def test_no_0_9_0_breaking_entry_announces_the_0_7_1_notes():
    bullets = _bullets(_sections()["## 0.9.0"])
    for bullet in bullets:
        if bullet.startswith("- Breaking:"):
            assert "fi.api.auth.HttpClient" not in bullet, bullet[:160]
            assert "file-upload calls that use `requests` directly" not in bullet, (
                bullet[:160]
            )
    # The caller-session entry distinguishes the 0.7.1 rule from its broader scope in 0.9.0.
    entry = next(
        b for b in bullets if b.startswith("- Breaking:") and "`FuturesSession`" in b
    )
    assert "0.7.1 shipped `KeyedProxyRefusedError`" in entry
    assert "0.8.1 also checks adapters" in entry
    assert "checks the sending `requests` session's proxy route and adapter" in entry


def test_the_all_proxy_entries_agree_on_which_requests_it_refuses():
    section = _sections()["## 0.9.0"]
    bullets = _bullets(section)
    entry = next(
        b
        for b in bullets
        if "`ALL_PROXY` set to a non-empty value routes an `http://` request" in b
    )
    assert "you pass in" in entry, (
        entry
    )  # a client or session the caller supplies; the SDK's own send goes direct
    direct = next(
        b for b in bullets if "read no `HTTP_PROXY`, `HTTPS_PROXY` or `ALL_PROXY`" in b
    )
    assert "the SDK sends itself" in direct


def test_the_whole_release_text_has_no_new_findings():
    spec = importlib.util.spec_from_file_location(
        "check_sdk_public_text", ROOT / "scripts" / "check_sdk_public_text.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    inherited = Counter(
        {
            # The published 0.7.0 changelog entry predates this release.
            (
                "python/CHANGELOG.md",
                "727d51a79ed6ae44adcc71621a8d11f4e7bd8dd7b9182aa67719c773f153ccca",
            ): 1,
            # The sync and async docstrings share the catalog wording with the published npm package.
            (
                "python/fi/platform/resources/base.py",
                "00b46f1f02a38aa27a365601f38365c2c62056aedbb9e9b1f0153694b6b182a4",
            ): 2,
        }
    )
    findings = Counter()
    for hit in module.whole_release(ROOT):
        if hit.startswith(("python/", "NOTICE")):
            path, _, detail = hit.split(":", 2)
            findings[path, hashlib.sha256(detail.strip().encode()).hexdigest()] += 1
    assert not findings - inherited
