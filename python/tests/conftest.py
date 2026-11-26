"""Settings shared by the tests in this directory."""

from pathlib import Path

import pytest

_PROXY_VARIABLES = ("HTTP_PROXY", "http_proxy", "ALL_PROXY", "all_proxy")

# Modules whose tests send keyed requests to fake plain-http hosts (such as ``http://gateway.test``) through
# transports mocked below the client (``respx``) or through clients the SDK builds. They opt in to plain http to a
# host that is not loopback. Other modules run without the opt-in.
_OPT_IN_MODULES = frozenset(
    {
        "gateway/test_agentcc_params_integration.py",
        "gateway/test_client.py",
        "gateway/test_fi_gateway.py",
        "gateway/test_live_fixes.py",
        "gateway/test_new_resources.py",
        "gateway/test_rerank.py",
        "gateway/test_resources.py",
        "gateway/test_responses_files.py",
        "gateway/test_review_fixes.py",
        "gateway/test_security_review_fixes.py",
        "gateway/test_session_metadata.py",
        "test_dataset_sdk_hardening.py",
    }
)
_HERE = Path(__file__).resolve().parent


@pytest.fixture(autouse=True)
def _plain_http_to_test_hosts(request, monkeypatch):
    """No proxy variable applies to the tests here; the modules listed above also opt in to plain http to a host
    that is not loopback. ``test_plain_http_key_guards.py`` sets these itself."""
    for name in _PROXY_VARIABLES:
        monkeypatch.delenv(name, raising=False)
    try:
        module = Path(str(request.node.path)).resolve().relative_to(_HERE).as_posix()
    except ValueError:
        module = ""
    if module in _OPT_IN_MODULES:
        monkeypatch.setenv("FI_ALLOW_INSECURE_HTTP", "1")
