#!/usr/bin/env python3
"""Offline pip/uv consumer migration matrix using pinned published legacy wheels.

Preparation downloads wheels to separate directories; this runner never downloads,
extracts, publishes or imports legacy distribution code. Supply optional repaired
ALK and agentcc shim wheels to qualify their cells; missing inputs stay explicit.
"""
from __future__ import annotations

import argparse
import base64
import csv
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import zipfile

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("ownership_gate", HERE / "check_ownership.py")
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


def digest(path):
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def pointer_wheel(directory):
    """Create a metadata-only, never-published pointer to measure uninstall behavior."""
    directory.mkdir()
    info = "ai_evaluation-2.0.0.dist-info"
    files = {
        info + "/METADATA": b"Metadata-Version: 2.1\nName: ai-evaluation\nVersion: 2.0.0\nRequires-Dist: futureagi>=0.7.0\n",
        info + "/WHEEL": b"Wheel-Version: 1.0\nRoot-Is-Purelib: true\nTag: py3-none-any\n",
    }
    out = io.StringIO()
    writer = csv.writer(out)
    for path, data in files.items():
        encoded = base64.urlsafe_b64encode(hashlib.sha256(data).digest()).rstrip(b"=").decode()
        writer.writerow([path, "sha256=" + encoded, len(data)])
    writer.writerow([info + "/RECORD", "", ""])
    files[info + "/RECORD"] = out.getvalue().encode()
    target = directory / "ai_evaluation-2.0.0-py3-none-any.whl"
    with zipfile.ZipFile(target, "w") as z:
        for path, data in files.items():
            z.writestr(path, data)
    return target


class Consumer:
    """An isolated virtual environment; all installer commands use the wheelhouse only."""
    def __init__(self, manager, label, args):
        self.args, self.manager = args, manager
        self.root = args.output / (manager + "-" + label)
        self.root.mkdir()
        self.logs = []
        self.call([sys.executable, "-m", "venv", str(self.root / "env")])
        self.python = str(self.root / "env/bin/python")
        self.call([self.python, "-I", "-m", "pip", "install", "--no-index", "--find-links", str(args.dependencies),
                   "pip==24.3.1"])
        self.install(["-r", str(args.requirements)])

    def call(self, command, expected=0):
        env = {k: v for k, v in os.environ.items() if not k.startswith(("FI_", "AGENTCC_", "PIP_", "UV_"))}
        env.update(PYTHONDONTWRITEBYTECODE="1", LITELLM_LOCAL_MODEL_COST_MAP="True",
                   FI_LOGIN_FILE="/nonexistent/consumer-login.json", FI_BASE_URL="http://127.0.0.1:9",
                   FI_PLATFORM_BASE_URL="http://127.0.0.1:9", OPENBLAS_NUM_THREADS="1",
                   PIP_CONFIG_FILE=os.devnull, UV_OFFLINE="1", UV_NO_CONFIG="1")
        proc = subprocess.run(command, cwd=self.root, env=env, text=True, capture_output=True, timeout=600)
        index = len(self.logs)
        self.logs.append({"argv": command, "returncode": proc.returncode})
        (self.root / f"step-{index}.log").write_text(proc.stdout + "\n" + proc.stderr)
        (self.root / "commands.json").write_text(json.dumps(self.logs, indent=2))
        if expected is not None and proc.returncode != expected:
            raise RuntimeError(f"{self.root.name} step {index}: exit {proc.returncode}, expected {expected}")
        return proc

    def install(self, targets, force=False, deps=False):
        command = ([self.python, "-I", "-m", "pip", "install"] if self.manager == "pip"
                   else [self.args.uv, "pip", "install", "--python", self.python])
        command += ["--no-index", "--find-links", str(self.args.dependencies)]
        if not deps:
            command += ["--no-deps"]
        if force:
            command += ["--force-reinstall"]
        self.call(command + [str(t) for t in targets])

    def uninstall(self, name):
        command = ([self.python, "-I", "-m", "pip", "uninstall", "-y"] if self.manager == "pip"
                   else [self.args.uv, "pip", "uninstall", "--python", self.python])
        self.call(command + [name])

    def probe(self, mode, expected=0):
        command = [self.python, "-I", str(HERE / "consumer_probe.py"), mode]
        if mode == "imports":
            command += ["--golden", str(self.args.golden)]
        proc = self.call(command, expected)
        return json.loads(proc.stdout)

    def healthy(self):
        self.probe("integrity")
        # All probes still execute. Incomplete binary inputs cannot qualify imports;
        # raw import failures remain in the per-command logs, never become a PASS.
        self.probe("imports", expected=None if self.args.missing_dependencies else 0)
        doctor = self.probe("doctor")
        assert not doctor["sections"]["Package ownership"].get("problems"), doctor


def run_matrix(args):
    """Evaluate each case independently; failures never suppress later cases."""
    args.output.mkdir(parents=True, exist_ok=False)
    legacy = {}
    for name, filename in {
        "sdk": "futureagi-0.6.13-py3-none-any.whl",
        "evals": "ai_evaluation-1.1.0-py3-none-any.whl",
        "alk": "agent_learning_kit-0.3.3-py3-none-any.whl",
        "agentcc": "agentcc-1.0.0-py3-none-any.whl",
    }.items():
        found = list(args.legacy.rglob(filename))
        legacy[name] = found[0] if len(found) == 1 else None
    inputs = [args.candidate, args.golden, args.requirements] + [p for p in legacy.values() if p]
    inputs += args.tracing + [p for p in (args.alk, args.shim) if p]
    result = {"python": sys.version, "input_digests": {str(p): digest(p) for p in inputs},
              "missing_dependencies": args.missing_dependencies, "cells": []}
    pointer = pointer_wheel(args.output / "local-pointer")

    def cell(manager, name, fn, missing=None):
        row = {"manager": manager, "case": name}
        if missing:
            row.update(status="NOT-EVALUATED", reason=missing)
        else:
            try:
                detail = fn()
                row.update(status="PASS", detail=detail)
                if args.missing_dependencies and (name in {"M1", "M2", "M3", "M3-upgrade"} or name.startswith("M5-")):
                    row.update(status="NOT-EVALUATED", reason="complete import dependency wheels unavailable",
                               missing_dependencies=args.missing_dependencies)
            except Exception as exc:
                row.update(status="FAIL", reason=f"{type(exc).__name__}: {exc}")
        result["cells"].append(row)
        (args.output / "matrix.json").write_text(json.dumps(result, indent=2) + "\n")

    def migration(manager, case, old):
        c = Consumer(manager, case, args)
        for package in old:
            c.install([legacy[package]])
        c.uninstall("agent-learning-kit" if "alk" in old else "ai-evaluation")
        c.install([args.candidate], force=True)
        c.healthy()
        c.uninstall("futureagi")
        c.probe("residue")

    def alk_upgrade(manager):
        gate.check_combination([args.candidate, args.alk])
        c = Consumer(manager, "M3-upgrade", args)
        c.install([legacy["sdk"]])
        c.install([legacy["alk"]])
        c.uninstall("agent-learning-kit")
        c.install([args.candidate], force=True)
        c.install([args.alk])
        c.healthy()
        c.uninstall("agent-learning-kit")
        c.probe("integrity")
        c.uninstall("futureagi")
        c.probe("residue")

    def coexist(manager, label, companions):
        gate.check_combination([args.candidate] + companions)
        for order in ("candidate-first", "companion-first"):
            c = Consumer(manager, label + "-" + order, args)
            groups = [[args.candidate], companions]
            for group in groups if order == "candidate-first" else reversed(groups):
                c.install(group)
            c.healthy()
            for wheel in companions:
                c.uninstall(gate.wheel_record(wheel)["name"])
                c.probe("integrity")
            c.healthy()

    def diagnostic(manager):
        c = Consumer(manager, "M6", args)
        c.install([args.candidate])
        c.install([legacy["evals"]])
        before = c.probe("doctor", expected=3)
        problems = before["sections"]["Package ownership"]["problems"]
        assert any("overlap:" in p for p in problems), problems
        assert any("hash-mismatch:" in p for p in problems), problems
        c.uninstall("ai-evaluation")
        after = c.probe("doctor", expected=3)
        assert any("missing-file:" in p for p in after["sections"]["Package ownership"]["problems"])
        c.install([args.candidate], force=True)
        c.healthy()
        return {"overlap_detected": True, "missing_files_detected": True, "repair_clean": True}

    def pointer_upgrade(manager, deps=True):
        c = Consumer(manager, "M7" if deps else "M7-no-deps-observation", args)
        c.install([legacy["sdk"]])
        c.install([legacy["evals"]])
        c.install([args.candidate], force=True)
        c.probe("integrity")
        # Dependency resolution ON: the already-satisfied futureagi requirement is material.
        c.install([pointer], deps=deps)
        after = c.probe("integrity", expected=None)
        return {"futureagi_files_survived": not after["errors"], "integrity": after,
                "dependency_resolution": deps, "qualifies_M7": deps,
                "pointer_digest": digest(pointer), "pointer_published": False}

    def shim_upgrade(manager):
        gate.check_combination([args.candidate, args.shim])
        c = Consumer(manager, "M4", args)
        c.install([legacy["agentcc"]])
        c.install([args.candidate])
        c.install([args.shim])
        c.uninstall("agentcc")
        c.probe("integrity")

    cell("archive", "REC-0", lambda: gate.check_combination([args.candidate]))
    for manager in ("pip", "uv"):
        for case, old in [("M1", ["sdk", "evals"]), ("M2", ["evals"]), ("M3", ["sdk", "alk"])]:
            missing = [key for key in old if legacy[key] is None]
            cell(manager, case, lambda case=case, old=old: migration(manager, case, old),
                 "missing published wheels: " + ", ".join(missing) if missing else None)
        cell(manager, "M3-upgrade", lambda: alk_upgrade(manager),
             "repaired ALK candidate or legacy inputs missing"
             if not args.alk or not legacy["sdk"] or not legacy["alk"] else None)
        cell(manager, "M4", lambda: shim_upgrade(manager),
             "agentcc shim candidate or legacy wheel missing" if not args.shim or not legacy["agentcc"] else None)
        cell(manager, "M5-tracing", lambda: coexist(manager, "M5-tracing", args.tracing),
             "tracing wheels not supplied" if not args.tracing else None)
        cell(manager, "M5-alk", lambda: coexist(manager, "M5-alk", [args.alk]),
             "repaired ALK candidate not supplied" if not args.alk else None)
        cell(manager, "M5-shim", lambda: coexist(manager, "M5-shim", [args.shim]),
             "agentcc shim candidate not supplied" if not args.shim else None)
        cell(manager, "M6", lambda: diagnostic(manager),
             "published evals wheel missing" if not legacy["evals"] else None)
        cell(manager, "M7", lambda: pointer_upgrade(manager),
             "published legacy wheels missing" if not legacy["sdk"] or not legacy["evals"] else
             "complete resolver dependency wheels unavailable" if args.missing_dependencies else None)
        if args.missing_dependencies:
            cell(manager, "M7-no-deps-observation", lambda: pointer_upgrade(manager, deps=False),
                 "published legacy wheels missing" if not legacy["sdk"] or not legacy["evals"] else None)
    for manager in ("pip", "uv"):
        parts = [r for r in result["cells"] if r["manager"] == manager and r["case"].startswith("M5-")]
        state = ("FAIL" if any(r["status"] == "FAIL" for r in parts) else
                 "NOT-EVALUATED" if any(r["status"] == "NOT-EVALUATED" for r in parts) else "PASS")
        result["cells"].append({"manager": manager, "case": "M5", "status": state,
                                "parts": [r["case"] for r in parts]})
    result["status"] = ("FAIL" if any(r["status"] == "FAIL" for r in result["cells"]) else
                        "NOT-EVALUATED" if any(r["status"] == "NOT-EVALUATED" for r in result["cells"]) else "PASS")
    (args.output / "matrix.json").write_text(json.dumps(result, indent=2) + "\n")
    return int(result["status"] != "PASS")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for arg in ("candidate", "legacy", "dependencies", "requirements", "output", "golden"):
        parser.add_argument("--" + arg, type=Path, required=True)
    parser.add_argument("--alk", type=Path)
    parser.add_argument("--shim", type=Path)
    parser.add_argument("--tracing", type=Path, nargs="*", default=[])
    parser.add_argument("--uv", default="uv")
    parser.add_argument("--dependency-status", type=Path, required=True,
                        help="preparation receipt; missing wheels prevent import qualification")
    args = parser.parse_args()
    missing = [name for name in ("candidate", "golden", "requirements", "dependency_status")
               if not getattr(args, name).is_file()]
    if missing:
        args.output.mkdir(parents=True, exist_ok=False)
        cells = [{"manager": manager, "case": f"M{i}", "status": "NOT-EVALUATED",
                  "reason": "required input missing: " + ", ".join(missing)}
                 for manager in ("pip", "uv") for i in range(1, 8)]
        (args.output / "matrix.json").write_text(json.dumps({"status": "NOT-EVALUATED", "cells": cells}, indent=2))
        return 1
    args.missing_dependencies = json.loads(args.dependency_status.read_text())["missing"]
    return run_matrix(args)


if __name__ == "__main__":
    raise SystemExit(main())
