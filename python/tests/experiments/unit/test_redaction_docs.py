"""Contract: fail-closed redaction is accepted, and the redaction list is documented in the SDK docs
(``fi/experiments/README.md``). This test fails when the page and ``_redact.py`` disagree: every word list, every
non-secret environment name and every secret-shape family in the code is named on the page."""

import re
from pathlib import Path

from fi.experiments import _redact

DOC = (Path(_redact.__file__).parent / "README.md").read_text(encoding="utf-8")


def _named(word: str) -> bool:
    return re.search(rf"(?<![A-Za-z0-9_]){re.escape(word)}(?![A-Za-z0-9])", DOC) is not None


def test_every_word_list_of_the_code_is_on_the_page():
    lists = ("_KEY_ENGLISH", "_KEY_NOT_SECRET_BEFORE", "_KEY_NOT_SECRET_AFTER", "_TOKEN_COUNT_BEFORE",
             "_TOKEN_COUNT_AFTER", "_KEY_COUNT_BEFORE", "_KEY_COUNT_AFTER", "_COUNT_ANYWHERE_BEFORE", "_SPECIAL_TOKENS")
    missing = {name: sorted(w for w in getattr(_redact, name) if not _named(w)) for name in lists}
    assert {k: v for k, v in missing.items() if v} == {}


def test_the_credential_words_and_env_rules_are_on_the_page():
    for word in ("authorization", "secret", "password", "passphrase", "credential", "cookie", "bearer", "api_key",
                 "private_key", "access_key"):
        assert _named(word), word
    for name in _redact._NOT_SECRET_ENV:
        assert _named(name), name
    for family in ("FI_*", "*_API_KEY", "*_TOKEN", "*_SECRET", "*_SECRET_KEY", "*_API_SECRET"):
        assert f"`{family}`" in DOC, family
    assert f"{_redact._MIN_LEN} characters or longer" in DOC


def test_every_secret_shape_family_is_on_the_page():
    pattern = _redact._SECRET_SHAPE.pattern
    for marker, words in {"bearer": ["Bearer"], "sk-": ["sk-"], "gsk_": ["gsk_"], "xai-": ["xai-"],
                          "github_pat_": ["github_pat_", "ghp_"], "AKIA": ["AKIA"], "xox": ["xoxb-"],
                          "AIza": ["AIza"], "hf_": ["hf_"], "eyJ": ["JWT"], "PRIVATE KEY": ["PRIVATE KEY"]}.items():
        assert marker in pattern, marker  # the code still has this family
        assert all(w in DOC for w in words), words


def test_the_page_says_the_rule_fails_closed_and_where_it_applies():
    assert "fails closed (the fail-closed contract)" in DOC and "[redacted]" in DOC
    assert "plan.json" in DOC and "model_config" in DOC and "span attributes" in DOC
