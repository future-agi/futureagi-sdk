"""A key three decodings deep in a header value is found whatever else the value holds."""

import base64

import pytest

from fi._core.header_key_scan import holds_key

KEY = "fi-depth-marker-" + "q7" * 8


def _b64(text):
    return base64.b64encode(text.encode("latin-1")).decode("ascii")


def _hex(text):
    return text.encode("latin-1").hex()


INNER = _b64(KEY)
DEEP = _hex(_b64(INNER))  # hex, then base64, then base64: the key is three decodings deep
SAME_INNER_LATER = _b64(_b64(_hex(INNER)))  # reaches the same inner text, three decodings deep as well


def test_the_key_three_decodings_deep_is_found_alone():
    assert holds_key(DEEP, [KEY])


@pytest.mark.parametrize("value", [DEEP + " " + SAME_INNER_LATER, SAME_INNER_LATER + " " + DEEP,
                                   DEEP + "," + SAME_INNER_LATER, SAME_INNER_LATER + ";" + DEEP],
                         ids=["deep-first", "deep-last", "comma", "semicolon"])
def test_the_key_three_decodings_deep_is_found_next_to_another_run_that_reaches_the_same_text(value):
    assert holds_key(value, [KEY])
