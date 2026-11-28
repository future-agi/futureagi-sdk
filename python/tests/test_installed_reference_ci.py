"""The installed-wheel reference check must not resolve SDK source imports."""

from pathlib import Path
import shlex

import yaml


ROOT = Path(__file__).resolve().parents[2]


def test_python_reference_check_uses_the_fresh_wheel_outside_the_checkout():
    workflow = yaml.safe_load((ROOT / ".github/workflows/ci.yml").read_text())
    steps = workflow["jobs"]["packages"]["steps"]
    install = next(step for step in steps if step.get("name") == (
        "Install the wheel into an empty virtualenv, run and type-check the consumer"
    ))
    commands = [shlex.split(line) for line in install["run"].splitlines() if line.strip()]
    create = commands.index(["python", "-m", "venv", "$RUNNER_TEMP/consumer"])
    wheel = commands.index([
        "$RUNNER_TEMP/consumer/bin/pip", "install", "--quiet", "python/dist/*.whl", "mypy",
    ])
    copy_checker = commands.index([
        "cp", "python/consumer/consumer.py", "python/consumer/docs_examples.py", "$RUNNER_TEMP/consumer/",
    ])
    copy_reference = commands.index([
        "cp", "-R", "docs/sdk-reference", "$RUNNER_TEMP/consumer/sdk-reference",
    ])
    leave_checkout = commands.index(["cd", "$RUNNER_TEMP/consumer"])
    check = commands.index(["./bin/python", "-I", "-B", "docs_examples.py", "sdk-reference"])
    assert create < wheel < copy_checker < leave_checkout < check
    assert wheel < copy_reference < leave_checkout
    assert [command for command in commands[leave_checkout:check] if command[0] == "cd"] == [
        ["cd", "$RUNNER_TEMP/consumer"]
    ]
