"""Independent public surface expectations, including assertions for OFF features."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
FEATURES = json.loads((ROOT / "openapi/connectors/features.json").read_text())
SURFACE = json.loads(Path(__file__).with_suffix(".json").read_text())
NAMESPACES = {"connectors": "mcp_core", "integrations": "data_integrations", "credentials": "credential_reads"}


def enabled(feature):
    parent = {"oauth_connect": "mcp_core", "slack_channels": "data_integrations"}.get(feature)
    return FEATURES[feature] and (parent is None or FEATURES[parent])


def assert_absent(client, name):
    feature, path = next((f, methods[name]) for f, methods in SURFACE.items() if name in methods)
    assert not enabled(feature), f"Enabled operation unexpectedly absent: {name}"
    namespace, *parts = path.split(".")
    if not enabled(NAMESPACES[namespace]):
        assert not hasattr(client, namespace)
    else:
        resource = getattr(client, namespace)
        for part in parts[:-1]:
            resource = getattr(resource, part)
        assert not hasattr(resource, parts[-1])
