"""python -m fi.context: explicit plan/apply and read-only byte diagnostics.

Registry requests use only the shared platform Client and L10 snapshot engine.
Credentials are environment-only; private plans never contain credential secrets.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Sequence

from pydantic import ValidationError

from fi.platform import Client, ContextAuth, RequestOptions
from fi.platform._errors import APIConnectionError, APIError

from .doctor import doctor
from .journal import Authorization, SafeProject, parse_plan, recover, write_plan
from .lock import CONTEXT_LOCK, Identity, InstallationError, SourceBundle, parse_lock
from .materialize import (
    apply_plan,
    from_verified_snapshot,
    inspect_plan,
    plan_install,
    plan_remove,
    verify,
)


class Registry:
    """A configured origin/scope, never an origin taken on trust from a plan."""

    def __init__(self) -> None:
        self.origin = self._required("FI_CONTEXT_ORIGIN").rstrip("/")
        self.organization_id = self._required("FI_CONTEXT_ORGANIZATION_ID")
        self.workspace_id = self._required("FI_CONTEXT_WORKSPACE_ID")
        credential = self._required("FI_CONTEXT_CREDENTIAL")
        self.client = Client(
            auth=ContextAuth(credential),
            base_url=self.origin,
            workspace_id=self.workspace_id,
        )

    @staticmethod
    def _required(name: str) -> str:
        value = os.getenv(name)
        if not value:
            raise InstallationError(
                "configuration_required",
                f"Set {name}; broad API-key variables are not used.",
                3,
            )
        return value

    def close(self) -> None:
        self.client.close()

    def check_scope(self, identity: Identity) -> None:
        if (identity.origin, identity.organization_id, identity.workspace_id) != (
            self.origin,
            self.organization_id,
            self.workspace_id,
        ):
            raise InstallationError(
                "scope_conflict",
                "Configured registry scope differs from the reviewed lock/plan.",
                3,
            )

    def resolve(
        self, name: str, *, label: str | None = None, version: int | None = None
    ) -> SourceBundle:
        try:
            from .client import ContextClient
            from .snapshot import ResolutionExpiredError
        except ImportError as exc:
            raise InstallationError(
                "snapshot_client_unavailable",
                "The integrated L10 snapshot package is required for registry consumption.",
                3,
            ) from exc
        try:
            snapshot = (
                ContextClient(self.client)
                .resolve(name, label=label, version=version)
                .read_all()
            )
        except ResolutionExpiredError as exc:
            raise InstallationError(
                "resolution_expired",
                "Resolution expired; discard incomplete staging and explicitly replan.",
                3,
            ) from exc
        return from_verified_snapshot(
            snapshot,
            origin=self.origin,
            organization_id=self.organization_id,
            workspace_id=self.workspace_id,
        )

    def authorize(self, authorization: Authorization) -> None:
        """Immutable manifest continuation is the live authorization check.

        Recheck every page with the original lease; never renew or resolve latest.
        The backend must enforce the full quarantine closure on this read.
        """
        if authorization.kind != "agent_context" or not isinstance(
            authorization.identity, Identity
        ):
            raise InstallationError(
                "leaf_contract_unavailable",
                "The generated leaf-consumption source must supply standalone-skill authorization.",
                3,
            )
        self.check_scope(authorization.identity)
        try:
            from .snapshot import ManifestCollector, ResolutionExpiredError
        except ImportError as exc:
            raise InstallationError(
                "snapshot_client_unavailable",
                "The integrated L10 snapshot package is required.",
                3,
            ) from exc
        identity = authorization.identity
        authorization.lease.require_live()
        path = f"/model-hub/skills/contexts/{identity.context_id}/versions/{identity.version}/manifest/"
        options = RequestOptions(resolution_id=authorization.lease.resolution_id)
        first = self.client.request(
            "GET", path, query={"file_offset": 0, "file_limit": 25}, options=options
        )
        # Continuations may omit lease fields; retain the original plan's lease.
        if not isinstance(first, dict):
            raise InstallationError(
                "integrity_failure", "Invalid immutable authorization response.", 6
            )
        if "resolution_id" not in first and "resolution_expires_at" not in first:
            first = {**first, **authorization.lease.model_dump()}
        collector = ManifestCollector(first, kind="agent_context")
        if (
            collector.identity.resource_id,
            collector.identity.version,
            collector.identity.version_id,
            collector.identity.digest,
        ) != (
            identity.context_id,
            identity.version,
            identity.version_id,
            identity.digest,
        ):
            raise InstallationError(
                "integrity_failure",
                "Authorization returned another immutable release.",
                6,
            )
        if collector.lease.resolution_id != authorization.lease.resolution_id:
            raise InstallationError(
                "integrity_failure",
                "Authorization substituted the resolution lease.",
                6,
            )
        while collector.next_offset is not None:
            authorization.lease.require_live()
            page = self.client.request(
                "GET",
                path,
                query={"file_offset": collector.next_offset, "file_limit": 25},
                options=options,
            )
            collector.add(page)
        try:
            collector.finish()
        except ResolutionExpiredError as exc:
            raise InstallationError(
                "resolution_expired",
                "The original installation lease expired; explicitly replan.",
                3,
            ) from exc
        authorization.lease.require_live()


def read_local(path: str | Path) -> bytes:
    absolute = Path(os.path.abspath(path))
    with SafeProject(absolute.parent) as filesystem:
        raw = filesystem.read(absolute.name)
    if raw is None:
        raise InstallationError(
            "input_missing", "The requested local file does not exist.", 2
        )
    return raw


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(
        description="Reviewed project context installation. Native profiles are preview, not delivery evidence."
    )
    result.add_argument(
        "--json", action="store_true", help="Versioned JSON is also the default output."
    )
    commands = result.add_subparsers(dest="command", required=True)
    make = commands.add_parser("plan")
    make.add_argument("--name", required=True)
    select = make.add_mutually_exclusive_group()
    select.add_argument("--label")
    select.add_argument("--version", type=int)
    make.add_argument("--client", choices=["codex", "claude-code"], required=True)
    make.add_argument("--project", required=True)
    make.add_argument("--adopt-local", action="store_true")
    make.add_argument("--allow-preview", action="store_true")
    make.add_argument("--out", "--plan", dest="out", required=True)
    apply = commands.add_parser("apply")
    apply.add_argument("--plan", required=True)
    apply.add_argument("--quiescent", action="store_true")
    inspection = commands.add_parser("inspect")
    inspection.add_argument("--plan", required=True)
    inspection.add_argument(
        "--diff",
        action="store_true",
        help="Explicitly print bounded source/local text diffs.",
    )
    for name in ("update", "restore", "remove", "verify", "doctor"):
        command = commands.add_parser(name)
        command.add_argument("--lock", default=CONTEXT_LOCK)
        command.add_argument("--project")
        if name in ("update", "restore", "remove"):
            command.add_argument("--plan", "--out", dest="out")
        if name in ("update", "restore"):
            command.add_argument("--allow-preview", action="store_true")
        if name == "update":
            command.add_argument("--check", action="store_true")
    recovery = commands.add_parser("recover")
    recovery.add_argument("--project", required=True)
    recovery.add_argument("--quiescent", action="store_true")
    return result


def execute(args: argparse.Namespace) -> tuple[dict[str, object], int]:
    registry: Registry | None = None
    try:
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

            apply_plan(plan, authorize=authorize, quiescent=args.quiescent)
            return {
                "schema": 1,
                "state": "removed" if plan.operation == "remove" else "installed",
                "plan_digest": plan.plan_digest,
                "preserved": plan.preserved,
                "discovery": "not_observed",
                "delivery": "not_observed",
            }, 0
        if args.command == "plan":
            registry = Registry()
            source = registry.resolve(args.name, label=args.label, version=args.version)
            plan = plan_install(
                source,
                project=args.project,
                profile=args.client,
                adopt_local=args.adopt_local,
                allow_preview=args.allow_preview,
            )
        else:
            project = (
                Path(args.project)
                if args.project
                else Path(os.path.abspath(args.lock)).parent
            )
            if args.command == "doctor":
                return doctor(project=project), 0
            lock = parse_lock(read_local(args.lock))
            if args.command == "verify":
                outcome = verify(project=project, lock=lock)
                return outcome, 0 if outcome["verified"] else 6
            if args.command == "remove":
                # Removal uses the current project's ownership, not a stale external lock.
                with SafeProject(project) as filesystem:
                    if filesystem.read(CONTEXT_LOCK) != read_local(args.lock):
                        raise InstallationError(
                            "stale_plan", "Removal requires the current project lock."
                        )
                plan = plan_remove(project=project)
            else:
                registry = Registry()
                registry.check_scope(lock)
                if args.command == "restore":
                    source = registry.resolve(lock.name, version=lock.version)
                    if (
                        source.identity.version_id,
                        source.identity.digest,
                        source.identity.context_id,
                    ) != (lock.version_id, lock.digest, lock.context_id):
                        raise InstallationError(
                            "integrity_failure",
                            "Exact restore differs from the retained lock.",
                            6,
                        )
                    # Preserve the reviewed follow/pin policy, but retrieve exact bytes.
                    source = source.model_copy(
                        update={
                            "identity": source.identity.model_copy(
                                update={"requested": lock.requested}
                            )
                        }
                    )
                else:
                    source = registry.resolve(
                        lock.name,
                        label=lock.requested.label,
                        version=lock.requested.version,
                    )
                    if args.check:
                        changed = (
                            source.identity.version_id,
                            source.identity.digest,
                        ) != (lock.version_id, lock.digest)
                        return {
                            "schema": 1,
                            "update_available": changed,
                            "requested": lock.requested.wire(),
                            "current_version_id": lock.version_id,
                            "resolved_version_id": source.identity.version_id,
                        }, (8 if changed else 0)
                plan = plan_install(
                    source,
                    project=project,
                    profile=lock.materialization.profile,
                    allow_preview=args.allow_preview,
                    operation=args.command,
                )
        if not args.out:
            raise InstallationError(
                "plan_path_required",
                "Choose a private --plan output file before applying changes.",
                2,
            )
        write_plan(Path(args.out), plan)
        return plan.review(), 0
    finally:
        if registry is not None:
            registry.close()


def main(argv: Sequence[str] | None = None) -> int:
    try:
        args = parser().parse_args(argv)
        outcome, status = execute(args)
    except InstallationError as exc:
        outcome, status = {
            "schema": 1,
            "error": {"code": exc.code, "message": str(exc)},
        }, exc.exit_code
    except APIError as exc:
        # Never echo arbitrary response bodies, request headers or signed URLs.
        code = str(getattr(exc, "code", "transport_error"))
        code = code if re.fullmatch(r"[a-z_]{1,80}", code) else "transport_error"
        status_code = getattr(exc, "status_code", None)
        status = 3 if status_code in (401, 403) else 4
        outcome = {
            "schema": 1,
            "error": {
                "code": code,
                "message": "Registry request failed. No fallback or automatic re-resolution occurred.",
            },
        }
    except APIConnectionError:
        outcome, status = {
            "schema": 1,
            "error": {
                "code": "transport_error",
                "message": "Registry transport failed. No fallback occurred.",
            },
        }, 4
    except (ValidationError, ValueError, UnicodeError):
        # Validation exceptions can contain submitted bytes: never print them.
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
