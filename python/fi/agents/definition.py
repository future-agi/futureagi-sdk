"""Versioned, declarative Console agent files. No credentials or runtime state."""
from __future__ import annotations

import copy
import hashlib
import json
import re
from typing import Any

from fi.errors import ConfigurationError

SCHEMA = "futureagi-agent/v1"
LIMIT = 1024 * 1024
DEFAULTS = {
    "examples": [],
    "skills": [],
    "unattended": False,
    "sharing": {"mode": "private", "accountIds": []},
}
REQUIRED = {
    "name",
    "role",
    "purpose",
    "responsibilities",
    "workMode",
    "connectorBindingIds",
}
OPTIONAL = set(DEFAULTS) | {
    "modelId",
    "environmentId",
    "environmentRevision",
    "toolPolicy",
}


def invalid(message: str, code: str = "agent_definition_invalid") -> None:
    raise ConfigurationError(message, code=code)


def object_(value: Any, required: set[str], optional: set[str] = frozenset()) -> dict:
    if (
        not isinstance(value, dict)
        or set(value) - required - optional
        or required - set(value)
    ):
        invalid("Agent definition has missing or unsupported fields.")
    return value


def text(value: Any, maximum: int) -> str:
    if (
        not isinstance(value, str)
        or not value
        or value != value.strip()
        or len(value.encode("utf-8")) > maximum
        or re.search(r"[\x00-\x1f\x7f]", value)
    ):
        invalid(
            f"Text must be canonical, nonempty, control-free and at most {maximum} UTF-8 bytes."
        )
    return value


def integer(value: Any) -> int:
    if type(value) is not int or not 1 <= value <= 9007199254740991:
        invalid("Revision must be a positive safe integer.")
    return value


def texts(value: Any, count: int, maximum: int) -> list[str]:
    if not isinstance(value, list) or len(value) > count:
        invalid(f"Expected an array of at most {count} items.")
    result = [text(item, maximum) for item in value]
    if len(set(result)) != len(result):
        invalid("Duplicate entries are not allowed.")
    return result


def canonical(value: Any) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
        allow_nan=False,
    )


def digest(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def validate(document: Any) -> dict:
    """Local structural validation; the backend still checks references, permissions and quotas."""
    object_(document, {"schemaVersion", "spec"})
    if document["schemaVersion"] != SCHEMA:
        invalid(f"Expected schemaVersion {SCHEMA}.")
    spec = copy.deepcopy(object_(document["spec"], REQUIRED, OPTIONAL))
    for key, maximum in (
        ("name", 200),
        ("role", 200),
        ("purpose", 4000),
        ("modelId", 256),
    ):
        if key in spec:
            text(spec[key], maximum)
    texts(spec["responsibilities"], 64, 1000)
    texts(spec["connectorBindingIds"], 64, 256)
    if spec["workMode"] not in ("on_demand", "always_on"):
        invalid("workMode must be on_demand or always_on.")
    for key, value in DEFAULTS.items():
        spec.setdefault(key, copy.deepcopy(value))
    if type(spec["unattended"]) is not bool:
        invalid("unattended must be a boolean.")
    examples = spec["examples"]
    if not isinstance(examples, list) or len(examples) > 16:
        invalid("At most 16 examples are supported.")
    for example in examples:
        object_(example, {"prompt", "response"})
        text(example["prompt"], 2000)
        text(example["response"], 2000)
    skills = spec["skills"]
    if not isinstance(skills, list) or len(skills) > 8:
        invalid("At most eight skills are supported.")
    seen = set()
    for skill in skills:
        object_(skill, {"id", "revision"})
        sid = text(skill["id"], 256)
        if not re.fullmatch(r"skill_[a-f0-9-]{36}", sid) or sid in seen:
            invalid("Skills require unique server-issued IDs.")
        seen.add(sid)
        integer(skill["revision"])
    sharing = object_(spec["sharing"], {"mode", "accountIds"})
    ids = texts(sharing["accountIds"], 64, 256)
    if sharing["mode"] not in ("private", "workspace", "selected") or (
        (sharing["mode"] == "selected") != bool(ids)
    ):
        invalid(
            "Selected sharing needs accountIds; private/workspace sharing needs an empty array."
        )
    if ("environmentId" in spec) != ("environmentRevision" in spec):
        invalid("environmentId and environmentRevision must be supplied together.")
    if "environmentId" in spec:
        text(spec["environmentId"], 256)
        integer(spec["environmentRevision"])
    if "toolPolicy" in spec:
        policy = object_(spec["toolPolicy"], {"protocol", "tools"}, {"defaultMode"})
        if policy["protocol"] != "omega-workforce-tool-policy/v1":
            invalid("Unsupported tool policy protocol.")
        modes = ("auto", "ask", "deny")
        if "defaultMode" in policy and policy["defaultMode"] not in modes:
            invalid("Invalid default tool mode.")
        if not isinstance(policy["tools"], dict) or len(policy["tools"]) > 256:
            invalid("At most 256 tool policies are supported.")
        for tool, entry in policy["tools"].items():
            text(tool, 256)
            object_(entry, {"mode"}, {"reason"})
            if entry["mode"] not in modes:
                invalid("Invalid tool mode.")
            if "reason" in entry:
                text(entry["reason"], 512)
    result = {"schemaVersion": SCHEMA, "spec": spec}
    if len(canonical(result).encode("utf-8")) > LIMIT:
        invalid("Agent definition exceeds 1 MiB.")
    return result


def project(envelope: Any, agent_id: str | None = None) -> tuple[str, int, dict]:
    """Read only authored fields, never runtime health, credentials or deployed-version fields."""
    if (
        not isinstance(envelope, dict)
        or envelope.get("schemaVersion") != "omega-workforce/v1"
    ):
        invalid("Malformed agent response.", "agent_response_invalid")
    agent = envelope.get("agent")
    if not isinstance(agent, dict):
        invalid("Missing agent response.", "agent_response_invalid")
    aid, version = text(agent.get("id"), 256), integer(agent.get("version"))
    if agent_id is not None and aid != agent_id:
        invalid("Server returned a different agent.", "agent_response_invalid")
    spec = {key: agent[key] for key in REQUIRED | OPTIONAL if key in agent}
    bindings = agent.get("connectorBindings")
    if not isinstance(bindings, list) or any(
        not isinstance(b, dict) or "id" not in b for b in bindings
    ):
        invalid("Missing connector references in response.", "agent_response_invalid")
    spec["connectorBindingIds"] = [b["id"] for b in bindings]
    if agent.get("environment") is not None:
        env = object_(agent["environment"], {"id", "revision"})
        spec.update(environmentId=env["id"], environmentRevision=env["revision"])
    return aid, version, validate({"schemaVersion": SCHEMA, "spec": spec})


def diff(before: Any, after: Any, path: str = "") -> list[dict]:
    """Stable JSON-pointer diff, preserving old values and array ordering (no fuzzy matching)."""
    if before == after:
        return []
    if isinstance(before, dict) and isinstance(after, dict):
        result = []
        for key in sorted(before.keys() | after.keys()):
            pointer = path + "/" + key.replace("~", "~0").replace("/", "~1")
            if key not in before:
                result.append({"op": "add", "path": pointer, "value": after[key]})
            elif key not in after:
                result.append({"op": "remove", "path": pointer, "old": before[key]})
            else:
                result.extend(diff(before[key], after[key], pointer))
        return result
    return [{"op": "replace", "path": path, "old": before, "value": after}]
