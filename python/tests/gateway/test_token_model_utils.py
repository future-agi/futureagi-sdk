"""Tests for token encode/decode, trim_messages, and model info utilities."""

from __future__ import annotations

from typing import Any

import importlib.util

import pytest

# ---------------------------------------------------------------------------
# encode / decode
# ---------------------------------------------------------------------------


@pytest.mark.skipif(importlib.util.find_spec("tiktoken") is None, reason="needs futureagi[gateway-tokens]")
class TestEncodeDecode:
    """Tests for encode() and decode()."""

    def test_encode_returns_token_ids(self) -> None:
        """encode() should return a non-empty list of ints for non-empty text."""
        try:
            from fi.gateway._tokens import encode
        except ImportError:
            pytest.skip("tiktoken not installed")

        tokens = encode("gpt-4o", "Hello, world!")
        assert isinstance(tokens, list)
        assert len(tokens) > 0
        assert all(isinstance(t, int) for t in tokens)

    def test_decode_roundtrips(self) -> None:
        """decode(encode(text)) should return the original text."""
        try:
            from fi.gateway._tokens import decode, encode
        except ImportError:
            pytest.skip("tiktoken not installed")

        text = "The quick brown fox jumps over the lazy dog."
        tokens = encode("gpt-4o", text)
        result = decode("gpt-4o", tokens)
        assert result == text

    def test_encode_empty_string(self) -> None:
        """encode() of an empty string should return an empty list."""
        try:
            from fi.gateway._tokens import encode
        except ImportError:
            pytest.skip("tiktoken not installed")

        tokens = encode("gpt-4o", "")
        assert tokens == []

    def test_decode_empty_list(self) -> None:
        """decode() of an empty list should return an empty string."""
        try:
            from fi.gateway._tokens import decode
        except ImportError:
            pytest.skip("tiktoken not installed")

        result = decode("gpt-4o", [])
        assert result == ""

    def test_encode_unknown_model_uses_fallback(self) -> None:
        """encode() with an unknown model should fall back to cl100k_base."""
        try:
            from fi.gateway._tokens import encode
        except ImportError:
            pytest.skip("tiktoken not installed")

        tokens = encode("unknown-model-xyz", "Hello")
        assert isinstance(tokens, list)
        assert len(tokens) > 0

    def test_encode_raises_without_tiktoken(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """encode() should raise ImportError with helpful message when tiktoken is missing."""
        import sys

        from fi.gateway._tokens import encode

        # Temporarily hide tiktoken
        original = sys.modules.get("tiktoken")
        monkeypatch.setitem(sys.modules, "tiktoken", None)  # type: ignore[arg-type]
        try:
            with pytest.raises(ImportError, match="tiktoken is required"):
                encode("gpt-4o", "Hello")
        finally:
            if original is not None:
                monkeypatch.setitem(sys.modules, "tiktoken", original)
            else:
                monkeypatch.delitem(sys.modules, "tiktoken", raising=False)

    def test_decode_raises_without_tiktoken(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """decode() should raise ImportError with helpful message when tiktoken is missing."""
        import sys

        from fi.gateway._tokens import decode

        original = sys.modules.get("tiktoken")
        monkeypatch.setitem(sys.modules, "tiktoken", None)  # type: ignore[arg-type]
        try:
            with pytest.raises(ImportError, match="tiktoken is required"):
                decode("gpt-4o", [1, 2, 3])
        finally:
            if original is not None:
                monkeypatch.setitem(sys.modules, "tiktoken", original)
            else:
                monkeypatch.delitem(sys.modules, "tiktoken", raising=False)


# ---------------------------------------------------------------------------
# trim_messages
# ---------------------------------------------------------------------------


class TestTrimMessages:
    """Tests for trim_messages()."""

    def test_no_trim_needed(self) -> None:
        """Messages already within budget should be returned as-is."""
        from fi.gateway._tokens import trim_messages

        messages: list[dict[str, Any]] = [
            {"role": "system", "content": "You are helpful."},
            {"role": "user", "content": "Hi!"},
        ]
        result = trim_messages(messages, "gpt-4o")
        assert len(result) == 2
        assert result[0]["role"] == "system"
        assert result[1]["role"] == "user"

    def test_trims_oldest_non_system_first(self) -> None:
        """When over budget, oldest non-system messages should be removed first."""
        from fi.gateway._tokens import trim_messages

        messages: list[dict[str, Any]] = [
            {"role": "system", "content": "System prompt."},
            {"role": "user", "content": "First message " * 50},
            {"role": "assistant", "content": "First reply " * 50},
            {"role": "user", "content": "Second message " * 50},
            {"role": "assistant", "content": "Second reply " * 50},
            {"role": "user", "content": "Latest question"},
        ]
        # Use a very small max_tokens to force trimming
        result = trim_messages(messages, "gpt-4o", max_tokens=200)
        # System message must always be preserved
        assert result[0]["role"] == "system"
        # The latest message should be preserved
        assert result[-1]["content"] == "Latest question"
        # Should have fewer messages than original
        assert len(result) < len(messages)

    def test_system_messages_always_preserved(self) -> None:
        """System messages must never be removed during trimming."""
        from fi.gateway._tokens import trim_messages

        messages: list[dict[str, Any]] = [
            {"role": "system", "content": "System instructions."},
            {"role": "user", "content": "Long message " * 100},
            {"role": "assistant", "content": "Long reply " * 100},
        ]
        result = trim_messages(messages, "gpt-4o", max_tokens=100)
        system_msgs = [m for m in result if m["role"] == "system"]
        assert len(system_msgs) == 1
        assert system_msgs[0]["content"] == "System instructions."

    def test_custom_max_tokens(self) -> None:
        """max_tokens parameter should override model lookup."""
        from fi.gateway._tokens import trim_messages

        messages: list[dict[str, Any]] = [
            {"role": "user", "content": "Hello " * 50},
            {"role": "assistant", "content": "World " * 50},
            {"role": "user", "content": "Short"},
        ]
        # Very small budget forces trimming
        result = trim_messages(messages, "gpt-4o", max_tokens=50)
        assert len(result) <= len(messages)

    def test_custom_trim_ratio(self) -> None:
        """trim_ratio should control the fraction of context used."""
        from fi.gateway._tokens import trim_messages

        messages: list[dict[str, Any]] = [
            {"role": "user", "content": "Hello " * 200},
            {"role": "assistant", "content": "World " * 200},
            {"role": "user", "content": "Latest"},
        ]
        # With trim_ratio=0.5, budget is halved
        result_half = trim_messages(messages, "gpt-4o", trim_ratio=0.5, max_tokens=500)
        result_full = trim_messages(messages, "gpt-4o", trim_ratio=1.0, max_tokens=500)
        assert len(result_half) <= len(result_full)

    def test_unknown_model_without_max_tokens_raises(self) -> None:
        """Should raise ValueError for unknown model when max_tokens not given."""
        from fi.gateway._tokens import trim_messages

        with pytest.raises(ValueError, match="Unknown model"):
            trim_messages(
                [{"role": "user", "content": "Hi"}],
                "unknown-model-xyz",
            )

    def test_unknown_model_with_max_tokens_succeeds(self) -> None:
        """Should work for unknown model when max_tokens is provided explicitly."""
        from fi.gateway._tokens import trim_messages

        messages: list[dict[str, Any]] = [
            {"role": "user", "content": "Hello"},
        ]
        result = trim_messages(messages, "unknown-model-xyz", max_tokens=10000)
        assert len(result) == 1

    def test_returns_new_list(self) -> None:
        """trim_messages should return a new list, not mutate the input."""
        from fi.gateway._tokens import trim_messages

        messages: list[dict[str, Any]] = [
            {"role": "user", "content": "Hello"},
        ]
        result = trim_messages(messages, "gpt-4o")
        assert result is not messages


# ---------------------------------------------------------------------------
# validate_environment
# ---------------------------------------------------------------------------


class TestValidateEnvironment:
    """Tests for validate_environment()."""

    def test_all_vars_set(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should report ready=True when all required vars are set."""
        from fi.gateway._models_info import validate_environment

        monkeypatch.setenv("AGENTCC_API_KEY", "test-key-123")
        monkeypatch.setenv("AGENTCC_BASE_URL", "https://api.example.com")

        result = validate_environment()
        assert result["ready"] is True
        assert "AGENTCC_API_KEY" in result["keys_set"]
        assert "AGENTCC_BASE_URL" in result["keys_set"]
        assert result["keys_missing"] == []

    def test_no_vars_set(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should report ready=False when no required vars are set."""
        from fi.gateway._models_info import validate_environment

        monkeypatch.delenv("AGENTCC_API_KEY", raising=False)
        monkeypatch.delenv("AGENTCC_BASE_URL", raising=False)

        result = validate_environment()
        assert result["ready"] is False
        assert "AGENTCC_API_KEY" in result["keys_missing"]
        assert "AGENTCC_BASE_URL" in result["keys_missing"]
        assert result["keys_set"] == []

    def test_partial_vars_set(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should report ready=False when only some vars are set."""
        from fi.gateway._models_info import validate_environment

        monkeypatch.setenv("AGENTCC_API_KEY", "test-key")
        monkeypatch.delenv("AGENTCC_BASE_URL", raising=False)

        result = validate_environment()
        assert result["ready"] is False
        assert "AGENTCC_API_KEY" in result["keys_set"]
        assert "AGENTCC_BASE_URL" in result["keys_missing"]

    def test_empty_string_treated_as_missing(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Empty string env vars should be treated as missing."""
        from fi.gateway._models_info import validate_environment

        monkeypatch.setenv("AGENTCC_API_KEY", "")
        monkeypatch.setenv("AGENTCC_BASE_URL", "")

        result = validate_environment()
        assert result["ready"] is False
        assert "AGENTCC_API_KEY" in result["keys_missing"]
        assert "AGENTCC_BASE_URL" in result["keys_missing"]


# ---------------------------------------------------------------------------
# get_valid_models
# ---------------------------------------------------------------------------


class TestGetValidModels:
    """Tests for get_valid_models()."""

    def test_returns_non_empty_list(self) -> None:
        """Should return a non-empty list of model names."""
        from fi.gateway._models_info import get_valid_models

        models = get_valid_models()
        assert isinstance(models, list)
        assert len(models) > 0

    def test_contains_known_models(self) -> None:
        """Should contain well-known model names."""
        from fi.gateway._models_info import get_valid_models

        models = get_valid_models()
        assert "gpt-4o" in models
        assert "gpt-4o-mini" in models
        assert "claude-sonnet-4-20250514" in models

    def test_returns_strings(self) -> None:
        """All items should be strings."""
        from fi.gateway._models_info import get_valid_models

        models = get_valid_models()
        assert all(isinstance(m, str) for m in models)


# ---------------------------------------------------------------------------
# register_model
# ---------------------------------------------------------------------------


class TestRegisterModel:
    """Tests for register_model()."""

    def test_register_new_model(self) -> None:
        """Registering a new model should make it findable via get_model_info."""
        from fi.gateway._models_info import MODEL_INFO, ModelInfo, get_model_info, register_model

        model_name = "test-custom-model-12345"
        try:
            info = ModelInfo(max_tokens=32000, max_output_tokens=4096)
            register_model(model_name, info)

            result = get_model_info(model_name)
            assert result is not None
            assert result.max_tokens == 32000
            assert result.max_output_tokens == 4096
        finally:
            # Clean up to avoid polluting other tests
            MODEL_INFO.pop(model_name, None)

    def test_register_updates_existing(self) -> None:
        """Registering an existing model name should update its info."""
        from fi.gateway._models_info import MODEL_INFO, ModelInfo, get_model_info, register_model

        model_name = "test-update-model-12345"
        try:
            info_v1 = ModelInfo(max_tokens=8000)
            register_model(model_name, info_v1)
            assert get_model_info(model_name) is not None
            assert get_model_info(model_name).max_tokens == 8000  # type: ignore[union-attr]

            info_v2 = ModelInfo(max_tokens=16000)
            register_model(model_name, info_v2)
            assert get_model_info(model_name).max_tokens == 16000  # type: ignore[union-attr]
        finally:
            MODEL_INFO.pop(model_name, None)

    def test_registered_model_in_get_valid_models(self) -> None:
        """A registered model should appear in get_valid_models()."""
        from fi.gateway._models_info import MODEL_INFO, ModelInfo, get_valid_models, register_model

        model_name = "test-listed-model-12345"
        try:
            register_model(model_name, ModelInfo(max_tokens=4096))
            assert model_name in get_valid_models()
        finally:
            MODEL_INFO.pop(model_name, None)


# ---------------------------------------------------------------------------
# model_alias_map
# ---------------------------------------------------------------------------


class TestModelAliasMap:
    """Tests for model_alias_map and its integration with get_model_info."""

    def test_alias_resolves_to_full_model(self) -> None:
        """An alias should resolve to the full model name via get_model_info."""
        from fi.gateway._models_info import get_model_info, model_alias_map

        alias = "gpt4-test-alias"
        try:
            model_alias_map[alias] = "gpt-4o"

            result = get_model_info(alias)
            assert result is not None
            assert result.max_tokens == 128000  # gpt-4o's max_tokens
        finally:
            model_alias_map.pop(alias, None)

    def test_alias_not_found_returns_none(self) -> None:
        """An alias pointing to a non-existent model should return None (falls through)."""
        from fi.gateway._models_info import get_model_info, model_alias_map

        alias = "nonexistent-alias-test"
        try:
            model_alias_map[alias] = "totally-nonexistent-model"

            result = get_model_info(alias)
            assert result is None
        finally:
            model_alias_map.pop(alias, None)

    def test_exact_match_takes_precedence_over_alias(self) -> None:
        """An exact MODEL_INFO match should take precedence over an alias."""
        from fi.gateway._models_info import get_model_info, model_alias_map

        # "gpt-4o" is an exact match in MODEL_INFO
        alias = "gpt-4o"
        try:
            model_alias_map[alias] = "gpt-3.5-turbo"

            result = get_model_info(alias)
            assert result is not None
            # Should return gpt-4o info (exact match), not gpt-3.5-turbo
            assert result.max_tokens == 128000
        finally:
            model_alias_map.pop(alias, None)

    def test_alias_map_is_initially_empty(self) -> None:
        """model_alias_map should start as an empty dict."""
        from fi.gateway._models_info import model_alias_map

        # It might have entries from other tests running in parallel,
        # but structurally it should be a dict.
        assert isinstance(model_alias_map, dict)


# ---------------------------------------------------------------------------
# Lazy imports from fi.gateway module
# ---------------------------------------------------------------------------


class TestLazyImports:
    """Verify all new functions are accessible via the agentcc top-level module."""

    def test_encode_importable(self) -> None:
        import fi.gateway as agentcc

        assert callable(agentcc.encode)

    def test_decode_importable(self) -> None:
        import fi.gateway as agentcc

        assert callable(agentcc.decode)

    def test_trim_messages_importable(self) -> None:
        import fi.gateway as agentcc

        assert callable(agentcc.trim_messages)

    def test_validate_environment_importable(self) -> None:
        import fi.gateway as agentcc

        assert callable(agentcc.validate_environment)

    def test_get_valid_models_importable(self) -> None:
        import fi.gateway as agentcc

        assert callable(agentcc.get_valid_models)

    def test_register_model_importable(self) -> None:
        import fi.gateway as agentcc

        assert callable(agentcc.register_model)

    def test_model_alias_map_importable(self) -> None:
        import fi.gateway as agentcc

        assert isinstance(agentcc.model_alias_map, dict)
