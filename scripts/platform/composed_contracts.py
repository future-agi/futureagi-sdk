"""Independently pinned additions to the shared public contract inventory."""
from __future__ import annotations

import copy


def catalog_source(source, models):
    """Compose the reviewed model-list slice, including its documented query overrides."""
    result = copy.deepcopy(source)
    path, method = models["path"], models["method"].lower()
    if method in result["paths"].get(path, {}):
        existing = result["paths"][path][method]
        if existing["operationId"] != models["operation_id"]:
            raise ValueError("models contract identity changed")
        # An already projected source is authoritative; its reviewed overrides
        # were applied when that source was staged.
        return result
    result["paths"].setdefault(path, {})[method] = {
        "operationId": models["operation_id"],
        "parameters": [{"name": name, "in": "query", "type": "string"}
                       for name in models["overrides"]["query"]],
        "responses": {"200": {"description": "Model catalog page", "schema": models["response_schema"]}},
    }
    return result


FEATURES = {"mcp_core", "oauth_connect", "data_integrations", "slack_channels", "credential_reads"}


def connector_features(source):
    features = source("openapi/connectors/features.json")
    if (not isinstance(features, dict) or set(features) != FEATURES
            or any(type(value) is not bool for value in features.values())):
        raise ValueError("connector features must declare every supported boolean switch")
    return features


def feature_enabled(features, feature):
    if feature not in FEATURES:
        raise ValueError("unknown connector features entry")
    dependency = {"oauth_connect": "mcp_core", "slack_channels": "data_integrations"}.get(feature)
    return features[feature] and (dependency is None or features[dependency])


def feature_absences(features):
    """Retain public absence obligations when hidden routes leave the case inventory."""
    paths = []
    if not features["mcp_core"]:
        paths.append(("mcp_core", "client.connectors", "client.connectors"))
    elif not features["oauth_connect"]:
        paths.append(("oauth_connect", "client.connectors.connect_app", "client.connectors.connectApp"))
    if not features["data_integrations"]:
        paths.append(("data_integrations", "client.integrations", "client.integrations"))
    elif not features["slack_channels"]:
        paths.append(("slack_channels", "client.integrations.slack_channels", "client.integrations.slackChannels"))
    if not features["credential_reads"]:
        paths.append(("credential_reads", "client.credentials", "client.credentials"))
    return [{"id": feature, "py": py, "ts": ts, "status": "NOT-OFFERED",
             "owner": "connectors", "reason": "Disabled in the connector feature inputs"}
            for feature, py, ts in paths]


def mapped_cases(source, case, operations, features):
    """Connector routes come from their own pinned slices, not runtime descriptors."""
    mapping = source("openapi/connectors/wrapper-map.json")
    documents = {name: source(info["slice"]) for name, info in mapping["sources"].items()}
    indexes = {name: {op["operationId"]: (method, path, op) for method, path, op, _ in operations(doc)}
               for name, doc in documents.items()}
    rows = []
    for name, entry in mapping["operations"].items():
        if entry.get("unwrapped"):
            continue
        if not feature_enabled(features, entry["feature"]):
            continue
        method, path, op = indexes[entry["source"]][entry["operation_id"]]
        row = case(documents[entry["source"]], method, path, op, name, "connectors")
        row["wrappers"] = entry["methods"]
        row["platform_origin"] = entry["source"] == "ee"
        row["envelope_adapter"] = False
        row["public_response_field"] = "result" if entry["source"] == "fa" else None
        if name == "connectors.connect":
            row["public_response_field"] = "authorizeUrl"
        row["public_page"] = name in {"platform.credentials.list", "integrations_connections_list",
                                       "integrations_connections_slack_channels_list", "integrations_sync-logs_list"}
        rows.append(row)
    return rows


def tracing_cases(source, case, operations):
    doc = source("openapi/tracing/source.json")
    mapping = source("openapi/tracing/wrapper-map.json")
    index = {op["operationId"]: (method, path, op) for method, path, op, _ in operations(doc)}
    rows = []
    for entry in mapping["operations"]:
        method, path, op = index[entry["operation_id"]]
        row = case(doc, method, path, op, "tracing." + entry["ts"], "tracing")
        row["wrapper"] = entry["public"]
        row["envelope_adapter"] = False
        rows.append(row)
    return rows
