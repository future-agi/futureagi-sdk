import ast
from pathlib import Path

import httpx
import pytest

import fi
from fi import errors


@pytest.mark.asyncio
@pytest.mark.parametrize("resource", ["prompts", "knowledge_bases", "scores"])
@pytest.mark.parametrize("status,error", [
    (400, errors.BadRequestError), (401, errors.AuthenticationError),
    (403, errors.PermissionDeniedError), (404, errors.NotFoundError),
    (409, errors.ConflictError), (422, errors.UnprocessableEntityError),
    (429, errors.RateLimitError), (500, errors.ServerError),
])
async def test_resources_share_error_mapping(resources, resource, status, error):
    resources.replies.append(httpx.Response(status, json={"code": "test_code", "detail": "refused"}, headers={"x-request-id": "same-request"}))
    with pytest.raises(error) as caught:
        await resources.call(getattr(resources, resource).list)
    assert caught.value.code == "test_code"
    assert caught.value.request_id == "same-request"
    assert len(resources.requests) == 1


@pytest.mark.asyncio
@pytest.mark.parametrize("operation", ["list", "for_source"])
async def test_logical_errors_keep_response_headers(resources, operation):
    resources.replies.append(httpx.Response(
        200, json={"status": False, "code": "invalid_score", "result": "bad score"},
        headers={"x-request-id": "logical-request", "Retry-After": "7"},
    ))
    args = ("observation_span", "span1") if operation == "for_source" else ()
    with pytest.raises(errors.BadRequestError) as caught:
        await resources.call(getattr(resources.root.scores, operation), *args)
    assert caught.value.code == "invalid_score"
    assert caught.value.request_id == "logical-request"
    assert caught.value.retry_after == 7
    assert len(resources.requests) == 1


@pytest.mark.asyncio
async def test_core_resources_handle_invalid_json_and_empty_success(resources):
    resources.replies.extend([httpx.Response(200, content=b"<html>not JSON</html>"), httpx.Response(204)])
    with pytest.raises(errors.FutureAGIAPIError) as caught:
        await resources.call(resources.prompts.list)
    assert caught.value.code == "invalid_json"
    assert await resources.call(resources.prompts.delete, "p1") is None


FI = Path(fi.__file__).resolve().parent
#: What every module under fi/_core may import (the repository's platform import gate).
PLATFORM_ALLOWED = ("fi._sdk_exception", "fi._credentials", "fi._http", "fi.errors", "fi._core", "fi.generated.platform")
#: Namespace modules also wrap the generated core client and share one private adapter.
NAMESPACE_ALLOWED = (*PLATFORM_ALLOWED, "fi.generated.openapi_client", "fi._resources", "fi.prompts", "fi.knowledge_bases", "fi.scores")
NAMESPACES = ("prompts", "knowledge_bases", "scores")


def _fi_imports(path):
    for node in ast.walk(ast.parse(path.read_text())):
        if isinstance(node, ast.ImportFrom) and node.module and node.module.startswith("fi."):
            yield node.module
        elif isinstance(node, ast.Import):
            yield from (alias.name for alias in node.names if alias.name.startswith("fi."))


def _module_file(name):
    base = FI.parent.joinpath(*name.split("."))
    return next((path for path in (base.with_suffix(".py"), base / "__init__.py") if path.exists()), None)


def _namespace_modules():
    """The namespace packages' files, the private modules they share, and the platform modules they reach.

    A platform module (``fi._core``, ``fi.errors`` ...) is checked but not followed: the repository's
    platform gate covers the rest of that tree.
    """
    pending = sorted(path for name in NAMESPACES for path in (FI / name).rglob("*.py"))
    seen = set()
    while pending:
        path = pending.pop()
        if path in seen:
            continue
        seen.add(path)
        for name in _fi_imports(path):
            found = None if name.startswith("fi.generated.") else _module_file(name)
            if found is None:
                continue
            if name.startswith(PLATFORM_ALLOWED):
                seen.add(found)
            else:
                pending.append(found)
    return sorted(seen)


def test_namespace_modules_keep_the_platform_import_rules():
    modules = _namespace_modules()
    assert {FI / name / "__init__.py" for name in NAMESPACES} <= set(modules)
    for path in modules:
        allowed = PLATFORM_ALLOWED if path.is_relative_to(FI / "_core") else NAMESPACE_ALLOWED
        for name in _fi_imports(path):
            assert name.startswith(allowed), f"{path.relative_to(FI)} imports {name}"


def test_namespace_modules_are_small_and_use_generated_paths():
    for path in _namespace_modules():
        text = path.read_text()
        assert len(text.splitlines()) <= 400, path
        for node in ast.walk(ast.parse(text)):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                assert not node.value.startswith("/model-hub/"), path
