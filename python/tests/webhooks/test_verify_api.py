"""The receiver-facing behaviour of ``fi.webhooks.verify`` beyond the vectors: header and body forms, error kinds, the
standard-library-only rule, and real time."""

from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

import pytest

from fi.webhooks import WebhookSecretError, WebhookVerificationError, sign, signature_header, verify

from ._stdlib import IS_STDLIB

SECRET = "whsec_AAECAwQFBgcICQoLDA0ODxAREhMUFRYXGBkaGxwdHh8="
OTHER = "whsec_QEFCQ0RFRkdISUpLTE1OT1BRUlNUVVZXWFlaW1xdXl8="
PY_ROOT = Path(__file__).resolve().parents[2]


def _request(body: bytes, *, msg_id="evt_01JBF3Q7Z8X4N6R2T5V9W0YB1C", t=None, secrets=(SECRET,)):
    t = int(time.time()) if t is None else t
    return {"webhook-id": msg_id, "webhook-timestamp": str(t),
            "webhook-signature": signature_header(list(secrets), msg_id, t, body)}


BODY = json.dumps({"id": "evt_01JBF3Q7Z8X4N6R2T5V9W0YB1C", "type": "prompt.label.changed", "test": True},
                  separators=(",", ":")).encode()


def test_now_by_default_and_the_parsed_event_with_test():
    event = verify(body=BODY, headers=_request(BODY), secret=SECRET)
    assert event["test"] is True and event["type"] == "prompt.label.changed"


def test_body_as_str_bytearray_and_memoryview():
    h = _request(BODY)
    for body in (BODY.decode(), bytearray(BODY), memoryview(BODY)):
        assert verify(body=body, headers=h, secret=SECRET)["id"].startswith("evt_")
    with pytest.raises(TypeError):
        verify(body={"id": 1}, headers=h, secret=SECRET)


def test_header_forms_django_meta_asgi_raw_pairs_and_any_case():
    h = _request(BODY)
    meta = {"HTTP_" + k.upper().replace("-", "_"): v for k, v in h.items()}
    meta["CONTENT_TYPE"] = "application/json"
    raw = [(k.encode(), v.encode()) for k, v in h.items()]
    title = {k.title(): v for k, v in h.items()}
    for headers in (meta, raw, title, list(h.items())):
        assert verify(body=BODY, headers=headers, secret=SECRET)["type"] == "prompt.label.changed"


def test_rotation_overlap_either_secret_verifies():
    h = _request(BODY, secrets=(SECRET, OTHER))
    assert verify(body=BODY, headers=h, secret=SECRET)
    assert verify(body=BODY, headers=h, secret=OTHER)


@pytest.mark.parametrize(
    "mutate, reason",
    [
        (lambda h, b: ({k: v for k, v in h.items() if k != "webhook-signature"}, b), "missing_headers"),
        (lambda h, b: ({**h, "webhook-timestamp": "soon"}, b), "invalid_timestamp"),
        (lambda h, b: ({**h, "webhook-timestamp": str(int(time.time()) - 5)}, b), "no_matching_signature"),
        (lambda h, b: (h, b[:-1] + b"]"), "no_matching_signature"),
        (lambda h, b: ({**h, "webhook-id": "evt_other"}, b), "no_matching_signature"),
    ],
    ids=["missing-signature", "bad-timestamp", "header-from-another-time", "tampered-body", "other-id"],
)
def test_refusals_raise_a_verification_error_with_the_reason(mutate, reason):
    headers, body = mutate(_request(BODY), BODY)
    with pytest.raises(WebhookVerificationError) as err:
        verify(body=body, headers=headers, secret=SECRET)
    assert err.value.reason == reason
    assert isinstance(err.value, ValueError)


def test_stale_and_future_timestamps():
    old = int(time.time()) - 301
    with pytest.raises(WebhookVerificationError) as err:
        verify(body=BODY, headers=_request(BODY, t=old), secret=SECRET)
    assert err.value.reason == "timestamp_too_old" and "300 s" in str(err.value)
    future = int(time.time()) + 400
    with pytest.raises(WebhookVerificationError) as err:
        verify(body=BODY, headers=_request(BODY, t=future), secret=SECRET)
    assert err.value.reason == "timestamp_too_new"
    assert verify(body=BODY, headers=_request(BODY, t=old), secret=SECRET, tolerance_s=600)


def test_a_malformed_secret_is_a_configuration_error_not_a_bad_request():
    h = _request(BODY)
    for bad, reason in (("AAECAwQFBgcICQoLDA0ODxAREhMUFRYXGBkaGxwdHh8=", "missing_prefix"),
                        ("whsec_not*base64*at*all*0000000000000000000", "not_base64"),
                        ("whsec_AAECAwQFBgcICQoLDA0ODxAREhMUFRY=", "bad_length")):
        with pytest.raises(WebhookSecretError) as err:
            verify(body=BODY, headers=h, secret=bad)
        assert err.value.reason == reason
        assert not isinstance(err.value, WebhookVerificationError)


def test_a_signed_body_that_is_not_a_json_object():
    for body in (b"[1,2]", b"\xff\xfe", b"not json"):
        with pytest.raises(WebhookVerificationError) as err:
            verify(body=body, headers=_request(body), secret=SECRET)
        assert err.value.reason == "invalid_body"


def test_a_body_with_a_utf8_bom_is_invalid_body_as_in_typescript():
    """The signature covers the raw bytes, so it matches; the parse step refuses the BOM in both languages (S4)."""
    from fi.webhooks import verify_result

    bom = b"\xef\xbb\xbf" + BODY
    h = _request(bom)
    assert verify_result(SECRET, h, bom) == "ok"
    for body in (bom, bom.decode("utf-8")):
        with pytest.raises(WebhookVerificationError) as err:
            verify(body=body, headers=h, secret=SECRET)
        assert err.value.reason == "invalid_body"


def test_the_error_never_contains_the_secret_or_expected_signature():
    h = _request(BODY)
    expected = sign(SECRET, h["webhook-id"], int(h["webhook-timestamp"]), BODY)
    with pytest.raises(WebhookVerificationError) as err:
        verify(body=BODY + b" ", headers=h, secret=SECRET)
    text = str(err.value) + repr(err.value)
    assert SECRET not in text and expected not in text and SECRET[6:] not in text


def test_verify_imports_only_the_standard_library():
    """A fresh interpreter that imports fi.webhooks.verify loads no third-party module (and not the client)."""
    code = IS_STDLIB + (
        f"import sys; sys.path.insert(0, {str(PY_ROOT)!r})\n"
        "from pathlib import Path\n"
        "before = set(sys.modules); import fi.webhooks.verify as v\n"
        "guard = sys.modules['_futureagi_namespace_guard']\n"
        f"expected = Path({str(PY_ROOT / '_futureagi_namespace_guard.py')!r}).resolve()\n"
        "assert Path(guard.__file__).resolve() == expected\n"
        "assert Path(guard.__spec__.origin).resolve() == expected\n"
        "new = sorted(m.split('.')[0] for m in set(sys.modules) - before)\n"
        "third = sorted({m for m in new if not is_stdlib(m) and m not in ('fi', '_futureagi_namespace_guard')})\n"
        "print(third); print('fi.webhooks._client' in sys.modules)\n"
    )
    out = subprocess.run([sys.executable, "-I", "-B", "-c", code], capture_output=True, text=True, check=True).stdout.split("\n")
    assert out[0] == "[]", out
    assert out[1] == "False"


def test_the_package_import_stays_light():
    code = ("import sys; import fi.webhooks as w; from fi.webhooks import verify; "
            "print(sorted(m for m in ('httpx', 'fi.webhooks._client', 'fi._http') if m in sys.modules))")
    out = subprocess.run([sys.executable, "-I", "-B", "-c", f"import sys; sys.path.insert(0, {str(PY_ROOT)!r}); {code}"],
                         capture_output=True, text=True, check=True).stdout.strip()
    assert out == "[]"
