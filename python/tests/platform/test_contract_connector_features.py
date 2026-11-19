"""Case generation follows feature inputs even before facade regeneration."""
import copy
import json

import pytest

from ._gates_support import REPO, load

FEATURES = ("mcp_core", "oauth_connect", "data_integrations", "slack_channels", "credential_reads")


def generate_with(monkeypatch, features):
    monkeypatch.syspath_prepend(str(REPO / "scripts/platform"))
    generator = load("connector_feature_cases", "scripts/platform/contract_cases.py")
    read = generator.read
    monkeypatch.setattr(generator, "read", lambda root, path: copy.deepcopy(features)
                        if path == "openapi/connectors/features.json" else read(root, path))
    return generator.generate()


@pytest.mark.parametrize("hidden", [*FEATURES, "all"])
def test_case_schedules_derive_connector_availability(monkeypatch, hidden):
    current = json.loads((REPO / "openapi/connectors/features.json").read_text())
    features = {name: current[name] and hidden not in (name, "all") for name in FEATURES}
    generated = generate_with(monkeypatch, features)
    mapping = json.loads((REPO / "openapi/connectors/wrapper-map.json").read_text())
    enabled = {**features,
               "oauth_connect": features["oauth_connect"] and features["mcp_core"],
               "slack_channels": features["slack_channels"] and features["data_integrations"]}
    expected = {"connectors:" + name for name, row in mapping["operations"].items()
                if row.get("feature") and enabled[row["feature"]]}
    actual = {row["id"] for row in generated["operations"] if row["adapter"] == "connectors"}
    assert actual == expected
    credentials = {"platform:platform.credentials." + method for method in ("bindings", "get", "list")}
    for mode in ("py_sync", "py_async", "ts"):
        scheduled = set(generated["public_cases"][mode])
        assert expected <= scheduled
        assert scheduled.intersection(credentials) == (credentials if features["credential_reads"] else set())
        assert not any("connectors:" + name in scheduled for name, row in mapping["operations"].items()
                       if row.get("feature") and not enabled[row["feature"]])
    assert "openapi/connectors/features.json" in generated["inputs"]
    expected_absent = []
    if not features["mcp_core"]:
        expected_absent.append(("client.connectors", "client.connectors"))
    elif not features["oauth_connect"]:
        expected_absent.append(("client.connectors.connect_app", "client.connectors.connectApp"))
    if not features["data_integrations"]:
        expected_absent.append(("client.integrations", "client.integrations"))
    elif not features["slack_channels"]:
        expected_absent.append(("client.integrations.slack_channels", "client.integrations.slackChannels"))
    if not features["credential_reads"]:
        expected_absent.append(("client.credentials", "client.credentials"))
    assert [(row["py"], row["ts"]) for row in generated["feature_absences"]] == expected_absent
    assert all(row["status"] == "NOT-OFFERED" and row["reason"] and row["owner"]
               for row in generated["feature_absences"])


@pytest.mark.parametrize("bad", [None, {}, {name: "false" for name in FEATURES},
                                   {**dict.fromkeys(FEATURES, True), "unknown": True}])
def test_connector_feature_inputs_fail_closed(monkeypatch, bad):
    with pytest.raises(ValueError, match="connector features"):
        generate_with(monkeypatch, bad)
