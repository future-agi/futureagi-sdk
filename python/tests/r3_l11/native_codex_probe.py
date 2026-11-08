"""Explicit cloud-only native diagnostic, separate from the ordinary unit suite.

Run with the exact installed codex executable as argv[1]. No login/provider call,
model self-report, customer repository, or native-delivery claim is involved.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from fi.context.materialize import apply_plan, plan_install, verify
from test_materializer import bundle


def main(binary: str) -> None:
    executable = str(Path(binary).absolute())
    version = subprocess.check_output(
        [executable, "--version"], text=True, timeout=15
    ).strip()
    if version != "codex-cli 0.167.0":
        raise RuntimeError("Native probe requires pinned codex-cli 0.167.0")
    with tempfile.TemporaryDirectory(prefix="fi-native-l11-") as temporary:
        root = Path(temporary)
        home, project = root / "home", root / "project"
        home.mkdir()
        project.mkdir()
        (home / ".codex").mkdir()
        source = bundle(
            root=b"# Approved rules\nSynthetic standing marker FI_L11_STANDING_9081.\n"
        )
        prepared = plan_install(
            source, project=project, profile="codex", allow_preview=True
        )
        apply_plan(prepared, authorize=lambda auth: None, quiescent=True)
        environment = {
            "PATH": os.environ["PATH"],
            "HOME": str(home),
            "CODEX_HOME": str(home / ".codex"),
            "LANG": "C.UTF-8",
        }
        result = subprocess.run(
            [
                executable,
                "--cd",
                str(project),
                "debug",
                "prompt-input",
                "Synthetic inventory request",
            ],
            cwd=root,
            env=environment,
            text=True,
            capture_output=True,
            timeout=60,
            check=True,
        )
        prompt = json.loads(result.stdout)
        rendered = json.dumps(prompt)
        if "FI_L11_STANDING_9081" not in rendered:
            raise AssertionError(
                "Actual native prompt diagnostic omitted managed AGENTS instructions"
            )
        skill_texts = [
            content["text"]
            for item in prompt
            if item.get("type") == "message"
            for content in item.get("content", [])
            if content.get("type") == "input_text"
            and content.get("text", "").startswith("<skills_instructions>")
        ]
        if len(skill_texts) != 1:
            raise AssertionError("Missing or ambiguous native skill catalog")
        roots = dict(re.findall(r"- `(r[0-9]+)` = `([^`]+)`", skill_texts[0]))
        root_ids = [
            key
            for key, value in roots.items()
            if value == str(project / ".agents/skills")
        ]
        if (
            len(root_ids) != 1
            or f"(file: {root_ids[0]}/refunds/SKILL.md)" not in skill_texts[0]
        ):
            raise AssertionError(
                "Actual native prompt diagnostic omitted the installed native skill catalog"
            )
        if not verify(project=project)["verified"]:
            raise AssertionError("Installed bytes failed verification")
        # Independent negative control: remove the managed entrypoint, not the oracle.
        (project / "AGENTS.md").unlink()
        changed = subprocess.run(
            [
                executable,
                "--cd",
                str(project),
                "debug",
                "prompt-input",
                "Synthetic inventory request",
            ],
            cwd=root,
            env=environment,
            text=True,
            capture_output=True,
            timeout=60,
            check=True,
        )
        if "FI_L11_STANDING_9081" in json.dumps(json.loads(changed.stdout)):
            raise AssertionError(
                "Native diagnostic control still exposed deleted project instructions"
            )
        if verify(project=project)["verified"]:
            raise AssertionError("Byte verifier did not detect a deleted entrypoint")
        print(
            json.dumps(
                {
                    "schema": 1,
                    "host": version,
                    "profile": "codex",
                    "profile_version": "1",
                    "native_discovery": "observed_in_prompt_diagnostic",
                    "standing_instructions": "observed_in_prompt_diagnostic",
                    "negative_control": "passed",
                    "model_delivery": "not_observed",
                    "model_invocation": "none_requested",
                    "prompt_diagnostic_sha256": hashlib.sha256(
                        result.stdout.encode()
                    ).hexdigest(),
                    "context_digest": source.identity.digest,
                },
                sort_keys=True,
            )
        )


if __name__ == "__main__":
    main(sys.argv[1])
