"""The local run journal.

``.futureagi/runs/<run_id>/plan.json`` and ``journal.jsonl`` under the working directory, or under
``$FI_RUN_DIR``. Written **before** any upload, so a crash, Ctrl-C or kill loses only in-flight
trials. Every file carries ``schema_version`` and the SDK version; the directories are 0700 and
the files 0600; a lock file stops two processes from writing one run. The first run writes
``.futureagi/.gitignore`` containing ``runs/`` (cassettes stay committable).
"""

from __future__ import annotations

import json
import os
import sys
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterator, Optional

from fi.experiments.errors import JournalError, RunLockedError

SCHEMA_VERSION = 1
TERMINAL = ("completed", "failed", "skipped")


def sdk_version() -> str:
    try:
        from importlib.metadata import version

        return version("futureagi")
    except Exception:
        return "unknown"


def runs_root(base: Optional[os.PathLike] = None) -> Path:
    if base is not None:
        return Path(base)
    env = os.environ.get("FI_RUN_DIR")
    if env:
        return Path(env)
    return Path.cwd() / ".futureagi" / "runs"


def _mkdir_private(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    if sys.platform != "win32":
        os.chmod(path, 0o700)


def _write_private(path: Path, text: str) -> None:
    fd = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        fh.write(text)
    if sys.platform != "win32":
        os.chmod(path, 0o600)


def _ensure_gitignore(root: Path) -> None:
    # Only for the default layout: <cwd>/.futureagi/runs -> <cwd>/.futureagi/.gitignore
    if root.name == "runs" and root.parent.name == ".futureagi":
        gi = root.parent / ".gitignore"
        if not gi.exists():
            gi.write_text("runs/\n", encoding="utf-8")


def _pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    if sys.platform == "win32":  # pragma: no cover - checked on the Windows VM
        return True
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


@dataclass
class JournalRecord:
    example_id: str
    trial: int
    status: str
    receipt_key: str
    item_bytes: bytes
    acked: bool = False

    @property
    def item(self) -> dict[str, Any]:
        return json.loads(self.item_bytes.decode("utf-8"))


@dataclass
class LoadedJournal:
    run_id: str
    plan: dict
    records: dict[tuple[str, int], JournalRecord] = field(default_factory=dict)
    checklists: dict[str, dict] = field(default_factory=dict)  # judge name -> its journaled checklist

    def terminal(self) -> set[tuple[str, int]]:
        return {k for k, r in self.records.items() if r.status in TERMINAL}

    def failed_example_ids(self) -> list[str]:
        """Example ids with any failed or skipped trial, or a trial that never finished, in plan order."""
        out: list[str] = []
        for ident in self.plan.get("items", []):
            key = (ident["example_id"], int(ident["trial"]))
            rec = self.records.get(key)
            if (rec is None or rec.status in ("failed", "skipped")) and key[0] not in out:
                out.append(key[0])
        return out

    def example_ids(self) -> list[str]:
        seen: list[str] = []
        for ident in self.plan.get("items", []):
            if ident["example_id"] not in seen:
                seen.append(ident["example_id"])
        return seen


class Journal:
    def __init__(self, run_id: str, root: Optional[os.PathLike] = None) -> None:
        self.run_id = str(run_id)
        self.root = runs_root(root)
        self.dir = self.root / self.run_id
        self.plan_path = self.dir / "plan.json"
        self.path = self.dir / "journal.jsonl"
        self.lock_path = self.dir / "lock"
        self._fh = None
        self._mutex = threading.Lock()
        self._locked = False

    # ---- lifecycle ----
    def create(self, plan: dict) -> None:
        _mkdir_private(self.root)
        _ensure_gitignore(self.root)
        _mkdir_private(self.dir)
        self.acquire()
        body = {"schema_version": SCHEMA_VERSION, "sdk_version": sdk_version(), **plan}
        _write_private(self.plan_path, json.dumps(body, sort_keys=True, indent=1))
        self._open()

    def reopen(self) -> LoadedJournal:
        if not self.plan_path.exists():
            raise JournalError(f"no journal for run {self.run_id} under {self.root}")
        self.acquire()
        loaded = load(self.run_id, self.root)
        self._open()
        return loaded

    def _open(self) -> None:
        fd = os.open(str(self.path), os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
        if sys.platform != "win32":
            os.chmod(self.path, 0o600)
        self._fh = os.fdopen(fd, "a", encoding="utf-8")

    def acquire(self) -> None:
        try:
            fd = os.open(str(self.lock_path), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except FileExistsError:
            try:
                pid = int(self.lock_path.read_text().strip() or "0")
            except (OSError, ValueError):
                pid = 0
            if pid != os.getpid() and _pid_alive(pid):
                stale = (" Windows cannot tell whether that process still runs (SDK-53): if it has exited, "
                         f"delete {self.lock_path}") if sys.platform == "win32" else (
                         f" If process {pid} is not this run (a reused process id), delete {self.lock_path}")
                raise RunLockedError(
                    f"run {self.run_id} is locked by process {pid}; wait for it to finish.{stale}"
                ) from None
            self.lock_path.unlink(missing_ok=True)
            fd = os.open(str(self.lock_path), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "w") as fh:
            fh.write(str(os.getpid()))
        self._locked = True

    def close(self) -> None:
        with self._mutex:
            if self._fh is not None:
                self._fh.flush()
                try:
                    os.fsync(self._fh.fileno())
                except OSError:
                    pass
                self._fh.close()
                self._fh = None
        if self._locked:
            self.lock_path.unlink(missing_ok=True)
            self._locked = False

    # ---- writes ----
    def append(self, record: JournalRecord) -> None:
        line = {
            "schema_version": SCHEMA_VERSION,
            "type": "item",
            "example_id": record.example_id,
            "trial": record.trial,
            "status": record.status,
            "receipt_key": record.receipt_key,
            "item": record.item_bytes.decode("utf-8"),
        }
        self._write(line)

    def ack(self, receipt_keys: list[str]) -> None:
        self._write({"schema_version": SCHEMA_VERSION, "type": "ack", "receipt_keys": receipt_keys})

    def event(self, kind: str, **data: Any) -> None:
        self._write({"schema_version": SCHEMA_VERSION, "type": kind, **data})

    def _write(self, obj: dict) -> None:
        with self._mutex:
            if self._fh is None:
                raise JournalError(f"journal for run {self.run_id} is not open")
            self._fh.write(json.dumps(obj, sort_keys=True, ensure_ascii=False) + "\n")
            self._fh.flush()


def _lines(path: Path) -> Iterator[dict]:
    if not path.exists():
        return
    with path.open(encoding="utf-8") as fh:
        for raw in fh:
            raw = raw.strip()
            if not raw:
                continue
            try:
                yield json.loads(raw)
            except ValueError:
                continue  # a torn last line after a kill: ignore it


def load(run_id: str, root: Optional[os.PathLike] = None) -> LoadedJournal:
    base = runs_root(root) / str(run_id)
    try:
        plan = json.loads((base / "plan.json").read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise JournalError(f"no readable journal for run {run_id} under {base.parent}", exc) from exc
    if int(plan.get("schema_version", 0)) > SCHEMA_VERSION:
        raise JournalError(
            f"run {run_id} was journaled by a newer SDK (schema {plan.get('schema_version')}); upgrade futureagi"
        )
    loaded = LoadedJournal(run_id=str(run_id), plan=plan)
    acked: set[str] = set()
    for line in _lines(base / "journal.jsonl"):
        if line.get("type") == "item":
            rec = JournalRecord(
                example_id=str(line["example_id"]),
                trial=int(line["trial"]),
                status=str(line["status"]),
                receipt_key=str(line["receipt_key"]),
                item_bytes=str(line["item"]).encode("utf-8"),
            )
            loaded.records[(rec.example_id, rec.trial)] = rec
        elif line.get("type") == "ack":
            acked.update(line.get("receipt_keys", []))
        elif line.get("type") == "judge_checklist" and isinstance(line.get("judge"), str):
            loaded.checklists.setdefault(line["judge"], line)  # the first: the one the run's rows were judged on
    for rec in loaded.records.values():
        rec.acked = rec.receipt_key in acked
    return loaded
