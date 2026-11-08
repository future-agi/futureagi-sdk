"""Current platform ground-truth setup and local refusals for removed routes.

The fake sits below requests/httpx; no live server or platform checkout is needed.
Setup's contract is an atomic PUT: both mappings, max_examples and enabled.
"""

import ast
from copy import deepcopy
import inspect
from pathlib import Path

import pytest

from fi.client import Client
from fi.errors import ConfigurationError, PlatformNotConfiguredError
from fi.evals import EvalTemplateManager
from fi.evals.manager_types import GroundTruthRoleMappingResponse, GroundTruthVariableMappingResponse
from fi.utils.routes import Routes
from fi.utils.types import Environments, ModelTypes

TEMPLATE_ID = "11111111-1111-4111-8111-111111111111"
GT_ID = "22222222-2222-4222-8222-222222222222"
SETUP_PATH = f"/model-hub/ground-truth/{GT_ID}/setup/"
VARIABLES = {"input": "question", "context": "context_column"}
ROLES = {"output": "answer", "explanation": "rationale"}
METHODS = ["set_ground_truth_variable_mapping", "set_ground_truth_role_mapping"]


@pytest.fixture
def manager():
    client = EvalTemplateManager()
    yield client
    client.close()


@pytest.mark.parametrize("method", METHODS)
@pytest.mark.parametrize("enabled", [True, False])
def test_mapping_uses_atomic_setup_and_preserves_all_supplied_fields(backend, manager, method, enabled):
    payload = {"variable_mapping": deepcopy(VARIABLES), "role_mapping": deepcopy(ROLES),
               "max_examples": 7, "enabled": enabled}
    original = deepcopy(payload)
    # Real setup responses include both mappings, status and the runtime config.
    result = {"id": GT_ID, "template_id": TEMPLATE_ID, "variable_mapping": VARIABLES,
              "role_mapping": ROLES, "embedding_status": "pending", "embeddings_stale": True,
              "config": {"enabled": enabled, "max_examples": 7, "similarity_threshold": 0.7}}
    backend.routes[("PUT", SETUP_PATH)] = lambda call: (200, {"status": True, "result": result})
    primary = "variable_mapping" if method == METHODS[0] else "role_mapping"
    mapping = payload.pop(primary)

    response = getattr(manager, method)(GT_ID, mapping, **payload)

    assert len(backend.calls) == 1  # no invented GET /setup/ or /detail/ read-merge
    call = backend.calls[0]
    assert (call["method"], call["path"], call["query"]) == ("PUT", SETUP_PATH, [])
    assert call["json"] == original  # no mode, no empty mapping or inferred settings
    expected_type = GroundTruthVariableMappingResponse if method == METHODS[0] else GroundTruthRoleMappingResponse
    assert isinstance(response, expected_type)
    assert response.id == GT_ID
    assert getattr(response, primary) == original[primary]
    assert response["config"]["enabled"] is enabled
    assert {primary: mapping, **payload} == original  # caller dictionaries stay unchanged


@pytest.mark.parametrize("method", METHODS)
@pytest.mark.parametrize("missing", ["variable_mapping", "role_mapping", "max_examples", "enabled"])
def test_setup_requires_explicit_state_without_http(backend, manager, method, missing):
    payload = {"variable_mapping": VARIABLES, "role_mapping": ROLES, "max_examples": 7, "enabled": False}
    payload[missing] = None
    with pytest.raises(ValueError, match=missing) as caught:
        getattr(manager, method)(GT_ID, **payload)
    assert isinstance(caught.value, ConfigurationError)
    assert backend.calls == []


@pytest.mark.parametrize("method", METHODS)
def test_legacy_mapping_call_binds_but_refuses_to_guess_state(backend, manager, method):
    mapping = VARIABLES if method == METHODS[0] else ROLES
    with pytest.raises(ValueError, match="required") as caught:
        getattr(manager, method)(GT_ID, mapping)
    assert isinstance(caught.value, ConfigurationError)
    assert backend.calls == []


@pytest.mark.parametrize("method", METHODS)
@pytest.mark.parametrize("max_examples", [0, 21, True, 2.5])
def test_setup_rejects_invalid_example_limit_before_http(backend, manager, method, max_examples):
    with pytest.raises(ValueError, match="max_examples") as caught:
        getattr(manager, method)(GT_ID, variable_mapping=VARIABLES, role_mapping=ROLES,
                                max_examples=max_examples, enabled=False)
    assert isinstance(caught.value, ConfigurationError)
    assert backend.calls == []


@pytest.mark.parametrize("method", METHODS)
@pytest.mark.parametrize("enabled", [0, 1, "false"])
def test_setup_rejects_invalid_enabled_before_http(backend, manager, method, enabled):
    with pytest.raises(ValueError, match="enabled") as caught:
        getattr(manager, method)(GT_ID, variable_mapping=VARIABLES, role_mapping=ROLES,
                                max_examples=7, enabled=enabled)
    assert isinstance(caught.value, ConfigurationError)
    assert backend.calls == []


@pytest.mark.parametrize("method", METHODS)
@pytest.mark.parametrize("unknown", ["outpt", "explantion", "Output", "metadata"])
def test_setup_rejects_unknown_role_keys_before_http(backend, manager, method, unknown):
    roles = {**ROLES, unknown: "answer"}
    original = deepcopy(roles)
    # The nested serializer drops unknown keys; a successful response must not hide the typo.
    backend.routes[("PUT", SETUP_PATH)] = lambda call: (200, {"status": True, "result": {
        "id": GT_ID, "variable_mapping": VARIABLES, "role_mapping": ROLES}})
    with pytest.raises(ValueError, match=unknown) as caught:
        getattr(manager, method)(GT_ID, variable_mapping=VARIABLES, role_mapping=roles,
                                max_examples=7, enabled=False)
    assert isinstance(caught.value, ConfigurationError)
    assert "role_mapping" in str(caught.value)
    assert roles == original
    assert backend.calls == []


@pytest.mark.parametrize("method", METHODS)
@pytest.mark.parametrize("output", ["output", "expected_output"])
@pytest.mark.parametrize("explanation", ["explanation", "reasoning", "reason"])
def test_setup_preserves_declared_role_keys_and_legacy_aliases(backend, manager, method, output, explanation):
    roles = {output: "answer", explanation: "rationale"}
    backend.routes[("PUT", SETUP_PATH)] = lambda call: (200, {"status": True, "result": {
        "id": GT_ID, "variable_mapping": VARIABLES, "role_mapping": roles}})
    getattr(manager, method)(GT_ID, variable_mapping=VARIABLES, role_mapping=roles,
                            max_examples=7, enabled=False)
    assert len(backend.calls) == 1
    assert backend.calls[0]["json"]["role_mapping"] == roles


@pytest.mark.parametrize(
    "method,args,kwargs,removed,replacements",
    [
        ("get_ground_truth_config", (TEMPLATE_ID,), {},
         f"/model-hub/eval-templates/{TEMPLATE_ID}/ground-truth-config/",
         ["list_ground_truth", f"GET /model-hub/eval-templates/{TEMPLATE_ID}/ground-truth/"]),
        ("set_ground_truth_config", (TEMPLATE_ID,),
         {"ground_truth_id": GT_ID, "mode": "manual", "max_examples": 7},
         f"/model-hub/eval-templates/{TEMPLATE_ID}/ground-truth-config/",
         ["set_ground_truth_variable_mapping", "set_ground_truth_role_mapping", f"PUT {SETUP_PATH}"]),
        ("set_ground_truth_config", (TEMPLATE_ID,), {},
         f"/model-hub/eval-templates/{TEMPLATE_ID}/ground-truth-config/",
         ["PUT /model-hub/ground-truth/{ground_truth_id}/setup/"]),
        ("search_ground_truth", (GT_ID,), {"query": "a question"},
         f"/model-hub/ground-truth/{GT_ID}/search/", ["no replacement"]),
    ],
)
def test_removed_manager_methods_fail_locally(backend, manager, method, args, kwargs, removed, replacements):
    with pytest.raises(PlatformNotConfiguredError) as caught:
        getattr(manager, method)(*args, **kwargs)
    assert backend.calls == []
    assert caught.value.code == "unsupported_operation"
    assert caught.value.operation == method
    assert removed in str(caught.value)
    assert "unsupported" in str(caught.value).lower()
    for replacement in replacements:
        assert replacement in str(caught.value)


def test_legacy_client_log_fails_locally(backend):
    client = Client()
    try:
        with pytest.raises(PlatformNotConfiguredError) as caught:
            client.log("model-id", ModelTypes.GENERATIVE_LLM, Environments.PRODUCTION)
        assert backend.calls == []
        assert caught.value.code == "unsupported_operation"
        assert caught.value.operation == "Client.log"
        assert "POST /sdk/api/v1/log/model/" in str(caught.value)
        assert "no replacement" in str(caught.value)
        assert "traceAI" in str(caught.value)
        assert "client.tracing" in str(caught.value)
        assert "FutureAGIClient" in str(caught.value)
    finally:
        client.close()


def test_list_ground_truth_is_still_the_supported_read(backend, manager):
    path = f"/model-hub/eval-templates/{TEMPLATE_ID}/ground-truth/"
    backend.routes[("GET", path)] = lambda call: (200, {"status": True, "result": {
        "template_id": TEMPLATE_ID, "items": [{"id": GT_ID, "name": "current-state",
            "variable_mapping": VARIABLES, "role_mapping": ROLES, "max_examples": 7, "enabled": False}],
        "total": 1}})
    result = manager.list_ground_truth(TEMPLATE_ID)
    assert result.total == 1
    current = result.items[0]
    assert current.variable_mapping == VARIABLES
    assert current.role_mapping == ROLES
    assert current["max_examples"] == 7
    assert current["enabled"] is False
    assert [(call["method"], call["path"]) for call in backend.calls] == [("GET", path)]


def test_dead_routes_are_never_referenced():
    """Compatibility constants stay available but no evals/client path may use them."""
    retired = {"ground_truth_config", "ground_truth_mapping", "ground_truth_role_mapping",
               "ground_truth_search", "log_model"}
    package = Path(__file__).resolve().parents[2] / "fi"
    sources = [package / "client.py", *sorted((package / "evals").rglob("*.py"))]
    references = []
    for path in sources:
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            # Also catch literal-based getattr(Routes, name) and Routes[name] lookups.
            name = node.attr if isinstance(node, ast.Attribute) else (
                node.value if isinstance(node, ast.Constant) and isinstance(node.value, str) else None
            )
            if name in retired:
                references.append((str(path.relative_to(package)), node.lineno, name))
    assert references == []
    assert Routes.ground_truth_setup.value == "model-hub/ground-truth/{ground_truth_id}/setup/"


@pytest.mark.parametrize("method", METHODS)
def test_mapping_signature_keeps_positional_arguments_and_adds_only_optional_keywords(method):
    signature = inspect.signature(getattr(EvalTemplateManager, method))
    primary = "variable_mapping" if method == METHODS[0] else "role_mapping"
    parameters = list(signature.parameters.values())
    assert [p.name for p in parameters[:3]] == ["self", "ground_truth_id", primary]
    assert all(p.kind is inspect.Parameter.POSITIONAL_OR_KEYWORD for p in parameters[:3])
    assert all(p.kind is inspect.Parameter.KEYWORD_ONLY and p.default is None for p in parameters[3:])
    signature.bind(None, GT_ID, {})  # old source still binds; missing setup is a local ValueError
