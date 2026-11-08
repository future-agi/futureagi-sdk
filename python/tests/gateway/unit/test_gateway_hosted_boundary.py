"""The hosted compatibility default is not a unit-client or environment bypass."""

import ast
import asyncio
from pathlib import Path

import httpx
import pytest

from fi.gateway._deprecation import AgentCCDeprecationWarning

from fi.gateway import AgentCC, AgentCCError, AsyncAgentCC
from fi.gateway._fi import AsyncGateway, Gateway

GATEWAY = Path(__file__).resolve().parents[3] / "fi" / "gateway"
HOSTED_NAMES = {"AGENTCC_GATEWAY_URL", "DEFAULT_GATEWAY_URL", "resolve_wrapper_settings"}
ENV_NAMES = (
    "FI_GATEWAY_API_KEY", "AGENTCC_API_KEY", "FI_GATEWAY_BASE_URL",
    "FI_GATEWAY_URL", "AGENTCC_BASE_URL", "FI_API_KEY", "FI_SECRET_KEY",
)


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    for name in ENV_NAMES:
        monkeypatch.delenv(name, raising=False)


def _uses(text, module):
    sites = []

    def visit(node, scope="<module>"):
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            scope = node.name if scope == "<module>" else f"{scope}.{node.name}"
        if isinstance(node, ast.ImportFrom):
            for alias in node.names:
                if alias.name in HOSTED_NAMES:
                    sites.append((module, scope, "import", node.module,
                                  alias.name, alias.asname or alias.name))
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
            if node.id in HOSTED_NAMES or (module == "_fi.py" and node.id == "_resolve"):
                sites.append((module, scope, "load", node.id))
        if isinstance(node, ast.Attribute) and node.attr in HOSTED_NAMES:
            sites.append((module, scope, "attribute", node.attr))
        for child in ast.iter_child_nodes(node):
            visit(child, scope)

    visit(ast.parse(text))
    return sites


def test_hosted_uses_are_exactly_the_released_wrapper_and_helper_sites():
    sites = []
    for path in sorted(GATEWAY.rglob("*.py")):
        if "management" not in path.relative_to(GATEWAY).parts:
            sites.extend(_uses(path.read_text(), path.relative_to(GATEWAY).as_posix()))
    assert sorted(sites) == sorted([
        ("__init__.py", "<module>", "import", "fi.gateway._constants", "AGENTCC_GATEWAY_URL", "AGENTCC_GATEWAY_URL"),
        ("_env.py", "resolve_wrapper_settings", "import", "fi.gateway._constants", "AGENTCC_GATEWAY_URL", "AGENTCC_GATEWAY_URL"),
        ("_env.py", "resolve_wrapper_settings", "load", "AGENTCC_GATEWAY_URL"),
        ("_fi.py", "<module>", "import", "fi.gateway._env", "resolve_wrapper_settings", "resolve_wrapper_settings"),
        ("_fi.py", "_resolve", "load", "resolve_wrapper_settings"),
        ("_fi.py", "Gateway.__init__", "load", "_resolve"),
        ("_fi.py", "AsyncGateway.__init__", "load", "_resolve"),
        ("_utils.py", "return_raw_request", "import", "fi.gateway._env", "resolve_wrapper_settings", "resolve_wrapper_settings"),
        ("_utils.py", "return_raw_request", "load", "resolve_wrapper_settings"),
    ])


def test_the_use_site_gate_detects_a_new_consumer_and_an_alias():
    assert _uses("def leak():\n    return AGENTCC_GATEWAY_URL\n", "_env.py") == [
        ("_env.py", "leak", "load", "AGENTCC_GATEWAY_URL"),
    ]
    assert _uses("from fi.gateway._constants import AGENTCC_GATEWAY_URL as host\n", "other.py") == [
        ("other.py", "<module>", "import", "fi.gateway._constants", "AGENTCC_GATEWAY_URL", "host"),
    ]


@pytest.mark.parametrize("cls", [AgentCC, AsyncAgentCC])
def test_unit_clients_still_require_an_explicit_origin(cls):
    with pytest.raises(AgentCCError, match="base_url is required"):
        cls(api_key="unit-key")


@pytest.mark.parametrize("cls", [Gateway, AsyncGateway])
def test_only_released_wrappers_default_to_the_fixed_https_origin(cls):
    with pytest.warns(DeprecationWarning, match="deprecated"):
        client = cls(api_key="unit-key")
    assert client._base_url == "https://gateway.futureagi.com"
    assert client._base_client is None


@pytest.mark.parametrize("cls", [Gateway, AsyncGateway])
@pytest.mark.parametrize("name", ["FI_GATEWAY_BASE_URL", "FI_GATEWAY_URL", "AGENTCC_BASE_URL"])
def test_environment_origins_are_validated_instead_of_falling_back(cls, name, monkeypatch):
    monkeypatch.setenv(name, "http://unsafe.example.test")
    seen, retained = [], []

    def handle(request):
        retained.append(request)
        seen.append(httpx.Request(request.method, request.url, headers=list(request.headers.raw)))
        return httpx.Response(200, json={"object": "list", "data": []})

    http_cls = httpx.AsyncClient if cls is AsyncGateway else httpx.Client
    http = http_cls(transport=httpx.MockTransport(handle))
    with pytest.warns(DeprecationWarning):
        client = cls(api_key="unit-key", http_client=http)
    with pytest.warns(AgentCCDeprecationWarning, match="sending gateway credentials in cleartext"):
        if cls is AsyncGateway:
            async def send():
                await client.models.list()
                await http.aclose()
            asyncio.run(send())
        else:
            client.models.list()
            http.close()
    assert len(seen) == 1
    assert str(seen[0].url) == "http://unsafe.example.test/v1/models"
    assert seen[0].headers["authorization"] == "Bearer unit-key"
    assert retained[0].headers["authorization"] == "[REDACTED]"
    monkeypatch.setenv(name, "https://explicit.example.test/v1/")
    with pytest.warns(DeprecationWarning):
        client = cls(api_key="unit-key")
    assert client._base_url == "https://explicit.example.test"
