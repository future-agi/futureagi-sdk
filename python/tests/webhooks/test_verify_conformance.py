"""``fi.webhooks.verify`` passes the language-neutral signing vectors byte for byte.

The vectors are vendored unchanged from the platform's webhooks core (future-agi ``futureagi/webhooks/core/conformance/``, conformance
1.4.0 at the recorded source). A drift test pins each file's sha256 to the vendored ``manifest.json``, and the manifest itself
to its sha256 at that commit, so a hand edit of any of them fails here.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from pathlib import Path

import pytest

from fi.webhooks import verify as verify_fn
from fi.webhooks.verify import (
    VERIFY_RESULTS,
    WebhookSecretError,
    secret_key,
    sign,
    signature_header,
    verify_result,
)

HERE = Path(__file__).resolve().parent / "conformance"
MANIFEST_SHA256 = "3e01168cb0dbf6b91af26d9e2f915f56f93731d045061c5efeb962e42cd5c875"  # 1.4.0, future-agi the recorded source
VENDORED = ("signing.json", "signing-v1.json")


def _load(name: str) -> dict:
    return json.loads((HERE / name).read_bytes())


SIGNING = _load("signing.json")
V1 = _load("signing-v1.json")


def test_vendored_files_match_the_manifest_byte_for_byte():
    manifest_bytes = (HERE / "manifest.json").read_bytes()
    assert hashlib.sha256(manifest_bytes).hexdigest() == MANIFEST_SHA256
    manifest = json.loads(manifest_bytes)
    assert manifest["conformance_version"] == "1.4.0"
    for name in VENDORED:
        raw = (HERE / name).read_bytes()
        entry = manifest["files"][name]
        assert len(raw) == entry["bytes"], name
        assert hashlib.sha256(raw).hexdigest() == entry["sha256"], name
        assert json.loads(raw)["conformance_version"] == "1.4.0", name


def test_the_rules_this_runner_relies_on():
    rules = SIGNING["rules"]
    assert rules["tolerance_s"] == 300
    assert tuple(rules["verify_results"]) == VERIFY_RESULTS


@pytest.mark.parametrize("case", SIGNING["secret_format"], ids=lambda c: c["id"])
def test_secret_format(case):
    if case["valid"]:
        key = secret_key(case["secret"])
        assert len(key) == case["key_bytes"]
        assert key.hex() == case["key_hex"]
    else:
        with pytest.raises(WebhookSecretError) as err:
            secret_key(case["secret"])
        assert err.value.reason == case["reason"]


@pytest.mark.parametrize("case", SIGNING["sign"], ids=lambda c: c["id"])
def test_sign(case):
    body = base64.b64decode(case["body_bytes_b64"])
    expected = case["expected"]
    sigs = [sign(s, case["msg_id"], case["timestamp"], body) for s in case["secrets"]]
    assert sigs == expected["signatures"]
    header = signature_header(case["secrets"], case["msg_id"], case["timestamp"], body)
    assert header == expected["webhook_signature"]
    assert expected["headers"]["webhook-signature"] == header
    assert expected["headers"]["webhook-id"] == case["msg_id"]
    assert expected["headers"]["webhook-timestamp"] == str(case["timestamp"])
    # every signed case also verifies with each of its secrets, at its own timestamp
    for s in case["secrets"]:
        assert verify_result(s, expected["headers"], body, now=case["timestamp"]) == "ok"


@pytest.mark.parametrize("case", SIGNING["verify"], ids=lambda c: c["id"])
def test_verify(case):
    body = base64.b64decode(case["body_bytes_b64"])
    assert verify_result(case["secret"], case["headers"], body, now=case["now"]) == case["expected"]
    if case["expected"] == "ok":
        event = verify_fn(body=body, headers=case["headers"], secret=case["secret"], now=case["now"])
        assert event == json.loads(body)
    else:
        from fi.webhooks import WebhookVerificationError

        with pytest.raises(WebhookVerificationError) as err:
            verify_fn(body=body, headers=case["headers"], secret=case["secret"], now=case["now"])
        assert err.value.reason == case["expected"]


def _v1_secret(letter: str) -> str:
    return V1[f"secret_{letter.lower()}"]


def test_design_5_6_vectors_from_signing_v1():
    body = base64.b64decode(V1["body_bytes_b64"])
    assert body.decode("utf-8") == V1["body_text"]
    assert len(body) == V1["bytes"] == 354
    assert hashlib.sha256(body).hexdigest() == V1["sha256"]
    assert sign(V1["secret_a"], V1["msg_id"], V1["timestamp"], body) == V1["signature_a"]
    assert sign(V1["secret_b"], V1["msg_id"], V1["timestamp"], body) == V1["signature_b"]
    assert signature_header([V1["secret_a"], V1["secret_b"]], V1["msg_id"], V1["timestamp"], body) == \
        V1["overlap_header"]


@pytest.mark.parametrize("case", V1["must_pass"], ids=lambda c: f"{c['secret']}-{c.get('header', 'own')}-{c['now']}")
def test_signing_v1_must_pass(case):
    body = base64.b64decode(V1["body_bytes_b64"])
    sig = V1["overlap_header"] if case.get("header") == "overlap" else "v1," + V1["signature_" + case["secret"].lower()]
    headers = {"webhook-id": V1["msg_id"], "webhook-timestamp": str(V1["timestamp"]), "webhook-signature": sig}
    assert verify_result(_v1_secret(case["secret"]), headers, body, now=case["now"]) == "ok"


@pytest.mark.parametrize("case", V1["must_fail"], ids=lambda c: f"{c['secret']}-{c.get('now', 'tampered')}")
def test_signing_v1_must_fail(case):
    body = base64.b64decode(case.get("body_bytes_b64") or V1["body_bytes_b64"])
    headers = {
        "webhook-id": V1["msg_id"],
        "webhook-timestamp": str(V1["timestamp"]),
        "webhook-signature": "v1," + V1["signature_a"],
    }
    assert verify_result(_v1_secret(case["secret"]), headers, body, now=case.get("now", V1["timestamp"])) != "ok"


def test_b8_delivered_event_is_the_same_vector_in_both_files():
    b8 = V1["b8_delivered"]
    case = next(c for c in SIGNING["verify"] if c["id"] == "b8-delivered-ok")
    body = base64.b64decode(case["body_bytes_b64"])
    assert len(body) == b8["bytes"]
    assert hashlib.sha256(body).hexdigest() == b8["sha256"]
    assert sign(V1["secret_a"], b8["msg_id"], b8["timestamp"], body) == b8["signature_a"]


def _ten_line_recipe(secret, headers, body, tolerance_s=300, now=None):
    """The documented ten-line receiver, verbatim but for ``now`` (so recorded vectors can be judged)."""
    key = base64.b64decode(secret.removeprefix("whsec_"))
    msg_id, ts = headers["webhook-id"], headers["webhook-timestamp"]
    if abs((time.time() if now is None else now) - int(ts)) > tolerance_s:
        return False
    mac = hmac.new(key, f"{msg_id}.{ts}.".encode() + body, hashlib.sha256).digest()
    expected = base64.b64encode(mac).decode()
    return any(s.startswith("v1,") and hmac.compare_digest(s[3:], expected) for s in headers["webhook-signature"].split(" "))


@pytest.mark.parametrize(
    "case",
    [c for c in SIGNING["verify"] if c["expected"] in ("ok", "no_matching_signature", "timestamp_too_old",
                                                       "timestamp_too_new") and "webhook-id" in c["headers"]],
    ids=lambda c: c["id"],
)
def test_sdk_and_the_ten_line_recipe_agree(case):
    body = base64.b64decode(case["body_bytes_b64"])
    sdk_ok = verify_result(case["secret"], case["headers"], body, now=case["now"]) == "ok"
    assert _ten_line_recipe(case["secret"], case["headers"], body, now=case["now"]) is sdk_ok
