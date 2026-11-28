"""Real ``rsync`` and ``scp`` through the real CLI: ``sandbox rsh`` as the transport, against the
fake channel server whose commands run on this machine in a temp folder. The trees are compared
byte for byte."""

from __future__ import annotations

import hashlib
import os
import shutil
import stat
import subprocess
import sys
from pathlib import Path

import pytest

from ._channel_fake import BEARER, SBX
from ._channel_support import channel_fixture  # noqa: F401

pytestmark = pytest.mark.skipif(
    not (shutil.which("rsync") and shutil.which("scp")), reason="needs rsync and scp on PATH")


def cli_prefix() -> list:
    return [sys.executable, "-m", "fi._cli"]


@pytest.fixture(name="env")
def env_fixture(channel):
    return {**os.environ, "OMEGA_BASE_URL": channel.base_url, "FUTUREAGI_OMEGA_API_KEY": BEARER,
            "PYTHONPATH": os.pathsep.join(p for p in sys.path if p)}


def make_tree(root: Path) -> None:
    (root / "deep" / "er").mkdir(parents=True)
    (root / "empty-dir").mkdir()
    (root / "a.txt").write_text("hello\n")
    (root / "binary.bin").write_bytes(os.urandom(3 * 1024 * 1024 + 17) + b"\x00" * 100)
    (root / "all-bytes").write_bytes(bytes(range(256)) * 300)
    (root / "empty").write_bytes(b"")
    (root / "deep" / "er" / "ünï cödé name.txt").write_text("x" * 100_000)
    (root / "with space.sh").write_text("#!/bin/sh\necho hi\n")
    (root / "with space.sh").chmod(0o755)
    os.symlink("a.txt", root / "link")


def digest(root: Path) -> dict:
    seen = {}
    for path in sorted(root.rglob("*")):
        rel = path.relative_to(root).as_posix()
        mode = path.lstat().st_mode
        if stat.S_ISLNK(mode):
            seen[rel] = ("link", os.readlink(path))
        elif path.is_dir():
            seen[rel] = ("dir",)
        else:
            seen[rel] = ("file", hashlib.sha256(path.read_bytes()).hexdigest(), mode & 0o111 != 0)
    return seen


def run(argv, env, cwd, timeout=120):
    done = subprocess.run(argv, env=env, cwd=cwd, capture_output=True, timeout=timeout)
    assert done.returncode == 0, (done.returncode, done.stdout[-2000:], done.stderr[-4000:])
    return done


def test_rsync_dash_e_rsh_pushes_a_tree_byte_for_byte(channel, env, tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    make_tree(src)
    shell = " ".join(cli_prefix() + ["sandbox", "rsh", SBX])
    run(["rsync", "-av", "-e", shell, "src/", ":dest/"], env, tmp_path)
    assert digest(channel.root / "dest") == digest(src)
    assert (channel.root / "dest" / "binary.bin").read_bytes() == (src / "binary.bin").read_bytes()
    run(["rsync", "-av", "-e", shell, "src/", ":dest/"], env, tmp_path)  # a second run sends nothing new
    assert channel.flow_errors == 0 and channel.max_unreleased <= 262144 and channel.max_stdin_pending <= 32768


def test_rsync_dash_e_rsh_pulls_a_tree_byte_for_byte(channel, env, tmp_path):
    remote = channel.root / "stuff"
    remote.mkdir()
    make_tree(remote)
    shell = " ".join(cli_prefix() + ["sandbox", "rsh", SBX])
    (tmp_path / "out").mkdir()
    run(["rsync", "-av", "-e", shell, ":stuff/", "out/"], env, tmp_path)
    assert digest(tmp_path / "out") == digest(remote)


def test_the_rsync_command_pushes_and_pulls(channel, env, tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    make_tree(src)
    run(cli_prefix() + ["sandbox", "rsync", SBX, "-a", "src/", ":via cli's/"], env, tmp_path)
    assert digest(channel.root / "via cli's") == digest(src)  # a space and a quote in the path survive
    (tmp_path / "back").mkdir()
    run(cli_prefix() + ["sandbox", "rsync", SBX, "-a", ":via cli's/", "back/"], env, tmp_path)
    assert digest(tmp_path / "back") == digest(src)


def test_scp_copies_a_file_and_a_tree_both_ways(channel, env, tmp_path):
    one = tmp_path / "one.bin"
    one.write_bytes(os.urandom(2 * 1024 * 1024 + 3) + b"\x00\x00")
    run(cli_prefix() + ["sandbox", "scp", SBX, str(one), ":up.bin"], env, tmp_path)
    assert (channel.root / "up.bin").read_bytes() == one.read_bytes()
    run(cli_prefix() + ["sandbox", "scp", SBX, ":up.bin", str(tmp_path / "down.bin")], env, tmp_path)
    assert (tmp_path / "down.bin").read_bytes() == one.read_bytes()

    src = tmp_path / "tree"
    src.mkdir()
    (src / "sub").mkdir()
    (src / "sub" / "f.bin").write_bytes(bytes(range(256)) * 50)
    (src / "g.txt").write_text("gee\n")
    run(cli_prefix() + ["sandbox", "scp", SBX, "-r", str(src), ":"], env, tmp_path)
    assert digest(channel.root / "tree") == digest(src)
    (tmp_path / "got").mkdir()
    run(cli_prefix() + ["sandbox", "scp", SBX, "-r", ":tree", str(tmp_path / "got")], env, tmp_path)
    assert digest(tmp_path / "got" / "tree") == digest(src)
