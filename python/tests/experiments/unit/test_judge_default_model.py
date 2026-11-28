"""``judge()`` defaults to ``gpt-4.1-mini`` and uses another model only when named. The
docs describe length and tone limitations on cheaper models and state the rate gate without
recommending retired models. Requests use an httpx.MockTransport (no network, no model)."""

import asyncio
import importlib
import json

import httpx
import pytest

from fi import experiments
from fi.experiments._dataset import load_local
from fi.experiments.errors import UsageError
from fi.experiments.evaluators._base import EvalContext
from tests.experiments.unit.judge_helpers import part_verdict, with_criteria

judge_mod = importlib.import_module("fi.experiments.evaluators.judge")  # the package exports judge() by that name

ROW = load_local([{"question": "where is my order?"}]).rows[0]


def _seen_model(j) -> list[str]:
    models = []

    def handler(request):
        body = json.loads(request.content)
        models.append(body["model"])
        return httpx.Response(200, json=part_verdict(True))

    j._transport = httpx.MockTransport(with_criteria(handler))
    scores = asyncio.run(j.aevaluate(EvalContext(row=ROW, output="It shipped.")))
    assert scores["judge"].status == "assessed"
    return models


def test_the_default_judge_model_is_gpt_4_1_mini(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-judge-key-123")
    monkeypatch.setenv("OPENAI_BASE_URL", "http://judge.local/v1")
    j = experiments.evaluators.judge("Is the reply polite?")
    assert j.model == "gpt-4.1-mini" == judge_mod.DEFAULT_JUDGE_MODEL
    assert _seen_model(j) == ["gpt-4.1-mini"]
    assert "judge gpt-4.1-mini via $OPENAI_API_KEY" in j.describe()


def test_another_model_is_used_only_when_named(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-judge-key-123")
    monkeypatch.setenv("OPENAI_BASE_URL", "http://judge.local/v1")
    assert _seen_model(experiments.evaluators.judge("Is the reply polite?", model="gpt-4o-mini")) == ["gpt-4o-mini"]


def test_another_provider_names_its_own_model():
    with pytest.raises(UsageError, match="needs model="):
        experiments.evaluators.judge("ok?", api_key_env="GROQ_API_KEY", base_url="https://api.groq.com/openai/v1")
    j = experiments.evaluators.judge("ok?", model="llama-3.1-8b-instant", api_key_env="GROQ_API_KEY",
                                     base_url="https://api.groq.com/openai/v1")
    assert j.model == "llama-3.1-8b-instant"
    with pytest.raises(ValueError, match="non-empty"):
        experiments.evaluators.judge("ok?", model="  ")


def test_the_docs_name_the_default_and_never_offer_the_retired_model():
    for doc in (judge_mod.__doc__, judge_mod.judge.__doc__):
        assert "gpt-4.1-mini" in doc and "nano" not in doc  # retired by OpenAI on 10-23
    assert "miss some length and tone controls" in judge_mod.judge.__doc__
    assert "ModelRetiredError" in judge_mod.judge.__doc__
    rate = " ".join(judge_mod.__doc__.split())
    assert "at least 5 of 6 seeded runs" in rate and "at most 5% misses" in rate and "error score, not a pass" in rate
    # The docs lead with the held-out comparison and distinguish two samples from a paired replay.
    # They describe the sentence-count miss and report how often the default judge failed the control suite.
    doc = " ".join(judge_mod.__doc__.split())
    assert "Its own known miss" in doc and "can miscount sentences" in doc
    assert "does not answer all of the INPUT" in doc and "the checklist did not (0 of 6)" in doc
    assert "2 misses in 84 verdicts, against 4 in 84" in doc and "two samples, not a paired replay" in doc
    assert "one-sided Fisher p = 0.34" in doc and "RED in 2 of its 3 runs on this judge" in doc
