"""RL 2251n: exact released-test ceilings and one optional-import exception.

These witnesses also load the unmodified base gate: RED must be an assertion
about its computed offenders, not an import of a helper absent from the base.
"""

import importlib.util
import subprocess
from pathlib import Path

import pytest


# Independent authorization record, not imported from the implementation.
AUTHORIZED_CEILINGS = {
    "python/tests/gateway/test_gateway_config.py": 923,
    "python/tests/gateway/test_advanced_features.py": 571,
    "python/tests/gateway/test_exceptions.py": 533,
    "python/tests/gateway/test_new_resources.py": 522,
    "python/tests/gateway/test_batch.py": 482,
    "python/tests/gateway/test_token_model_utils.py": 472,
    "python/tests/gateway/test_responses_files.py": 458,
    "python/tests/gateway/test_security_review_fixes.py": 450,
}
TOKENS = "python/fi/gateway/_tokens.py"


@pytest.fixture
def gates():
    spec = importlib.util.spec_from_file_location(
        "gateway_gates_under_test", Path(__file__).with_name("test_gw_gates.py")
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def ceiling_validator(gates):
    validator = getattr(gates, "_assert_ceiling_history", None)
    # The pre-fix base must fail here, outside each expected-rejection context.
    assert callable(validator), "append-only ceiling validation is required"
    return validator


def _computed_size_offenders(gates):
    """Read the existing gate's computed list, including on the pre-fix base."""
    try:
        gates.test_every_module_is_at_most_400_lines()
    except AssertionError as error:
        traceback = error.__traceback__
        while traceback is not None:
            frame = traceback.tb_frame
            if frame.f_code is gates.test_every_module_is_at_most_400_lines.__code__:
                # Earlier vendor/census assertions are not size offenders.
                if "over" not in frame.f_locals:
                    raise
                return frame.f_locals["over"]
            traceback = traceback.tb_next
        raise
    return []


def _mock_line_counts(monkeypatch, gates, counts):
    read_text = Path.read_text
    by_path = {gates.REPO / path: count for path, count in counts.items()}

    def read(path, *args, **kwargs):
        if path in by_path:
            return "# synthetic line\n" * by_path[path]
        return read_text(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", read)


def test_released_size_exemption_census_is_exact(gates):
    ceilings = getattr(gates, "RELEASED_TEST_LINE_CEILINGS", {})
    histories = getattr(gates, "CEILING_HISTORY", {})
    assert set(ceilings) == set(AUTHORIZED_CEILINGS)
    assert set(histories) == set(AUTHORIZED_CEILINGS)
    # A future growth ruling must explicitly amend this empty-record census.
    assert getattr(gates, "GROWTH_RECORDS", None) == {}


def test_released_size_ceilings_ratchet_with_current_counts(gates, ceiling_validator):
    ceilings = getattr(gates, "RELEASED_TEST_LINE_CEILINGS", {})
    histories = getattr(gates, "CEILING_HISTORY", {})
    records = getattr(gates, "GROWTH_RECORDS", None)
    assert set(ceilings) == set(histories) == set(AUTHORIZED_CEILINGS)
    assert isinstance(records, dict) and set(records) <= set(AUTHORIZED_CEILINGS)
    for path, ceiling in ceilings.items():
        count = len((gates.REPO / path).read_text().splitlines())
        ceiling_validator(histories[path], AUTHORIZED_CEILINGS[path], ceiling,
                          count, records.get(path, []))
        # Preserve the existing stronger pin: a shrink must append a lower bound.
        assert count == ceiling


@pytest.mark.parametrize("history, count", [
    ([923], 923), ([923, 900], 900), ([923, 900, 875], 875), ([923, 900], 899),
])
def test_ceiling_history_accepts_strict_decreases(ceiling_validator, history, count):
    ceiling_validator(history, 923, history[-1], count, [])


def test_shrink_then_regrowth_below_original_maximum_requires_a_record(ceiling_validator):
    with pytest.raises(AssertionError, match="increase needs a growth record"):
        ceiling_validator([923, 900, 910], 923, 910, 910, [])


def test_ceiling_raise_without_a_record_is_rejected(ceiling_validator):
    with pytest.raises(AssertionError, match="increase needs a growth record"):
        ceiling_validator([923, 924], 923, 924, 924, [])


@pytest.mark.parametrize("history, records", [
    ([923, 900, 910], [{"record": "test-only-growth-ruling", "to": 910}]),
    ([923, 924], [{"record": "test-only-growth-ruling", "to": 924}]),
    ([923, 900, 910, 890, 910], [
        {"record": "test-only-first-ruling", "to": 910},
        {"record": "test-only-second-ruling", "to": 910},
    ]),
])
def test_ceiling_raise_with_exact_records_is_accepted(ceiling_validator, history, records):
    original = [record.copy() for record in records]
    ceiling_validator(history, 923, history[-1], history[-1], records)
    assert records == original  # Validation never consumes the persisted data.


@pytest.mark.parametrize("history, ceiling, count", [
    ([], 923, 923), ([922], 922, 922), ([923, 923], 923, 923),
    ([923, 900, 900], 900, 900), ([923, 900], 910, 900),
    ([923, 900], 900, 901), ([923, 0], 0, 0), ([923, True], 1, 1),
])
def test_ceiling_history_rejects_invalid_bounds(ceiling_validator, history, ceiling, count):
    with pytest.raises(AssertionError):
        ceiling_validator(history, 923, ceiling, count, [])


@pytest.mark.parametrize("records", [
    [{"record": "test-only-growth-ruling", "to": 911}],
    [{"record": "test-only-growth-ruling", "to": "910"}],
    [{"record": "", "to": 910}], [{"record": "   ", "to": 910}],
    [{"to": 910}], [{"record": "test-only-growth-ruling", "to": 910, "extra": True}],
    [None],
])
def test_ceiling_growth_records_require_exact_target_and_ruling(ceiling_validator, records):
    with pytest.raises(AssertionError):
        ceiling_validator([923, 900, 910], 923, 910, 910, records)


@pytest.mark.parametrize("history, records", [
    ([923, 900], [{"record": "test-only-unused-ruling", "to": 910}]),
    ([923, 900], [None]),
    ([923, 900, 910, 890, 910], [{"record": "test-only-used-once", "to": 910}]),
    ([923, 900, 900], [{"record": "test-only-equality-ruling", "to": 900}]),
])
def test_ceiling_growth_records_cannot_be_unused_reused_or_authorize_equality(
    ceiling_validator, history, records,
):
    with pytest.raises(AssertionError):
        ceiling_validator(history, 923, history[-1], history[-1], records)


def test_gate_accepts_the_eight_released_files_at_their_ceilings(gates, monkeypatch):
    ceilings = getattr(gates, "RELEASED_TEST_LINE_CEILINGS", AUTHORIZED_CEILINGS)
    _mock_line_counts(monkeypatch, gates, ceilings)
    offenders = _computed_size_offenders(gates)
    rejected = [row for row in offenders if row.split(":", 1)[0] in AUTHORIZED_CEILINGS]
    assert rejected == []


@pytest.mark.parametrize("path", sorted(AUTHORIZED_CEILINGS))
def test_each_released_file_still_fails_above_its_ceiling(gates, monkeypatch, path):
    ceilings = getattr(gates, "RELEASED_TEST_LINE_CEILINGS", AUTHORIZED_CEILINGS)
    count = ceilings[path] + 1
    _mock_line_counts(monkeypatch, gates, {path: count})
    assert f"{path}: {count}" in _computed_size_offenders(gates)


@pytest.mark.parametrize("path", [
    "python/tests/gateway/unit/test_gateway_config.py",
    "python/fi/gateway/test_gateway_config.py",
    "scripts/gateway/test_gateway_config.py",
])
def test_non_exempt_same_basename_over_400_still_fails(gates, monkeypatch, path):
    # Synthetic in-memory input: no extra module is written into the repository.
    sources = gates._gateway_sources()
    monkeypatch.setattr(gates, "_gateway_sources", lambda: sources + [gates.REPO / path])
    _mock_line_counts(monkeypatch, gates, {path: 401})
    assert f"{path}: 401" in _computed_size_offenders(gates)


def test_base_dependency_allowlist_is_not_broadened(gates):
    assert gates.ALLOWED_THIRD_PARTY == {
        "httpx", "anyio", "pydantic", "typing_extensions", "jsonschema",
    }


def test_released_guarded_tiktoken_sites_are_accepted(gates, monkeypatch):
    path = gates.REPO / TOKENS
    assert len([module for _, module in gates._imports(path) if module == "tiktoken"]) == 3
    monkeypatch.setattr(gates, "_gateway_sources", lambda: [path])
    gates.test_only_the_planned_dependencies_are_imported()


@pytest.mark.parametrize("module, source", [
    ("python/fi/gateway/other.py", "try:\n    import tiktoken\nexcept ImportError:\n    pass\n"),
    ("python/fi/gateway/other/_tokens.py", "try:\n    import tiktoken\nexcept ImportError:\n    pass\n"),
    (TOKENS, "import tiktoken\n"),
    (TOKENS, "from tiktoken import get_encoding\n"),
    (TOKENS, "try:\n    import tiktoken\nexcept Exception:\n    pass\n"),
    (TOKENS, "try:\n    pass\nexcept ImportError:\n    import tiktoken\n"),
    (TOKENS, "try:\n    pass\nexcept ImportError:\n    pass\nelse:\n    import tiktoken\n"),
    (TOKENS, "try:\n    pass\nexcept ImportError:\n    pass\nfinally:\n    import tiktoken\n"),
    (TOKENS, "try:\n    def later():\n        import tiktoken\nexcept ImportError:\n    pass\n"),
    (TOKENS, "try:\n    import tiktoken, numpy\nexcept ImportError:\n    pass\n"),
])
def test_dependency_gate_rejects_wrong_module_or_unguarded_import(
    gates, monkeypatch, tmp_path, module, source,
):
    path = tmp_path / module
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(source)
    monkeypatch.setattr(gates, "REPO", tmp_path)
    monkeypatch.setattr(gates, "_gateway_sources", lambda: [path])
    with pytest.raises(AssertionError):
        gates.test_only_the_planned_dependencies_are_imported()


def test_gateway_import_and_token_fallbacks_without_tiktoken(gates):
    # A fresh interpreter avoids both installed-tokenizer and cached-module effects.
    # Catch the subprocess error so a regression reports as an assertion failure.
    code = '''
import importlib
import sys
import pytest

with pytest.MonkeyPatch.context() as monkeypatch:
    monkeypatch.setitem(sys.modules, "tiktoken", None)
    assert "fi.gateway" not in sys.modules
    assert "fi.gateway._tokens" not in sys.modules
    gateway = importlib.import_module("fi.gateway")
    assert callable(getattr(gateway, "AgentCC", None))
    tokens = importlib.import_module("fi.gateway._tokens")
    assert tokens is sys.modules["fi.gateway._tokens"]
    with pytest.warns(DeprecationWarning):
        assert gateway.token_counter("unknown", text="abcdefgh") == 2
        assert tokens.token_counter("unknown", text="") == 1
        assert tokens.token_counter("unknown") == 0
        assert tokens.token_counter("unknown", messages=[
            {"role": "user", "content": "abcd"},
        ]) == 8
        messages = [
            {"role": "user", "content": "old!"},
            {"role": "user", "content": "new!"},
        ]
        assert tokens.trim_messages(messages, "unknown", max_tokens=8, trim_ratio=1) == messages[1:]
        assert len(messages) == 2
        for name, argument in [("encode", "hello"), ("decode", [1, 2])]:
            with pytest.raises(ImportError, match=f"tiktoken is required for {name}"):
                getattr(tokens, name)("unknown", argument)
    assert "tiktoken" in sys.modules and sys.modules["tiktoken"] is None
print("optional-tokenizer-fallbacks-ok")
'''
    try:
        output = gates._fresh(code)
    except subprocess.CalledProcessError as error:
        pytest.fail(f"Fresh import/fallback assertion failed: {error.stderr}")
    assert output == "optional-tokenizer-fallbacks-ok"
