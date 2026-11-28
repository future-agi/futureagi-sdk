"""The unified ``futureagi-py agents`` command group; no independent executable."""
from __future__ import annotations

import json
import os
from pathlib import Path

from .code._client import require_enabled
from .definition import invalid, validate
from .files import read_json, write_json


def register(subparsers):
    if os.environ.get("FI_AGENT_CODE_ENABLED") != "1":
        return
    from fi._cli.registry import set_section

    import argparse

    group = subparsers.choices.get("agents")
    if group is None:
        group = subparsers.add_parser(
            "agents", help="Preview: saved Console agent definitions as code"
        )
    commands = next(
        (action for action in group._actions if isinstance(action, argparse._SubParsersAction)), None
    )
    if commands is None:
        commands = group.add_subparsers(dest="agent_command", required=True)
    for command in ("validate", "plan", "apply", "export", "import"):
        parser = commands.add_parser(command)
        parser.add_argument(
            "--json", action="store_true", help="Machine-readable result and errors"
        )
        if command == "export":
            parser.add_argument("agent_id")
            parser.add_argument(
                "--out",
                required=True,
                help="New JSON definition file (never overwritten)",
            )
        else:
            parser.add_argument("file", help="UTF-8 JSON agent definition")
        if command in ("plan", "apply", "import"):
            parser.add_argument(
                "--lockfile",
                help="Defaults to FILE.lock.json; bound to backend and workspace",
            )
        if command == "apply":
            parser.add_argument(
                "--force",
                action="store_true",
                help="Acknowledge observed drift; concurrent edits still fail",
            )
        if command == "import":
            parser.add_argument(
                "--agent-id",
                help="Bind an existing ID only if its definition matches exactly",
            )
        if command != "validate":
            parser.add_argument("--platform-base-url")
            parser.add_argument("--organization-id")
            parser.add_argument("--workspace-id")
        parser.set_defaults(func=run)
    set_section("agents", "platform")


def run(args):
    require_enabled()
    command = args.agent_command
    document = None if command == "export" else validate(read_json(args.file))
    if command == "validate":
        result = {
            "valid": True,
            "validation": "local-structure",
            "schemaVersion": document["schemaVersion"],
            "note": "References, permissions, quotas and model availability are checked by the backend on apply.",
        }
    else:
        from fi import FutureAGIClient

        lockfile = None
        if command in ("plan", "apply", "import"):
            lockfile = args.lockfile or (args.file + ".lock.json")
            if Path(args.file).resolve() in (
                Path(lockfile).resolve(),
                Path(lockfile + ".guard").resolve(),
            ):
                invalid(
                    "Definition and lockfile paths must be distinct.",
                    "agent_file_error",
                )
        with FutureAGIClient(
            platform_base_url=args.platform_base_url,
            organization_id=args.organization_id,
            workspace_id=args.workspace_id,
        ) as client:
            agents = client.agents.code
            if command == "plan":
                result = agents.plan(document, lockfile=lockfile)
            elif command == "apply":
                result = agents.apply(document, lockfile=lockfile, force=args.force)
            elif command == "import":
                result = agents.import_definition(
                    document, lockfile=lockfile, agent_id=args.agent_id
                )
            else:
                exported = agents.export(args.agent_id)
                write_json(args.out, exported)
                result = {
                    "action": "export",
                    "agentId": args.agent_id,
                    "file": args.out,
                }
    # Both modes retain the exact field-level diff; --json also controls shared CLI errors.
    print(
        json.dumps(
            result, ensure_ascii=False, sort_keys=True, indent=None if args.json else 2
        )
    )
    return 0
