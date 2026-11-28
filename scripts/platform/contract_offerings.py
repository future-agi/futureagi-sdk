"""Public case scheduling is separate from the complete contract inventory."""
MODES = {"py_sync": "py", "py_async": "py", "ts": "ts"}


def declaration(value):
    if (not isinstance(value, dict) or value.get("status") != "NOT-OFFERED"
            or not value.get("owner") or not value.get("reason")):
        raise ValueError("NOT-OFFERED requires status, owner and reason")
    return value


def match(name, entries):
    keys = [key for key in entries if name == key or name.startswith(key + ".")]
    return entries[max(keys, key=len)] if keys else None


def public_inventory(rows, platform_unavailable, offerings):
    schedules, excluded = {m: [] for m in MODES}, {m: [] for m in MODES}
    for value in platform_unavailable.values():
        declaration(value)
    for row in rows:
        wrappers = row.get("wrappers", [row.get("wrapper", {})])
        for mode, language in MODES.items():
            unavailable = match(row["name"], platform_unavailable) if row["adapter"] == "platform" else None
            unavailable = unavailable or match(row["name"], offerings.get(row["adapter"], {}).get(mode, {}))
            offered = [w for w in wrappers if w.get(language)]
            if not unavailable and not offered:
                unavailable = wrappers[0].get("not_offered", {}).get(language)
                if not unavailable:
                    raise ValueError(f"missing {language} public path: {row['id']}")
                unavailable = {"owner": row["name"].split(".")[0], **unavailable}
            if unavailable:
                excluded[mode].append({"id": row["id"], **declaration(unavailable)})
            else:
                # Choose this language's real primary method, not wrappers[0]'s absent twin.
                root = offered[0][language].split(".")[0]
                if root != "client" and not row.get("handle_fixtures", {}).get(root, {}).get(language):
                    raise ValueError(f"public handle fixture required for {root}: {row['id']}")
                row.setdefault("public_wrappers", {})[mode] = offered[0]
                schedules[mode].append(row["id"])
    return schedules, excluded
