import json

import httpx

from fi import FutureAGIClient


def _client_with_transport(handler):
    client = FutureAGIClient(
        api_key="api-key",
        secret_key="secret-key",
        base_url="http://api.test",
    )
    client.generated_client.set_httpx_client(
        httpx.Client(
            base_url="http://api.test",
            headers={
                "X-Api-Key": "api-key",
                "X-Secret-Key": "secret-key",
            },
            transport=httpx.MockTransport(handler),
        )
    )
    return client


def test_futureagi_client_sends_auth_headers_and_query_params():
    requests = []

    def handler(request):
        requests.append(request)
        assert request.headers["X-Api-Key"] == "api-key"
        assert request.headers["X-Secret-Key"] == "secret-key"
        assert request.url.path == "/model-hub/annotation-queues/"
        assert request.url.params["limit"] == "10"
        return httpx.Response(200, json={"count": 0, "results": []})

    client = _client_with_transport(handler)

    assert client.annotation_queues.list(limit=10) == {
        "count": 0,
        "results": [],
    }
    assert len(requests) == 1


def test_futureagi_client_wraps_discussion_comments():
    requests = []

    def handler(request):
        requests.append(request)
        assert request.method == "POST"
        assert request.url.path == (
            "/model-hub/annotation-queues/q1/items/"
            "11111111-1111-1111-1111-111111111111/discussion/"
        )
        assert json.loads(request.content) == {
            "comment": "@reviewer please check this item",
            "mentioned_user_ids": ["u1"],
        }
        return httpx.Response(
            200,
            json={
                "status": True,
                "result": {"review_comments": [], "review_threads": []},
            },
        )

    client = _client_with_transport(handler)

    client.annotation_queues.discussion.comment(
        "q1",
        "11111111-1111-1111-1111-111111111111",
        {
            "comment": "@reviewer please check this item",
            "mentioned_user_ids": ["u1"],
        },
    )
    assert len(requests) == 1


def test_futureagi_client_wraps_common_public_sdk_paths():
    requests = []
    expected = [
        ("GET", "/model-hub/develops/dataset-1/get-dataset-table/"),
        ("GET", "/model-hub/experiments/v2/experiment-1/rows/"),
        ("GET", "/tracer/trace/list_voice_calls/"),
        ("GET", "/accounts/user-info/"),
        ("GET", "/tracer/user-alert-logs/alert-1/list/"),
    ]

    def handler(request):
        requests.append(request)
        method, path = expected.pop(0)
        assert request.method == method
        assert request.url.path == path
        return httpx.Response(200, json={"ok": True})

    client = _client_with_transport(handler)

    client.datasets.get_table("dataset-1", limit=5)
    client.experiments_v2.rows("experiment-1", page=1)
    client.tracing.voice_calls(project_id="project-1")
    client.users.current()
    client.alerts.logs_for_alert("alert-1")

    assert len(requests) == 5
    assert expected == []


def test_futureagi_client_wraps_eval_paths():
    requests = []
    expected = [
        ("POST", "/model-hub/eval-templates/list/"),
        ("POST", "/model-hub/eval-templates/create-v2/"),
        ("GET", "/model-hub/eval-templates/eval-template-1/detail/"),
        ("PUT", "/model-hub/eval-templates/eval-template-1/update/"),
        ("GET", "/model-hub/eval-templates/eval-template-1/versions/"),
        ("POST", "/sdk/api/v1/new-eval/"),
        ("GET", "/sdk/api/v1/new-eval/"),
    ]

    def handler(request):
        requests.append(request)
        method, path = expected.pop(0)
        assert request.method == method
        assert request.url.path == path
        return httpx.Response(200, json={"ok": True})

    client = _client_with_transport(handler)

    client.evals.list_templates({"filters": {}})
    client.evals.create_template({"name": "Faithfulness"})
    client.evals.get_template("eval-template-1")
    client.evals.update_template("eval-template-1", {"name": "Faithfulness v2"})
    client.evals.template_versions("eval-template-1")
    client.evals.run_v2({"eval_id": "run-1", "data": []})
    client.evals.get_run_v2("11111111-1111-1111-1111-111111111111")
    assert len(requests) == 7
    assert expected == []


# ---- transport defaults: timeouts, retries and keys resolved on first use --------------------

import asyncio  # noqa: E402

import pytest  # noqa: E402

from fi._credentials import resolve  # noqa: E402
from fi._http import AsyncRetryingTransport, LazyKeyAuth, RetryingTransport  # noqa: E402

_NO_ENV = {"FI_API_KEY": "", "FI_SECRET_KEY": "", "FI_BASE_URL": ""}


@pytest.fixture
def clean_env(monkeypatch, tmp_path):
    for name in ("FI_API_KEY", "FI_SECRET_KEY", "FI_BASE_URL"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("FI_LOGIN_FILE", str(tmp_path / "login.json"))
    return tmp_path


def test_default_timeout_is_30s_connect_10s(clean_env):
    client = FutureAGIClient(base_url="http://api.test")
    timeout = client.generated_client.get_httpx_client().timeout
    assert (timeout.read, timeout.connect) == (30.0, 10.0)


def test_retry_on_503_honours_retry_after():
    calls, sleeps = [], []

    def handler(request):
        calls.append(request)
        if len(calls) == 1:
            return httpx.Response(503, headers={"Retry-After": "2"})
        return httpx.Response(200, json={"ok": True})

    transport = RetryingTransport(httpx.MockTransport(handler), sleep=sleeps.append)
    with httpx.Client(transport=transport, base_url="http://api.test") as http:
        response = http.put("/x", json={"a": 1})  # idempotent: a POST is not retried on a 5xx (M1)
    assert response.status_code == 200
    assert len(calls) == 2 and calls[1].content == calls[0].content
    assert sleeps == [2.0]


def test_retry_502_only_for_idempotent_methods():
    def handler(request):
        return httpx.Response(502)

    sleeps = []
    transport = RetryingTransport(httpx.MockTransport(handler), retries=2, sleep=sleeps.append)
    with httpx.Client(transport=transport, base_url="http://api.test") as http:
        assert http.post("/x").status_code == 502
        assert sleeps == []
        assert http.get("/x").status_code == 502
        assert sleeps == [0.5, 1.0]


def test_async_retry_on_429():
    calls, sleeps = [], []

    def handler(request):
        calls.append(request)
        return httpx.Response(429 if len(calls) < 3 else 200, json={})

    async def fake_sleep(s):
        sleeps.append(s)

    async def go():
        transport = AsyncRetryingTransport(httpx.MockTransport(handler), sleep=fake_sleep)
        async with httpx.AsyncClient(transport=transport, base_url="http://api.test") as http:
            return await http.get("/x")

    assert asyncio.run(go()).status_code == 200
    assert sleeps == [0.5, 1.0]


def test_no_raise_without_keys_until_first_request(clean_env):
    from fi.utils.errors import MissingAuthError

    client = FutureAGIClient(base_url="http://api.test")  # no keys anywhere: no raise
    with pytest.raises(MissingAuthError) as info:
        client.datasets.list()
    # M3: no `futureagi-py login` in the fix line until the login command is registered (A6)
    assert "FI_API_KEY" in str(info.value) and "futureagi-py login" not in str(info.value)


def test_keys_resolved_on_first_request(clean_env, monkeypatch):
    seen = []

    def handler(request):
        seen.append((request.headers.get("X-Api-Key"), request.headers.get("X-Secret-Key")))
        return httpx.Response(200, json={"results": []})

    client = FutureAGIClient(base_url="http://api.test")
    http = client.generated_client.get_httpx_client()
    http._transport = RetryingTransport(httpx.MockTransport(handler))
    monkeypatch.setenv("FI_API_KEY", "k-env")
    monkeypatch.setenv("FI_SECRET_KEY", "s-env")
    client.datasets.list()
    assert seen == [("k-env", "s-env")]


def test_saved_login_bound_to_its_base_url(clean_env):
    login = clean_env / "login.json"
    login.write_text(json.dumps({"base_url": "http://saved.test", "api_key": "k1", "secret_key": "s1"}))
    used = resolve(environ={})
    assert (used.api_key, used.base_url, used.keys_source) == ("k1", "http://saved.test", "login")
    # an FI_BASE_URL from anywhere else disables the saved keys
    other = resolve(environ={"FI_BASE_URL": "http://evil.test"})
    assert other.api_key is None and other.keys_source == "none"
    assert "not sent to http://evil.test" in other.login_skipped
    # the same host it was saved with keeps working
    same = resolve(environ={"FI_BASE_URL": "http://saved.test/"})
    assert same.keys_source == "login"


def test_env_keys_win_over_saved_login(clean_env):
    (clean_env / "login.json").write_text(
        json.dumps({"base_url": "http://saved.test", "api_key": "k1", "secret_key": "s1"})
    )
    creds = resolve(environ={"FI_API_KEY": "k2", "FI_SECRET_KEY": "s2"})
    # S12: env keys never take the login's server; without FI_BASE_URL they go to the default
    assert (creds.api_key, creds.keys_source) == ("k2", "env")
    assert (creds.base_url, creds.base_url_source) == ("https://api.futureagi.com", "default")
    assert "used only with its own keys" in creds.login_skipped
    creds = resolve("k3", "s3", environ={})
    assert (creds.keys_source, creds.base_url, creds.base_url_source) == ("argument", "https://api.futureagi.com", "default")
    # naming the login's server explicitly sends the env keys there (the explicit choice wins)
    creds = resolve(environ={"FI_API_KEY": "k2", "FI_SECRET_KEY": "s2", "FI_BASE_URL": "http://saved.test"})
    assert (creds.api_key, creds.base_url, creds.base_url_source) == ("k2", "http://saved.test", "env")
    assert creds.login_skipped is None
    # no login file: no note
    (clean_env / "login.json").unlink()
    assert resolve(environ={"FI_API_KEY": "k2", "FI_SECRET_KEY": "s2"}).login_skipped is None


def test_lazy_auth_resolves_once():
    calls = []

    def resolver():
        calls.append(1)
        return resolve("k", "s", "http://api.test")

    auth = LazyKeyAuth(resolver)
    for _ in range(3):
        request = httpx.Request("GET", "http://api.test/x")
        next(auth.auth_flow(request))
        assert request.headers["X-Api-Key"] == "k"
    assert calls == [1]


def test_old_names_still_import_and_experiments_renamed(clean_env):
    import fi

    for name in fi.__all__:
        assert getattr(fi, name) is not None
    from fi import AsyncFutureAGIClient, FutureAGIClient as C  # noqa: F401
    from fi.utils.errors import SDKException
    from fi._sdk_exception import SDKException as Base

    assert SDKException is Base
    client = C(base_url="http://api.test")
    assert client.experiments_v2 is not None
    with pytest.warns(DeprecationWarning):
        assert client.experiments is client.experiments_v2


def test_async_client_lazy_and_typed(clean_env, monkeypatch):
    from fi import AsyncFutureAGIClient

    def handler(request):
        assert request.headers["X-Api-Key"] == "k"
        return httpx.Response(200, json={"ok": 1})

    async def go():
        client = AsyncFutureAGIClient(base_url="http://api.test")
        monkeypatch.setenv("FI_API_KEY", "k")
        monkeypatch.setenv("FI_SECRET_KEY", "s")
        http = client.generated_client.get_async_httpx_client()
        http._transport = AsyncRetryingTransport(httpx.MockTransport(handler))
        try:
            return await client.request("GET", "/x")
        finally:
            await client.aclose()

    assert asyncio.run(go()) == {"ok": 1}


def test_both_httpx_clients_get_a_working_retrying_transport(clean_env):
    """The generated client hands httpx_args to the sync AND the async httpx client; each must work
    (a sync-only transport made get_async_httpx_client() raise AttributeError)."""
    from fi import AsyncFutureAGIClient

    def handler(request):
        return httpx.Response(200, json={"path": request.url.path})

    for cls in (FutureAGIClient, AsyncFutureAGIClient):
        client = cls(api_key="k-test-1234", secret_key="s-test-1234", base_url="http://api.test")
        transport = client.generated_client._httpx_args["transport"]
        transport._wrapped = httpx.MockTransport(handler)
        transport._wrapped_async = httpx.MockTransport(handler)
        assert client.generated_client.get_httpx_client().get("/sync").json() == {"path": "/sync"}

        async def go(client=client):
            return (await client.generated_client.get_async_httpx_client().get("/async")).json()

        assert asyncio.run(go()) == {"path": "/async"}


def test_unreachable_server_raises_connect_error_on_both_paths(clean_env):
    client = FutureAGIClient(api_key="k-test-1234", secret_key="s-test-1234", base_url="http://127.0.0.1:9",
                             retries=0)
    with pytest.raises(httpx.ConnectError):
        client.generated_client.get_httpx_client().get("/x")

    async def go():
        await client.generated_client.get_async_httpx_client().get("/x")

    with pytest.raises(httpx.ConnectError):
        asyncio.run(go())


def test_clients_import_nothing_from_fi_utils_or_fi_api():
    """Another distribution ships fi/utils; the clients must not need it."""
    import subprocess
    import sys

    code = (
        "import sys; import fi.futureagi_client, fi.futureagi_async_client; "
        "print(sorted(m for m in sys.modules if m == 'fi.utils' or m.startswith(('fi.utils.', 'fi.api'))))"
    )
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=60)
    assert out.returncode == 0, out.stderr
    assert out.stdout.strip() == "[]"


def test_missing_auth_error_is_one_class_under_both_names(clean_env):
    from fi._credentials import CredentialsMissingError, MissingAuthError
    from fi.utils.errors import MissingAuthError as LegacyMissingAuthError

    assert LegacyMissingAuthError is MissingAuthError
    client = FutureAGIClient(base_url="http://api.test")
    with pytest.raises(CredentialsMissingError) as info:
        client.datasets.list()
    err = info.value
    assert isinstance(err, MissingAuthError)
    assert err.get_error_code() == "MISSING_FI_CLIENT_AUTHENTICATION"
    assert err.missing == ("FI_API_KEY", "FI_SECRET_KEY") and err.base_url == "http://api.test"


@pytest.mark.parametrize("asynchronous", [False, True])
def test_client_auth_is_sdk_authentication_and_credentials_is_read_only(clean_env, asynchronous):
    """SDK authentication and read-only workspace credential metadata are distinct surfaces."""
    import importlib
    from pathlib import Path
    from fi import AsyncFutureAGIClient
    from fi._credentials import Credentials as SDKAuthentication, MissingAuthError

    features = json.loads((Path(__file__).resolve().parents[2] / "openapi/connectors/features.json").read_text())
    cls = AsyncFutureAGIClient if asynchronous else FutureAGIClient
    client = cls(api_key="k-test-1234", secret_key="s-test-1234", base_url="http://api.test")
    auth = client.auth
    assert isinstance(auth, SDKAuthentication)
    assert auth.api_key == "k-test-1234" and auth.keys_source == "argument"
    assert auth.secret_key == "s-test-1234" and auth.base_url == "http://api.test"
    unauthenticated = cls(base_url="http://api.test")
    with pytest.raises(MissingAuthError):
        unauthenticated.auth
    if not features["credential_reads"]:
        assert not hasattr(client, "credentials")
        assert not hasattr(unauthenticated, "credentials")
        with pytest.raises(ModuleNotFoundError, match="fi.credentials"):
            importlib.import_module("fi.credentials")
        return
    from fi.credentials import AsyncCredentials, Credentials
    namespace = AsyncCredentials if asynchronous else Credentials
    assert hasattr(client, "credentials"), "Read-only credentials namespace must be registered"
    credentials = client.credentials
    assert isinstance(credentials, namespace)
    assert credentials is not auth and credentials._client is client
    assert {name for name in dir(credentials) if not name.startswith("_")} == {"bindings", "get", "list"}
    assert all(callable(getattr(credentials, name)) for name in ("bindings", "get", "list"))
    for name in ("create", "delete", "revoke", "rotate", "api_key", "secret_key"):
        assert not hasattr(credentials, name)
    assert isinstance(unauthenticated.credentials, namespace)


@pytest.mark.parametrize("asynchronous", [False, True])
def test_unauthenticated_credential_reads_refuse_before_transport(clean_env, asynchronous):
    import asyncio
    from pathlib import Path
    from unittest.mock import Mock

    from fi import AsyncFutureAGIClient
    from fi._credentials import MissingAuthError

    features = json.loads((Path(__file__).resolve().parents[2] / "openapi/connectors/features.json").read_text())
    cls = AsyncFutureAGIClient if asynchronous else FutureAGIClient
    client = cls(base_url="http://127.0.0.1:9")
    if not features["credential_reads"]:
        assert not hasattr(client, "credentials")
        with pytest.raises(MissingAuthError):
            client.auth
        return
    requests = Mock(side_effect=AssertionError("An unauthenticated read reached the transport"))
    transport = httpx.MockTransport(requests)
    client._platform.shared._recorder._inner = transport
    client._platform.shared._recorder._inner_async = transport
    with pytest.raises(MissingAuthError):
        if asynchronous:
            asyncio.run(client.credentials.list())
        else:
            client.credentials.list()
    requests.assert_not_called()
    # A positive control proves these are the transport hooks the read actually uses.
    recorded = Mock(return_value=httpx.Response(200, json={"credentials": []}))
    authenticated = cls(api_key="fixture-key", secret_key="fixture-secret", base_url="http://127.0.0.1:9")
    control = httpx.MockTransport(recorded)
    authenticated._platform.shared._recorder._inner = control
    authenticated._platform.shared._recorder._inner_async = control
    if asynchronous:
        asyncio.run(authenticated.credentials.list())
    else:
        authenticated.credentials.list()
    recorded.assert_called_once()
    request = recorded.call_args.args[0]
    assert request.url.path == "/omega/api/workspace/credentials"
    assert request.headers["x-api-key"] == "fixture-key"
    assert request.headers["x-secret-key"] == "fixture-secret"
