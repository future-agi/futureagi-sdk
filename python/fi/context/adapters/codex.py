"""Project-scoped Codex materialization; native discovery remains unqualified.

No host process, hooks, settings, package scripts or model calls are executed.
Only explicitly managed instruction outputs and native skill files are written.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal
from urllib.parse import quote, unquote, urlsplit

from ..lock import InstallationError, collision_key, validate_path

PROFILE_VERSION = "1"


@dataclass(frozen=True)
class Profile:
    id: Literal["codex", "claude-code"]
    skills_directory: str
    import_file: str | None
    version: str = PROFILE_VERSION
    qualification: str = "preview"


PROFILE = Profile("codex", ".agents/skills", None)


def managed_block(context_id: str, body: bytes) -> bytes:
    return (
        f"<!-- futureagi:context:{context_id}:begin -->\n".encode()
        + body
        + (b"" if body.endswith(b"\n") else b"\n")
        + f"<!-- futureagi:context:{context_id}:end -->\n".encode()
    )


def split_managed(content: bytes, context_id: str) -> tuple[bytes, bytes, bytes]:
    begin = f"<!-- futureagi:context:{context_id}:begin -->\n".encode()
    end = f"<!-- futureagi:context:{context_id}:end -->\n".encode()
    if (
        content.count(begin) != 1
        or content.count(end) != 1
        or content.count(b"<!-- futureagi:context:") != 2
    ):
        raise InstallationError(
            "local_modifications",
            "Managed instruction boundaries are missing, duplicated, or edited.",
        )
    start = content.index(begin)
    stop = content.index(end) + len(end)
    if stop <= start:
        raise InstallationError(
            "local_modifications", "Managed instruction boundaries are out of order."
        )
    return content[:start], content[start:stop], content[stop:]


def preserve_local(
    content: bytes | None, block: bytes, *, adopt: bool
) -> tuple[bytes, bytes, bool]:
    if content is None:
        return block, b"", False
    if b"<!-- futureagi:context:" in content:
        raise InstallationError(
            "unmanaged_collision",
            "Preexisting managed-looking instructions require their original ownership lock.",
        )
    if not adopt:
        raise InstallationError(
            "unmanaged_collision",
            "Existing project instructions require an explicit local-segment adoption plan.",
        )
    # Put the managed block first, preserving every preexisting local byte exactly.
    return block + content, content, True


def check_supporting_path(path: str) -> None:
    """Reject imported host-control names even when those names do not yet exist."""
    validate_path(path, source=True)
    parts = [collision_key(part) for part in path.split("/")]
    forbidden = {
        ".git",
        ".github",
        ".claude",
        ".codex",
        ".cursor",
        ".gemini",
        ".vscode",
        ".agents",
        ".mcp.json",
        "node_modules",
    }
    names = {
        "agents.md",
        "agents.override.md",
        "claude.md",
        "claude.local.md",
        "gemini.md",
        "package.json",
        "pyproject.toml",
        "setup.py",
        "setup.cfg",
        "makefile",
        "dockerfile",
        "compose.yml",
        "docker-compose.yml",
        ".env",
        ".gitmodules",
    }
    if any(part in forbidden or part in names for part in parts):
        raise InstallationError(
            "destination_forbidden",
            "Supporting content includes a host-control or alternate instruction path.",
            7,
        )


def check_skill_frontmatter(raw: bytes) -> None:
    """Conservative portable subset; unknown YAML/control semantics fail closed.

    This is not a general YAML rewriter. Quoted keys, aliases, tags, merge keys,
    flow mappings and host extensions need separate qualification, not a guess.
    """
    text = raw.decode("utf-8")
    lines = text.splitlines()
    if not lines or lines[0] != "---" or "---" not in lines[1:]:
        raise InstallationError(
            "runtime_incompatible", "A skill lacks portable frontmatter.", 7
        )
    header = lines[1 : lines[1:].index("---") + 1]
    if len("\n".join(header).encode()) > 16384:
        raise InstallationError(
            "runtime_incompatible", "Skill frontmatter exceeds its limit.", 7
        )
    allowed = {"name", "description", "license", "compatibility", "metadata"}
    seen: set[str] = set()
    for line in header:
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if "\t" in line or re.search(r"(^|\s)[&*!]|<<\s*:", line):
            raise InstallationError(
                "runtime_incompatible",
                "Advanced YAML/control semantics are not qualified for installation.",
                7,
            )
        if line.startswith(" "):
            continue
        match = re.fullmatch(r"([a-z][a-z-]*):(?:\s.*)?", line)
        if match is None or match[1] not in allowed or match[1] in seen:
            raise InstallationError(
                "runtime_incompatible",
                "Host extensions or nonportable frontmatter require manual integration.",
                7,
            )
        seen.add(match[1])
    if not {"name", "description"}.issubset(seen):
        raise InstallationError(
            "runtime_incompatible", "Skill name and description are required.", 7
        )


def project_entrypoint(
    raw: bytes, source_paths: set[str], generation: str, skills_directory: str
) -> bytes:
    """Rewrite only simple inline Markdown links with known snapshot targets.

    Code, prose and JSON paths are never guessed. Ambiguous Markdown and literal
    relative-file references needing relocation fail with a manual-integration
    diagnostic rather than a verified-installation claim.
    """
    text = raw.decode("utf-8")
    if b"<!-- futureagi:context:" in raw:
        raise InstallationError(
            "runtime_incompatible",
            "Source instructions contain reserved ownership markers.",
            7,
        )
    result: list[str] = []
    fence: str | None = None
    for line in text.splitlines(keepends=True):
        stripped = line.lstrip()
        if stripped.startswith(("```", "~~~")):
            marker = stripped[:3]
            fence = None if fence == marker else marker if fence is None else fence
            result.append(line)
            continue
        if fence is not None:
            # Relocating a literal path in executable examples would change semantics.
            if any(path != "AGENTS.md" and path in line for path in source_paths):
                raise InstallationError(
                    "runtime_incompatible",
                    "A fenced example references relocated files; review manual integration.",
                    7,
                )
            result.append(line)
            continue
        if re.search(r"^\s*\[[^\]]+\]:", line) or "<a " in line or "<img " in line:
            raise InstallationError(
                "runtime_incompatible",
                "Reference/HTML links are not qualified for relocation.",
                7,
            )
        pieces = re.split(r"(`+[^`]*`+)", line)
        for index, piece in enumerate(pieces):
            if piece.startswith("`"):
                literal = piece.strip("`")
                if literal in source_paths and literal != "AGENTS.md":
                    raise InstallationError(
                        "runtime_incompatible",
                        "A code path requires manual relocation.",
                        7,
                    )
                continue

            def rewrite(match: re.Match[str]) -> str:
                target = match[2]
                parsed = urlsplit(target)
                if parsed.scheme or parsed.netloc or target.startswith("#"):
                    return match[0]
                path = unquote(parsed.path)
                if path.startswith("./"):
                    path = path[2:]
                validate_path(path, source=True)
                if path not in source_paths or parsed.query:
                    raise InstallationError(
                        "runtime_incompatible",
                        "A relative instruction link has no unambiguous snapshot target.",
                        7,
                    )
                destination = (
                    skills_directory + "/" + path[len("skills/") :]
                    if path.startswith("skills/")
                    else generation + "/" + path
                )
                destination = quote(destination, safe="/")
                if parsed.fragment:
                    destination += "#" + parsed.fragment
                return f"{match[1]}({destination})"

            # Titles, whitespace and nested parentheses are deliberately unsupported.
            simple = re.compile(r"(!?\[[^\]\n]*\])\(([^\s()]+)\)")
            if re.search(r"\]\(", simple.sub("", piece)):
                raise InstallationError(
                    "runtime_incompatible",
                    "Complex Markdown links require manual integration.",
                    7,
                )
            pieces[index] = simple.sub(rewrite, piece)
        result.append("".join(pieces))
    return "".join(result).encode("utf-8")
