"""Adapt the generated management wrapper map without inventing runtime calls."""
UUID = "00000000-0000-4000-8000-000000000001"


def normalize(doc, mapping):
    if isinstance(mapping["operations"], dict):
        return mapping  # The small, independent public-call contract fixtures.
    result = {}
    for entry in mapping["operations"]:
        if entry["python"] == "NOT-OFFERED":
            if entry["python_async"] != "NOT-OFFERED" or entry["typescript"] != "NOT-OFFERED" or not entry["reason"]:
                raise ValueError("incomplete management absence declaration")
            continue
        name = entry["python"]
        if entry["python_async"] != name:
            raise ValueError("management Python twin mismatch")
        if name in result:
            raise ValueError("duplicate management wrapper")
        matches = [op for item in doc["paths"].values() for method, op in item.items()
                   if method in ("get", "post", "put", "patch", "delete") and op["operationId"] == entry["operation_id"]]
        if len(matches) != 1:
            raise ValueError("unknown or duplicate management operation")
        descriptor = matches[0]["x-sdk-management"]
        if descriptor["name"] != name or entry["fixed_path"] != descriptor.get("fixed_path", {}):
            raise ValueError("management wrapper identity mismatch")
        expected_args = [p for p in descriptor["path_params"] if p not in entry["fixed_path"]]
        if descriptor.get("body_arg"):
            expected_args.append(descriptor["body_arg"])
        if entry["arguments"] != expected_args:
            raise ValueError("management wrapper argument mismatch")
        args = [UUID if arg in descriptor["path_params"] else {} for arg in entry["arguments"]]
        result[name] = {"operation_id": entry["operation_id"], "methods": [{
            "py": "client." + name, "ts": "client." + entry["typescript"],
            "contract": {"py": {"args": args, "kwargs": {}}, "ts": {"args": args}},
        }]}
    return {"operations": result}
