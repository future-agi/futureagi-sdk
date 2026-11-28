"""Shared and supplemental maps must agree on the exposed connector surface."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def test_shared_map_never_advertises_hidden_connector_operations():
    supplemental = json.loads((ROOT / "openapi/connectors/wrapper-map.json").read_text())["operations"]
    shared = json.loads((ROOT / "openapi/platform/wrapper-map.json").read_text())["operations"]
    for name in supplemental.keys() & shared.keys():
        row, other = supplemental[name], shared[name]
        if "unwrapped" in row:
            assert "methods" not in other, f"{name}: shared map advertises a hidden operation"
            assert other["unwrapped"]
            if row.get("feature"):
                assert other["languages"] == {"py": "NOT-OFFERED", "ts": "NOT-OFFERED"}
        else:
            for language in ("py", "ts"):
                assert [m[language] for m in other["methods"]] == [m[language] for m in row["methods"]]
