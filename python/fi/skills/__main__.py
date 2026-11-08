"""Standalone-skill byte verification/removal, without executing repository code.

Online leaf planning/application is deliberately not advertised until the
serializer-generated consumption source is integrated. The installer library
accepts L10's verified leaf snapshots and an explicit live authorizer today.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

from fi.context.__main__ import read_local
from fi.context.journal import Authorization, parse_plan, recover, write_plan
from fi.context.lock import InstallationError

from .installer import apply_skill_plan, plan_remove_skill, verify_skills


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("verify", "remove", "recover"):
        command = commands.add_parser(name)
        command.add_argument("--project", required=True)
        if name == "remove":
            command.add_argument("--name", required=True)
            command.add_argument("--plan", required=True)
        if name == "recover":
            command.add_argument("--quiescent", action="store_true")
    apply = commands.add_parser("apply")
    apply.add_argument("--plan", required=True)
    apply.add_argument("--quiescent", action="store_true")
    args = parser.parse_args(argv)
    try:
        status = 0
        if args.command == "verify":
            outcome = verify_skills(project=args.project)
            status = 0 if outcome["verified"] else 6
        elif args.command == "remove":
            plan = plan_remove_skill(project=args.project, name=args.name)
            write_plan(Path(args.plan), plan)
            outcome = plan.review()
        elif args.command == "recover":
            outcome = recover(args.project, quiescent=args.quiescent)
        else:
            plan = parse_plan(read_local(args.plan))
            if plan.authorizations:
                raise InstallationError(
                    "leaf_contract_unavailable",
                    "Online leaf application requires the generated consumption authorizer. Use apply_skill_plan with that bound source; no legacy route fallback is allowed.",
                    3,
                )

            def denied(auth: Authorization) -> None:
                raise InstallationError(
                    "credential_required", "Live authorization is required.", 3
                )

            apply_skill_plan(plan, authorize=denied, quiescent=args.quiescent)
            outcome = {
                "schema": 1,
                "state": "removed",
                "preserved": plan.preserved,
                "delivery": "not_observed",
            }
    except InstallationError as exc:
        outcome, status = {
            "schema": 1,
            "error": {"code": exc.code, "message": str(exc)},
        }, exc.exit_code
    except (ValueError, OSError):
        outcome, status = {
            "schema": 1,
            "error": {
                "code": "input_invalid",
                "message": "Input/filesystem validation failed. No fallback occurred.",
            },
        }, 6
    print(json.dumps(outcome, sort_keys=True))
    return status


if __name__ == "__main__":
    sys.exit(main())
