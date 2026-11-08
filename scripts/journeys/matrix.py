"""Fail-closed result assembly; absence never qualifies a capability."""
from catalog import applies, catalog
from absence_evidence import collect


def state(checks):
    if any(c["state"] == "FAIL" for c in checks):
        return "FAIL"
    if not checks or any(c["state"] == "NOT-EVALUATED" for c in checks):
        return "NOT-EVALUATED"
    return "PASS"


def build(binding, policy, probes, archive, selected, network):
    rows = []
    for definition in catalog():
        identity, namespace = definition["id"], definition["namespace"]
        for variant in ("py", "ts", "absence"):
            row = {**definition, "variant": variant, "gate_kind": "absence" if variant == "absence" else "capability",
                   "state": "NOT-EVALUATED", "reason": "Backend journey not implemented; definition only", "checks": []}
            if variant == "absence":
                row["applies_when"] = "served:sdk-artifacts & admitted:sdk"
            if not applies(row["applies_when"], binding):
                row["reason"] = "LM served/admitted predicate is false or unbound"
            elif variant == "absence" and identity not in ("N00", "N01"):
                off = [lang for lang in ("py", "ts") if policy["states"][namespace][lang] == "OFF"]
                if not off:
                    row["reason"] = "No language of this namespace is OFF"
                else:
                    for lang in off:
                        row["checks"].extend(collect(namespace, lang, policy, probes, archive))
                    row["state"] = state(row["checks"])
                    row["reason"] = "Absence evidence only; never announcement evidence"
            elif variant == "absence":
                row["reason"] = "Core install/config cannot be independently removed"
            elif identity not in selected:
                row["reason"] = "Not selected for this run"
            elif identity in ("N00", "N01"):
                prefix = "install." if identity == "N00" else "config."
                profiles = ("base", "evals", "tracing") if identity == "N00" else ("base",)
                expected = [f"py-{v}-{extra}" for v in ("3.10", "3.12") for extra in profiles] if variant == "py" else ["ts-20", "ts-22"]
                for runtime in expected:
                    probe = probes.get(runtime, {"checks": []})
                    relevant = [c for c in probe["checks"] if c["name"].startswith(prefix)]
                    if not relevant:
                        row["checks"].append({"name": prefix + "missing-runtime", "state": "NOT-EVALUATED", "reason": "No evidence for required runtime/profile", "runtime": runtime})
                    if runtime.startswith(variant + "-"):
                        row["checks"].extend({**c, "runtime": runtime} for c in relevant)
                        if identity == "N00":
                            row["checks"].extend({**c, "runtime": runtime} for c in probe["checks"] if c["name"].startswith("absence.") and not c["name"].endswith(".docs"))
                if identity == "N00":
                    row["checks"].extend(c for c in archive[variant] if not c["name"].endswith(".docs"))
                row["state"] = state(row["checks"])
                row["reason"] = "Installed-artifact local fixture evidence; not backend qualification"
            elif identity == "N15" and variant == "ts" and policy.get("ts_agent_code_offered") is not True:
                row.update(state="NOT-OFFERED", reason="TypeScript facade not admitted",
                           authority="SDK plan section 5.5: TypeScript agents-as-code only if its facade lands")
            # Global forbidden egress contaminates every attempted result, even if a caller caught the error.
            if row["checks"] and (network["denied_count"] or network.get("complete") is False):
                row["state"] = "FAIL"
                row["reason"] = "Forbidden network attempt detected" if network["denied_count"] else "Container network accounting incomplete"
            rows.append(row)
    return rows


def table(rows):
    lines = ["Namespace             Python          TypeScript      Absence", "-" * 71]
    for definition in catalog():
        entries = {r["variant"]: r["state"] for r in rows if r["id"] == definition["id"]}
        lines.append(f'{definition["id"]} {definition["namespace"]:18} {entries["py"]:15} {entries["ts"]:15} {entries["absence"]}')
    lines.append("NOT-EVALUATED is OFF. Absence PASS never enables a namespace. See JSON for reasons.")
    return "\n".join(lines) + "\n"
