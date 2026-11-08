"""Redaction by key and by value shape (reports/WAVE1.md section; L-SDK-w1 "found, not fixed"): wave 0
matched the substrings ``key|token|secret|password|authorization`` and blanked ``max_tokens`` in the
journaled plan and in the uploaded run's ``model_config``. Both directions are tested: credentials
still go, non-secret config stays. No network, no model; uploads go to the in-process stand-in."""

import json
from pathlib import Path

import pytest

from fi import experiments
from fi.experiments._redact import REDACTED, Redactor, is_credential_key, redact_shapes
from tests.experiments.unit.contract_server import ContractServer, client_for

# fake credentials, shaped like the real ones (random letters and digits, never a live key); the JWT, Google and
# Hugging Face ones are built at run time so the source holds no literal the pre-ship secret scan refuses
OPENAI_SHAPED = "sk-proj-Ab3dEf6hIj9kLm2nOp5qRs8tUv1wXy4z"
ANTHROPIC_SHAPED = "sk-ant-api03-Zz9Yy8Xx7Ww6Vv5Uu4Tt3Ss2Rr1Qq0"
JWT_SHAPED = ".".join(["ey" + "JhbGciOiJIUzI1NiJ9", "ey" + "JzdWIiOiIxMjM0NTY3ODkwIn0", "dBjftJeZ4CVPmB92K27uhbUJU1p1r_wW1gFWFOEjXk"])
HEX32 = "3f9a0c7e5b2d4186a7c9e0f1b2d3c4e5"  # Azure OpenAI / FutureAGI style: 32 hex, no known prefix, no shape
GOOGLE_SHAPED = "AI" + "za" + "Sy" + "Qz7Lm3Np8Rt2Vw6Xy1Bc4Df9Gh0Jk5MsT"
HF_SHAPED = "h" + "f_" + "QwErTyUiOpAsDfGhJkLzXcVbNmQwErTyUi"
# names wave 0 (the recorded revision) redacted and the recorded revision did not (L-SDK2a regression coverage, probe test_review_redaction.py)
WAVE0_NAMES = ["key", "openai_key", "azure_key", "gemini_key", "google_key", "fi_key", "hf_key", "app_key", "ssh_key",
               "OPENAI_KEY", "azureKey", "token_value", "auth_tokens", "tokens"]


@pytest.mark.parametrize("key", [
    "api_key", "apiKey", "OPENAI_API_KEY", "x-api-key", "Authorization", "http.request.header.authorization",
    "password", "passwd", "client_secret", "secret_key", "private_key", "gcp.private_key", "aws_access_key_id",
    "credentials", "client.credentials", "cookie", "set-cookie", "oauth.bearer", "token", "access_token",
    "refresh_token", "id_token", "x-auth-token", "hf_token", "AUTH_TOKEN", "signing_key", "license_key",
    # names wave 0 redacted that the recorded revision let through: any "key" / "tokens" word fails closed
    *WAVE0_NAMES, "openaikey", "passkey", "keys", "KEY", "fi.experiment.param.openai_key", "fi.experiment.param.tokens",
])
def test_credential_keys_are_credentials(key):
    assert is_credential_key(key)


@pytest.mark.parametrize("key", [
    "max_tokens", "max_completion_tokens", "max_new_tokens", "token_count", "llm.token_count.prompt",
    "gen_ai.usage.input_tokens", "gen_ai.request.max_tokens", "tokenizer", "keyword", "keywords", "monkey",
    "primary_key", "sort_key", "cache_key", "top_k", "temperature", "model", "eos_token", "pad_token", "stop_token",
    "num_keys", "turkey_count", "input_key", "output_key", "key_count", "sort_keys", "idempotency_key",
    "prompt_tokens", "completion_tokens", "max_output_tokens", "budget_tokens", "tokens_per_minute", "stop_tokens",
    "fi.experiment.param.max_tokens", "llm.token_count.completion_details.reasoning",
    "gen_ai.usage.cache_creation_input_tokens",
])
def test_non_secret_config_keys_are_not_credentials(key):
    assert not is_credential_key(key)


def test_max_tokens_and_other_numeric_config_survive_redaction():
    r = Redactor([])
    params = {"model": "gpt-4.1-nano", "max_tokens": 256, "max_completion_tokens": 300, "temperature": 0.0,
              "top_k": 40, "seed": 7, "stream": False, "stop": None, "eos_token": "</s>", "token_count": 12}
    assert r.value(params) == params


def test_credentials_still_go_by_key_whatever_their_nesting():
    r = Redactor([])
    got = r.value({
        "api_key": "abc", "Authorization": "x", "nested": {"password": "p", "keep": "me"},
        "headers": [{"x-api-key": "k1"}, {"cookie": "c=1"}], "credentials": {"user": "bob", "pin": "1234"},
        "access_token": b"raw-bytes", "client_secret": ["a", "b"], "empty_secret": "",
    })
    assert got == {
        "api_key": REDACTED, "Authorization": REDACTED, "nested": {"password": REDACTED, "keep": "me"},
        "headers": [{"x-api-key": REDACTED}, {"cookie": REDACTED}],
        "credentials": {"user": REDACTED, "pin": REDACTED},
        "access_token": REDACTED, "client_secret": [REDACTED, REDACTED], "empty_secret": "",
    }


def test_numbers_and_flags_under_a_credential_key_are_config_not_secrets():
    r = Redactor([])
    assert r.value({"api_key_set": True, "secret_rotation_days": 30, "token": None, "password": "hunter22"}) == {
        "api_key_set": True, "secret_rotation_days": 30, "token": None, "password": REDACTED}


def test_an_object_under_a_credential_key_is_never_kept_as_is():
    class SecretStr:
        def __repr__(self):
            return "SecretStr('...')"

    assert Redactor([]).value({"api_key": SecretStr()}) == {"api_key": REDACTED}


def test_credential_shaped_values_go_under_any_key_of_config():
    r = Redactor([])
    got = r.value({
        "note": f"use {OPENAI_SHAPED} for this", "provider_key": ANTHROPIC_SHAPED,
        "header": "Bearer 9f8e7d6c5b4a39281706f5e4d3c2b1a0", "jwt": JWT_SHAPED,
        "aws": "AKIAIOSFODNN7EXAMPLE", "argv": ["--param", f"k={OPENAI_SHAPED}"],
        "pem": "-----BEGIN RSA PRIVATE KEY-----\nMIIEow\n-----END RSA PRIVATE KEY-----",
    })
    assert got == {
        "note": f"use {REDACTED} for this", "provider_key": REDACTED, "header": REDACTED, "jwt": REDACTED,
        "aws": REDACTED, "argv": ["--param", f"k={REDACTED}"], "pem": REDACTED,
    }


@pytest.mark.parametrize("text", [
    "/data/sk-learn-examples-dataset.jsonl",  # a path: lowercase words, no digits
    "sk-short",
    "Bearer tokens are rotated daily",  # prose
    "6cc0342b1f0e9d8c7b6a5f4e3d2c1b0a9f8e7d6c",  # a git sha
    "7d8b1d7e-6a3c-4f4f-9c0e-6e2b0d6b1a11",  # a uuid
    "gpt-4.1-nano", "claude-haiku-5-5", "xai-grok", "task-ABCDEFGHIJKLMNOPQRSTUVWXYZ",
])
def test_non_secret_strings_keep_their_shape(text):
    assert redact_shapes(text) == text
    assert Redactor([]).value({"value": text}) == {"value": text}


def test_name_value_strings_with_a_credential_name_lose_the_value():
    """argv tokens (journaled in the run specification and sent as run metadata): ``--param api_key=…`` is redacted by
    the name in the token, even when the value has no known shape and is in no environment variable."""
    r = Redactor([])
    argv = ["run", "agent.py:task", "--param", "api_key=plain-value-no-shape", "--param", "max_tokens=256",
            "--param-str", "x-auth-token=abc", "--token=abc", "--param", "keyword=refund", "--dataset", "a=b.jsonl"]
    assert r.value(argv) == ["run", "agent.py:task", "--param", f"api_key={REDACTED}", "--param", "max_tokens=256",
                             "--param-str", f"x-auth-token={REDACTED}", f"--token={REDACTED}", "--param",
                             "keyword=refund", "--dataset", "a=b.jsonl"]
    assert r.value({"note": "password=hunter22"}) == {"note": f"password={REDACTED}"}
    assert r.value("max_tokens=256") == "max_tokens=256"


def test_the_resume_line_keeps_max_tokens_and_drops_a_param_key():
    from fi.experiments._cli.commands import resume_line

    line = resume_line(["run", "a.py:task", "--param", "max_tokens=256", "--param", "api_key=plain-value-no-shape"],
                       "R1")
    assert line == f"futureagi-py run a.py:task --param max_tokens=256 --param 'api_key={REDACTED}' --resume R1"


def test_outputs_are_redacted_by_known_secrets_only():
    r = Redactor(["supersecret-1"])
    out = {"answer": f"shipped {OPENAI_SHAPED}", "api_key": "model said this", "msg": "a supersecret-1 b"}
    assert r.value(out, by_key=False) == {"answer": f"shipped {OPENAI_SHAPED}", "api_key": "model said this",
                                         "msg": f"a {REDACTED} b"}


def test_the_journaled_plan_keeps_max_tokens_and_redacts_the_key(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-unit-test-0123456789")
    result = experiments.run([{"q": 1}], lambda row: "ok", upload=False, progress=False, trace=False,
                             params={"model": "m", "max_tokens": 256, "temperature": 0.0, "api_key": "abc",
                                     "base_url_token": "sk-unit-test-0123456789"})
    plan = json.loads((Path(result.journal_dir) / "plan.json").read_text())
    assert plan["params"] == {"model": "m", "max_tokens": 256, "temperature": 0.0, "api_key": REDACTED,
                              "base_url_token": REDACTED}


def test_the_uploaded_model_config_keeps_max_tokens_and_redacts_the_key():
    server = ContractServer()
    experiments.run(experiments.dataset([{"question": "q1", "expected": "a"}], name="t-redaction"), lambda row: "a", [],
                    client=client_for(server),
                    trace=False, progress=False, metadata={"max_tokens_note": "kept", "password": "pw"},
                    params={"model": "gpt-4.1-nano", "max_tokens": 256, "max_completion_tokens": 300,
                            "api_key": OPENAI_SHAPED, "note": f"key {OPENAI_SHAPED}"})
    [run] = server.runs.values()
    body = run["body"]
    assert body["model_config"] == {"model": "gpt-4.1-nano", "max_tokens": 256, "max_completion_tokens": 300,
                                    "api_key": REDACTED, "note": f"key {REDACTED}"}
    assert body["metadata"]["max_tokens_note"] == "kept" and body["metadata"]["password"] == REDACTED
    assert OPENAI_SHAPED not in json.dumps(body)


def test_span_param_attributes_keep_max_tokens():
    pytest.importorskip("opentelemetry.sdk")  # trace=True (absent on 3.14, TA-1)
    seen = {}

    @experiments.evaluator(name="root")
    def root(trace):
        seen["attrs"] = next(s for s in trace if s["name"] == "experiment.trial")["attributes"]
        return 1.0

    experiments.run([{"q": 1}], lambda row: "ok", [root], upload=False, progress=False, instrument=False,
                    params={"max_tokens": 256, "api_key": "abc"})
    assert seen["attrs"]["fi.experiment.param.max_tokens"] == "256"
    assert seen["attrs"]["fi.experiment.param.api_key"] == REDACTED


@pytest.mark.parametrize("key", WAVE0_NAMES)
def test_a_plain_secret_under_a_name_wave0_redacted_is_still_redacted(key):
    assert Redactor([]).value({key: HEX32}) == {key: REDACTED}


def test_wave0_names_are_redacted_in_the_plan_the_upload_and_the_span_params():
    """M1 end to end: plan.json params and argv, the uploaded model_config and metadata, the
    ``fi.experiment.param.*`` attributes (baggage: on every span, next test) and the export scrubber."""
    params = {k: HEX32 for k in WAVE0_NAMES}
    server = ContractServer()
    result = experiments.run(experiments.dataset([{"question": "q1", "expected": "a"}], name="t-redaction"), lambda row: "a", [],
                    client=client_for(server),
                             trace=False, progress=False, params={**params, "max_tokens": 256},
                             metadata={"openai_key": HEX32, "max_tokens_note": "kept"})
    plan_text = (Path(result.journal_dir) / "plan.json").read_text()
    plan = json.loads(plan_text)
    assert plan["params"] == {**{k: REDACTED for k in WAVE0_NAMES}, "max_tokens": 256}
    assert HEX32 not in plan_text
    [run] = server.runs.values()
    assert run["body"]["model_config"] == {**{k: REDACTED for k in WAVE0_NAMES}, "max_tokens": 256}
    assert run["body"]["metadata"]["openai_key"] == REDACTED and run["body"]["metadata"]["max_tokens_note"] == "kept"
    assert HEX32 not in json.dumps(run["body"])


def test_wave0_names_are_scrubbed_from_exported_span_params():
    pytest.importorskip("opentelemetry.sdk")  # the exporter (absent on 3.14, TA-1)
    from fi.experiments._tracing.export import scrub_attributes

    spans = scrub_attributes(Redactor([]), {f"fi.experiment.param.{k}": HEX32 for k in WAVE0_NAMES})
    assert set(spans.values()) == {REDACTED}
    assert scrub_attributes(Redactor([]), {"fi.experiment.param.max_tokens": "256"}) == {
        "fi.experiment.param.max_tokens": "256"}


def test_argv_forms_lose_a_credential_value_and_keep_the_rest():
    """``--param openai_key=…`` (M1), ``--param=api_key=…``, an eval spec ``NAME:k=v,...`` (S8) and a JSON
    ``--param`` value lose the credential's value only."""
    r = Redactor([])
    argv = ["run", "a.py:task", "--param", f"openai_key={HEX32}", "--param", f"key={HEX32}", f"--param=api_key={HEX32}",
            "--eval", f"judge:api_key={HEX32},model=gpt-4.1-nano", "--param", f'cfg={{"azure_key": "{HEX32}", "n": 2}}',
            "--param", "max_tokens=256", "--param", f"tokens={HEX32}"]
    got = r.value(argv)
    assert HEX32 not in json.dumps(got)
    assert got == ["run", "a.py:task", "--param", f"openai_key={REDACTED}", "--param", f"key={REDACTED}",
                   f"--param=api_key={REDACTED}", "--eval", f"judge:api_key={REDACTED},model=gpt-4.1-nano",
                   "--param", f'cfg={{"azure_key": "{REDACTED}", "n": 2}}', "--param", "max_tokens=256",
                   "--param", f"tokens={REDACTED}"]


def test_google_and_hugging_face_key_shapes_go_under_any_key():
    """S3: Gemini / AI Studio ``AIza…`` keys and Hugging Face ``hf_…`` tokens under a neutral key."""
    r = Redactor([])
    got = r.value({"note": f"use {GOOGLE_SHAPED} here", "x": HF_SHAPED, "argv": ["--param-str", f"g={GOOGLE_SHAPED}"]})
    assert got == {"note": f"use {REDACTED} here", "x": REDACTED, "argv": ["--param-str", f"g={REDACTED}"]}
    for text in ("hf_hub_download", "hf_transfer", "AIza", "repo: hf-internal-testing/tiny-random-gpt2"):
        assert redact_shapes(text) == text
