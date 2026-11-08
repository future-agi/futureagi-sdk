"""intended-differences.json: its schema, the reviewer record, the baselines, and
how narrow a proven entry must be.

API design 5.3: a difference passes only if an entry with evidence, a test id and a
reviewer signature covers it. The comparators let only ``proven`` entries
cover; these tests hold the file to the rest.
"""

from __future__ import annotations

import collections
import re

from ._fixtures import GOLDEN, load
from ._review import assert_review_record
from .compare import covers, diff, load_recording, matches, view

INTENDED = load("intended-differences.json")["differences"]
GOLDENS = sorted(load("catalog.json")["goldens"])
# The new recordings a label may name (labels.py reads the same table).
NEW = tuple(sorted(load("catalog.json")["comparisons"]["new_recordings"]))
NEW_LABELS = [f"{g}->{n}" for g in GOLDENS for n in NEW]
FIXED_LABELS = [f"{a}->{b}" for a in GOLDENS for b in GOLDENS if a != b]
WILDCARD = re.compile(r"[*?]")
# Text no recorded value contains. The comparators apply a rule's old / new
# regex with re.search, so a regex that finds a match here (".*", "", "x?", "."
# or a whitespace class) finds one in every value: it pins nothing.
PROBES = ("<<parity probe: no recorded value is this text>>", "\x00\n")


def _applies(entry: dict, labels: list[str]) -> list[str]:
    return [x for x in labels if any(matches(p, x) for p in entry["applies_to"])]


def test_intended_differences_are_well_formed() -> None:
    ids = [d["id"] for d in INTENDED]
    assert len(ids) == len(set(ids))
    for d in INTENDED:
        assert d["status"] in {"planned", "proven"}, d["id"]
        assert (
            d["summary"]
            and isinstance(d["applies_to"], list)
            and isinstance(d["match"], list)
        ), d["id"]
        for rule in d["match"]:
            assert set(rule) <= {"path", "kind", "old", "new", "top_level"}, d["id"]
            assert rule.get("kind", "any") in {"any", "changed", "added", "removed"}, d[
                "id"
            ]
            for side in ("old", "new"):
                if side in rule:
                    re.compile(rule[side])
    plan_ids = {f"D-{n:02d}" for n in range(2, 22)}
    assert plan_ids <= set(
        ids
    ), f"fold-plan deltas missing: {sorted(plan_ids - set(ids))}"


def test_a_proven_entry_carries_evidence_a_test_id_and_a_reviewer_record() -> None:
    for d in INTENDED:
        if d["status"] != "proven":
            continue
        assert d["evidence"] and d["test_id"], f"{d['id']}: evidence and test_id"
        assert_review_record(d)


def test_a_planned_entry_claims_no_proof() -> None:
    """A planned entry covers nothing, so it must not look signed either."""
    for d in INTENDED:
        if d["status"] == "planned":
            assert not d["test_id"] and d["reviewer"] is None, d["id"]


def _judges_against_1_0_0(entries: list[dict]) -> list[tuple[str, str]]:
    return [
        (d["id"], label)
        for d in entries
        for label in _applies(d, NEW_LABELS)
        if label.startswith("ts-client-1.0.0-") or d["id"].startswith("D-01")
    ]


def _pins(regex: str) -> bool:
    return not any(re.search(regex, probe) for probe in PROBES)


def _loose(rule: dict) -> bool:
    """A rule is pinned by an exact path or by an old / new regex that pins."""
    exact = not WILDCARD.search(rule.get("path", "*"))
    return not exact and not any(
        _pins(rule[side]) for side in ("old", "new") if side in rule
    )


def _loose_rules(entries: list[dict]) -> list[tuple[str, dict]]:
    return [
        (d["id"], rule)
        for d in entries
        if d["status"] == "proven" and _applies(d, NEW_LABELS)
        for rule in d["match"]
        if _loose(rule)
    ]


def test_new_typescript_client_recordings_are_judged_against_1_0_1_only() -> None:
    """The 1.0.0 -> 1.0.1 step (D-01) is proven between the two fixed goldens and
    applies to nothing else, so it can never hide a difference in a port."""
    assert _judges_against_1_0_0(INTENDED) == []


def test_a_proven_rule_that_can_judge_a_new_recording_is_pinned() -> None:
    """Every rule of a proven entry that applies to a new recording names an
    exact path or constrains the old or new value with a regex that pins (one
    that matches arbitrary text, such as ".*", does not), so it cannot cover a
    whole case or a whole subtree (the D-02 / D-07 / D-16 globs must be
    narrowed first)."""
    loose = _loose_rules(INTENDED)
    assert not loose, f"proven rules too broad for a new recording: {loose[:5]}"


def test_negative_controls_for_the_baseline_and_pinning_guards() -> None:
    """No proven entry judges a new recording yet, so the two guards above are
    shown to bite on synthetic entries."""
    bare = {"path": "stream.*"}
    # regression check (verify3 info): a regex that pins nothing is no pin
    unpinned = [
        {"path": "*", "new": ".*"},
        {"path": "stream.*", "old": "", "new": "x?"},
        {"path": "env.*", "kind": "changed", "new": "."},
        {"path": "*/headers/*", "new": "\\s*"},
    ]
    entry = {
        "id": "D-x",
        "status": "proven",
        "applies_to": ["py-agentcc-1.0.0->e-new-py", "ts-client-1.0.*->e-new-ts-esm"],
        "match": [
            bare,
            {"path": "env.base_url.localhost[async]/requests/0/host"},
            {"path": "stream.*/message", "new": "^x$"},
            {"path": "*/headers/user-agent", "new": "^futureagi-python/"},
            {"path": "*/requests/*/url", "old": "/v1/v1/", "new": ".*"},
            {"path": "env.*/stdout", "new": "^$"},
            *unpinned,
        ],
    }
    assert _loose_rules([entry]) == [("D-x", r) for r in [bare, *unpinned]]
    assert _loose_rules([{**entry, "status": "planned"}]) == []
    assert _judges_against_1_0_0([entry]) == [
        ("D-x", "ts-client-1.0.0-cjs->e-new-ts-esm"),
        ("D-x", "ts-client-1.0.0-esm->e-new-ts-esm"),
    ]


def test_every_rule_of_a_proven_golden_to_golden_entry_is_used() -> None:
    """A rule that covers nothing in the fixed comparisons is breadth nothing
    needed, so it is refused."""
    used: dict[str, set[int]] = collections.defaultdict(set)
    fixed = [d for d in INTENDED if d["status"] == "proven"]
    for label in FIXED_LABELS:
        entries = [d for d in fixed if _applies(d, [label])]
        if not entries:
            continue
        old, new = label.split("->")
        a = load_recording(GOLDEN / old)["cases"]
        b = load_recording(GOLDEN / new)["cases"]
        for change in diff(view(a), view(b)):
            for d in entries:
                for i, rule in enumerate(d["match"]):
                    if covers(rule, change):
                        used[d["id"]].add(i)
    for d in fixed:
        if _applies(d, FIXED_LABELS):
            unused = [
                r["path"] for i, r in enumerate(d["match"]) if i not in used[d["id"]]
            ]
            assert not unused, f"{d['id']}: rules that cover nothing: {unused}"


# The agentcc 2.0.0 shim entries (ids starting SHIM-) are judged by the shim's own
# golden comparison. Each of their rules pins one difference completely: one exact path,
# an explicit kind, and the whole of every side the difference has, as an escaped
# literal between "^" and "(?![\s\S])" (Python's "$" also matches before a final
# newline). The only text that may vary is Node's process id in a warning line.
SHIM_END = r"(?![\s\S])"
SHIM_TOKENS = (r"\(node:\d+\)",)
# re.escape escapes exactly these; anything else after a backslash is a class or escape.
_ESCAPED = frozenset("()[]{}?*+-|^$\\.&~# \t\n\r\v\f")
_META = frozenset("()[]{}?*+|^$.\\")
_SIDES = {"added": ("new",), "removed": ("old",), "changed": ("old", "new")}


def _literal(regex: str) -> bool:
    """True for "^" + an escaped literal (plus allowed tokens) + SHIM_END."""
    if not (regex.startswith("^") and regex.endswith(SHIM_END)):
        return False
    body = regex[1 : -len(SHIM_END)]
    for token in SHIM_TOKENS:
        body = body.replace(token, "")
    i = 0
    while i < len(body):
        if body[i] == "\\":
            if i + 1 == len(body) or body[i + 1] not in _ESCAPED:
                return False
            i += 2
        elif body[i] in _META:
            return False
        else:
            i += 1
    return True


# The declaration recorder writes `export * from "x"` as the record "star * <- x", so that
# record's path holds a "*" the comparator's glob cannot escape. Such a path is exact
# but for that one character, and only when the same entry pins the file's sha256: any
# other text in the file (an `export * as ns` included) changes the pinned hash.
_STAR_RECORD = re.compile(r"\A(<index>/dts/[^*?]+\.d\.[cm]?ts)/exports/star \* <- [^*?]+\Z")


def _exact_path(path: str, pinned_files: set[str]) -> bool:
    if not WILDCARD.search(path):
        return True
    star = _STAR_RECORD.match(path)
    return bool(star) and star.group(1) in pinned_files


def _imprecise_shim_rules(entries: list[dict]) -> list[tuple[str, dict]]:
    out = []
    for d in entries:
        if not d["id"].startswith("SHIM-"):
            continue
        pinned_files = {
            r["path"].removesuffix("/sha256")
            for r in d["match"]
            if r.get("path", "").endswith("/sha256")
            and not WILDCARD.search(r["path"])
            and r.get("kind") in ("added", "changed")
            and _literal(r.get("new", ""))
        }
        for rule in d["match"]:
            sides = _SIDES.get(rule.get("kind", "any"))
            if (
                sides is None
                or not _exact_path(rule.get("path", "*"), pinned_files)
                or set(rule) != {"path", "kind", *sides}
                or not all(_literal(rule[side]) for side in sides)
            ):
                out.append((d["id"], rule))
    return out


def test_a_shim_rule_pins_one_exact_path_and_its_complete_values() -> None:
    """A cluster rule is never broader than its cause, so a shim
    rule cannot accept an unrelated change after a matching prefix, an arbitrary
    added value, or the same change at another path."""
    shim = [d for d in INTENDED if d["id"].startswith("SHIM-")]
    assert shim and all(d["status"] == "proven" for d in shim)
    loose = _imprecise_shim_rules(INTENDED)
    assert not loose, f"{len(loose)} shim rules are broader than one difference: {loose[:3]}"


def test_negative_controls_for_the_shim_precision_guard() -> None:
    """The shapes the shim review found must fail the guard; exact rules pass."""
    sse = re.escape('data: {"id":"c","choices":[{"delta":{"content":"Hi"}}]}\n\n')
    loose = [
        # a prefix followed by anything (the streamed text and the error frame)
        {"path": "integration.nextjs.stream/result/text", "kind": "changed",
         "old": "^data:\\ \\{\"id\":\"c\"[\\s\\S]*", "new": "^data:\\ \\{\"id\":\"c\"[\\s\\S]*"},
        # a pinned head and tail around an arbitrary middle
        {"path": "a[sync]/raised", "kind": "added", "new": "^\\{\"args\":\\[\"The[\\s\\S]*key\\.\"\\]\\}" + SHIM_END},
        # an added value with no new side, and a removal with no old side
        {"path": "response_header.all/result/configIgnored", "kind": "added"},
        {"path": "config.section.cache/result", "kind": "removed"},
        # the same change at any path
        {"path": "*/result/agentcc/clientRequestId", "kind": "added", "new": "^null" + SHIM_END},
        # "$" instead of the end of the text, an unanchored or class-bearing value, kind any
        {"path": "a/b", "kind": "changed", "old": "^x$", "new": "^y" + SHIM_END},
        {"path": "a/b", "kind": "changed", "old": "x", "new": "^y" + SHIM_END},
        {"path": "a/b", "kind": "added", "new": "^\\d+" + SHIM_END},
        {"path": "a/b", "new": "^y" + SHIM_END},
        # a side the difference does not have
        {"path": "a/b", "kind": "added", "old": "^x" + SHIM_END, "new": "^y" + SHIM_END},
        # an export-star record of a file whose sha256 the entry does not pin, and a "*"
        # anywhere else in a declaration path
        {"path": "<index>/dts/p/dist/esm/other.d.ts/exports/star * <- x", "kind": "added", "new": "^true" + SHIM_END},
        {"path": "<index>/dts/p/dist/esm/index.d.ts/exports/star * <- *", "kind": "added", "new": "^true" + SHIM_END},
        {"path": "<index>/dts/p/dist/*/index.d.ts/exports/star * <- x", "kind": "added", "new": "^true" + SHIM_END},
    ]
    exact = [
        {"path": "integration.nextjs.stream_error/result", "kind": "changed",
         "old": "^" + sse + SHIM_END, "new": "^" + sse + SHIM_END},
        {"path": "response_header.all/result/configIgnored", "kind": "added",
         "new": "^" + re.escape('["fallback","loadbalance"]') + SHIM_END},
        {"path": "resource.chat.create/console/0/1", "kind": "added",
         "new": "^" + re.escape("(node:1) [AGENTCC_DEPRECATED] x").replace(r"\(node:1\)", r"\(node:\d+\)") + SHIM_END},
        {"path": "a/b", "kind": "removed", "old": "^true" + SHIM_END},
        {"path": "<index>/dts/p/dist/esm/index.d.ts/sha256", "kind": "changed", "old": "^a" + SHIM_END, "new": "^b" + SHIM_END},
        {"path": "<index>/dts/p/dist/esm/index.d.ts/exports/star * <- x", "kind": "added", "new": "^true" + SHIM_END},
    ]
    entry = {"id": "SHIM-x", "status": "proven", "applies_to": ["py-agentcc-1.0.0->e-shim-py"], "match": loose + exact}
    assert _imprecise_shim_rules([entry]) == [("SHIM-x", r) for r in loose]
    assert _imprecise_shim_rules([{**entry, "id": "D-x"}]) == []
    # The end marker refuses the extra final newline Python's "$" would accept.
    assert re.search("^a$", "a\n") and not re.search("^a" + SHIM_END, "a\n")
