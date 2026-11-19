"""Bounded, filesystem-only inputs to the namespace repair safety gate."""
from __future__ import annotations

from importlib.util import cache_from_source
from itertools import islice
from pathlib import Path
import stat
from typing import Any


MAX_SCAN_ENTRIES = 20_000
MAX_SCAN_DEPTH = 64


def lexical_records(owner: dict[str, Any]) -> dict[str, Path]:
    """Never resolve a final symlink before deriving pip's removal paths."""
    if not callable(owner["locate"]):
        raise ValueError("RECORD locations cannot be established")
    if len(owner["rows"]) > MAX_SCAN_ENTRIES:
        raise ValueError("RECORD entry limit exceeded")
    return {row[0]: Path(owner["locate"](row[0])).absolute() for row in owner["rows"]
            if len(row) == 3 and row[0]}


class SimpleState:
    """One bounded audit shared by all candidates at the command-selection gate.

    No links are followed. Missing declared roots or removal files are allowed;
    errors while enumerating an existing namespace, special files, and exhausted
    budgets fail closed. Payload contents are never opened by this audit.
    """

    def __init__(self) -> None:
        self.remaining = MAX_SCAN_ENTRIES
        self.checked: dict[Path, Any] = {}

    def spend(self) -> None:
        self.remaining -= 1
        if self.remaining < 0:
            raise ValueError("namespace/RECORD scan entry limit exceeded")

    def mode(self, path: Path) -> int | None:
        if path not in self.checked:
            self.spend()
            try:
                self.checked[path] = path.lstat().st_mode
            except FileNotFoundError:
                self.checked[path] = None
        mode = self.checked[path]
        if mode is not None and stat.S_ISLNK(mode):
            raise ValueError(f"symlink at {path}")
        return mode

    def no_links(self, path: Path) -> int | None:
        path = path.absolute()
        if ".." in path.parts:
            raise ValueError(f"nonlexical RECORD location {path}")
        chain = [*reversed(path.parents), path]
        for index, component in enumerate(chain):
            mode = self.mode(component)
            if mode is None:
                return None
            if index < len(chain) - 1 and not stat.S_ISDIR(mode):
                raise ValueError(f"non-directory path component {component}")
        return mode

    def children(self, path: Path):
        # Consume incrementally: neither a wide directory nor a faulty iterator
        # can allocate an unbounded list before the budget is enforced.
        for child in path.iterdir():
            self.spend()
            yield child

    def walk(self, root: Path) -> None:
        mode = self.no_links(root)
        if mode is None:
            return
        pending = [(root, mode, 0)]
        while pending:
            path, mode, depth = pending.pop()
            if depth > MAX_SCAN_DEPTH:
                raise ValueError(f"namespace depth limit exceeded at {path}")
            if stat.S_ISDIR(mode):
                for child in self.children(path):
                    child_mode = self.mode(child)
                    if child_mode is None:
                        raise ValueError(f"namespace entry disappeared at {child}")
                    pending.append((child, child_mode, depth + 1))
            elif not stat.S_ISREG(mode):
                raise ValueError(f"non-regular namespace entry at {path}")

    def namespace_errors(self, supported) -> list[tuple[str, str]]:
        errors = []
        for name, owner, patterns in supported:
            try:
                if not callable(owner["locate"]):
                    raise ValueError("namespace locations cannot be established")
                # Recorded claims outside policy roots must not alias a removal
                # path either. This is deliberately stricter than root-only walks.
                for target in lexical_records(owner).values():
                    self.no_links(target)
                if owner["metadata_path"] is None:
                    raise ValueError("metadata location cannot be established")
                self.no_links(owner["metadata_path"])
                for pattern in patterns:
                    if pattern.endswith("*"):
                        site = Path(owner["locate"]("")).absolute()
                        if self.no_links(site) is None:
                            raise ValueError(f"namespace site is absent at {site}")
                        for child in self.children(site):
                            if child.name.casefold().startswith(pattern[:-1].casefold()):
                                self.walk(child)
                    else:
                        self.walk(Path(owner["locate"](pattern.rstrip("/"))).absolute())
            except (OSError, RuntimeError, ValueError) as exc:
                errors.append((name, f"namespace audit failed: {exc}"))
        return errors

    def removal_paths(self, owner: dict[str, Any]) -> tuple[list[tuple[str, Path]], list[str]]:
        # Labels are diagnostic text, NEVER keys: a real RECORD filename can be
        # identical to a derived path's display label and must remain protected.
        paths: list[tuple[str, Path]] = []
        errors: list[str] = []
        try:
            paths = list(lexical_records(owner).items())
            for row, target in list(paths):
                self.spend()
                self.no_links(target)
                source = str(target)
                if source.endswith(".py"):
                    # Match pip's filename slicing, including a literal '.py'
                    # (Path.suffix/with_suffix give different answers for it).
                    derived = {Path(source[:-3] + suffix) for suffix in (".pyc", ".pyo")}
                    # pip also uses the ACTIVE optimization, which may exceed 2.
                    # All cache calls honor sys.pycache_prefix when configured.
                    derived.add(Path(cache_from_source(source)))
                    derived.update(Path(cache_from_source(source, optimization=opt))
                                   for opt in ("", "1", "2"))
                    for bytecode in sorted(derived):
                        self.no_links(bytecode)
                        paths.append((f"{row} -> {bytecode}", bytecode))
            info = owner["metadata_path"]
            if info is None:
                raise ValueError("metadata scripts location cannot be established")
            if self.no_links(info / "scripts") is not None:
                errors.append("legacy metadata/scripts directory is present")
        except (OSError, RuntimeError, ValueError, NotImplementedError) as exc:
            errors.append(f"RECORD removal audit failed: {exc}")
        if owner["scripts"]:
            # Entry-point metadata does not prove an installer's bin scheme or
            # every platform-specific wrapper is covered by RECORD. Do not infer
            # safety from matching basenames; these states require manual repair.
            scripts = ", ".join(repr(script) for _, script in owner["scripts"])
            errors.append(f"implicit entry-point or legacy script removals are not SIMPLE: {scripts}")
        return paths, errors


def physical_namespace_paths(owner: dict[str, Any], target: Path,
                             patterns: list[str], *, diagnostic_aliases: bool = False) -> set[str] | None:
    """Map lexical removals into policy roots, never using aliases to admit commands.

    Only already-blocked plans request best-effort alias names for manual guidance.
    The namespace walk itself never follows a symlink.
    """
    locate = owner["locate"]
    if not callable(locate):
        return None
    paths: set[str] = set()
    try:
        physical = (target.resolve() if diagnostic_aliases else target).as_posix().casefold()
        for pattern in patterns:
            if pattern.endswith("*"):
                children = list(islice(Path(locate("")).iterdir(), MAX_SCAN_ENTRIES + 1))
                if len(children) > MAX_SCAN_ENTRIES:
                    return None
                roots = [child.name for child in children
                         if child.name.casefold().startswith(pattern[:-1].casefold())]
            else:
                roots = [pattern.rstrip("/")]
            for logical in roots:
                root_path = Path(locate(logical)).absolute()
                root = (root_path.resolve() if diagnostic_aliases else root_path).as_posix().casefold().rstrip("/")
                if physical == root or root.startswith(physical.rstrip("/") + "/"):
                    paths.add(logical + "/_" if pattern.endswith(("/", "*")) else logical)
                elif physical.startswith(root.rstrip("/") + "/"):
                    paths.add(logical + physical[len(root):])
    except (OSError, RuntimeError, ValueError):
        return None
    return paths


def distutils_scripts(info: Any) -> tuple[list[tuple[str, str]], bool]:
    """Retain pip's metadata/scripts entries even when RECORD does not list them."""
    if not isinstance(info, Path):
        return [], False
    try:
        directory = info / "scripts"
        if not stat.S_ISDIR(directory.lstat().st_mode):
            return [], False  # Do not enumerate a symlink or a special file.
        children = list(islice(directory.iterdir(), MAX_SCAN_ENTRIES + 1))
    except (FileNotFoundError, NotADirectoryError):
        return [], True
    except OSError:
        return [], False
    scripts = [("distutils_scripts", child.name) for child in children]
    try:
        return scripts, len(children) <= MAX_SCAN_ENTRIES and all(child.is_file() for child in children)
    except OSError:
        return scripts, False


def script_names(owner: dict[str, Any]) -> set[str]:
    """Include implicit pip removals, conservatively across platforms and schemes."""
    names: set[str] = set()
    for group, name in owner["scripts"]:
        if group == "distutils_scripts":
            endings = ("", ".bat")
        else:
            suffix = "-script.pyw" if group == "gui_scripts" else "-script.py"
            endings = ("", ".exe", ".exe.manifest", suffix)
        names.update((name + ending).casefold() for ending in endings)
    return names
