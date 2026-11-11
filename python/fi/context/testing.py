"""Whole-context tests through the public API, not a runtime-session adapter.

Use a user-bound platform Client. Consumption credentials cannot author private
paid jobs. Preview and create are intentionally separate: callers must inspect
outbound files and supply the exact fingerprint, inventory review and consent.
Run IDs, configuration and operation keys should be retained for recovery.

CLI: python -m fi.context.testing preview CONTEXT_ID --input configuration.json
     python -m fi.context.testing create CONTEXT_ID --input reviewed-request.json
         --idempotency-key UUID --acknowledge-provider-processing
Credentials use the existing FI_API_KEY/FI_SECRET_KEY environment variables.

Whole-set path (one command per decision, same server guards):
     python -m fi.context.testing plan-set CONTEXT_ID [CONTEXT_ID ...] --request TEXT
         --expect TEXT --reviewed-case [--draft | --version N] [--model ID] [--limit USD]
         [--reference N] --out plan.json
         Previews every context separately and prints each context's exact candidate,
         cost bound, outbound files and flagged files, plus one plan digest.
     python -m fi.context.testing run-set --plan plan.json --reviewed-plan DIGEST
         --reviewed-inventory --no-known-answer-keys
         --classify-flagged reference_material --reason TEXT
         --acknowledge-provider-processing
         Each context is created with its own fingerprint, inventory review, classification
         of exactly the files its preview flagged, and a retry-safe operation key. Waits
         for every run and prints each context's own status and verdicts.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import time
from pathlib import Path
from uuid import UUID, uuid5, NAMESPACE_URL

from fi.platform import Client, RequestOptions
from fi.platform._errors import APIConnectionError, APIError


class ContextTestingClient:
    """Private whole-context job lifecycle on the shared platform transport.

    No automatic preview refresh, provider acknowledgment or paid-job polling.
    Retry an uncertain create explicitly with the original key and exact body.
    """

    def __init__(self, client: Client) -> None:
        self.client = client

    @staticmethod
    def _path(context_id: str, run_id: str | None = None) -> str:
        path = f"/model-hub/skills/contexts/{UUID(context_id)}/test-runs/"
        return path if run_id is None else path + str(UUID(run_id)) + "/"

    def preview(self, context_id: str, configuration: dict) -> object:
        return self.client.request(
            "POST", self._path(context_id) + "preview/", body=configuration,
            options=RequestOptions(max_retries=0),
        )

    def create(
        self, context_id: str, *, configuration: dict,
        expected_fingerprint: str, inventory_review: dict,
        acknowledge_provider_processing: bool, idempotency_key: str,
    ) -> object:
        if acknowledge_provider_processing is not True:
            raise ValueError("Explicit provider-processing acknowledgment is required")
        if not isinstance(expected_fingerprint, str) or not re.fullmatch(
            r"sha256:[a-f0-9]{64}", expected_fingerprint
        ):
            raise ValueError("Use the exact reviewed preview fingerprint")
        return self.client.request(
            "POST", self._path(context_id), body={
                "configuration": configuration,
                "expected_fingerprint": expected_fingerprint,
                "inventory_review": inventory_review,
                "acknowledge_provider_processing": True,
            }, options=RequestOptions(
                idempotency_key=str(UUID(idempotency_key)), max_retries=0
            ),
        )

    def list(self, context_id: str, *, page: int = 1, page_size: int = 25) -> object:
        return self.client.request("GET", self._path(context_id),
                                   query={"page": page, "page_size": page_size})

    def get(self, context_id: str, run_id: str) -> object:
        return self.client.request("GET", self._path(context_id, run_id))

    def results(self, context_id: str, run_id: str, *, page: int = 1,
                page_size: int = 25) -> object:
        return self.client.request("GET", self._path(context_id, run_id) + "results/",
                                   query={"page": page, "page_size": page_size})

    def attempt(self, context_id: str, run_id: str, attempt_id: str) -> object:
        return self.client.request(
            "GET", self._path(context_id, run_id) + f"attempts/{UUID(attempt_id)}/"
        )

    def cancel(self, context_id: str, run_id: str) -> object:
        return self.client.request("POST", self._path(context_id, run_id) + "cancel/",
                                   body={}, options=RequestOptions(max_retries=0))


_CLASSIFICATIONS = ("reference_material", "evaluation_material")
_TERMINAL = {"completed", "failed", "cancelled"}


def _canonical(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def plan_digest(contexts: list[dict]) -> str:
    """Digest of exactly what the operator is shown: each context, candidate and preview."""
    shown = [{"context_id": row["context_id"], "configuration": row["configuration"],
              "fingerprint": row["fingerprint"],
              "flagged": row["flagged"], "findings": row["findings"]} for row in contexts]
    return "sha256:" + hashlib.sha256(_canonical(shown).encode()).hexdigest()


def flagged_files(preview: dict) -> list[dict]:
    """Files whose classification the reviewer must record, de-duplicated like the UI."""
    seen: dict[tuple, dict] = {}
    for bundle in preview.get("inventory", []):
        for item in bundle["files"]:
            if "evaluation_artifact" in item["flags"] or "case_overlap" in item["flags"]:
                key = (bundle["skill_id"], item["path"], item["sha256"])
                seen[key] = {"skill_id": bundle["skill_id"], "path": item["path"], "sha256": item["sha256"],
                             "flags": sorted(item["flags"])}
    return list(seen.values())


def plan_set(tests: "ContextTestingClient", context_ids: list[str], *, request: str, expect: str,
             reviewed_case: bool, version: int | None = None, model: str | None = None, limit: str = "2.00",
             reference: int | None = None) -> dict:
    """Preview every context separately. Nothing is classified, acknowledged or run."""
    if not request.strip() or not expect.strip():
        raise ValueError("A request and an expected answer are required")
    if reviewed_case is not True:
        raise ValueError("State that the request and its expected answer were reviewed")
    if not context_ids or len(set(context_ids)) != len(context_ids):
        raise ValueError("Name each context once")
    options = tests.client.request("GET", "/model-hub/skills/testing-options/")
    runnable = [row["model_id"] for row in options["models"] if row.get("can_run")]
    if model is None:
        model = runnable[0] if runnable else None
    if model not in runnable:
        raise ValueError("Choose a model this workspace can run")
    contexts = []
    for context_id in context_ids:
        base = f"/model-hub/skills/contexts/{UUID(context_id)}/"
        if version is None:
            draft = tests.client.request("GET", base + "draft/")
            candidate = {"kind": "draft", "revision": draft["revision"], "digest": draft["digest"]}
        else:
            release = tests.client.request("GET", base + f"versions/{int(version)}/inspection/")["manifest"]
            candidate = {"kind": "version", "version": int(version), "digest": release["digest"]}
        configuration = {
            "harness": "contexts-text-v1.2", "candidate": candidate,
            "cases": {"kind": "ad_hoc", "cases": [{
                "id": str(uuid5(NAMESPACE_URL, f"case:{context_id}:{request}:{expect}")),
                "title": "Reviewed context regression", "source_group_id": "manual-context-test",
                "prompt": request, "fixtures": [], "expected_trigger": None,
                "checks": [{"id": str(uuid5(NAMESPACE_URL, f"check:{context_id}:{expect}")), "kind": "contains",
                            "critical": True, "config": {"text": expect, "case_sensitive": False}}],
                "reviewed": True}]},
            "baselines": [{"kind": "version", "version": int(reference)}] if reference else [{"kind": "without_context"}],
            "competitors": [], "model": {"model_id": model, "temperature": 0, "max_output_tokens": 1024},
            "judge": None, "profile": "quick", "repetitions": 1,
            "limits": {"max_total_tokens": options["limits"]["profiles"]["quick"]["max_total_tokens"],
                       "max_estimated_cost_usd": limit},
            "purpose": "regression", "parent_run_id": None,
        }
        preview = tests.preview(context_id, configuration)
        contexts.append({
            "context_id": context_id, "configuration": configuration, "fingerprint": preview["fingerprint"],
            "attempts": preview["attempt_count"], "upper_bound_usd": preview["estimate"]["upper_bound_usd"],
            "provider": preview["provider_disclosure"]["task_provider"],
            "files": sum(len(bundle["files"]) for bundle in preview["inventory"]),
            "flagged": flagged_files(preview),
            "findings": [finding["finding_id"] for finding in preview.get("outbound_findings", [])],
        })
    return {"schema": 1, "request": request, "expect": expect, "contexts": contexts, "plan_digest": plan_digest(contexts)}


def run_set(tests: "ContextTestingClient", plan: dict, *, reviewed_plan: str,
            reviewed_inventory: bool, no_known_answer_keys: bool, classify_flagged: str | None,
            reason: str | None, acknowledge_provider_processing: bool, wait_seconds: float = 240) -> dict:
    """Create one private run per previewed context using only what the operator reviewed."""
    if plan.get("schema") != 1 or plan_digest(plan["contexts"]) != plan.get("plan_digest"):
        raise ValueError("The plan file was changed after it was previewed")
    if reviewed_plan != plan["plan_digest"]:
        raise ValueError("Review and name the exact plan digest")
    if not (reviewed_inventory and no_known_answer_keys and acknowledge_provider_processing is True):
        raise ValueError("Review the inventory, state the answer-key finding and acknowledge provider processing")
    if any(row["findings"] for row in plan["contexts"]):
        raise ValueError("Secret findings need an individual false-positive review in the full request")
    any_flagged = any(row["flagged"] for row in plan["contexts"])
    if any_flagged and (classify_flagged not in _CLASSIFICATIONS or not (reason or "").strip()):
        raise ValueError("Classify the flagged files with a reason")
    runs = []
    for row in plan["contexts"]:
        configuration = row["configuration"]
        classifications = [{"skill_id": item["skill_id"], "path": item["path"], "sha256": item["sha256"],
                            "classification": classify_flagged, "reason": reason.strip()} for item in row["flagged"]]
        fingerprint = row["fingerprint"]
        key = str(uuid5(NAMESPACE_URL, f"{plan['plan_digest']}:{row['context_id']}"))
        created = tests.create(row["context_id"], configuration=configuration, expected_fingerprint=fingerprint,
            inventory_review={"fingerprint": fingerprint, "reviewed_all_files": True, "no_known_answer_keys": True,
                              "classifications": classifications, "false_positive_secret_findings": []},
            acknowledge_provider_processing=True, idempotency_key=key)
        runs.append({"context_id": row["context_id"], "run_id": created["id"]})
    deadline = time.monotonic() + wait_seconds
    outcomes = []
    for run in runs:
        while True:
            state = tests.get(run["context_id"], run["run_id"])
            if state["status"] in _TERMINAL or time.monotonic() > deadline:
                break
            time.sleep(2)
        verdicts = []
        if state["status"] == "completed":
            for result in tests.results(run["context_id"], run["run_id"])["results"]:
                for variant in result["variants"]:
                    verdicts += [{"variant": variant["variant"], "answer": item["answer_verdict"]} for item in variant["attempts"]]
        outcomes.append({**run, "status": state["status"], "candidate_digest": state["candidate"]["digest"], "verdicts": verdicts})
    return {"plan_digest": plan["plan_digest"], "runs": outcomes}


def _set_main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="python -m fi.context.testing")
    commands = parser.add_subparsers(dest="command", required=True)
    plan = commands.add_parser("plan-set")
    plan.add_argument("context_ids", nargs="+")
    plan.add_argument("--request", required=True)
    plan.add_argument("--expect", required=True)
    plan.add_argument("--reviewed-case", action="store_true")
    source = plan.add_mutually_exclusive_group()
    source.add_argument("--draft", action="store_true")
    source.add_argument("--version", type=int)
    plan.add_argument("--model")
    plan.add_argument("--limit", default="2.00")
    plan.add_argument("--reference", type=int)
    plan.add_argument("--out", required=True, type=Path)
    run = commands.add_parser("run-set")
    run.add_argument("--plan", required=True, type=Path)
    run.add_argument("--reviewed-plan", required=True)
    run.add_argument("--reviewed-inventory", action="store_true")
    run.add_argument("--no-known-answer-keys", action="store_true")
    run.add_argument("--classify-flagged", choices=_CLASSIFICATIONS)
    run.add_argument("--reason")
    run.add_argument("--acknowledge-provider-processing", action="store_true")
    run.add_argument("--wait-seconds", type=float, default=240)
    args = parser.parse_args(argv)
    try:
        organization = str(UUID(os.environ["FI_ORGANIZATION_ID"]))
        workspace = str(UUID(os.environ["FI_WORKSPACE_ID"]))
        with Client(workspace_id=workspace, default_headers={"X-Organization-Id": organization}) as client:
            tests = ContextTestingClient(client)
            if args.command == "plan-set":
                for context_id in args.context_ids:
                    UUID(context_id)
                result = plan_set(tests, args.context_ids, request=args.request, expect=args.expect,
                                  reviewed_case=args.reviewed_case, version=args.version, model=args.model, limit=args.limit, reference=args.reference)
                args.out.write_text(json.dumps(result))
                args.out.chmod(0o600)
                print(json.dumps({"plan_digest": result["plan_digest"], "plan_file": str(args.out),
                                  "contexts": [{k: v for k, v in row.items() if k != "configuration"} for row in result["contexts"]]},
                                 ensure_ascii=False))
            else:
                text = args.plan.read_bytes()[: 2 * 1024 * 1024 + 1]
                if len(text) > 2 * 1024 * 1024:
                    raise ValueError("Plan exceeds the 2 MiB CLI limit")
                result = run_set(tests, json.loads(text), reviewed_plan=args.reviewed_plan,
                    reviewed_inventory=args.reviewed_inventory,
                    no_known_answer_keys=args.no_known_answer_keys, classify_flagged=args.classify_flagged,
                    reason=args.reason, acknowledge_provider_processing=args.acknowledge_provider_processing,
                    wait_seconds=args.wait_seconds)
                print(json.dumps(result, ensure_ascii=False))
        return 0
    except (APIConnectionError, APIError) as error:
        code = getattr(error, "code", None)
        status = getattr(error, "status_code", None)
        suffix = f" (HTTP {status}" + (f", {code}" if isinstance(code, str) and re.fullmatch(r"[a-z0-9_]{1,64}", code) else "") + ")" if isinstance(status, int) else ""
        print(f"Context test request failed{suffix}; inspect the original operation before retrying.", file=sys.stderr)
        return 1
    except (ValueError, KeyError, OSError) as error:
        # Local validation text names a missing review step, never request content.
        print(f"Invalid context test input or scoped SDK configuration: {error}"
              if isinstance(error, ValueError) else "Invalid context test input or scoped SDK configuration.", file=sys.stderr)
        return 2


def main(argv: list[str] | None = None) -> int:
    if (argv if argv is not None else sys.argv[1:])[:1] in (["plan-set"], ["run-set"]):
        return _set_main(list(argv if argv is not None else sys.argv[1:]))
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("preview", "create", "list", "get", "results", "attempt", "cancel"):
        sub = commands.add_parser(name)
        sub.add_argument("context_id")
        if name in {"get", "results", "attempt", "cancel"}:
            sub.add_argument("run_id")
        if name == "attempt":
            sub.add_argument("attempt_id")
        if name in {"preview", "create"}:
            sub.add_argument("--input", required=True, type=Path)
        if name == "create":
            sub.add_argument("--idempotency-key", required=True)
            sub.add_argument("--acknowledge-provider-processing", action="store_true")
        if name in {"list", "results"}:
            sub.add_argument("--page", type=int, default=1)
            sub.add_argument("--page-size", type=int, default=25)
    args = parser.parse_args(argv)
    try:
        UUID(args.context_id)
        body = None
        if hasattr(args, "input"):
            # A bounded JSON document, never an import or executable command.
            raw = args.input.open("rb")
            with raw:
                text = raw.read(2 * 1024 * 1024 + 1)
            if len(text) > 2 * 1024 * 1024:
                raise ValueError("Request exceeds the 2 MiB CLI limit")
            body = json.loads(text)
            if not isinstance(body, dict):
                raise ValueError("Input must be a JSON object")
        if args.command == "create" and not args.acknowledge_provider_processing:
            raise ValueError("Explicit provider-processing acknowledgment is required")
        organization = str(UUID(os.environ["FI_ORGANIZATION_ID"]))
        workspace = str(UUID(os.environ["FI_WORKSPACE_ID"]))
        with Client(workspace_id=workspace,
                    default_headers={"X-Organization-Id": organization}) as client:
            tests = ContextTestingClient(client)
            if args.command == "preview":
                result = tests.preview(args.context_id, body)
            elif args.command == "create":
                if set(body) != {"configuration", "expected_fingerprint", "inventory_review"}:
                    raise ValueError("Supply configuration, expected_fingerprint and inventory_review")
                result = tests.create(args.context_id, **body,
                    acknowledge_provider_processing=True, idempotency_key=args.idempotency_key)
            elif args.command == "list":
                result = tests.list(args.context_id, page=args.page, page_size=args.page_size)
            elif args.command == "results":
                result = tests.results(args.context_id, args.run_id,
                                       page=args.page, page_size=args.page_size)
            elif args.command == "attempt":
                result = tests.attempt(args.context_id, args.run_id, args.attempt_id)
            else:
                result = getattr(tests, args.command)(args.context_id, args.run_id)
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except (APIConnectionError, APIError) as error:
        # Server messages, details and URLs may include private request content. Keep
        # uncertain operation keys in the caller's retained input, not stderr. Only the
        # HTTP status and the machine error code (a short token) are safe to print.
        code = getattr(error, "code", None)
        status = getattr(error, "status_code", None)
        suffix = f" (HTTP {status}" + (f", {code}" if isinstance(code, str) and re.fullmatch(r"[a-z0-9_]{1,64}", code) else "") + ")" if isinstance(status, int) else ""
        print(f"Context test request failed{suffix}; inspect the original operation before retrying.", file=sys.stderr)
        return 1
    except (ValueError, KeyError, OSError):
        print("Invalid context test input or scoped SDK configuration.", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
