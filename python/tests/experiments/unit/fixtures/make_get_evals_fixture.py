"""Build a get-evals fixture from template YAMLs, or refresh its public metadata.

The normal mode reads a caller-selected backend revision using read-only Git commands.
The --public-fixture mode preserves an existing response byte-for-byte as parsed JSON.
"""
from copy import deepcopy
import json
import subprocess
import sys
import uuid

import yaml


def public_fixture(document):
    """Keep the response unchanged and describe its source without private checkout details."""
    result = deepcopy(document)
    result["_provenance"] = {
        "kind": "generated from template YAMLs, NOT recorded from a server",
        "backend_repo": "Future AGI backend",
        "shape": "sdk/views/evaluations.py GetEvalsView.get; _folder is fixture-only",
        "note": "criteria, config.code and config.rule_prompt omitted and descriptions cut to 160 chars to keep the fixture small",
        "generated_by": "template response fixture generator",
        "templates": len(result["response"]["result"]),
    }
    return result


def generate(repo, ref):
    sha = subprocess.run(["git", "-C", repo, "rev-parse", ref], capture_output=True, text=True).stdout.strip()
    names = subprocess.run(["git", "-C", repo, "ls-tree", "-r", "--name-only", sha], capture_output=True, text=True).stdout.split()
    files = sorted(n for n in names if "/model_hub/system_evals/" in n and n.endswith(".yaml"))
    records = []
    for file in files:
        source = subprocess.run(["git", "-C", repo, "show", f"{sha}:{file}"], capture_output=True, text=True).stdout
        data = yaml.safe_load(source)
        records.append({
            "id": str(uuid.uuid5(uuid.NAMESPACE_URL, "fixture:" + data["name"])),
            "name": data["name"],
            "description": (data.get("description") or "")[:160],
            "eval_id": data.get("eval_id"),
            "eval_tags": data.get("eval_tags") or [],
            "config": {key: value for key, value in (data.get("config") or {}).items() if key not in ("code", "rule_prompt")},
            "criteria": None,
            "choices": data.get("choices"),
            "multi_choice": data.get("multi_choice", False),
            "owner": "system",
            "_folder": file.split("/system_evals/")[1].split("/")[0],
        })
    return public_fixture({"response": {"status": True, "result": records}})


def main(argv):
    if argv[0] == "--public-fixture":
        with open(argv[1], encoding="utf-8") as source:
            original = json.load(source)
        result = public_fixture(original)
        assert result["response"] == original["response"]
        output = argv[2]
    else:
        result = generate(argv[0], argv[1])
        output = argv[2]
    with open(output, "w", encoding="utf-8") as destination:
        destination.write(json.dumps(result, indent=1, ensure_ascii=False) + "\n")
    print(len(result["response"]["result"]))


if __name__ == "__main__":
    main(sys.argv[1:])
