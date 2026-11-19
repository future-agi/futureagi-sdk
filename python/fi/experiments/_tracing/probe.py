"""The check of the tracing add-ons, for ``futureagi-py doctor`` and for an explicit
``instrument=[...]`` before any request: each installed traceAI instrumentor is imported **and instrumented in a
subprocess**, so a broken one is reported as broken, with its error, and never as "installed".

- Import and ``instrument()`` both: traceAI-anthropic 0.1.10 imports fine with anthropic 1.x and fails only inside
  ``instrument()`` (``No module named 'anthropic.resources.completions'``; e2e FW-16bL-TA, tracing regression). An
  import-only check called it "installed".
- A subprocess, not this process: importing an instrumentor has side effects (traceAI prints on import, F9a),
  ``instrument()`` patches the client library, and an instrumentor binds to one provider per process. The child
  instruments against its own in-memory ``TracerProvider`` (no exporter, nothing sent) and exits; this process is
  left as it was.
- The child runs this interpreter (``sys.executable -I``) with this process's ``sys.path``, so it imports exactly
  what a run in this process would. When OpenTelemetry's SDK is not importable there, or the class has no
  ``instrument``, only the import is checked (``Probe.instrumented`` is False).
- The probes run side by side, each with a time limit (``TIMEOUT_S``). One that does not finish in time, or a child
  that dies without an answer, is reported as broken with what was seen.
- Only installed add-ons are probed (``find_spec``); a missing one stays "not installed".
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from typing import Mapping, Optional, Sequence

TIMEOUT_S = 30.0
MARK = "FI-DOCTOR-PROBE "
_CHILD = r"""
import importlib, json, sys
paths, module, cls = json.loads(sys.argv[1])
sys.path[:] = paths
stage, instrumented = "import", False
try:
    klass = getattr(importlib.import_module(module), cls)
    if callable(getattr(klass, "instrument", None)):
        try:
            from opentelemetry.sdk.trace import TracerProvider
        except ImportError:
            TracerProvider = None
        if TracerProvider is not None:
            stage = "instrument"
            klass().instrument(tracer_provider=TracerProvider())
            instrumented = True
except BaseException as exc:
    text = type(exc).__name__ + ": " + str(exc)
    print("\n" + MARK + json.dumps({"ok": False, "stage": stage, "error": text[:300]}), flush=True)
else:
    print("\n" + MARK + json.dumps({"ok": True, "instrumented": instrumented}), flush=True)
""".replace("MARK", repr(MARK))


@dataclass(frozen=True)
class Probe:
    ok: bool
    error: Optional[str] = None  # the error, or what was seen instead of an answer
    stage: Optional[str] = None  # where it failed: "import" or "instrument" (None: no answer, or it worked)
    instrumented: bool = False  # instrument() ran and returned (False: import only, see the module docstring)

    def why(self) -> str:
        """The error as one phrase for a message: an instrument() failure says so."""
        if self.stage == "instrument":
            return f"instrument() raised {self.error}"
        return self.error or "no answer from the probe"


def _answer(stdout: str, stderr: str, code: Optional[int]) -> Probe:
    for line in reversed(stdout.splitlines()):
        if line.startswith(MARK):
            try:
                data = json.loads(line[len(MARK):])
            except ValueError:
                break
            return Probe(bool(data.get("ok")), data.get("error"), data.get("stage"), bool(data.get("instrumented")))
    last = next((ln.strip() for ln in reversed(stderr.splitlines()) if ln.strip()), "")
    return Probe(False, f"the import probe exited with code {code} and no answer" + (f": {last[:200]}" if last else ""))


def probe_imports(targets: Mapping[str, tuple[str, str]], *, timeout_s: float = TIMEOUT_S,
                  paths: Optional[Sequence[str]] = None) -> dict[str, Probe]:
    """``{name: Probe}`` for each ``name -> (module, class)``, each imported (and instrumented) in its own
    subprocess."""
    search = list(sys.path if paths is None else paths)
    started: dict[str, subprocess.Popen] = {}
    out: dict[str, Probe] = {}
    for name, (module, cls) in targets.items():
        try:  # all start at once: each reads its job from argv, so the probes run side by side
            started[name] = subprocess.Popen(
                [sys.executable, "-I", "-c", _CHILD, json.dumps([search, module, cls])], stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=dict(os.environ))
        except OSError as exc:  # no interpreter to start: say so, never "installed"
            out[name] = Probe(False, f"the import probe could not start ({type(exc).__name__}: {exc})")
    deadline = time.monotonic() + timeout_s
    for name, proc in started.items():
        try:
            stdout, stderr = proc.communicate(timeout=max(0.1, deadline - time.monotonic()))
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.communicate()
            out[name] = Probe(False, f"importing it did not finish within {timeout_s:g} s")
            continue
        out[name] = _answer(stdout, stderr, proc.returncode)
    return out
