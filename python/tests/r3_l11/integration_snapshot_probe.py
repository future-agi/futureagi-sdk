"""Run explicitly after integrating L10's actual snapshot files.

This exercises the real L10 engine, SDK-F transport, and CLI against transport-
boundary fixtures. It fails if the prerequisite package is missing; no skip or
fabricated leaf route is used. It is not a live-backend acceptance claim.
"""

from __future__ import annotations

import contextlib
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import httpx
from fi.context.__main__ import main
from fi.context.client import ContextClient
from fi.context.lock import sha256
from fi.platform import Client as PlatformClient
from test_materializer import bundle


class SnapshotMaterializationContract(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="fi-l11-contract-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.home, self.project = self.root / "home", self.root / "repo"
        self.home.mkdir()
        self.project.mkdir()
        self.source = bundle(
            extra={
                **{
                    f"references/file-{i:02d}.md": f"Reference {i}".encode()
                    for i in range(30)
                },
                "references/unicode.md": ("雪🐍" * 18000).encode(),
            }
        )
        self.requests = []
        self.revoked = False
        self.env = patch.dict(
            os.environ,
            {
                "HOME": str(self.home),
                "FI_CONTEXT_ORIGIN": self.source.identity.origin,
                "FI_CONTEXT_ORGANIZATION_ID": self.source.identity.organization_id,
                "FI_CONTEXT_WORKSPACE_ID": self.source.identity.workspace_id,
                "FI_CONTEXT_CREDENTIAL": "synthetic-only-credential",
                "FI_API_KEY": "stale-broad-key",
                "FI_SECRET_KEY": "stale-broad-secret",
                "FI_WORKSPACE_ID": "stale-workspace",
            },
        )
        self.env.start()
        self.addCleanup(self.env.stop)

    def response(self, request):
        self.requests.append(request)
        self.assertEqual(
            request.headers["Authorization"], "Context synthetic-only-credential"
        )
        self.assertEqual(
            request.headers["X-Workspace-Id"], self.source.identity.workspace_id
        )
        self.assertNotIn("X-Api-Key", request.headers)
        self.assertNotIn("X-Secret-Key", request.headers)
        identity = self.source.identity
        prefix = "/model-hub/skills/contexts/"
        resolving = request.url.path == prefix + "resolve/"
        if not resolving:
            self.assertEqual(
                request.headers["X-Context-Resolution"], self.source.lease.resolution_id
            )
            if self.revoked:
                return httpx.Response(
                    403,
                    json={
                        "status": False,
                        "code": "context_credential_revoked",
                        "message": "Synthetic revocation",
                    },
                )
        version_prefix = f"{prefix}{identity.context_id}/versions/{identity.version}/"
        self.assertTrue(resolving or request.url.path.startswith(version_prefix))
        if resolving or request.url.path == version_prefix + "manifest/":
            files = [
                {"path": p, "sha256": sha256(b), "size_bytes": len(b)}
                for p, b in sorted(self.source.files.items())
            ]
            offset = int(request.url.params.get("file_offset", 0))
            size = int(request.url.params.get("file_limit", 25))
            result = {
                "resource_id": identity.context_id,
                "kind": "agent_context",
                "name": identity.name,
                "description": "Reviewed policy",
                "version": identity.version,
                "version_id": identity.version_id,
                "digest": identity.digest,
                "requested": (
                    {"label": "production"}
                    if resolving
                    else {"version": identity.version}
                ),
                "entrypoint": "AGENTS.md",
                "descriptor_path": ".futureagi/context.json",
                "file_count": len(files),
                "file_offset": offset,
                "next_file_offset": (
                    offset + size if offset + size < len(files) else None
                ),
                "files": files[offset : offset + size],
            }
            if resolving:
                result.update(self.source.lease.model_dump())
        else:
            self.assertEqual(request.url.path, version_prefix + "files/")
            path = request.url.params["path"]
            offset = int(request.url.params.get("offset", 0))
            content = self.source.files[path]
            text = content.decode()
            chunk = (
                text[offset:]
                .encode("utf-8")[: int(request.url.params["max_bytes"])]
                .decode("utf-8", errors="ignore")
            )
            end = offset + len(chunk)
            result = {
                "path": path,
                "sha256": sha256(content),
                "size_bytes": len(content),
                "total_chars": len(text),
                "offset": offset,
                "next_offset": end if end < len(text) else None,
                "eof": end == len(text),
                "text": chunk,
                "resource_id": identity.context_id,
                "kind": "agent_context",
                "version_id": identity.version_id,
                "digest": identity.digest,
            }
        return httpx.Response(200, json={"status": True, "result": result})

    def client(self, **kwargs):
        return PlatformClient(
            **kwargs,
            http_client=httpx.Client(transport=httpx.MockTransport(self.response)),
        )

    def invoke(self, arguments):
        output = io.StringIO()
        with patch(
            "fi.context.__main__.Client", self.client
        ), contextlib.redirect_stdout(output):
            status = main(arguments)
        return status, json.loads(output.getvalue())

    def planned(self):
        path = self.root / "install.json"
        status, output = self.invoke(
            [
                "plan",
                "--name",
                "team-policy",
                "--client",
                "codex",
                "--project",
                str(self.project),
                "--out",
                str(path),
                "--allow-preview",
            ]
        )
        self.assertEqual(status, 0, output)
        self.assertNotIn("synthetic-only-credential", path.read_text())
        return path

    def test_real_snapshot_to_cli_plan_and_apply_retains_lease_and_exact_identity(self):
        self.assertTrue(ContextClient)
        plan = self.planned()
        status, output = self.invoke(["apply", "--plan", str(plan), "--quiescent"])
        self.assertEqual(status, 0, output)
        self.assertEqual(
            sum(request.url.path.endswith("/resolve/") for request in self.requests), 1
        )
        manifest_requests = [
            request
            for request in self.requests
            if request.url.path.endswith("/manifest/")
        ]
        self.assertGreaterEqual(len(manifest_requests), 3)
        lock = json.loads((self.project / ".futureagi-context.lock.json").read_bytes())
        self.assertEqual(lock["version_id"], self.source.identity.version_id)
        self.assertEqual(lock["digest"], self.source.identity.digest)
        self.assertEqual(len(lock["files"]), len(self.source.files))
        status, output = self.invoke(
            ["verify", "--lock", str(self.project / ".futureagi-context.lock.json")]
        )
        self.assertEqual(status, 0, output)
        self.assertEqual(output["delivery"], "not_observed")

    def test_revocation_between_plan_and_apply_changes_no_files(self):
        plan = self.planned()
        self.revoked = True
        status, output = self.invoke(["apply", "--plan", str(plan), "--quiescent"])
        self.assertEqual(status, 3, output)
        self.assertEqual(output["error"]["code"], "context_credential_revoked")
        self.assertEqual(list(self.project.iterdir()), [])
        self.assertEqual(
            sum(request.url.path.endswith("/resolve/") for request in self.requests), 1
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
