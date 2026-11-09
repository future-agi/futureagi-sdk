"""The prompt execution examples must select a version and request a run."""

from __future__ import annotations

import json
import re

import httpx
from fi.platform import Client

from .test_prompt_lookup_examples import example


def test_python_run_example_sends_execution_parameters():
    requests = []

    def handler(request):
        requests.append(request)
        return httpx.Response(200, json={})

    with httpx.Client(transport=httpx.MockTransport(handler)) as http:
        with Client(
            api_key="test-key", secret_key="test-secret",
            base_url="https://api.example.test", http_client=http,
        ) as client:
            exec(example("prompts.run", "python"), {"client": client})
            exec(example("prompts.run_status", "python"), {"client": client})
    run, status = requests
    assert run.method == "POST"
    assert run.url.path.endswith("/run_template/")
    assert json.loads(run.content) == {"version": "v1", "is_run": "prompt"}
    assert status.method == "GET"
    assert status.url.path.endswith("/get-run-status/")
    assert status.url.params["template_version"] == "v1"
    assert status.url.path.rsplit("/", 2)[0] == run.url.path.rsplit("/", 2)[0]


def test_typescript_run_example_includes_execution_parameters():
    source = example("prompts.run", "typescript")
    fields = dict(re.findall(r'(\w+):\s*("[^"\n]*")', source))
    assert {name: json.loads(value) for name, value in fields.items()} == {
        "version": "v1", "is_run": "prompt",
    }
    status = example("prompts.run_status", "typescript")
    assert "client.prompts.runStatus(" in status
    assert 'template_version: "v1"' in status
