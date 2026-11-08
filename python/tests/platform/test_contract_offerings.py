"""Every public case has an explicit language schedule, including unavailable APIs."""
import copy
import json

import pytest

from ._gates_support import REPO, load


def module(monkeypatch):
    monkeypatch.syspath_prepend(str(REPO / "scripts/platform"))
    return load("offering_cases", "scripts/platform/contract_cases.py")


def test_committed_inputs_and_language_inventories(monkeypatch):
    generated = module(monkeypatch).generate()
    assert generated == json.loads((REPO / "tests/fixtures/contracts/operations.json").read_text())
    assert set(generated["public_cases"]) == {"py_sync", "py_async", "ts"}
    assert generated["public_cases"]["py_sync"] != generated["public_cases"]["py_async"]
    for mode, ids in generated["public_cases"].items():
        excluded = {r["id"] for r in generated["not_offered"][mode]}
        assert set(ids).isdisjoint(excluded)
        assert set(ids) | excluded == {r["id"] for r in generated["operations"]}
        assert all(r["status"] == "NOT-OFFERED" and r["reason"] and r["owner"]
                   for r in generated["not_offered"][mode])


@pytest.mark.parametrize("absent", ["py", "ts"])
def test_missing_language_is_never_scheduled(monkeypatch, absent):
    generator = module(monkeypatch)
    wrapper = {"py": "client.things.list", "ts": "client.things.list"}
    wrapper.pop(absent)
    wrapper["not_offered"] = {absent: {"status": "NOT-OFFERED", "reason": "Not implemented", "owner": "namespace"}}
    row = {"id": "platform:things.list", "adapter": "platform", "name": "things.list", "wrappers": [wrapper]}
    schedules, excluded = generator.public_inventory([row], {}, {})
    for mode in ("py_sync", "py_async", "ts"):
        unavailable = mode.startswith(absent)
        assert schedules[mode] == ([] if unavailable else [row["id"]])
        assert bool(excluded[mode]) is unavailable


def test_absent_namespace_requires_named_owner(monkeypatch):
    generator = module(monkeypatch)
    row = {"id": "platform:things.list", "adapter": "platform", "name": "things.list",
           "wrappers": [{"py": "client.things.list", "ts": "client.things.list"}]}
    pending = {"things": {"status": "NOT-OFFERED", "reason": "Facade not integrated", "owner": "namespace"}}
    schedules, excluded = generator.public_inventory([row], pending, {})
    assert all(not ids for ids in schedules.values())
    assert all(rows[0]["owner"] == "namespace" for rows in excluded.values())
    pending["things"].pop("owner")
    with pytest.raises(ValueError, match="owner"):
        generator.public_inventory([row], pending, {})


@pytest.mark.parametrize("metadata", ["basePath", "servers"])
def test_effective_url_prefix_is_namespace_drift(monkeypatch, metadata):
    module(monkeypatch)
    drift = load("prefix_drift", "scripts/platform/catalog_contracts.py")
    catalog = {"operations": [{"operation_id": "things", "public": "things.list"}]}
    old = {"swagger": "2.0", "paths": {"/things": {"get": {"operationId": "things"}}}}
    old[metadata] = "/v1" if metadata == "basePath" else [{"url": "https://example.test/v1"}]
    new = copy.deepcopy(old)
    new[metadata] = "/v2" if metadata == "basePath" else [{"url": "https://example.test/v2"}]
    projected = drift.project(new, catalog)
    assert projected[metadata] == new[metadata]
    assert drift.drift(old, projected, catalog)["things"]["changed"] == ["things.list"]


def test_every_scheduled_method_resolves_on_real_root_clients(monkeypatch):
    import asyncio
    from ._contract_public import method_at, public_path
    from ._contract_runtime import Runtime
    generated = module(monkeypatch).generate()
    async def run():
        for mode in ("sync", "async"):
            ids = generated["public_cases"]["py_" + mode]
            for row in generated["operations"]:
                if row["id"] not in ids and not row.get("public_absence"):
                    continue
                subject = Runtime(row, mode, lambda _: pytest.fail("resolution must not request"))
                try:
                    if row.get("public_absence"):
                        from ._console_absence import assert_console_absent
                        assert_console_absent(subject)
                        continue
                    await subject.prepare()
                    assert callable(method_at(subject.client, public_path(subject.row), subject.handles))
                finally:
                    await subject.close()
    asyncio.run(run())


def test_unavailable_declarations_do_not_hide_registered_python_methods(monkeypatch):
    import asyncio
    from ._contract_public import absence_candidates, method_at
    from ._contract_runtime import Runtime
    generated = module(monkeypatch).generate()
    async def run():
        for mode in ("sync", "async"):
            ids = {row["id"] for row in generated["not_offered"]["py_" + mode]}
            for row in generated["operations"]:
                if row["id"] not in ids:
                    continue
                subject = Runtime(row, mode, lambda _: pytest.fail("resolution must not request"))
                try:
                    for path in absence_candidates(subject.row, generated["operations"]):
                        # Setup failures are not evidence of public absence.
                        # Resolve each candidate, including non-primary wrappers,
                        # through the same real public handle as offered cases.
                        await subject.prepare(path)
                        with pytest.raises(AttributeError):
                            method_at(subject.client, path, subject.handles)
                finally:
                    await subject.close()
    asyncio.run(run())


def test_management_availability_is_explicit_and_public(monkeypatch):
    generated = module(monkeypatch).generate()
    assert "management" not in generated["modules"]
    rows = [row for row in generated["operations"] if row["adapter"] == "management"]
    assert len(rows) == 19
    for ids in generated["public_cases"].values():
        assert {row["id"] for row in rows} <= set(ids)
