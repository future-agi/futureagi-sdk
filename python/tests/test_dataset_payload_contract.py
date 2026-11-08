"""T-068 source-pinned wire contract; real SDK builder, mocked transport only.

SOURCE comparison, not server/provider execution or live qualification.
FA e0a4f1f60dbb970c8bd04f2e73f335640fb4ef0f, paths under futureagi/model_hub/:
- views/run_prompt.py (git blob 5362bfbb360c99d315022edf03a54055166f1fdd):
  AddRunPromptColumnView :1724-1729 reads the request and nested config;
  :1752,1761-1762,1771-1789 reads model/messages/output/concurrency;
  :1777-1781 reads the five generation fields below from run_prompt_config;
  :1782-1783,1807 reads response_format/tool_choice/tools from config itself.
- serializers/run_prompt.py (git blob 03904ee722def5c6921b790a6a3a9792cbf40e1e):
  PromptConfigSerializer :167-182 accepts nested mixed JSON and message parts;
  :218-250 accepts the optional outer fields; AddRunPromptSerializer :366-369.

The inventory below is transcribed from those pinned readers, not SDK output.
False tool_choice and zero concurrency test lossless public-argument forwarding,
not server acceptance (the serializer restricts tool_choice/concurrency).
"""
from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from fi.api.types import HttpMethod
from fi.datasets.dataset import Dataset, DatasetResponseHandler
from fi.datasets.types import DatasetConfig
from fi.utils.errors import DatasetError, DatasetValidationError, UnexpectedDataFormatError

FA_REVISION = "e0a4f1f60dbb970c8bd04f2e73f335640fb4ef0f"
GENERATION_FIELDS = {"max_tokens", "temperature", "presence_penalty", "frequency_penalty", "top_p"}
DEFAULTS = dict(max_tokens=500, temperature=0.5, presence_penalty=1, frequency_penalty=1, top_p=1)
DATASET_ID = "11111111-1111-4111-8111-111111111111"
COLUMN_ID = "22222222-2222-4222-8222-222222222222"
BASE_URL = "https://payload.invalid"


@pytest.fixture
def dataset():
    # Bypass credential discovery and construction-time dataset fetching, not builders.
    client = object.__new__(Dataset)
    client._base_url = BASE_URL
    client.dataset_config = DatasetConfig(id=DATASET_ID, name="fixture", model_type="GenerativeLLM")

    def transport(*, config, response_handler):
        assert response_handler is DatasetResponseHandler
        if config.method == HttpMethod.GET:
            assert config.url == f"{BASE_URL}/model-hub/develops/{DATASET_ID}/get-dataset-table/"
            assert config.params == {"page_size": 1, "current_page_index": 0}
            return SimpleNamespace(columns=[SimpleNamespace(id=COLUMN_ID, name="input")])
        assert config.method == HttpMethod.POST
        assert config.url == f"{BASE_URL}/model-hub/develops/add_run_prompt_column/"
        assert config.timeout == 30
        return {"result": "synthetic success"}

    client.request_with_retry = Mock(side_effect=transport)
    return client


def posted(dataset):
    posts = [call.kwargs["config"].json for call in dataset.request_with_retry.call_args_list
             if call.kwargs["config"].method == HttpMethod.POST]
    assert len(posts) == 1
    return posts[0]


@pytest.mark.parametrize("options,expected", [
    ({}, DEFAULTS),
    (dict(max_tokens=123, temperature=0.2, presence_penalty=-0.3, frequency_penalty=0.7, top_p=0.8),
     dict(max_tokens=123, temperature=0.2, presence_penalty=-0.3, frequency_penalty=0.7, top_p=0.8)),
    (dict.fromkeys(GENERATION_FIELDS, 0), dict.fromkeys(GENERATION_FIELDS, 0)),
], ids=["defaults", "all-nondefault", "explicit-zero"])
def test_generation_options_use_server_nested_config(dataset, options, expected):
    result = dataset.add_run_prompt("answer", "synthetic-model", [{"role": "user", "content": "hello"}], **options)
    assert result is dataset
    body = posted(dataset)
    assert body["config"].get("run_prompt_config") == expected, FA_REVISION
    assert not GENERATION_FIELDS.intersection(body["config"])
    assert body == {
        "dataset_id": DATASET_ID, "name": "answer",
        "config": {"model": "synthetic-model", "output_format": "string", "concurrency": 5,
                   "messages": [{"role": "user", "content": [{"type": "text", "text": "hello"}]}],
                   "run_prompt_config": expected},
    }


@pytest.mark.parametrize("optional", [
    {"tools": [{"id": "33333333-3333-4333-8333-333333333333"}], "tool_choice": "required",
     "response_format": {"type": "json_schema", "json_schema": {"name": "reply", "strict": False, "schema": {"type": "object"}}}},
    {"tools": [], "tool_choice": False, "response_format": {}},
    {"tool_choice": ""},
], ids=["populated-with-false-json-value", "explicit-empty-and-false", "empty-tool-choice"])
def test_optional_fields_stay_at_outer_config_and_preserve_values(dataset, optional):
    dataset.add_run_prompt("answer", "synthetic-model", [{"role": "user", "content": "hello"}],
                           output_format="object", concurrency=1, **deepcopy(optional))
    config = posted(dataset)["config"]
    for key in ("tools", "tool_choice", "response_format"):
        if key in optional:
            assert key in config
            assert config[key] == optional[key]
        else:
            assert key not in config
        assert key not in config.get("run_prompt_config", {})
    assert config["output_format"] == "object"
    assert config["concurrency"] == 1


def test_omitted_and_none_optionals_are_absent(dataset):
    dataset.add_run_prompt("answer", "synthetic-model", [{"role": "user", "content": "hello"}],
                           tools=None, tool_choice=None, response_format=None)
    config = posted(dataset)["config"]
    assert not {"tools", "tool_choice", "response_format"}.intersection(config)


def test_message_column_translation_and_explicit_zero_concurrency_unchanged(dataset):
    messages = [{"role": "system", "content": "read {{input}}"},
                {"role": "user", "content": [{"type": "text", "text": "again {{input}}"},
                                               {"type": "image_url", "image_url": {"url": "synthetic"}}, 7]}]
    assert dataset.add_run_prompt("answer", "synthetic-model", messages, concurrency=0) is dataset
    config = posted(dataset)["config"]
    assert config["messages"] == [
        {"role": "system", "content": [{"type": "text", "text": f"read {{{{{COLUMN_ID}}}}}"}]},
        {"role": "user", "content": [{"type": "text", "text": f"again {{{{{COLUMN_ID}}}}}"},
                                     {"type": "image_url", "image_url": {"url": "synthetic"}},
                                     {"type": "text", "text": "7"}]},
    ]
    assert config["concurrency"] == 0
    assert dataset.request_with_retry.call_count == 3


@pytest.mark.parametrize("overrides,error,match", [
    ({"name": ""}, DatasetValidationError, "name cannot be empty"),
    ({"model": ""}, DatasetValidationError, "Model cannot be empty"),
    ({"messages": []}, DatasetValidationError, "Messages list cannot be empty"),
    ({"messages": ["bad"]}, UnexpectedDataFormatError, "must be a dictionary"),
    ({"messages": [{"content": "no role"}]}, UnexpectedDataFormatError, "role.*content"),
], ids=["empty-name", "empty-model", "empty-messages", "invalid-message", "missing-role"])
def test_local_validation_unchanged(dataset, overrides, error, match):
    options = dict(name="answer", model="synthetic-model", messages=[{"role": "user", "content": "hello"}])
    options.update(overrides)
    with pytest.raises(error, match=match):
        dataset.add_run_prompt(**options)
    dataset.request_with_retry.assert_not_called()


def test_missing_dataset_id_still_refused_before_request(dataset):
    dataset.dataset_config = None
    with pytest.raises(DatasetError, match="configured with an ID"):
        dataset.add_run_prompt("answer", "synthetic-model", [{"role": "user", "content": "hello"}])
    dataset.request_with_retry.assert_not_called()


def test_missing_column_still_refused_before_post(dataset):
    with pytest.raises(DatasetError, match="not found in dataset"):
        dataset.add_run_prompt("answer", "synthetic-model", [{"role": "user", "content": "{{missing}}"}])
    assert dataset.request_with_retry.call_count == 1
    assert dataset.request_with_retry.call_args.kwargs["config"].method == HttpMethod.GET
