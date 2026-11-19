"""Exact platform policy pins for each credential-read artifact configuration."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CREDENTIAL_READS = json.loads((ROOT / "openapi/connectors/features.json").read_text())["credential_reads"]
OPERATION_COUNT = 57 if CREDENTIAL_READS else 54
HTTP_IDEMPOTENT_COUNT = 35 if CREDENTIAL_READS else 32
PAGINATED_COUNT = 5 if CREDENTIAL_READS else 4
CREDENTIAL_OPERATIONS = {"platform.credentials.bindings", "platform.credentials.get", "platform.credentials.list"}


def assert_credential_scope(names):
    expected = CREDENTIAL_OPERATIONS if CREDENTIAL_READS else set()
    assert {name for name in names if name.startswith("platform.credentials.")} == expected
