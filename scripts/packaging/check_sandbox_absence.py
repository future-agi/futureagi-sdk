"""Fail closed when candidate archives contain an unavailable sandbox surface.

Accepts the in-memory archive maps used by check_artifacts.py. Shared error
classes are retained: they are not sandbox clients or callable operations.
"""
from __future__ import annotations

import json
from pathlib import PurePosixPath
import re
from typing import Mapping


_DOCUMENT_SUFFIXES = {".md", ".markdown", ".mdx", ".rst", ".txt", ".html", ".htm", ".adoc"}
_DOCUMENT_NAMES = {"readme", "metadata", "pkg-info"}
# Standalone names cover CLI command lists and reference headings as well as
# qualified imports/accessors, without rejecting shared SandboxStateError names.
_SANDBOX_REFERENCE = re.compile(rb"\bsandbox(?:es)?\b", re.IGNORECASE)


def check_sandbox_absence(wheel: Mapping[str, bytes], source: Mapping[str, bytes], npm: Mapping[str, bytes]) -> None:
    """Require physical absence, including generated calls and declarations."""
    for label, archive in (("wheel", wheel), ("sdist", source), ("npm", npm)):
        for path, content in archive.items():
            member = PurePosixPath(path)
            parts = member.parts
            if member.suffix.lower() in _DOCUMENT_SUFFIXES or member.name.lower() in _DOCUMENT_NAMES:
                assert not _SANDBOX_REFERENCE.search(content), f"{label}: sandbox registration or documentation {path}"
            runtime = "fi" in parts or "dist" in parts
            if runtime:
                assert b"fi.sandboxes" not in content, f"{label}: sandbox import reference {path}"
                assert "sandboxes" not in parts, f"{label}: sandbox module {path}"
                assert PurePosixPath(path).name.split(".", 1)[0] != "sandboxes", f"{label}: sandbox module {path}"
                if "platform" in parts and "generated" in parts:
                    assert b"sandboxes." not in content, f"{label}: sandbox operation {path}"
                    assert b"WorkspaceSandbox" not in content, f"{label}: sandbox declaration {path}"
                if PurePosixPath(path).name.startswith(("futureagi_client.", "futureagi_async_client.", "futureagi-client.")):
                    assert b"sandboxes" not in content, f"{label}: sandbox accessor {path}"
    package = json.loads(npm["package/package.json"])
    assert not any("sandbox" in name.lower() for name in package.get("exports", {})), "sandbox export"
    for mapping in package.get("typesVersions", {}).values():
        assert not any("sandbox" in name.lower() for name in mapping), "sandbox typesVersions"
