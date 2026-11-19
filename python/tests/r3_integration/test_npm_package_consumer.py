"""The package gate must test retained artifact bytes, not a newly packed build."""

import os
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]


@pytest.fixture
def consumer_gate(tmp_path):
    package = tmp_path / "package"
    scripts = package / "scripts"
    scripts.mkdir(parents=True)
    script = scripts / "check-consumer.sh"
    shutil.copyfile(ROOT / "typescript/futureagi/scripts/check-consumer.sh", script)
    consumers = package / "consumer"
    consumers.mkdir()
    for name in ("consumer.mts", "context-consumer.mjs", "tsconfig.json"):
        (consumers / name).write_text("{}")
    binaries = tmp_path / "bin"
    binaries.mkdir()
    installed = tmp_path / "installed-bytes"
    # No registry, build tool, or JavaScript executes in these shell-contract tests.
    commands = {
        "npm": '#!/bin/sh\ncase "$1" in\n'
        '  pack) echo "unexpected repack" >&2; exit 97;;\n'
        '  install) cp ./package.tgz "$INSTALLED_BYTES";;\n'
        "esac\n",
        "npx": '#!/bin/sh\nexit "${COMPILER_STATUS:-0}"\n',
        "node": "#!/bin/sh\nexit 0\n",
    }
    for name, content in commands.items():
        binary = binaries / name
        binary.write_text(content)
        binary.chmod(0o700)
    env = {
        **os.environ,
        "PATH": f"{binaries}:{os.environ['PATH']}",
        "INSTALLED_BYTES": str(installed),
    }
    return script, env, installed


@pytest.mark.parametrize("relative", [False, True])
def test_existing_tarball_is_installed_unchanged_without_a_source_build(
    consumer_gate, tmp_path, relative
):
    script, env, installed = consumer_gate
    artifact = tmp_path / "retained package.tgz"
    artifact.write_bytes(b"the exact retained artifact\x00\xff")
    argument = artifact.name if relative else str(artifact)
    result = subprocess.run(
        ["bash", str(script), argument], cwd=tmp_path, env=env,
        capture_output=True, text=True, timeout=10,
    )
    assert result.returncode == 0, result.stderr
    assert installed.read_bytes() == artifact.read_bytes()
    assert "consumer: ok" in result.stdout
    assert not (script.parents[1] / "dist").exists()


@pytest.mark.parametrize("arguments", [["missing.tgz"], ["one.tgz", "two.tgz"]])
def test_invalid_tarball_arguments_fail_before_install(consumer_gate, arguments):
    script, env, installed = consumer_gate
    result = subprocess.run(
        ["bash", str(script), *arguments], env=env,
        capture_output=True, text=True, timeout=10,
    )
    assert result.returncode != 0
    assert not installed.exists()


def test_retained_artifact_does_not_mask_consumer_failure(consumer_gate, tmp_path):
    script, env, installed = consumer_gate
    artifact = tmp_path / "retained.tgz"
    artifact.write_bytes(b"retained artifact")
    result = subprocess.run(
        ["bash", str(script), str(artifact)],
        env={**env, "COMPILER_STATUS": "42"},
        capture_output=True, text=True, timeout=10,
    )
    assert result.returncode == 42
    assert installed.read_bytes() == artifact.read_bytes()
    assert "consumer: ok" not in result.stdout
