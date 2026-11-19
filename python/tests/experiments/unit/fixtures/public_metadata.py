"""Project recorded judge fixtures onto public, behavior-bearing metadata."""
from copy import deepcopy
from hashlib import sha256


def public_fixture(value: dict) -> dict:
    """Keep model exchanges and verdicts intact; omit private collection provenance."""
    result = deepcopy(value)
    provenance = result.get("provenance", {})
    for key in ("e2e_sha", "sdk_sha", "sdk_sha_note", "suite_run_id", "row"):
        provenance.pop(key, None)
    provenance["record"] = "judge-paraphrase-and-criteria-regressions"

    def visit(node):
        if isinstance(node, dict):
            for key, item in node.items():
                if key == "system_fingerprint" and isinstance(item, str) and not item.startswith("sha256:"):
                    # An opaque, deterministic digest preserves equality between provider versions.
                    node[key] = "sha256:" + sha256(item.encode()).hexdigest()
                else:
                    visit(item)
        elif isinstance(node, list):
            for item in node:
                visit(item)

    visit(result)
    return result
