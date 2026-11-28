"""Exact platform policy pins for each credential-read artifact configuration."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CREDENTIAL_READS = json.loads((ROOT / "openapi/connectors/features.json").read_text())["credential_reads"]
# The 24 sandbox operations (sandboxes.*) add 24 operations, 15 http-idempotent, 4 paginated.
OPERATION_COUNT = 81 if CREDENTIAL_READS else 78
HTTP_IDEMPOTENT_COUNT = 50 if CREDENTIAL_READS else 47
PAGINATED_COUNT = 9 if CREDENTIAL_READS else 8
CREDENTIAL_OPERATIONS = {"platform.credentials.bindings", "platform.credentials.get", "platform.credentials.list"}


def assert_credential_scope(names):
    expected = CREDENTIAL_OPERATIONS if CREDENTIAL_READS else set()
    assert {name for name in names if name.startswith("platform.credentials.")} == expected
