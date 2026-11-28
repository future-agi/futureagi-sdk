"""Check the shape and digest of the recorded plain-transport fixture.

``fixtures/plaintext_rule_rows.json`` lists, for the gRPC exporter, the HTTP exporter and the experiments exporter,
one row per cell of host kind, scheme or insecure source, ``FI_ALLOW_INSECURE_HTTP`` value and proxy setting, with
the decision it recorded. This test checks fixture integrity, not the SDK's transport decisions.
SDK-built plain transports ignore proxy settings from the environment; the sealed oracle
(``test_plaintext_oracle_conformance``) checks current behavior row by row.
``plaintext_rule_rows.json.sha256`` records the fixture digest in ``sha256sum`` format.
"""

import hashlib
import json
import pathlib

FIXTURE = pathlib.Path(__file__).parent / "fixtures" / "plaintext_rule_rows.json"
ROWS = json.loads(FIXTURE.read_text())["rows"]


def test_the_fixture_has_one_row_per_cell():
    ids = [row["id"] for row in ROWS]
    assert len(ids) == len(set(ids)) == 468
    assert {row["transport"] for row in ROWS} == {"grpc", "http", "experiments-exporter"}


def test_the_fixture_sidecar_matches_the_file():
    sidecar = FIXTURE.with_name(FIXTURE.name + ".sha256").read_text()
    digest, _, name = sidecar.strip().partition("  ")
    assert name == FIXTURE.name
    assert digest == hashlib.sha256(FIXTURE.read_bytes()).hexdigest()
