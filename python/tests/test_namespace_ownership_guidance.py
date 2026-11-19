"""Manual wrapper guidance includes reference text, never an emitted pip command."""
from __future__ import annotations

import pytest

from fi._core import namespace_ownership as ownership
from test_namespace_ownership_repair import distribution, sdk
from test_namespace_ownership_safety import assert_manual_only


@pytest.mark.parametrize("name", ["unrelated-cli", "foreign-runtime"])
@pytest.mark.parametrize("group", ["console_scripts", "gui_scripts"])
@pytest.mark.parametrize("recorded_wrapper", [False, True])
def test_manual_wrapper_guidance_names_copyable_command_and_recheck(
        tmp_path, monkeypatch, name, group, recorded_wrapper):
    from fi._cli import ownership as section

    root = tmp_path.resolve()
    own = sdk(root)
    payload = {
        "fi/evals/foreign.py": b"# foreign\n",
        "fixture.dist-info/entry_points.txt": f"[{group}]\nfi = unrelated:main\n".encode(),
    }
    if recorded_wrapper:
        payload["bin/fi"] = b"# recorded wrapper\n"
    offender = distribution(root / "offender", name, payload=payload)
    monkeypatch.setattr(ownership.metadata, "distributions", lambda: [own, offender])

    result = ownership.inspect_installed()
    assert {"kind": "unowned-path", "distribution": name,
            "path": "fi/evals/foreign.py"} in result["issues"]
    assert_manual_only(result, [name], "fi")
    steps = result["repair_commands"]
    references = [step for step in steps if step.startswith(f"Manual guidance for {name}:")]
    assert len(references) == 1, steps
    reference = references[0]
    command = f"pip uninstall {name}"
    assert f"'{command}'" in reference
    assert "reference only" in reference and "not a repair step" in reference
    assert "Do not run" in reference and "SIMPLE" in reference
    assert "futureagi-py doctor --offline" in reference
    assert command not in steps
    assert "-y" not in "\n".join(steps)
    assert steps.index(reference) > next(i for i, step in enumerate(steps)
                                         if step.startswith("Manual repair required"))

    # Exercise the real renderer and scanner, not a substituted scan result.
    lines = section.section(None)
    assert reference in lines
    assert not any(line.startswith("pip ") or "Ownership check failed" in line for line in lines)
    assert lines.index(reference) < lines.index("futureagi-py doctor --offline")
    assert lines[-1] == "futureagi-py doctor --offline"
    assert (root / "sdk/fi/__init__.py").read_bytes() == b"# sdk\n"
    if recorded_wrapper:
        assert (root / "offender/bin/fi").read_bytes() == payload["bin/fi"]
