"""Template config: NAME:k=v,... on the CLI and template(name, **config) in Python."""

import pytest

from fi import experiments
from fi.experiments.errors import UsageError
from fi.experiments.evaluators._base import EvalContext
from fi.experiments._dataset import load_local
from fi.experiments.evaluators.hosted import HostedTemplate, Template, parse_eval_spec, templates_from_cli


def test_cli_spec_parsing():
    t = parse_eval_spec("contains:keyword=refund,case_sensitive=false")
    assert t == Template("contains", {"keyword": "refund", "case_sensitive": False})
    assert parse_eval_spec("task_completion") == Template("task_completion")
    with pytest.raises(UsageError):
        parse_eval_spec("contains:keyword")


def test_python_template_and_cli_maps_and_labels():
    assert experiments.template("contains", keyword="refund").config == {"keyword": "refund"}
    tpls = templates_from_cli(["customer_agent_task_completion", "tone"],
                              ["customer_agent_task_completion:agent_prompt=@p.txt", "tone:output=answer"],
                              ["tone=neutral"])
    assert tpls[0].map == {"agent_prompt": "@p.txt"}
    assert tpls[1].map == {"output": "answer"} and tpls[1].pass_label == "neutral"
    with pytest.raises(UsageError):
        templates_from_cli(["a"], ["b:k=v"], [])
    with pytest.raises(UsageError):
        templates_from_cli(["a"], [], ["b=x"])


def test_request_body_carries_config_under_params_and_literals():
    row = load_local([{"question": "q", "expected": "e"}]).rows[0]
    ev = HostedTemplate(Template("contains", {"keyword": "refund"}), None)
    ev.record = {"config": {"eval_type_id": "CustomCodeEval", "required_keys": ["text"]}}
    ev.mapping = {"text": "==refund issued"}
    body = ev.body(EvalContext(row=row, output="x"))
    assert body == {"eval_name": "contains", "inputs": {"text": "refund issued"}, "config": {"params": {"keyword": "refund"}}}


def test_choices_score_with_pass_label():
    ev = HostedTemplate(Template("tone", pass_label="neutral"), "j")
    ok = ev.score({"result": [{"evaluations": [{"output": "neutral", "reason": "calm"}]}]})
    bad = ev.score({"result": [{"evaluations": [{"output": "anger"}]}]})
    assert (ok.passed, ok.label, ok.value) == (True, "neutral", 1.0) and bad.passed is False
    none = HostedTemplate(Template("tone"), "j").score({"result": [{"evaluations": [{"output": "joy"}]}]})
    assert none.passed is None and none.value is None and none.label == "joy"
