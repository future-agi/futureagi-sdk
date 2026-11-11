"""Whole-context tests through the public API, not a runtime-session adapter.

Use a user-bound platform Client. Consumption credentials cannot author private
paid jobs. Preview and create are intentionally separate: callers must inspect
outbound files and supply the exact fingerprint, inventory review and consent.
Run IDs, configuration and operation keys should be retained for recovery.

CLI: python -m fi.context.testing preview CONTEXT_ID --input configuration.json
     python -m fi.context.testing create CONTEXT_ID --input reviewed-request.json
         --idempotency-key UUID --acknowledge-provider-processing
Credentials use the existing FI_API_KEY/FI_SECRET_KEY environment variables.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from uuid import UUID

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


def main(argv: list[str] | None = None) -> int:
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
    except (APIConnectionError, APIError):
        # Server messages and URLs may include private request content. Keep
        # uncertain operation keys in the caller's retained input, not stderr.
        print("Context test request failed; inspect the original operation before retrying.", file=sys.stderr)
        return 1
    except (ValueError, KeyError, OSError):
        print("Invalid context test input or scoped SDK configuration.", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
