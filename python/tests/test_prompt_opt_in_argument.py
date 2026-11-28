"""Plain-HTTP policy for prompt entry points that build their own keyed client.

The prompt classmethods accept an explicit opt-in or read the environment. Future AGI
hosts are excluded, and requests for opted-in custom hosts use a direct route.
The lookup shim resolves the named test hosts to the loopback listeners, which
record connections and planted marker bytes at the target and proxy.
"""

from __future__ import annotations

import secrets

import pytest

from fi.errors import ConfigurationError, InsecureHttpRefusedError
from fi.prompt import Prompt, PromptTemplate
from tests.test_plain_http_key_guards import KEY, PLAIN, SECRET, _attempt, net, use_proxy  # noqa: F401

HOST = "api.futureagi.com"


def _name() -> str:
    # Distinct names cause each lookup to reach the transport rather than the prompt cache.
    return "tpl-" + secrets.token_hex(6)


def _keys(base: str) -> dict:
    return {"fi_api_key": KEY, "fi_secret_key": SECRET, "fi_base_url": base}


CALLS = {
    "list-templates": lambda base, **kw: Prompt.list_templates(**_keys(base), **kw),
    "delete-template-by-name": lambda base, **kw: Prompt.delete_template_by_name(_name(), **_keys(base), **kw),
    "get-template-by-name": lambda base, **kw: Prompt.get_template_by_name(_name(), **_keys(base), **kw),
    "get-template-by-name-with-label": lambda base, **kw: Prompt.get_template_by_name(
        _name(), label="staging", **_keys(base), **kw
    ),
    "assign-label-to-template-version": lambda base, **kw: Prompt.assign_label_to_template_version(
        template_name=_name(), version="v1", label="staging", **_keys(base), **kw
    ),
    "remove-label-from-template-version": lambda base, **kw: Prompt.remove_label_from_template_version(
        template_name=_name(), version="v1", label="staging", **_keys(base), **kw
    ),
    "set-default-version": lambda base, **kw: Prompt.set_default_version(
        template_name=_name(), version="v1", **_keys(base), **kw
    ),
    "get-template-labels": lambda base, **kw: Prompt.get_template_labels(template_name=_name(), **_keys(base), **kw),
}


def _base(net, host=HOST) -> str:
    return f"http://{host}:{net.target.port}"


def _origin_refused(exc):
    assert isinstance(exc, InsecureHttpRefusedError), repr(exc)
    assert exc.code == "INSECURE_HTTP_REFUSED"
    assert KEY not in str(exc) and SECRET not in str(exc)


@pytest.mark.parametrize("call", list(CALLS), ids=list(CALLS))
def test_opt_in_argument_sends_directly_with_environment_proxy(monkeypatch, net, call):
    use_proxy(monkeypatch, net)
    exc = _attempt(lambda: CALLS[call](_base(net, PLAIN), allow_insecure_http=True))
    net.delivered_direct()
    assert not isinstance(exc, (TypeError, ConfigurationError)), repr(exc)


@pytest.mark.parametrize("call", list(CALLS), ids=list(CALLS))
def test_opt_in_argument_false_overrides_environment_opt_in(monkeypatch, net, call):
    use_proxy(monkeypatch, net)
    monkeypatch.setenv("FI_ALLOW_INSECURE_HTTP", "1")
    exc = _attempt(lambda: CALLS[call](_base(net, PLAIN), allow_insecure_http=False))
    net.nothing_sent()
    assert isinstance(exc, ConfigurationError), repr(exc)
    assert exc.code == "insecure_http_origin"


@pytest.mark.parametrize("call", list(CALLS), ids=list(CALLS))
def test_without_opt_in_keyed_plain_http_is_refused(monkeypatch, net, call):
    use_proxy(monkeypatch, net)
    exc = _attempt(lambda: CALLS[call](_base(net)))
    net.nothing_sent()
    _origin_refused(exc)


@pytest.mark.parametrize("call", list(CALLS), ids=list(CALLS))
@pytest.mark.parametrize("host", [HOST, PLAIN])
def test_environment_opt_in_is_limited_to_custom_hosts(monkeypatch, net, call, host):
    use_proxy(monkeypatch, net)
    monkeypatch.setenv("FI_ALLOW_INSECURE_HTTP", "1")
    exc = _attempt(lambda: CALLS[call](_base(net, host)))
    if host == HOST:
        net.nothing_sent()
        _origin_refused(exc)
    else:
        net.delivered_direct()
        assert not isinstance(exc, (TypeError, ConfigurationError)), repr(exc)


# ``Prompt(template=...)`` without an id fetches the template by name in ``__init__`` and logs a warning in place of
# any error, a refusal included; these cases read the listeners only.


def _construct(base: str, **kw):
    return Prompt(template=PromptTemplate(name=_name()), **_keys(base), **kw)


def test_constructor_with_opt_in_argument_sends_nothing_to_future_agi_host(monkeypatch, net):
    use_proxy(monkeypatch, net)
    error = _attempt(lambda: _construct(_base(net), allow_insecure_http=True))
    net.nothing_sent()
    assert error is None  # The constructor handles the failed lookup internally.


@pytest.mark.parametrize(
    "opt_in, environment",
    [(None, None), (False, "1")],
    ids=["default-without-environment", "false-over-environment"],
)
def test_constructor_without_opt_in_sends_nothing(monkeypatch, net, opt_in, environment):
    use_proxy(monkeypatch, net)
    if environment is not None:
        monkeypatch.setenv("FI_ALLOW_INSECURE_HTTP", environment)
    kw = {} if opt_in is None else {"allow_insecure_http": opt_in}
    prompt = _attempt(lambda: _construct(_base(net), **kw))
    assert prompt is None  # the constructor raised nothing
    net.nothing_sent()
