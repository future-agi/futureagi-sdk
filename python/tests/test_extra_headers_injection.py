"""Header injection through FI_EXTRA_HEADERS and extra_headers= is refused (fi._extra_headers).

A value with CR, LF, CRLF, NUL or any other control character, and a name with ':' or whitespace,
is refused with EXTRA_HEADERS_INVALID, through the setting and through the argument (mapping and
text). In the setting (and the text form of the argument) ';', CR and LF separate entries by
design, so "X-A=1\\nX-B=2" is two headers, each checked; an injection payload such as
"X-A=1\\r\\nX-Api-Key: other" fails because its second entry has no '=', and
"X-A=1\\r\\nX-Api-Key=other" because X-Api-Key is one of the SDK's own auth headers.
The wire-level proof (exact request bytes on a raw 127.0.0.1 socket) is
tests/test_extra_headers_injection_wire.py.
"""

from __future__ import annotations

import pytest

from fi import _extra_headers as xh
from fi._extra_headers import ARGUMENT, ENV_VAR, ExtraHeaders, ExtraHeadersError

BASE = "http://127.0.0.1:9"

# every C0 control character and DEL
CONTROLS = [chr(c) for c in range(0x20)] + ["\x7f"]
# CR and LF are entry separators in the text forms (setting, text argument): checked separately below
TEXT_CONTROLS = [c for c in CONTROLS if c not in "\r\n"]
POSITIONS = {"inside": "a{}b", "leading": "{}ab", "trailing": "ab{}"}

BAD_VALUES = {
    "cr-header": "1\rX-Evil: 1",
    "lf-header": "1\nX-Evil: 1",
    "crlf-api-key": "1\r\nX-Api-Key: other",
    "crlf-trailing": "1\r\n",
    "lf-leading": "\n1",
    "crlf-smuggle": "1\r\n\r\nGET /smuggled HTTP/1.1",
    "nul-header": "1\x00X-Evil: 1",
    "nul-trailing": "1\x00",
    "tab-header": "1\tX-Evil: 1",
    "vt-trailing": "1\x0b",
    "ff-leading": "\x0c1",
    "esc": "1\x1b[2J",
    "us-0x1f-trailing": "1\x1f",
    "fs-0x1c-leading": "\x1c1",
    "del": "1\x7f",
    "nel-0x85": "1\x85",
    "ls-u2028-header": "1 X-Evil: 1",
}

BAD_NAMES = {
    "colon": "X:A",
    "colon-trailing": "X-A:",
    "colon-leading": ":X-A",
    "header-line": "X-A: 1\r\nX-Evil",
    "space-inside": "X A",
    "tab-inside": "X\tA",
    "crlf-inside": "X-A\r\nX-Evil",
    "lf-trailing": "X-A\n",
    "cr-trailing": "X-A\r",
    "nul-trailing": "X-A\x00",
    "vt-trailing": "X-A\x0b",
    "space-leading": " X-A",
    "space-trailing": "X-A ",
    "nbsp-trailing": "X-A\xa0",
}

# names that are bad in the text forms too (spaces around a name are the text format's padding;
# a name with CR or LF splits into two entries, covered by SETTING_INJECTIONS)
TEXT_BAD_NAMES = {k: v for k, v in BAD_NAMES.items() if not v.strip(" ") == "X-A" and "\r" not in v and "\n" not in v}

SETTING_INJECTIONS = {
    "crlf-colon-api-key": ("X-A=1\r\nX-Api-Key: other", "entry 2 has no '='"),
    "crlf-equals-api-key": ("X-A=1\r\nX-Api-Key=other", "entry 2: X-Api-Key cannot be set"),
    "lf-colon-authorization": ("X-A=1\nAuthorization: Bearer evil-token-1", "entry 2 has no '='"),
    "lf-equals-authorization": ("X-A=1\nAuthorization=Bearer evil-token-1", "entry 2: Authorization cannot be set"),
    "cr-colon-secret-key": ("X-A=1\rX-Secret-Key: other", "entry 2 has no '='"),
    "semicolon-api-key": ("X-A=1;x-api-key=other", "entry 2: x-api-key cannot be set"),
    "crlf-smuggled-request": ("X-A=1\r\n\r\nGET /smuggled HTTP/1.1", "entry 2 has no '='"),
    "nul-api-key": ("X-A=1\x00X-Api-Key: other", "(X-A): the value has a control character"),
    "tab-api-key": ("X-A=1\tX-Api-Key: other", "(X-A): the value has a control character"),
    "vt-entry": ("X-A=1\n\x0b\n", "entry 2 has no '='"),
    "colon-name": ("X-A: 1=2", "entry 1: the name is not a valid HTTP header name"),
}


def _refused(call, source: str, *fragments: str) -> ExtraHeadersError:
    with pytest.raises(ExtraHeadersError) as info:
        call()
    error = info.value
    message = str(error)
    assert error.get_error_code() == "EXTRA_HEADERS_INVALID"
    assert message.startswith(source), message
    for fragment in ("=other", ": other", "X-Evil", "evil-token-1", "smuggled", "\r", "\n", "\x00"):
        assert fragment not in message and fragment not in repr(error), (fragment, message)
    for fragment in fragments:
        assert fragment in message, (fragment, message)
    return error


@pytest.fixture(autouse=True)
def _no_setting(monkeypatch):
    monkeypatch.delenv(ENV_VAR, raising=False)


# ---- values -------------------------------------------------------------------------------------


@pytest.mark.parametrize("value", list(BAD_VALUES.values()), ids=list(BAD_VALUES))
def test_injection_value_refused_in_the_argument_mapping(value):
    _refused(lambda: xh.validate({"X-A": value}), f"{ARGUMENT} entry 1 (X-A)")
    _refused(lambda: ExtraHeaders(BASE, {"X-A": value}), f"{ARGUMENT} entry 1 (X-A)")
    _refused(lambda: xh.resolve({"X-A": value}, environ={}), f"{ARGUMENT} entry 1 (X-A)")


@pytest.mark.parametrize("char", CONTROLS, ids=[f"0x{ord(c):02x}" for c in CONTROLS])
@pytest.mark.parametrize("where", list(POSITIONS))
def test_injection_every_control_character_refused_in_the_argument_mapping(char, where):
    value = POSITIONS[where].format(char)
    _refused(lambda: xh.validate({"X-A": value}), f"{ARGUMENT} entry 1 (X-A)", "control character")


@pytest.mark.parametrize("char", TEXT_CONTROLS, ids=[f"0x{ord(c):02x}" for c in TEXT_CONTROLS])
@pytest.mark.parametrize("where", list(POSITIONS))
def test_injection_every_control_character_refused_in_the_setting_and_the_argument_text(char, where):
    text = "X-A=" + POSITIONS[where].format(char)
    _refused(lambda: xh.from_env({ENV_VAR: text}), f"{ENV_VAR} entry 1 (X-A)", "control character")
    _refused(lambda: xh.parse(text), f"{ENV_VAR} entry 1 (X-A)", "control character")
    _refused(lambda: xh.validate(text), f"{ARGUMENT} entry 1 (X-A)", "control character")
    _refused(lambda: ExtraHeaders(BASE, text), f"{ARGUMENT} entry 1 (X-A)", "control character")


def test_injection_setting_read_per_request_refuses_before_any_header_is_returned(monkeypatch):
    extra = ExtraHeaders(BASE, {"X-Arg": "argument-value-1"})
    monkeypatch.setenv(ENV_VAR, "X-A=1\r\nX-Api-Key: other")
    _refused(lambda: extra.for_url(f"{BASE}/x"), f"{ENV_VAR} entry 2 has no '='")
    headers: dict = {}
    _refused(lambda: extra.apply(headers, f"{BASE}/x"), f"{ENV_VAR} entry 2")
    assert headers == {}  # nothing was added before the error
    assert xh.describe()["error"].startswith(f"{ENV_VAR} entry 2") and xh.describe()["names"] == []


# ---- names --------------------------------------------------------------------------------------


@pytest.mark.parametrize("name", list(BAD_NAMES.values()), ids=list(BAD_NAMES))
def test_injection_name_refused_in_the_argument_mapping(name):
    _refused(lambda: xh.validate({name: "1"}), f"{ARGUMENT} entry 1: the name is not a valid HTTP header name")
    _refused(lambda: ExtraHeaders(BASE, {name: "1"}), f"{ARGUMENT} entry 1: the name is not a valid")


@pytest.mark.parametrize("name", list(TEXT_BAD_NAMES.values()), ids=list(TEXT_BAD_NAMES))
def test_injection_name_refused_in_the_setting_and_the_argument_text(name):
    text = f"{name}=1"
    _refused(lambda: xh.from_env({ENV_VAR: text}), f"{ENV_VAR} entry 1: the name is not a valid HTTP header name")
    _refused(lambda: xh.validate(text), f"{ARGUMENT} entry 1: the name is not a valid HTTP header name")


# ---- the setting's separators, and payloads written as the setting --------------------------------


@pytest.mark.parametrize("payload", [v[0] for v in SETTING_INJECTIONS.values()], ids=list(SETTING_INJECTIONS))
def test_injection_payload_refused_in_the_setting_and_the_argument_text(payload):
    words = dict(SETTING_INJECTIONS.values())[payload]
    _refused(lambda: xh.from_env({ENV_VAR: payload}), ENV_VAR, words)
    _refused(lambda: xh.validate(payload), ARGUMENT, words)
    _refused(lambda: ExtraHeaders(BASE, payload), ARGUMENT, words)


@pytest.mark.parametrize(
    "text, expected",
    [
        ("X-A=1\nX-B=2", {"X-A": "1", "X-B": "2"}),
        ("X-A=1\r\nX-B=2", {"X-A": "1", "X-B": "2"}),
        ("X-A=1\rX-B=2", {"X-A": "1", "X-B": "2"}),
        ("X-A=1\r\n", {"X-A": "1"}),
        ("\r\nX-A=1;;\n", {"X-A": "1"}),
        (" X-A = 1 ", {"X-A": "1"}),
    ],
    ids=["lf-two-headers", "crlf-two-headers", "cr-two-headers", "crlf-trailing-one-header", "empty-entries", "padding"],
)
def test_injection_separators_by_design_give_separate_checked_headers(text, expected):
    assert xh.from_env({ENV_VAR: text}) == expected
    assert xh.validate(text) == expected
    for value in expected.values():  # no value ever holds a separator or a control character
        assert not any(c in value for c in CONTROLS)


def test_injection_dollar_trap_a_trailing_newline_never_passes_a_check():
    # Python's re '$' matches before a trailing '\n'; the checks use fullmatch, so these are refused
    for name in ("X-A\n", "X-A\r\n"):
        _refused(lambda: xh.validate({name: "1"}), ARGUMENT)
    for value in ("1\n", "Bearer abc\n"):
        _refused(lambda: xh.validate({"X-A": value}), ARGUMENT)
