"""Reviewed standalone-skill installation through isolated consumption credentials."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Sequence

from fi.context.__main__ import Registry, read_local
from fi.context.doctor import doctor
from fi.context.journal import Authorization, parse_plan, recover, write_plan
from fi.context.lock import InstallationError
from fi.context.materialize import inspect_plan
from fi.context.snapshot import ResolutionExpiredError
from fi.platform import APIConnectionError, APIError

from .client import SkillsClient
from .installer import (
    apply_skill_plan,
    from_verified_snapshot,
    plan_install_skill,
    plan_remove_skill,
    read_ownership,
    retained_identity,
    verify_skills,
)


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--json", action="store_true")
    commands = result.add_subparsers(dest="command", required=True)
    for name in ("plan", "update", "restore", "verify", "remove", "recover", "doctor"):
        command = commands.add_parser(name)
        command.add_argument("--project", required=True)
        if name in ("plan", "update", "restore", "remove"):
            command.add_argument("--name", required=True)
            command.add_argument(
                "--plan", "--out", dest="out", required=name != "update"
            )
        if name in ("plan", "update", "restore"):
            command.add_argument("--allow-preview", action="store_true")
        if name == "plan":
            command.add_argument(
                "--client", choices=["codex", "claude-code"], required=True
            )
            selector = command.add_mutually_exclusive_group()
            selector.add_argument("--label")
            selector.add_argument("--version", type=int)
        if name == "update":
            command.add_argument("--check", action="store_true")
        if name == "restore":
            command.add_argument(
                "--lock",
                required=True,
                help="Retained v1 skill lock; current ownership is also required.",
            )
        if name == "recover":
            command.add_argument("--quiescent", action="store_true")
    apply = commands.add_parser("apply")
    apply.add_argument("--plan", required=True)
    apply.add_argument("--quiescent", action="store_true")
    inspect = commands.add_parser("inspect")
    inspect.add_argument("--plan", required=True)
    inspect.add_argument("--diff", action="store_true")
    return result


def execute(args: argparse.Namespace) -> tuple[dict[str, object], int]:
    registry: Registry | None = None
    try:
        if args.command == "verify":
            outcome = verify_skills(project=args.project)
            return outcome, 0 if outcome["verified"] else 6
        if args.command == "doctor":
            return doctor(project=args.project), 0
        if args.command == "recover":
            return recover(args.project, quiescent=args.quiescent), 0
        if args.command == "inspect":
            return (
                inspect_plan(parse_plan(read_local(args.plan)), include_diff=args.diff),
                0,
            )
        if args.command == "apply":
            plan = parse_plan(read_local(args.plan))
            if plan.authorizations:
                registry = Registry()

            def authorize(auth: Authorization) -> None:
                if registry is None:
                    raise InstallationError(
                        "configuration_required", "Live authorization is required.", 3
                    )
                registry.authorize(auth)

            apply_skill_plan(plan, authorize=authorize, quiescent=args.quiescent)
            return {
                "schema": 1,
                "state": "removed" if plan.operation == "remove" else "installed",
                "plan_digest": plan.plan_digest,
                "preserved": plan.preserved,
                "discovery": "not_observed",
                "delivery": "not_observed",
            }, 0
        if args.command == "remove":
            plan = plan_remove_skill(project=args.project, name=args.name)
        else:
            if not args.out and not (args.command == "update" and args.check):
                raise InstallationError(
                    "plan_path_required", "Choose a private --plan output file.", 2
                )
            registry = Registry()
            current = None
            if args.command == "plan":
                profile, label, version = args.client, args.label, args.version
            else:
                ownership = read_ownership(project=args.project)
                matches = [s for s in ownership.skills if s.identity.name == args.name]
                if len(matches) != 1:
                    raise InstallationError(
                        "ownership_missing", "The project does not own this skill.", 5
                    )
                current = matches[0].identity
                registry.check_scope(current)
                profile = ownership.profile
                if args.command == "restore":
                    current = retained_identity(read_local(args.lock), current)
                    label, version = None, current.version
                else:
                    label, version = current.requested.label, current.requested.version
            verified = (
                SkillsClient(registry.client)
                .resolve(args.name, label=label, version=version)
                .read_all()
            )
            bundle = from_verified_snapshot(
                verified,
                origin=registry.origin,
                organization_id=registry.organization_id,
                workspace_id=registry.workspace_id,
            )
            if current is not None:
                if bundle.identity.skill_id != current.skill_id:
                    raise InstallationError(
                        "identity_collision",
                        "The name now resolves to another skill UUID.",
                        6,
                    )
                if args.command == "restore":
                    if (bundle.identity.version_id, bundle.identity.digest) != (
                        current.version_id,
                        current.digest,
                    ):
                        raise InstallationError(
                            "integrity_failure",
                            "Exact restore differs from the retained lock.",
                            6,
                        )
                    bundle = bundle.model_copy(update={"identity": current})
                elif args.check:
                    changed = (bundle.identity.version_id, bundle.identity.digest) != (
                        current.version_id,
                        current.digest,
                    )
                    return {
                        "schema": 1,
                        "update_available": changed,
                        "requested": current.requested.wire(),
                        "current_version_id": current.version_id,
                        "resolved_version_id": bundle.identity.version_id,
                    }, (8 if changed else 0)
            plan = plan_install_skill(
                bundle,
                project=args.project,
                profile=profile,
                allow_preview=args.allow_preview,
                operation="install" if args.command == "plan" else args.command,
            )
        write_plan(Path(args.out), plan)
        return plan.review(), 0
    finally:
        if registry is not None:
            registry.close()


def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        outcome, status = execute(args)
    except InstallationError as exc:
        outcome, status = {
            "schema": 1,
            "error": {"code": exc.code, "message": str(exc)},
        }, exc.exit_code
    except ResolutionExpiredError:
        outcome, status = {
            "schema": 1,
            "error": {
                "code": "resolution_expired",
                "message": "The original lease expired; explicitly replan.",
            },
        }, 3
    except APIError as exc:
        code = str(getattr(exc, "code", "transport_error"))
        code = code if re.fullmatch(r"[a-z_]{1,80}", code) else "transport_error"
        outcome, status = {
            "schema": 1,
            "error": {
                "code": code,
                "message": "Registry request failed. No fallback or re-resolution occurred.",
            },
        }, (3 if exc.status_code in (401, 403) else 4)
    except APIConnectionError:
        outcome, status = {
            "schema": 1,
            "error": {
                "code": "transport_error",
                "message": "Registry transport failed. No fallback occurred.",
            },
        }, 4
    except ValueError:
        outcome, status = {
            "schema": 1,
            "error": {
                "code": "integrity_failure",
                "message": "Input or immutable content validation failed.",
            },
        }, 6
    except OSError:
        outcome, status = {
            "schema": 1,
            "error": {
                "code": "filesystem_error",
                "message": "Filesystem operation failed; inspect doctor/recover before retry.",
            },
        }, 5
    print(json.dumps(outcome, sort_keys=True))
    return status


if __name__ == "__main__":
    sys.exit(main())
