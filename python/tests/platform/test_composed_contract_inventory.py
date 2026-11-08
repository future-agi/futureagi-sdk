"""The composed inventory exercises public handles and proves hidden roots absent."""
import asyncio
import copy
import json

import pytest

from ._contract_public import method_at, public_path
from ._contract_runtime import Runtime, success
from ._gates_support import REPO
from .test_operation_contracts import check_wire
from ._console_absence import assert_console_absent

DATA = json.loads((REPO / "tests/fixtures/contracts/operations.json").read_text())
INPUTS = json.loads((REPO / "openapi/contract-inputs.json").read_text())


def approvals():
    return copy.deepcopy(next(row for row in DATA["operations"] if row["id"] == "platform:runs.approvals"))


@pytest.mark.parametrize("mode", ["sync", "async"])
@pytest.mark.parametrize("declaration", INPUTS["namespace_absences"], ids=lambda row: row["id"])
def test_hidden_namespace_declaration_requires_real_absence(mode, declaration):
    async def run():
        subject = Runtime(approvals(), mode, lambda _: pytest.fail("absence must not request"))
        try:
            assert declaration["status"] == "NOT-OFFERED"
            assert declaration["owner"] and declaration["reason"]
            for path in declaration["py"]:
                assert path.startswith("client.") and path.count(".") == 1
                assert not hasattr(subject.client, path.split(".")[1]), path
        finally:
            await subject.close()
    asyncio.run(run())


@pytest.mark.parametrize("mode", ["sync", "async"])
def test_run_fixture_uses_public_factory_and_real_approval_method(mode):
    row = approvals()
    async def run():
        requests = []
        subject = Runtime(row, mode, lambda request: requests.append(request) or success(row))
        try:
            if row.get("public_absence"):
                assert_console_absent(subject)
                assert requests == []
                return
            await subject.prepare()
            assert len(subject.setup_requests) == 1
            assert requests == []
            assert callable(method_at(subject.client, public_path(subject.row), subject.handles))
            await subject.call()
            await subject.call()
            assert len(subject.setup_requests) == 1
            assert len(requests) == 2
            for request in requests:
                check_wire(row, request)
            assert not hasattr(subject.handles["Run"], "decide")
        finally:
            await subject.close()
    asyncio.run(run())


@pytest.mark.parametrize("mode", ["sync", "async"])
@pytest.mark.parametrize("mutation", ["missing_fixture", "missing_method", "misroute", "factory_misroute"])
def test_broken_run_public_dispatch_is_not_masked(mode, mutation):
    row = approvals()
    async def run():
        requests = []
        subject = Runtime(row, mode, lambda request: requests.append(request) or success(row))
        try:
            if row.get("public_absence"):
                assert_console_absent(subject)
                assert requests == []
                return
            if mutation == "missing_fixture":
                row["handle_fixtures"] = {}
                subject.row["handle_fixtures"] = {}
                with pytest.raises(ValueError, match="public handle fixture required"):
                    await subject.call()
                assert not requests and not subject.setup_requests
                return
            if mutation == "factory_misroute":
                # Mutate the fixture's public factory path, not the executor.
                subject.row["handle_fixtures"]["Run"]["py"]["path"] = "client.agents.runs.delete"
                with pytest.raises(AssertionError):
                    await subject.prepare()
                assert not requests
                return
            await subject.prepare()
            handle = subject.handles["Run"]
            object.__setattr__(handle, "approvals", None if mutation == "missing_method" else handle.cancel)
            if mutation == "missing_method":
                with pytest.raises(TypeError, match="callable"):
                    await subject.call()
                assert not requests
            else:
                await subject.call()
                assert len(requests) == 1
                with pytest.raises(AssertionError):
                    check_wire(row, requests[0])
        finally:
            await subject.close()
    asyncio.run(run())


def test_composed_namespaces_are_scheduled_in_all_three_modes():
    required = {"platform:runs.approvals", "platform:runs.events", "platform:platform.agents.roster",
                "platform:platform.environments.list", "platform:platform.schedules.list",
                "catalog:models.list", "core:tracing.traces"}
    features = json.loads((REPO / "openapi/connectors/features.json").read_text())
    hidden = {row["id"] for row in DATA["operations"] if row.get("public_absence")}
    for mode, ids in DATA["public_cases"].items():
        assert required - hidden <= set(ids)
        assert not (required & hidden & set(ids))
        assert required & hidden <= {row["id"] for row in DATA["not_offered"][mode]}
        assert ("platform:platform.credentials.list" in ids) is features["credential_reads"]
        assert any(case.startswith("connectors:connectors.") for case in ids) is features["mcp_core"]
        assert any(case.startswith("connectors:integrations_") for case in ids) is features["data_integrations"]
        assert any(case.startswith("tracing:") for case in ids)
    assert DATA["namespace_absences"] == INPUTS["namespace_absences"]


@pytest.mark.parametrize("mode", ["sync", "async"])
def test_hidden_connector_features_require_real_absence(mode):
    async def run():
        subject = Runtime(approvals(), mode, lambda _: pytest.fail("absence must not request"))
        try:
            for declaration in DATA["feature_absences"]:
                assert declaration["status"] == "NOT-OFFERED"
                assert declaration["owner"] and declaration["reason"]
                parts = declaration["py"].split(".")
                assert parts[0] == "client"
                owner = subject.client
                for part in parts[1:-1]:
                    owner = getattr(owner, part)
                assert not hasattr(owner, parts[-1]), declaration["py"]
        finally:
            await subject.close()
    asyncio.run(run())
