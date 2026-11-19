"""Management wire contract tests use only httpx mock transports, not backend acceptance."""
import asyncio
import importlib
import inspect
import json
import re
import runpy
from pathlib import Path

import httpx
import pytest

from fi import AsyncFutureAGIClient, FutureAGIClient
from fi._core.fa_management import GatewayConfigWarning, GatewayConfigWarningError
from fi.errors import BadRequestError, ConfigurationError, PermissionDeniedError, UnexpectedRedirectError

ROOT = Path(__file__).resolve().parents[2]
ROWS = json.loads((ROOT / "openapi/fa-mgmt/generated/operations.json").read_text())


def make(handler, asynchronous=False, **kwargs):
    cls = AsyncFutureAGIClient if asynchronous else FutureAGIClient
    options = dict(api_key="fixture-api", secret_key="fixture-secret", base_url="http://localhost:9012",
                   workspace_id="workspace-fixture", organization_id="organization-fixture", retries=0)
    options.update(kwargs)
    client = cls(**options)
    client._management.shared._recorder._inner = httpx.MockTransport(handler)
    return client


def invoke(client, row, **extra):
    target = client
    for name in row["name"].split("."):
        target = getattr(target, name)
    args = {p: "sample" for p in row["path_params"] if p not in row.get("fixed_path", {})}
    if row.get("body_arg"):
        args[row["body_arg"]] = {"cache": {"enabled": True, "default_ttl": None}} if row["name"].startswith("gateway.config.") else {"display_name": "sample"}
    args.update(extra)
    return target(**args)


@pytest.mark.parametrize("asynchronous", [False, True])
@pytest.mark.parametrize("row", ROWS, ids=lambda r: r["name"])
def test_every_operation_method_path_auth_body_and_raw_metadata(row, asynchronous):
    calls = []
    def handler(request):
        calls.append(request)
        assert request.headers["x-api-key"] == "fixture-api"
        assert request.headers["x-secret-key"] == "fixture-secret"
        assert request.headers["x-workspace-id"] == "workspace-fixture"
        assert request.headers["x-organization-id"] == "organization-fixture"
        assert "authorization" not in request.headers
        assert "idempotency-key" not in request.headers
        assert request.extensions["fi.retry"]["class"] == row["retry_class"]
        value = {"id": "answer", "user": "person"}
        if row.get("page"):
            value = {"count": 1, "next": None, "previous": None, "results": [value]}
        return httpx.Response(200, json={"status": True, "result": value}, headers={"x-request-id": "request-fixture"})
    client = make(handler, asynchronous)
    result = invoke(client, row)
    if asynchronous:
        result = asyncio.run(result)
    assert len(calls) == 1
    assert calls[0].method == row["method"]
    path = row["path"]
    for p in row["path_params"]:
        path = path.replace("{"+p+"}", row.get("fixed_path", {}).get(p, "sample"))
    assert calls[0].url.path == path
    if row.get("body_arg"):
        body = json.loads(calls[0].content)
        if row["name"].startswith("gateway.config."):
            assert body == {"cache": {"enabled": True, "default_ttl": None}}
    if row.get("page"):
        assert result.items == [{"id": "answer", "user": "person"}]
    else:
        assert result == {"id": "answer", "user": "person"}


@pytest.mark.parametrize("asynchronous", [False, True])
@pytest.mark.parametrize("mode", ["link", "totals"])
def test_three_drf_pages_with_filters_and_no_url_following(asynchronous, mode):
    seen = []
    def handler(request):
        seen.append(request)
        number = int(request.url.params["page"])
        assert request.url.host == "localhost"
        assert request.url.params["limit"] == "1"
        page = {"results": [{"id": str(number), "user": "person"}], "count": 3, "current_page": number, "total_pages": 3}
        if mode == "link":
            page["next"] = "https://untrusted.invalid/wrong?page="+str(number+1) if number < 3 else None
        return httpx.Response(200, json={"status": True, "result": page})
    client = make(handler, asynchronous)
    async def consume():
        return [row async for row in await client.gateway.keys.list(limit=1)]
    result = asyncio.run(consume()) if asynchronous else list(client.gateway.keys.list(limit=1))
    assert [r["id"] for r in result] == ["1", "2", "3"]
    assert len(seen) == 3


@pytest.mark.parametrize("asynchronous", [False, True])
@pytest.mark.parametrize("code,status,error", [("secret_in_config", 400, BadRequestError), ("KEY_LIMIT_NOT_ENFORCED", 400, BadRequestError), ("permission_denied", 403, PermissionDeniedError)])
def test_fa_error_shape_preserves_code_and_request_id(asynchronous, code, status, error):
    client = make(lambda r: httpx.Response(status, json={"status": False, "result": {"error_code": code, "message": "denied"}}, headers={"x-request-id": "request-fixture"}), asynchronous)
    with pytest.raises(error) as caught:
        result = client.gateway.config.update({"cache": {"enabled": True}})
        if asynchronous:
            asyncio.run(result)
    assert caught.value.code == code
    assert caught.value.request_id == "request-fixture"


@pytest.mark.parametrize("asynchronous", [False, True])
def test_warning_and_strict_mode_after_mutation(asynchronous):
    result = {"version": 3, "gateway_synced": False, "warnings": [{"code": "unsupported_routing_key"}]}
    client = make(lambda r: httpx.Response(200, json={"status": True, "result": result}), asynchronous)
    with pytest.warns(GatewayConfigWarning):
        value = client.gateway.config.update({"cache": {"enabled": True}})
        if asynchronous:
            value = asyncio.run(value)
    assert value == result
    with pytest.raises(GatewayConfigWarningError):
        value = client.gateway.config.update({"cache": {"enabled": True}}, strict=True)
        if asynchronous:
            asyncio.run(value)


@pytest.mark.parametrize("asynchronous", [False, True])
@pytest.mark.parametrize("secret", ["credential-fixture-sensitive", "abc"])
def test_provider_masking_and_reflected_write_secret(asynchronous, secret):
    client = make(lambda r: httpx.Response(200, json={"status": True, "result": {"credentials": {"api_key": secret, "short": "abc", "nested": [secret]}, "name": "safe"}}), asynchronous)
    value = client.gateway.provider_credentials.get("provider")
    if asynchronous:
        value = asyncio.run(value)
    assert secret not in repr(value)
    assert "abc" not in repr(value)
    assert value["name"] == "safe"
    client = make(lambda r: httpx.Response(400, json={"code": "invalid_credential", "message": "invalid "+secret}), asynchronous)
    with pytest.raises(BadRequestError) as caught:
        value = client.gateway.provider_credentials.rotate("provider", {"credentials": {"api_key": secret}})
        if asynchronous:
            asyncio.run(value)
    assert secret not in str(caught.value)
    assert secret not in repr(caught.value.payload)


@pytest.mark.parametrize("asynchronous", [False, True])
@pytest.mark.parametrize("options", [{"api_key": "sk-agentcc-fixture"}, {"platform_token": "token-fixture"}])
def test_control_plane_refuses_gateway_and_ee_credentials_before_send(asynchronous, options):
    client = make(lambda r: pytest.fail("wrong credential reached transport"), asynchronous, **options)
    with pytest.raises(ConfigurationError):
        value = client.gateway.config.get_active()
        if asynchronous:
            asyncio.run(value)


@pytest.mark.parametrize("asynchronous", [False, True])
@pytest.mark.parametrize("patch", [{"user": "other"}, {"owner": "org"}, {"rate_limit_rpm": 30}, {"metadata": {"allowed_ips": []}}])
def test_keys_have_no_create_or_ownership_rebinding(asynchronous, patch):
    client = make(lambda r: pytest.fail("forbidden mutation reached transport"), asynchronous)
    assert not hasattr(client.gateway.keys, "create")
    assert not hasattr(client.gateway.keys, "sync")
    with pytest.raises(ConfigurationError):
        value = client.gateway.keys.update("key", patch)
        if asynchronous:
            asyncio.run(value)


@pytest.mark.parametrize("asynchronous", [False, True])
def test_raw_metadata_redirects_and_option_copies(asynchronous):
    client = make(lambda r: httpx.Response(200, json={"status": True, "result": None}, headers={"x-request-id": "raw-id"}), asynchronous)
    copy = client.with_options(timeout=2, retries=0)
    assert copy._management.shared is client._management.shared
    value = copy.gateway.config.with_raw_response.get_active()
    if asynchronous:
        value = asyncio.run(value)
    assert value.data is None and value.request_id == "raw-id"
    client = make(lambda r: httpx.Response(302, headers={"location": "https://untrusted.invalid/"}), asynchronous)
    with pytest.raises(UnexpectedRedirectError):
        value = client.gateway.config.get_active()
        if asynchronous:
            asyncio.run(value)


@pytest.mark.parametrize("asynchronous", [False, True])
def test_legacy_organization_keys_are_not_presented_as_personal(asynchronous):
    client = make(lambda r: httpx.Response(200, json={"status": True, "result": {"id": "legacy", "user": None}}), asynchronous)
    with pytest.raises(ConfigurationError) as caught:
        value = client.gateway.keys.get("legacy")
        if asynchronous:
            asyncio.run(value)
    assert caught.value.code == "non_personal_gateway_key"


def test_generated_surface_has_language_twins_and_excludes_unenforced_fields():
    generated = runpy.run_path(str(ROOT / "scripts/fa-management/generate.py"))
    for path, content in generated["generate"]().items():
        assert path.read_text() == content
    models = importlib.import_module("fi.generated.platform.fa_management.models")
    assert "semantic" not in models.CacheConfig.__annotations__
    assert "conditional_routes" not in models.RoutingConfig.__annotations__
    assert "default_model" not in models.RoutingConfig.__annotations__
    mapping = json.loads((ROOT / "openapi/fa-mgmt/wrapper-map.json").read_text())
    client = make(lambda r: pytest.fail("signature inspection must not send"))
    for row in mapping["operations"]:
        assert row["python"] == row["python_async"]
        assert row["typescript"]
        if row["python"] != "NOT-OFFERED":
            target = client
            for part in row["python"].split("."):
                target = getattr(target, part)
            args = [p.name for p in inspect.signature(target).parameters.values() if p.kind == p.POSITIONAL_OR_KEYWORD]
            assert args == row["arguments"]
    assert all("/accounts/keys/" not in row["path"] for row in ROWS)


@pytest.mark.parametrize("asynchronous", [False, True])
def test_create_version_documents_replacement_and_default_reset(asynchronous):
    client = make(lambda r: pytest.fail("documentation inspection must not send"), asynchronous)
    doc = inspect.getdoc(client.gateway.config.create_version)
    assert "omitted sections reset to server defaults" in doc
    assert "not copied from the active version" in doc
    assert "config.update" in doc
    assert "omitted sections are retained" not in doc


@pytest.mark.parametrize("row", ROWS, ids=lambda r: r["name"])
def test_scoped_swagger_preserves_required_path_parameters(row):
    source = json.loads((ROOT / "openapi/fa-mgmt/swagger.json").read_text())
    scoped = json.loads((ROOT / "openapi/fa-mgmt/generated/spec.json").read_text())
    path = row["path"]
    method = row["method"].lower()
    def parameters(spec):
        item = spec["paths"][path]
        # Operation parameters override path-item parameters by (name, in).
        return {(p["name"], p["in"]): p for p in item.get("parameters", []) + item[method].get("parameters", [])}
    expected = {k: v for k, v in parameters(source).items() if k[1] == "path"}
    actual = {k: v for k, v in parameters(scoped).items() if k[1] == "path"}
    assert actual == expected
    assert {name for name, _ in actual} == set(re.findall(r"\{([^}]+)\}", path))
    assert all(p.get("required") is True and p.get("type") for p in actual.values())


def test_configuration_write_types_intersect_management_and_gateway_contracts():
    source = ROOT / "openapi/fa-mgmt"
    swagger = json.loads((source / "swagger.json").read_text())
    admin = json.loads((source / "admin.schema.json").read_text())
    excluded = json.loads((source / "surface.json").read_text())["untyped_config_fields"]
    accepted = swagger["definitions"]["GatewayConfigPatchRequest"]["properties"]
    expected = set(accepted) & set(admin["$defs"]["OrgConfig"]["properties"]) - set(excluded["OrgConfig"])
    models = importlib.import_module("fi.generated.platform.fa_management.models")
    assert set(models.ConfigSections.__annotations__) == expected
    assert not {"identity", "managed_models", "tools"} & set(models.ConfigSections.__annotations__)
    for section in expected:
        schema = admin["$defs"]["OrgConfig"]["properties"][section]
        if "$ref" in schema:
            name = schema["$ref"].rsplit("/", 1)[1]
            fields = set(admin["$defs"][name].get("properties", {})) - set(excluded.get(name, []))
            assert set(getattr(models, name).__annotations__) == fields


@pytest.mark.parametrize("asynchronous", [False, True])
@pytest.mark.parametrize("secret", ["x", "xy", "abc", 'xy"\\', "credential-fixture-sensitive"])
@pytest.mark.parametrize("method", ["create", "update", "rotate"])
def test_provider_write_responses_scrub_reflection_outside_credential_fields(asynchronous, secret, method):
    body = {"credentials": {"api_key": secret}}
    response = {"credentials": {"api_key": secret}, "diagnostic": "accepted " + secret,
                "details": [{"echo_" + secret: "submitted " + secret}], "name": "safe"}
    def handler(request):
        assert json.loads(request.content) == body
        return httpx.Response(200, json={"status": True, "result": response})
    client = make(handler, asynchronous)
    target = getattr(client.gateway.provider_credentials.with_raw_response, method)
    result = target(*([] if method == "create" else ["provider"]), body)
    if asynchronous:
        result = asyncio.run(result)
    assert result.data["diagnostic"] == "accepted [redacted]"
    # JSON keys are wire schema, not credential values, even when they collide.
    assert result.data["details"] == [{"echo_" + secret: "submitted [redacted]"}]
    assert result.data["name"] == "safe"
    assert result.data["credentials"] == {"api_key": "[REDACTED]"}
    assert set(result.data) == set(response)
    assert response["diagnostic"] == "accepted " + secret
