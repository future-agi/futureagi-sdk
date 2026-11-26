"""The ``allow_insecure_http`` argument on the ``fi.prompt`` classmethods that build their own keyed client.

``Prompt.list_templates``, ``Prompt.delete_template_by_name``, ``Prompt.get_template_by_name`` and the label
classmethods (``assign_label_to_template_version``, ``remove_label_from_template_version``,
``set_default_version``, ``get_template_labels``) each build a client that sends ``X-Api-Key`` and ``X-Secret-Key``.
They take ``allow_insecure_http`` like every other client: ``True`` sends plain http to a host that is not loopback
directly, through no proxy; ``False`` refuses it even with ``FI_ALLOW_INSECURE_HTTP=1``; the default (``None``) reads
the environment.

Listeners run on the loopback interface; ``api.futureagi.com`` resolves to them through the lookup shim of
``test_plain_http_key_guards`` (its ``net`` fixture applies here too), so no case reaches a real host. Each case
reads the connection count and the number of bytes holding the marker key at the target and at the proxy listener.
"""

from __future__ import annotations

import inspect
import secrets

import pytest

from fi.prompt import Prompt, PromptTemplate
from tests.test_plain_http_key_guards import CODE, KEY, SECRET, _attempt, net, refused, use_proxy  # noqa: F401

HOST = "api.futureagi.com"


def _name() -> str:
    # A fresh name per call, so the prompt cache never answers in place of a request.
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
METHODS = {
    "list-templates": Prompt.list_templates,
    "delete-template-by-name": Prompt.delete_template_by_name,
    "get-template-by-name": Prompt.get_template_by_name,
    "assign-label-to-template-version": Prompt.assign_label_to_template_version,
    "remove-label-from-template-version": Prompt.remove_label_from_template_version,
    "set-default-version": Prompt.set_default_version,
    "get-template-labels": Prompt.get_template_labels,
}


def _base(net) -> str:
    return f"http://{HOST}:{net.target.port}"


def _not_refused(exc: BaseException | None) -> None:
    # The listener answers ``{}``, which a method may fail to parse; only a refusal or a rejected argument counts.
    assert not isinstance(exc, TypeError), f"TypeError: {exc}"
    assert getattr(exc, "code", None) != CODE, f"refused: {exc}"


@pytest.mark.parametrize("method", list(METHODS), ids=list(METHODS))
def test_classmethod_takes_the_opt_in_argument_defaulting_to_none(method):
    parameter = inspect.signature(METHODS[method]).parameters.get("allow_insecure_http")
    assert parameter is not None, "no allow_insecure_http parameter"
    assert parameter.default is None
    assert parameter.kind in (parameter.KEYWORD_ONLY, parameter.POSITIONAL_OR_KEYWORD)


@pytest.mark.parametrize("call", list(CALLS), ids=list(CALLS))
def test_opt_in_argument_sends_directly_past_environment_proxy(monkeypatch, net, call):
    use_proxy(monkeypatch, net)
    exc = _attempt(lambda: CALLS[call](_base(net), allow_insecure_http=True))
    _not_refused(exc)
    net.delivered_direct()


@pytest.mark.parametrize("call", list(CALLS), ids=list(CALLS))
def test_opt_in_argument_false_wins_over_environment(monkeypatch, net, call):
    use_proxy(monkeypatch, net)
    monkeypatch.setenv("FI_ALLOW_INSECURE_HTTP", "1")
    exc = _attempt(lambda: CALLS[call](_base(net), allow_insecure_http=False))
    refused(exc, ValueError)
    net.nothing_sent()


@pytest.mark.parametrize("call", list(CALLS), ids=list(CALLS))
def test_without_opt_in_keyed_plain_http_is_refused(monkeypatch, net, call):
    use_proxy(monkeypatch, net)
    exc = _attempt(lambda: CALLS[call](_base(net)))
    refused(exc, ValueError)
    net.nothing_sent()


@pytest.mark.parametrize("call", list(CALLS), ids=list(CALLS))
def test_opt_in_by_environment_still_sends_directly(monkeypatch, net, call):
    use_proxy(monkeypatch, net)
    monkeypatch.setenv("FI_ALLOW_INSECURE_HTTP", "1")
    exc = _attempt(lambda: CALLS[call](_base(net)))
    _not_refused(exc)
    net.delivered_direct()


# ``Prompt(template=...)`` without an id fetches the template by name in ``__init__`` and logs a warning in place of
# any error, a refusal included; these cases read the listeners only.


def _construct(base: str, **kw):
    return Prompt(template=PromptTemplate(name=_name()), **_keys(base), **kw)


def test_constructor_with_opt_in_argument_sends_directly_past_environment_proxy(monkeypatch, net):
    use_proxy(monkeypatch, net)
    _not_refused(_attempt(lambda: _construct(_base(net), allow_insecure_http=True)))
    net.delivered_direct()


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
