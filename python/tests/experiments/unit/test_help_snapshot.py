"""--help shows exactly the 13 everyday flags; --help-all shows every flag of this build, grouped."""

import re

from fi.experiments._cli import commands
from tests.experiments.unit.cli_helpers import cli

EVERYDAY = ["--dataset", "--eval", "--judge-model", "--trials", "--concurrency", "--limit", "--timeout-s",
            "--max-cost-usd", "--param", "--model", "--name", "--no-upload", "--fail-under"]
MORE = ["--version", "--input-column", "--expected-column", "--rows", "--seed", "--from-column", "--eval-map",
        "--pass-label", "--description", "--metadata", "--experiment", "--project", "--retries", "--fail-fast",
        "--price", "--param-str", "--no-trace", "--instrument", "--json", "--max-error-rate", "--error-policy", "--resume",
        "--list",
        "--filter", "--quiet", "--verbose", "--env-file", "--no-env-file"]
NEVER = ["--config", "--sample", "--from-run", "--dry-run", "--depth", "--voice", "--connect", "--side-effects"]


def _flags(text):
    """Option names at the start of help rows (not flags mentioned inside help text)."""
    found = set()
    for line in text.splitlines():
        m = re.match(r"^\s+((?:-\w, )?--[a-z][a-z-]*(?:, --[a-z][a-z-]*)?)", line)
        if m:
            found |= set(re.findall(r"--[a-z][a-z-]*", m.group(1)))
    return found


def test_help_tier_one():
    code, out, _ = cli("run", "--help")
    assert code == 0
    section = out.split("everyday options:")[1]
    shown = _flags(section) - {"--help-all", "--local"}
    assert shown == set(EVERYDAY) and len(EVERYDAY) == 13
    assert "--help-all" in out


def test_help_all_tier_two():
    code, out, _ = cli("run", "--help-all")
    assert code == 0
    flags = _flags(out)
    assert set(EVERYDAY) | set(MORE) <= flags
    assert not flags & set(NEVER)
    for title, _ in commands.MORE:
        assert f"\n{title}:\n" in out


def test_help_does_not_mention_third_party_voice_platforms():
    for argv in (("run", "--help"), ("run", "--help-all"), ("--help",)):
        out = cli(*argv)[1].lower()
        for word in ("vapi", "retell", "bland", "elevenlabs", "sip"):
            assert word not in out
