"""Single source of definitions for the consumer language/namespace matrix."""

ROWS = [
    ("install", "Install/import every documented entry point; Python 3.10/3.12 base, evals, tracing; Node 20/22 ESM/CJS; doctor JSON", "OFF namespaces absent; no fi console script"),
    ("config", "Login from environment; default client; identical personal-key headers per namespace", "Mixed credentials and unsafe origins refused; FI pair refused by AgentCC; virtual key never sent to management"),
    ("datasets", "Create, add rows, read back, version snapshot when served, delete", "Other organization refused with zero change"),
    ("experiments", "Python deterministic runner/upload/readback; both languages management list/get", "Other organization refused"),
    ("evals", "Deterministic evaluation; templates list; Python evals CLI", "Other organization refused; missing key gives typed error"),
    ("tracing", "Separate instrumentation package and stub agent; query spans with intact parent-child relation; alerts", "Other organization refused"),
    ("prompts", "Create, commit version, label, get by label, compile", "Other organization refused"),
    ("knowledge_bases", "Create, add text document, list, delete", "Other organization refused"),
    ("annotations", "Create queue, add item, submit score, read; default queue with label_ids", "Other organization refused"),
    ("simulations", "List agent definitions; create and get scenario", "Other organization refused"),
    ("gateway", "Plain/stream chat, embeddings, models, responses, messages, feedback, guardrail typed error, metadata, no ignored config; TS framework examples", "FI pair refused; revoked personal virtual key refused"),
    ("gateway_management", "Active config, cache update and data-plane effect, rollback; session-created personal key use/revoke; masked providers, logs, analytics, feedback, alerts create/delete", "Member update refused with typed 403; other organization logs refused"),
    ("billing", "Models and personal-key reads when certified; cloud billing reads; never legacy organization-key fetch", "Self-host ProductNotAvailableError; other organization refused"),
    ("agents", "Create/get/update/revision/release/rollback; schedule create/run/delete; environments", "Other organization refused"),
    ("runs", "Authoritative runs journey: create with idempotency/wait; events resume; cancel", "Authoritative runs journey: other organization and mixed auth refused"),
    ("agent_code", "Authoritative agents-as-code journey", "No independent substitute for authoritative journey"),
    ("sandboxes", "Create network-off; run echo ok; file write/read; kill", "Network-on typed refusal; other organization refused"),
    ("deployments", "Create tarball; health; logs; delete", "Other organization refused"),
    ("connectors", "Catalog; OAuth URL without completion; loopback custom MCP refresh/attach/detach/delete; stub FA source validate/pause/resume/sync/logs", "Other organization refused"),
    ("webhooks", "Delivered and tampered event verification; Python endpoint management", "Tampered event rejected"),
]
# API identities: Python modules, client accessors, TypeScript names, probe calls.
# These are not emitted file paths. ts_inventory derives those from the tarball.
SURFACES = {
    "datasets": (["datasets"], ["datasets"], ["datasets"], ["datasets.list", "datasets.list"]),
    "experiments": (["experiments"], ["experiments", "experiments_v2", "experiment_runs"], ["experiments", "experimentsV2", "experimentRuns"], ["experiments_v2.list", "experimentsV2.list"]),
    "evals": (["evals"], ["evals"], ["evals"], ["evals.list_templates", "evals.listTemplates"]),
    "tracing": (["tracing"], ["tracing", "alerts"], ["tracing", "alerts"], ["tracing.projects", "tracing.projects"]),
    "prompts": (["prompts", "prompt"], ["prompts"], ["prompts", "prompt"], ["prompts.list", "prompts.list"]),
    "knowledge_bases": (["knowledge_bases", "kb"], ["knowledge_bases"], ["knowledgeBases", "kb"], ["knowledge_bases.list", "knowledgeBases.list"]),
    "annotations": (["annotations", "queues", "scores"], ["annotation_queues", "scores"], ["annotationQueues", "scores", "queues", "annotations"], ["annotation_queues.list", "annotationQueues.list"]),
    "simulations": (["simulations"], ["simulations"], ["simulations"], ["simulations.agent_definitions.list", "simulations.agentDefinitions.list"]),
    "gateway": (["gateway"], [], ["gateway"], []),
    "gateway_management": (["gateway_management"], ["gateway"], ["gatewayManagement"], ["gateway.config.get_active", "gateway.config.getActive"]),
    "billing": (["billing", "models", "keys"], ["billing", "models", "keys"], ["billing", "models", "keys"], ["models.list", "models.list"]),
    "agents": (["agents", "environments"], ["agents", "environments"], ["agents", "environments"], ["agents.list", "agents.list"]),
    "runs": (["runs", "agents.runs"], ["agents.runs"], ["runs"], ["agents.runs.list", "agents.runs.list"]),
    "agent_code": (["agents.code"], ["agents.code"], ["agents/code"], ["agents.code.list", "agents.code.list"]),
    "sandboxes": (["sandboxes"], ["sandboxes"], ["sandboxes"], ["sandboxes.list", "sandboxes.list"]),
    "deployments": (["deployments"], ["deployments"], ["deployments"], ["deployments.list", "deployments.list"]),
    "connectors": (["connectors", "integrations", "credentials"], ["connectors", "integrations", "credentials"], ["connectors", "integrations", "credentials"], ["connectors.catalog.list", "connectors.catalog.list"]),
    "webhooks": (["webhooks"], ["webhooks"], ["webhooks"], []),
}


def catalog():
    rows = []
    for i, (name, positive, negative) in enumerate(ROWS):
        surface = "sdk-artifacts" if i == 0 else "sdk-config" if i == 1 else name
        product = "console" if i in (13, 14, 15) else "sdk"
        row = {"id": f"N{i:02}", "namespace": name, "positive": positive, "negative": negative,
               "applies_when": f"served:{surface} & admitted:{product}", "if_absent": "NOT-EVALUATED"}
        if i in (14, 15):
            row["authoritative_journey"] = "J30" if i == 14 else "J23"
        row["not_offered"] = []
        if i == 3:
            row["not_offered"] = [{"language": "ts", "part": "runner", "authority": "SDK plan section 5.5: no TypeScript experiment runner"}]
        if i == 19:
            row["not_offered"] = [{"language": "ts", "part": "management", "authority": "SDK plan section 5.5: TypeScript verifies only"}]
        for part in row["not_offered"]:
            part["state"] = "NOT-OFFERED"
        rows.append(row)
    return rows


def legs():
    return [{**row, "id": row["id"] + "." + variant, "namespace_id": row["id"], "variant": variant,
             "gate_kind": "absence" if variant == "absence" else "capability",
             "applies_when": "served:sdk-artifacts & admitted:sdk" if variant == "absence" else row["applies_when"],
             "absence_when": "namespace OFF for either language" if variant == "absence" else None,
             "steps": ["Artifact files, imports, client accessors, export map and documentation absent"] if variant == "absence" else [row["positive"], row["negative"]]}
            for row in catalog() for variant in ("py", "ts", "absence")]


def applies(expression, binding):
    """Only the served/admitted grammar is accepted; unknown input fails closed."""
    for token in expression.split(" & "):
        kind, value = token.split(":", 1)
        if kind not in ("served", "admitted"):
            raise ValueError("Unsupported binding predicate")
        if value not in binding.get(kind, []):
            return False
    return True
