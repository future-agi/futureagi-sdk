"""Independent response fixtures, including the public envelope contract."""
import copy


def envelope_adapter(row):
    return row.get("envelope_adapter", row["name"].split(".")[0] in ("prompts", "knowledgeBases", "scores")) or row["adapter"] == "management"


def unwraps(row):
    return row.get("unwrap_result", envelope_adapter(row) and row["name"] != "scores.forSource")


def payloads(row):
    explicit = row.get("invocation", {}).get("response")
    if explicit:
        return explicit["wire"], explicit["public"]
    if row.get("success_status") == 204:
        return None, None
    page = {"count": 1, "next": None, "previous": None, "results": [{"marker": "kept"}],
            "total_pages": 1, "current_page": 1}
    if row["adapter"] == "catalog":
        op = row["catalog"]
        def put(path, value):
            parts, target = path.split("."), page
            for part in parts[:-1]:
                target = target.setdefault(part, {})
            target[parts[-1]] = value
        if op["pagination"]:
            put(op["pagination"]["items"], [{"marker": "kept"}])
            if op["pagination"].get("total_items"):
                put(op["pagination"]["total_items"], 1)
        return ({op["unwrap"]: page} if op["unwrap"] else page), page
    if envelope_adapter(row):
        wire = {"status": True, "result": page}
        return wire, page if unwraps(row) else wire
    if row["adapter"] == "core":
        wire = copy.deepcopy(row.get("response_example", {"status": True, "result": page}))
        return wire, wire
    wire = copy.deepcopy(row.get("response_example", page))
    field = row.get("public_response_field")
    return wire, wire.get(field, wire) if field and isinstance(wire, dict) else wire


def plain(result):
    if hasattr(result, "to_dict"):
        return plain(result.to_dict())
    if isinstance(result, dict):
        return {k: plain(v) for k, v in result.items()}
    if isinstance(result, list):
        return [plain(v) for v in result]
    return result
