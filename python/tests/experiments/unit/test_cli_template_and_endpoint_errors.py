"""Two SDK findings from the stack-server rows (VM-ROWS.md B-3), each pinned here.

- **CLI-22 implementation / evaluation regression:** ``futureagi-py upload FILE --eval contains:keyword=order`` exited 3 with
  METRIC_BINDING ("model: This field may not be null."): the template metric body sent ``"model": null``
  for a function template, and the server's ``UserEvalMutationRequestSerializer`` takes ``model`` as an
  optional non-null string. The contract stand-in now refuses a null model the same way. With the null gone,
  the stack server refused the metric's name ``sdk · contains · <hash>`` (``validate_eval_name``: lowercase
  letters, digits, ``-`` and ``_`` only): the name is now ``sdk-contains-<hash>`` (VM-ROWS B3-1). With the
  name accepted, the SDK still could not find the metric it had made: ``get_evals_list?eval_type=user`` leaves
  out metrics whose template is hidden from the UI picker (``visible_ui`` false; ``contains`` is one of 24 such
  system templates on the stack server). The SDK now also asks the compare list, which does not filter on it.
- **CLI-03 implementation:** ``futureagi-py doctor`` with an unreachable ``OPENAI_BASE_URL`` exited 0 and never named
  it. It now prints the URL as a doctor problem and exits 3 (the shared doctor's ``Problem`` lines).
"""

import json

import pytest

from fi.experiments.evaluators.hosted import Template, metric_body, metric_name
from tests.experiments.unit.cli_helpers import cli
from tests.experiments.unit.contract_server import ContractServer
from tests.experiments.unit.test_hosted_mapping import CATALOG, FIXTURE

ROWS = [{"id": f"T{i}", "input": f"where is order {i}?", "expected": "shipped"} for i in range(4)]


def test_a_function_template_metric_sends_no_model():
    tpl = Template("contains", {"keyword": "order"})
    body = metric_body(CATALOG["contains"], tpl, {"text": "output"}, None)
    assert "model" not in body
    judged = metric_body(CATALOG["task_completion"], Template("task_completion"), {"output": "output"}, "my-judge")
    assert judged["model"] == "my-judge"


@pytest.mark.parametrize("name", ["contains", "fuzzy_match", "Task Completion", "_odd--Name_", "x" * 80, "--"])
def test_metric_names_pass_the_servers_eval_name_rule(name):
    import re

    got = metric_name(Template(name, {"keyword": "k"}), {"text": "output"}, None)
    assert re.fullmatch(r"[a-z0-9_-]+", got) and got[0] not in "-_" and got[-1] not in "-_"
    assert "_-" not in got and "-_" not in got and len(got) <= 50


def _client_with_evals(server, scored):
    import httpx

    from fi.futureagi_client import FutureAGIClient

    def handler(request):
        if request.url.path == "/sdk/api/v1/get-evals/":
            return httpx.Response(200, json=FIXTURE["response"])
        if request.url.path == "/sdk/api/v1/new-eval/":
            body = json.loads(request.content)
            scored.append(body)
            out = "Passed" if body["config"]["params"]["keyword"] in body["inputs"]["text"] else "Failed"
            return httpx.Response(200, json={"status": True, "result": [{"evaluations": [
                {"name": body["eval_name"], "output": out, "reason": "r", "output_type": "Pass/Fail"}]}]})
        return server(request)

    c = FutureAGIClient(api_key="k-test-1234", secret_key="s-test-1234", base_url="http://srv.test")
    c.generated_client.get_httpx_client()._transport = httpx.MockTransport(handler)
    return c


def test_cli22_upload_with_a_function_template_stores_a_score_per_item(tmp_path, monkeypatch):
    """CLI-22 implementation: exit 0, one JSON object, and an assessed template score_ref on each of the 4 items."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "support.jsonl").write_text("\n".join(json.dumps(r) for r in ROWS) + "\n")
    outputs = ["your order shipped", "it is on the way", "order T2 shipped", "no idea"]
    (tmp_path / "results.jsonl").write_text(
        "\n".join(json.dumps({"id": r["id"], "output": o}) for r, o in zip(ROWS, outputs)) + "\n")
    server, scored = ContractServer(), []
    server.hidden_templates.add(CATALOG["contains"]["id"])  # as on the stack server: contains is visible_ui false
    import fi.experiments._log_results as lr

    real = lr.log_results
    monkeypatch.setattr(lr, "log_results", lambda *a, **k: real(*a, client=_client_with_evals(server, scored), **k))
    code, out, err = cli("upload", "results.jsonl", "--dataset", "support.jsonl", "--dataset-name", "support",
                         "--eval", "contains:keyword=order",
                         "--pass-label", "contains=Passed", "--json", "--no-env-file")
    assert code == 0, out + err
    summary = json.loads(out.strip().splitlines()[-1])
    assert summary["status"] == "completed" and summary["items"] == 4
    [add] = [b for m, p, b in server.requests if p.endswith("/add_user_eval/")]
    assert "model" not in add and add["run"] is False and add["name"].startswith("sdk-contains-")
    [run] = server.runs.values()
    refs = [ref for it in run["items"].values() for ref in it["score_refs"]]
    assert len(refs) == 4 and all(ref["status"] == "assessed" for ref in refs)
    assert sorted(ref["value"] for ref in refs) == [0.0, 0.0, 1.0, 1.0]
    assert len(scored) == 4 and all("model" not in b for b in scored)
    assert [p for m, p, b in server.requests if p.endswith("get-evals-list/")] == ["/model-hub/datasets/compare/get-evals-list/"] * 2


def test_a_visible_templates_metric_is_found_again_by_the_first_list(tmp_path, monkeypatch):
    """The compare list is asked only when the dataset's user-eval list has no metric of that name: here once, before
    the metric exists; after add_user_eval the first list finds it."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "support.jsonl").write_text("\n".join(json.dumps(r) for r in ROWS) + "\n")
    (tmp_path / "results.jsonl").write_text("\n".join(json.dumps({"id": r["id"], "output": "order ok"}) for r in ROWS) + "\n")
    server, scored = ContractServer(), []
    import fi.experiments._log_results as lr

    real = lr.log_results
    monkeypatch.setattr(lr, "log_results", lambda *a, **k: real(*a, client=_client_with_evals(server, scored), **k))
    code, out, err = cli("upload", "results.jsonl", "--dataset", "support.jsonl", "--dataset-name", "support",
                         "--eval", "contains:keyword=order",
                         "--pass-label", "contains=Passed", "--json", "--no-env-file")
    assert code == 0, out + err
    lookups = [p.rsplit("/", 2)[-2] for m, p, b in server.requests if p.endswith(("get_evals_list/", "get-evals-list/"))]
    assert lookups == ["get_evals_list", "get-evals-list", "get_evals_list"]


# ---- CLI-03 implementation: an unreachable OPENAI_BASE_URL ------------------------------------------------------


def _doctor_env(monkeypatch, tmp_path):
    for var in ("FI_API_KEY", "FI_SECRET_KEY", "FI_JUDGE_MODEL"):
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setenv("FI_BASE_URL", "http://127.0.0.1:9")
    monkeypatch.setenv("FI_LOGIN_FILE", str(tmp_path / "none" / "login.json"))


def test_cli03_doctor_names_an_unreachable_openai_base_url_and_exits_3(monkeypatch, tmp_path):
    _doctor_env(monkeypatch, tmp_path)
    monkeypatch.setenv("OPENAI_BASE_URL", "http://127.0.0.1:9/v1")  # nothing listens on the discard port
    code, out, err = cli("doctor")
    assert code == 3, out + err
    line = next(x for x in out.splitlines() if x.startswith("OpenAI"))
    assert "OPENAI_BASE_URL=http://127.0.0.1:9/v1 is unreachable" in line and "judge()" in line
    code, out, err = cli("doctor", "--json")
    assert code == 3
    problems = json.loads(out)["sections"]["experiments"]["problems"]
    assert len(problems) == 1 and "127.0.0.1:9" in problems[0]


def test_cli03_a_reachable_or_unset_openai_base_url_keeps_exit_0(monkeypatch, tmp_path):
    import httpx

    _doctor_env(monkeypatch, tmp_path)
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
    code, out, err = cli("doctor")
    assert code == 0 and "OPENAI_BASE_URL" not in out  # unset: nothing is sent anywhere
    monkeypatch.setenv("OPENAI_BASE_URL", "http://user:pw@proxy.test/v1")
    seen = []

    def fake_get(url, timeout):
        seen.append(url)
        return httpx.Response(401, request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx, "get", fake_get)
    code, out, err = cli("doctor")
    assert code == 0 and seen == ["http://user:pw@proxy.test/v1/models"]
    assert "OPENAI_BASE_URL=http://proxy.test/v1 reachable (HTTP 401 without a key)" in out and "pw@" not in out
    code, out, err = cli("doctor", "--offline")
    assert code == 0 and "(not checked: --offline)" in out and len(seen) == 1
