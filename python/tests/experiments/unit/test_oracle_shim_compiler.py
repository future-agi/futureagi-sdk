"""The resolver shim of the oracle conformance tests follows ``FI_REQUIRE_RESOLVER_SHIM`` as the core shim tests do:
with no C compiler its tests fail when the variable is 1 and skip otherwise."""

import shutil
import sys

import pytest

from tests.experiments.unit import test_plaintext_oracle_conformance as oracle


def _without_a_compiler(monkeypatch):
    monkeypatch.setattr(shutil, "which", lambda name, *args, **kwargs: None)
    monkeypatch.setitem(sys.modules, "ziglang", None)


def _build_shim(tmp_path_factory):
    """Run the body of the oracle module's ``shim`` fixture."""
    wrapped = getattr(oracle.shim, "__pytest_wrapped__", None)
    body = wrapped.obj if wrapped is not None else oracle.shim._get_wrapped_function()
    return body(tmp_path_factory)


def test_a_required_oracle_shim_with_no_c_compiler_fails_the_test(monkeypatch, tmp_path_factory):
    _without_a_compiler(monkeypatch)
    monkeypatch.setenv("FI_REQUIRE_RESOLVER_SHIM", "1")

    with pytest.raises((pytest.fail.Exception, pytest.skip.Exception)) as outcome:
        _build_shim(tmp_path_factory)
    assert outcome.type is pytest.fail.Exception, f"the shim fixture skipped: {outcome.value}"
    assert "FI_REQUIRE_RESOLVER_SHIM" in str(outcome.value)


def test_an_oracle_shim_with_no_c_compiler_skips_the_test_when_not_required(monkeypatch, tmp_path_factory):
    _without_a_compiler(monkeypatch)
    monkeypatch.delenv("FI_REQUIRE_RESOLVER_SHIM", raising=False)

    with pytest.raises(pytest.skip.Exception, match="no C compiler"):
        _build_shim(tmp_path_factory)
