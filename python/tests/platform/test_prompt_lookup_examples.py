"""Prompt lookup examples must send the selectors required by the API."""

from __future__ import annotations

import json
import re
from pathlib import Path

import httpx
import pytest

from fi.platform import Client

REFERENCE = Path(__file__).resolve().parents[3] / "docs/sdk-reference/prompts.mdx"
LOOKUPS = [
    ("prompts.get_by_name", "prompts.getByName", {"name": "customer_support"}),
    (
        "prompts.labels.get_template",
        "prompts.labels.getTemplate",
        {"name": "customer_support", "label": "production"},
    ),
    (
        "prompts.labels.for_template",
        "prompts.labels.forTemplate",
        {"template_name": "customer_support"},
    ),
]


def section(operation: str) -> str:
    return REFERENCE.read_text().split(f"### {operation}\n", 1)[1].split("\n### ", 1)[0]


def example(operation: str, language: str) -> str:
    match = re.search(rf"```{language} [^\n]+\n(.*?)\n```", section(operation), re.S)
    assert match is not None
    return match.group(1)


@pytest.mark.parametrize("operation,ts_method,expected", LOOKUPS)
def test_python_lookup_examples_send_selectors(operation, ts_method, expected):
    requests = []

    def handler(request):
        requests.append(request)
        return httpx.Response(200, json={})

    with httpx.Client(transport=httpx.MockTransport(handler)) as http:
        with Client(
            api_key="test-key", secret_key="test-secret",
            base_url="https://api.example.test", http_client=http,
        ) as client:
            exec(example(operation, "python"), {"client": client})
    assert len(requests) == 1
    assert requests[0].method == "GET"
    for name, value in expected.items():
        assert requests[0].url.params.get(name) == value


@pytest.mark.parametrize("operation,ts_method,expected", LOOKUPS)
def test_typescript_lookup_examples_include_selectors(operation, ts_method, expected):
    source = example(operation, "typescript")
    assert f"client.{ts_method}(" in source
    # These examples use string-valued selectors in an object literal.
    fields = dict(re.findall(r'(\w+):\s*("[^"\n]*")', source))
    assert {name: json.loads(value) for name, value in fields.items()} == expected


@pytest.mark.parametrize("operation", ["prompts.get_by_name", "prompts.labels.get_template"])
def test_lookup_name_is_documented_as_required(operation):
    assert '<ParamField query="name" type="string" required' in section(operation)


@pytest.mark.parametrize(
    "operation,field,alternative",
    [
        ("prompts.labels.get_template", "label", "version"),
        ("prompts.labels.get_template", "version", "label"),
        ("prompts.labels.for_template", "template_name", "template_id"),
        ("prompts.labels.for_template", "template_id", "template_name"),
    ],
)
def test_alternative_selectors_document_the_requirement(operation, field, alternative):
    match = re.search(
        rf'<ParamField query="{field}"[^>]*>(.*?)</ParamField>', section(operation), re.S,
    )
    assert match is not None
    assert f"Required unless `{alternative}` is supplied." in match.group(1)
