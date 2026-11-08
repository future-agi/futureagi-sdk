"""The unreleased simulation family is absent, not a callable placeholder."""

import functools
import importlib
import importlib.util
import json
import re
from pathlib import Path

import pytest

from fi import AsyncFutureAGIClient, FutureAGIClient

ROOT = Path(__file__).resolve().parents[2]
SUBNAMESPACES = (
    "agent_definitions", "run_tests", "test_executions", "personas", "scenarios"
)
CLASSES = (
    "SimulationsClient", "SimulationAgentDefinitionsClient", "SimulationRunTestsClient",
    "SimulationTestExecutionsClient", "SimulationPersonasClient", "SimulationScenariosClient",
)
COMMON = {
    "agents", "annotation_labels", "connectors", "credentials", "environments",
    "experiment_runs", "gateway", "integrations", "knowledge_bases", "models",
    "optimizations", "prompts", "scores", "tracing", "workspaces",
}
SYNC_ONLY = {"alerts", "annotation_queues", "datasets", "evals", "experiments", "experiments_v2", "users"}


@pytest.mark.parametrize("client_class", [FutureAGIClient, AsyncFutureAGIClient])
def test_simulation_namespace_is_absent(client_class):
    original = client_class("fixture-api", "fixture-secret", base_url="http://localhost:9031")
    for client in (original, original.with_options(timeout=2)):
        assert not hasattr(client, "simulations")
        for namespace in SUBNAMESPACES:
            assert not hasattr(client, namespace)
            with pytest.raises(AttributeError):
                getattr(getattr(client, "simulations"), namespace)


@pytest.mark.parametrize("client_class", [FutureAGIClient, AsyncFutureAGIClient])
def test_other_namespace_snapshot(client_class):
    client = client_class("fixture-api", "fixture-secret", base_url="http://localhost:9031")
    expected = COMMON | (SYNC_ONLY if client_class is FutureAGIClient else set())
    for instance in (client, client.with_options(timeout=2)):
        properties = {
            name for name, value in vars(client_class).items() if isinstance(value, (property, functools.cached_property))
        }
        names = (set(vars(instance)) | properties) - {"base_url", "generated_client", "auth", "api_key", "secret_key"}
        assert {name for name in names if not name.startswith("_")} == expected


@pytest.mark.parametrize("module_name", ["fi", "fi.futureagi_client", "fi.futureagi_async_client"])
def test_simulation_facades_are_not_importable(module_name):
    module = importlib.import_module(module_name)
    for name in CLASSES:
        assert not hasattr(module, name)
        assert not hasattr(module, "Async" + name)


def test_generated_simulation_operations_are_absent():
    spec = json.loads((ROOT / "openapi/sdk/generated/futureagi-sdk.openapi.json").read_text())
    assert not [path for path in spec["paths"] if path.startswith(("/simulate/", "/sdk/api/v1/simulation/"))]
    for name in ("simulate", "scenarios", "simulations", *("simulation_" + name for name in SUBNAMESPACES)):
        assert importlib.util.find_spec(f"fi.generated.openapi_client.api.{name}") is None
    for source in (ROOT / "python/fi/generated/openapi_client/api").rglob("*.py"):
        assert '"/simulate/' not in source.read_text()
        assert '"/sdk/api/v1/simulation/' not in source.read_text()


def test_wrapper_map_has_no_simulation_entries():
    mapping = json.loads((ROOT / "openapi/sdk/wrapper-map.json").read_text())
    assert not [name for name in mapping if name.lower().startswith("simulation")]


@pytest.mark.parametrize("path", ["python/README.md", "typescript/futureagi/README.md"])
def test_readme_does_not_offer_simulations(path):
    assert "client.simulations" not in (ROOT / path).read_text()


WITHDRAWAL_NOTICE = "### Not in this release\n\n- Simulation APIs are not offered in this release."
FACADE_SCOPE_NOTICE = (
    "### Simulation facade scope\n\n"
    "- Only the Python `fi.simulate` facade is withdrawn; its clear-error stub points\n"
    "  to `fi.alk.simulate`. The released Python and TypeScript platform clients keep\n"
    "  their `client.simulation` resource, with no alias to the facade or ALK."
)
STUB_MIGRATION = (
    "- `fi.simulate` and `fi.opt` remain clear-error stubs pointing to\n"
    "  `fi.alk.simulate` and `fi.alk.opt`."
)


def _assert_changelog_withdrawal(text, *, scoped_notice):
    # The root distinguishes the retained released platform resource from the
    # withdrawn facade. Neither that notice nor a clear-error stub is an offer
    # of the withdrawn response types. Exempt only the exact statements, never
    # an entire section that could hide a newly advertised type or method.
    notice = FACADE_SCOPE_NOTICE if scoped_notice else WITHDRAWAL_NOTICE
    assert text.count(notice) == 1
    remainder = text.replace(notice, "").replace(STUB_MIGRATION, "")
    assert not re.search(r"simulat|persona|run[-.]?test|test-execution", remainder, re.IGNORECASE)


@pytest.mark.parametrize("path", ["CHANGELOG.md", "python/CHANGELOG.md", "typescript/futureagi/CHANGELOG.md"])
def test_changelog_does_not_reoffer_withdrawn_response_types(path):
    _assert_changelog_withdrawal((ROOT / path).read_text(), scoped_notice=path == "CHANGELOG.md")


@pytest.mark.parametrize("scoped_notice", [False, True])
@pytest.mark.parametrize("claim", [
    "- Add SimulationResponse and client.simulations responses.",
    "- Add PersonaResponse types.",
    "- Add run-test response types.",
    "- Add test-execution response types.",
    "- `fi.simulate` now returns response types.",
    "- Add new simulation fields to client.simulation.",
])
def test_changelog_guard_rejects_reoffers_before_and_after_notice(scoped_notice, claim):
    notice = FACADE_SCOPE_NOTICE if scoped_notice else WITHDRAWAL_NOTICE
    text = STUB_MIGRATION + "\n\n" + notice
    _assert_changelog_withdrawal(text, scoped_notice=scoped_notice)
    for changed in (claim + "\n" + text, text + "\n" + claim):
        with pytest.raises(AssertionError):
            _assert_changelog_withdrawal(changed, scoped_notice=scoped_notice)


@pytest.mark.parametrize("scoped_notice", [False, True])
def test_changelog_guard_requires_one_exact_withdrawal_notice(scoped_notice):
    notice = FACADE_SCOPE_NOTICE if scoped_notice else WITHDRAWAL_NOTICE
    for text in ("", STUB_MIGRATION, notice + "\n" + notice):
        with pytest.raises(AssertionError):
            _assert_changelog_withdrawal(text, scoped_notice=scoped_notice)
