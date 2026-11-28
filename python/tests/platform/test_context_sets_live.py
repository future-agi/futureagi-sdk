"""The whole-context set commands (fi.context.authoring / fi.context.release) against a real backend.

These modules call uncatalogued authoring routes through ``client.request``, so the
all-operations completeness check never sees them and their unit tests use a mocked
transport. This suite runs them end to end with ``strict_responses`` on: create two
contexts over the shared skill library from one reviewed plan, apply their exact
locks, publish the set from one reviewed comparison, and preview the release.
Nothing is released and no label moves.
"""

from __future__ import annotations

import uuid


def _name(prefix: str) -> str:
    return f"sdk-{prefix}-{uuid.uuid4().hex[:8]}"


def test_context_set_create_publish_and_release_preview(client, requires_skills):
    from fi.context import authoring, release

    skill = _name("set-skill")
    text = f"---\nname: {skill}\ndescription: Use for SDK context-set validation.\n---\nFollow the refund policy.\n"
    published = client.skills.publish(
        files=[{"path": "SKILL.md", "content": text}], labels=["sdk-set"], acknowledge_warnings=True,
    )
    # Other suites share this account's library; pin each of their skills to its
    # current version so only the new skill follows the reviewed label.
    library = authoring.published_skills(client)
    assert published.skill.id in {row["id"] for row in library}
    others = {row["name"]: row["latest_version"] for row in library if row["id"] != published.skill.id}
    names = [_name("set-a"), _name("set-b")]

    plan = authoring.plan_create(
        client, names, description="SDK set validation", root="Use the linked skills for refunds.\n",
        label="sdk-set", pins={name: dict(others) for name in names},
    )
    assert [row["name"] for row in plan["contexts"]] == names
    for row in plan["contexts"]:
        assert not row["errors"], row
        followed = [item for item in row["resolved"] if (item["selector"] or {}).get("label") == "sdk-set"]
        assert [item["version"] for item in followed] == [published.version["number"]]

    applied = authoring.apply_create(client, plan, reviewed_plan=plan["plan_digest"], accept_resolved_versions=True)
    assert [row["digest"] for row in applied["applied"]] == [row["candidate_digest"] for row in plan["contexts"]]
    context_ids = [row["context_id"] for row in applied["applied"]]

    publish_plan = release.plan_publish(client, context_ids)
    for row, created in zip(publish_plan["contexts"], plan["contexts"]):
        assert row["candidate_digest"] == created["candidate_digest"]
        assert row["changed_from_origin"], "the comparison must list the new draft's files"
        assert {link["mount"] for link in row["accepted_lock"]} == {item["mount"] for item in created["resolved"]}
    done = release.publish_set(
        client, publish_plan, reviewed_plan=publish_plan["plan_digest"], reviewed_changes=True,
        acknowledge_warnings=True, note="SDK set validation",
    )
    assert [row["digest"] for row in done["published"]] == [row["candidate_digest"] for row in publish_plan["contexts"]]
    assert {row["version"] for row in done["published"]} == {1}

    release_plan = release.plan_release(client, context_ids, version=1, label="sdk-set")
    for row, sent in zip(release_plan["contexts"], done["published"]):
        assert row["candidate_digest"] == sent["digest"]
        assert row["to_version"] == 1 and row["fingerprint"]
