"""A space separator is removed from server text only inside the span that holds a token.

A token split by spaces is detected, and the span that holds it (its pieces and the spaces between them) is
replaced as a whole. Spaces outside that span, including spaces between ordinary words, are preserved.
"""

from __future__ import annotations

import re

import pytest
from fi.sandbox.channel_errors import channel_closed, clean_server_text

TOKEN_PATTERN = re.compile(r"sct_[A-Za-z0-9]+")


def _scrub(text: str) -> str:
    return TOKEN_PATTERN.sub("[token]", text)


def _scrub_exact(text: str) -> str:
    return text.replace("sct_ABC123456", "[token]")


def test_the_spaces_outside_the_token_span_stay_and_the_span_is_replaced():
    text = "sct_AAAA BBB... was rejected, please retry later"
    assert clean_server_text(text, _scrub) == "[token]... was rejected, please retry later"


def test_a_close_reason_keeps_its_spaces_around_the_token():
    error = channel_closed(4401, "bad token sct_AAAA BBB. It was rejected, please retry later", _scrub)
    assert error.server_reason == "bad token [token]. It was rejected, please retry later"


@pytest.mark.parametrize("space", [" ", " ", " ", " ", " ", " ", "　"])
def test_every_space_separator_inside_the_span_is_dropped(space):
    assert clean_server_text(f"a {'sct_AB' + space + 'CD'}. b", _scrub) == "a [token]. b"


def test_a_token_split_in_several_places_is_found_by_an_exact_match_scrub():
    assert clean_server_text("see sct_ABC 123 456, now", _scrub_exact) == "see [token], now"


def test_a_space_between_ordinary_words_is_never_removed():
    for text in ("pass word", "a pass word is not a token", "pass  word", "pass word"):
        assert clean_server_text(text, _scrub) == text


def test_a_scrub_that_finds_nothing_leaves_the_text_as_it_was():
    assert clean_server_text("one two  three four", _scrub) == "one two  three four"


def test_the_text_before_and_after_a_token_keeps_every_space():
    assert clean_server_text("a  b sct_AA BB. c  d", _scrub) == "a  b [token]. c  d"


def test_a_token_without_spaces_is_replaced_in_place():
    assert clean_server_text("x sct_AABB. y z", _scrub) == "x [token]. y z"


def test_no_scrub_keeps_every_space():
    assert clean_server_text("a b  c", None) == "a b  c"


def _exact(text: str) -> str:
    return text.replace("sct_ABC123456", "[token]")


@pytest.mark.parametrize(
    "text, expected",
    [
        ("sct_ABC123456 a b sct_ABC123456", "[token] a b [token]"),
        ("sct_ABC123456 sct_ABC123456", "[token] [token]"),
        ("sct_ABC123456  sct_ABC123456", "[token]  [token]"),
        ("sct_ABC123456 x sct_ABC123456", "[token] x [token]"),
        ("sct_ABC123456 x y z sct_ABC123456 q", "[token] x y z [token] q"),
        ("s ct_ABC 123456 a b sct_ABC123456 c d", "[token] a b [token] c d"),
        ("a b sct_ABC123456 sct_AB C123456 d e", "a b [token] [token] d e"),
    ],
)
def test_spaces_between_two_spans_stay(text, expected):
    assert clean_server_text(text, _exact) == expected

