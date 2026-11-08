"""Optional loopback-only backend smoke adapted from the catalog SDK's E2E flows.

Set FI_CATALOG_SMOKE_URL plus a disposable FI_API_KEY/FI_SECRET_KEY pair. This
suite tolerates specifically named plan/backend gaps and is not acceptance.
FI_E2E_REQUIRED=1 makes missing configuration fail instead of silently skipping.
No provider-dependent operation or optimization run is started here.
"""
import os
import uuid
from urllib.parse import urlsplit

import pytest

from fi import FutureAGIClient
from fi.errors import FutureAGIAPIError, NotFoundError


@pytest.fixture(scope="module")
def client():
    base = os.environ.get("FI_CATALOG_SMOKE_URL")
    if not base:
        if os.environ.get("FI_E2E_REQUIRED") == "1":
            pytest.fail("FI_CATALOG_SMOKE_URL is required for catalog smoke")
        pytest.skip("loopback backend smoke is not configured")
    parsed = urlsplit(base)
    if parsed.scheme != "http" or parsed.hostname not in {"localhost", "127.0.0.1", "::1"} or parsed.username or parsed.password:
        pytest.fail("catalog smoke accepts only an explicit HTTP loopback origin")
    if not os.environ.get("FI_API_KEY") or not os.environ.get("FI_SECRET_KEY"):
        pytest.fail("a disposable backend key pair is required")
    with FutureAGIClient(base_url=base, retries=0) as root:
        yield root


def allow(call, *statuses):
    try:
        return call()
    except FutureAGIAPIError as error:
        if error.status_code not in statuses:
            raise
        return None


def test_context(client):
    # The identity read is the core client's users.current() (the same endpoint).
    assert client.users.current()
    workspaces = client.workspaces.list()["workspaces"]
    assert workspaces
    assert client.workspaces.get(workspaces[0]["id"])["workspaces"]


def test_dashboard_lifecycle(client):
    dashboards = client.tracing.dashboards
    name = "sdk-smoke-" + uuid.uuid4().hex[:8]
    dashboard = dashboards.create({"name": name})
    identity = dashboard["id"]
    try:
        assert dashboards.get(identity)["name"] == name
        assert dashboards.update(identity, {"name": name + "-updated"})["name"] == name + "-updated"
        assert identity in [row["id"] for row in dashboards.list()]
    finally:
        dashboards.delete(identity)
    with pytest.raises(NotFoundError):
        dashboards.get(identity)


def test_plan_gated_error_clusters(client):
    # Error clusters are the core client's tracing.issues() / issue() (the same endpoints).
    allow(lambda: client.tracing.issues(), 402)
    allow(lambda: client.tracing.issue(str(uuid.uuid4())), 400, 402, 404)


def test_unqualified_usage_read_is_absent():
    # This absence check needs no backend and must never send a billing request.
    with FutureAGIClient("fixture-api", "fixture-secret", base_url="http://localhost:9012") as root:
        assert not hasattr(root, "usage")
