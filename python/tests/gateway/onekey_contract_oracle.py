"""Independent contract-r3 oracles; no production classification imports."""

import json
from pathlib import Path

import httpx
import fi.gateway as gw

CONTRACT = json.loads(Path(__file__).with_name("onekey_contract_rows.json").read_text())
R3_ADDITIONS = json.loads(Path(__file__).with_name("onekey_contract_r3_rows.json").read_text())
ROWS = CONTRACT["rows"] + R3_ADDITIONS["rows"]
BY_CODE = {row["code"]: row for row in ROWS}
TIMEOUT_REMEDY = (
    "The gateway timed out; check whether the request was applied before sending it again."
)
R1 = {
    "managed_credits_exhausted", "managed_credits_insufficient", "agent_budget_exhausted",
    "budget_exceeded", "org_budget_exceeded", "managed_spend_velocity",
    "rate_limit_exceeded", "managed_billing_unavailable",
}
CREDIT = {"managed_credits_exhausted", "managed_credits_insufficient", "payment_required"}
AGENT = {
    "agent_budget_exhausted", "agent_call_cap_exceeded", "call_cap_unenforceable",
    "agent_run_stopped", "agent_key_budget_exhausted",
}
BUDGET = {"budget_exceeded", "org_budget_exceeded", "usage_paused", "quota_exceeded"}
RATE = {"managed_spend_velocity", "rate_limit_exceeded", "token_rate_limit_exceeded", "budget_throttled"}
BACKOFF = {"rate_limit_exceeded", "token_rate_limit_exceeded", "managed_billing_unavailable", "key_list_not_loaded", "budget_state_unavailable"}
AFTER = {"budget_throttled", "provider_busy", "idempotency_in_progress"}
STATUS_CLASSES = {
    400: gw.BadRequestError, 401: gw.AuthenticationError, 402: gw.APIStatusError,
    403: gw.PermissionDeniedError, 404: gw.NotFoundError, 409: gw.APIStatusError,
    410: gw.APIStatusError, 422: gw.UnprocessableEntityError, 429: gw.RateLimitError,
    503: gw.ServiceUnavailableError, 504: gw.GatewayTimeoutError,
}


def expected_class(row):
    code = row["code"]
    if code in CREDIT:
        return gw.InsufficientCreditsError
    if code in AGENT:
        return gw.AgentBudgetExhaustedError
    if code in BUDGET:
        return gw.BudgetExceededError
    if code == "future_agi_credits_off":
        return gw.FutureAGICreditsOffError
    return STATUS_CLASSES[row["status"]]


def expected_category(row):
    code = row["code"]
    if code in CREDIT:
        return "out_of_credits"
    if code in AGENT:
        return "agent_budget"
    if code in BUDGET or code == "managed_spend_paused":
        return "budget_limit"
    if code in RATE:
        return "rate_limit"
    if code in {"managed_billing_unavailable", "budget_state_unavailable"}:
        return "billing_unavailable"
    if row["status"] == 403:
        return "permission"
    if code == "invalid_api_key":
        return "invalid_key"
    return "generic"


def sample(schema):
    if schema is None:
        return None
    if "oneOf" in schema:
        return sample(schema["oneOf"][0])
    if "const" in schema:
        return schema["const"]
    if "enum" in schema:
        return schema["enum"][0]
    kind = schema.get("type")
    if kind == "object":
        return {name: sample(value) for name, value in schema["properties"].items()}
    if kind == "array":
        return ["fixture-model"]
    if kind in ("number", "integer"):
        return 1
    if kind == "null" or isinstance(kind, list):
        return None
    return "fixture-value"


def wire(row, metadata=None):
    error = {"message": "contract refusal", "code": row["code"], "type": row["type"]}
    if metadata is not None:
        error["metadata"] = metadata
    return {"error": error}


def response(row, metadata=None, header="2"):
    headers = {} if header is None else {"Retry-After": header}
    return httpx.Response(row["status"], json=wire(row, metadata), headers=headers)


def expected_remedy(row):
    return TIMEOUT_REMEDY if row["code"] == "gateway_timeout" else row["remedy"]


def check_error(exc, row, metadata):
    assert type(exc) is expected_class(row)
    assert exc.category == expected_category(row)
    assert exc.remedy == expected_remedy(row)
    assert exc.code == row["code"]
    assert getattr(exc, "metadata", None) == (metadata or {})
    for key, value in (metadata or {}).items():
        assert getattr(exc, key, "missing") == value


def expected_attempts(row, metadata, header="2"):
    code = row["code"]
    meta = metadata or {}
    if code in BACKOFF:
        return 6
    if code in AFTER:
        return 6 if header is not None and header == "2" else 1
    if code == "managed_spend_velocity":
        return 6 if meta.get("remedy_hint") == "retry" and "reason" not in meta and header == "2" else 1
    if code == "managed_credits_insufficient":
        return 2 if (meta.get("limit_source"), meta.get("remedy_hint"), header) == ("agentcc_in_flight", "retry", "2") else 1
    return 1
