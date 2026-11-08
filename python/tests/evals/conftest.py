"""Every evals test runs under the no-egress guard, with the fake keys the compatibility harness uses.

``FI_BASE_URL`` points at ``http://127.0.0.1:9`` (nothing listens there) and the saved login file
does not exist, so a request the fake in ``_mock_http`` does not answer fails at once instead of
leaving the machine.
"""

import pytest

from tests.core import _egress
from tests.evals import _mock_http


@pytest.fixture(autouse=True)
def _no_egress(monkeypatch, tmp_path):
    _egress.install(monkeypatch, tmp_path)
    monkeypatch.setenv("FI_API_KEY", _mock_http.KEY)
    monkeypatch.setenv("FI_SECRET_KEY", _mock_http.SECRET)
    monkeypatch.setenv("LITELLM_LOCAL_MODEL_COST_MAP", "True")
    _mock_http.reset_caches()
    yield
    _egress.assert_no_attempts()


@pytest.fixture
def backend(monkeypatch):
    """A fresh fake eval API for standalone requests and the shared httpx transport."""
    import httpx
    import requests

    fake = _mock_http.FakeBackend()

    def send(transport, request):
        prepared = requests.Request(request.method, str(request.url),
                                    headers=dict(request.headers), data=request.content).prepare()
        response = fake.send(prepared)
        return httpx.Response(response.status_code, content=response.content,
                              headers=response.headers, request=request)

    monkeypatch.setattr(httpx.HTTPTransport, "handle_request", send)
    with _mock_http.serve(fake):
        yield fake
