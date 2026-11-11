"""LangChain's standard sandbox tests (``SandboxIntegrationTests``) against a real sandbox.

Opt-in only: it runs when ``FI_E2E_REQUIRED=1`` and the sandbox environment are set (``OMEGA_BASE_URL``
plus ``FI_API_KEY`` and ``FI_SECRET_KEY``, or ``FUTUREAGI_OMEGA_API_KEY``) and when ``deepagents`` and
``langchain-tests`` are installed (``futureagi[sandbox-deepagents]`` and the test package). One sandbox is
created for the class and deleted after it. ``FI_SANDBOX_TEMPLATE`` picks its template (the
deployment's default otherwise). Building the backend fails first when the template has no python3.
The standard tests' files live under ``/workspace/test_sandbox_ops/``, the folder the files API
reaches. ``test_futureagi_edit_over_50_kb`` is expected to fail until large edits work (see the
README's "Not supported").
"""

from __future__ import annotations

import os
import sys

import pytest

if os.environ.get("FI_E2E_REQUIRED") != "1":
    pytest.skip("live sandbox tests require explicit opt-in: set FI_E2E_REQUIRED=1", allow_module_level=True)
if not os.environ.get("OMEGA_BASE_URL") or not (
    os.environ.get("FUTUREAGI_OMEGA_API_KEY")
    or (os.environ.get("FI_API_KEY") and os.environ.get("FI_SECRET_KEY"))
):
    pytest.skip(
        "live sandbox tests need OMEGA_BASE_URL and FI_API_KEY + FI_SECRET_KEY or FUTUREAGI_OMEGA_API_KEY",
        allow_module_level=True,
    )
if sys.version_info < (3, 11):
    pytest.skip("Deep Agents needs Python 3.11+", allow_module_level=True)

pytest.importorskip("deepagents")
integration_tests = pytest.importorskip("langchain_tests.integration_tests")

from fi.sandbox import Sandbox  # noqa: E402
from fi.sandbox_integrations.deepagents import FutureAGISandbox  # noqa: E402


class TestFutureAGISandboxStandard(integration_tests.SandboxIntegrationTests):
    @property
    def sandbox_root_dir(self) -> str:
        # The files API (upload_files, download_files) reaches files under /workspace only, so the
        # standard tests' files go there instead of their default /tmp root.
        return "/workspace/test_sandbox_ops/"

    @pytest.fixture(scope="class")
    def sandbox(self):
        sbx = Sandbox.create(
            name="deepagents-standard-tests", template=os.environ.get("FI_SANDBOX_TEMPLATE") or None
        )
        try:
            yield FutureAGISandbox(sandbox=sbx)
        finally:
            try:
                sbx.delete()
            finally:
                sbx.close()

    @pytest.mark.xfail(
        strict=True,
        reason="Deep Agents stages an edit over 50,000 bytes in /tmp through upload_files, which "
        "reaches /workspace only; remove this mark once large edits are staged where the files "
        "API reaches",
    )
    def test_futureagi_edit_over_50_kb(self, sandbox) -> None:
        path = self.sandbox_root_dir.rstrip("/") + "/test_futureagi_edit_over_50_kb/large_edit.txt"
        old = "a" * 30_000
        new = "b" * 30_000
        written = sandbox.write(path, f"start\n{old}\nend\n")
        assert written.error is None
        edited = sandbox.edit(path, old, new)
        assert edited.error is None
        content = sandbox.download_files([path])[0].content
        assert content == f"start\n{new}\nend\n".encode()
