"""Local errors for unsupported config/search and invalid legacy log payloads.

Current list/setup cannot reproduce the old config's mode/injection_format.
Client.log retains published validation and dispatch for compatible backends;
its client-side behavior does not establish hosted endpoint availability.
"""

import inspect

import pytest

from fi.client import Client
from fi.errors import PlatformNotConfiguredError
from fi.evals import EvalTemplateManager
from fi.utils.errors import MissingRequiredKey
from fi.utils.types import Environments, ModelTypes


TEMPLATE_ID = "11111111-1111-4111-8111-111111111111"
GT_ID = "22222222-2222-4222-8222-222222222222"


def config_write_message(ground_truth_id):
    return (
        "set_ground_truth_config is unsupported on the current platform: "
        f"PUT /model-hub/eval-templates/{TEMPLATE_ID}/ground-truth-config/ "
        "was removed before Future AGI platform 1.56.1; no compatible replacement exists. "
        "Use set_ground_truth_variable_mapping or set_ground_truth_role_mapping "
        "with a ground-truth ID, both mappings, max_examples and enabled via "
        f"PUT /model-hub/ground-truth/{ground_truth_id}/setup/. "
        "Setup cannot set mode, similarity_threshold or injection_format."
    )


@pytest.mark.parametrize(
    "method,args,kwargs,message",
    [
        pytest.param(
            "get_ground_truth_config", (TEMPLATE_ID,), {},
            "get_ground_truth_config is unsupported on the current platform: "
            f"GET /model-hub/eval-templates/{TEMPLATE_ID}/ground-truth-config/ "
            "was removed before Future AGI platform 1.56.1; no compatible replacement exists. "
            "Use list_ground_truth(template_id) via "
            f"GET /model-hub/eval-templates/{TEMPLATE_ID}/ground-truth/ "
            "to read dataset state, not the legacy template config; "
            "mode and injection_format are unavailable.",
            id="get_ground_truth_config",
        ),
        pytest.param(
            "set_ground_truth_config", (TEMPLATE_ID,), {},
            config_write_message("{ground_truth_id}"),
            id="set_ground_truth_config-defaults",
        ),
        pytest.param(
            "set_ground_truth_config", (TEMPLATE_ID,),
            {"enabled": False, "ground_truth_id": GT_ID, "mode": "manual",
             "max_examples": 7, "similarity_threshold": 0.8, "injection_format": "xml"},
            config_write_message(GT_ID),
            id="set_ground_truth_config-explicit",
        ),
        pytest.param(
            "search_ground_truth", (GT_ID,), {"query": "a question", "max_results": 5},
            "search_ground_truth is unsupported on the current platform: "
            f"POST /model-hub/ground-truth/{GT_ID}/search/ "
            "was removed before Future AGI platform 1.56.1; there is no replacement search route. "
            "Use get_ground_truth_data(ground_truth_id) via "
            f"GET /model-hub/ground-truth/{GT_ID}/data/ "
            "to read paginated rows, not similarity-search results.",
            id="search_ground_truth",
        ),
    ],
)
def test_manager_error_is_exact_and_makes_no_request(backend, method, args, kwargs, message):
    manager = EvalTemplateManager()
    try:
        with pytest.raises(PlatformNotConfiguredError) as caught:
            getattr(manager, method)(*args, **kwargs)
        assert type(caught.value) is PlatformNotConfiguredError
        assert caught.value.code == "unsupported_operation"
        assert caught.value.operation == method
        assert backend.calls == []
        assert str(caught.value) == message
    finally:
        manager.close()


@pytest.mark.filterwarnings("ignore:Client.log is deprecated:DeprecationWarning")
def test_client_log_validates_before_making_a_request(backend):
    client = Client()
    try:
        with pytest.raises(MissingRequiredKey) as caught:
            # Published validation checks conversation structure before timestamp range.
            client.log("model-id", ModelTypes.GENERATIVE_LLM, Environments.PRODUCTION,
                       "v1", -1, {"invalid": "conversation"}, {"tag": "value"}, 10)
        assert type(caught.value) is MissingRequiredKey
        assert backend.calls == []
    finally:
        client.close()


def test_client_log_keeps_published_0613_signature():
    # pub.whl: fi/client.py:256-266; the six optional arguments default to None.
    parameters = list(inspect.signature(Client.log).parameters.values())
    assert [p.name for p in parameters] == [
        "self", "model_id", "model_type", "environment", "model_version",
        "prediction_timestamp", "conversation", "tags", "timeout",
    ]
    assert all(p.kind is inspect.Parameter.POSITIONAL_OR_KEYWORD for p in parameters)
    assert all(p.default is inspect.Parameter.empty for p in parameters[:4])
    assert all(p.default is None for p in parameters[4:])
