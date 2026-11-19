"""Hidden handle absence requires proof for every mapped public factory."""
import copy
import json
from types import SimpleNamespace

import pytest

from . import test_contract_offerings as offerings
from ._gates_support import REPO


@pytest.fixture
def hidden_handle(monkeypatch):
    inventory = json.loads((REPO / "tests/fixtures/contracts/operations.json").read_text())
    original = next(r for r in inventory["operations"] if r["id"] == "platform:deployments.get")

    def declare(mode, root="Deployment", factories=("create", "get", "list")):
        row = copy.deepcopy(original)
        row["wrappers"] = [{"py": root + ".refresh", "ts": root + ".refresh"}]
        row.pop("public_wrappers", None)
        row["handle_fixtures"] = {}
        generated = {"operations": [row], "not_offered": {"py_sync": [], "py_async": []}}
        generated["not_offered"]["py_" + mode] = [{"id": row["id"]}]
        for name in factories:
            generated["operations"].append({"id": "factory:" + name, "wrappers": [{
                "ts": "client.deployments." + name,
                "not_offered": {"py": {"status": "NOT-OFFERED", "reason": "Unavailable", "owner": "deployments"}},
                "returns": "Page[Deployment]" if name == "list" else "Deployment",
            }]})
        monkeypatch.setattr(offerings, "module", lambda _: SimpleNamespace(generate=lambda: generated))
    return declare


@pytest.mark.parametrize("mode", ["sync", "async"])
def test_hidden_handle_requires_all_mapped_factories_absent(monkeypatch, hidden_handle, mode):
    hidden_handle(mode)
    offerings.test_unavailable_declarations_do_not_hide_registered_python_methods(monkeypatch)


@pytest.mark.parametrize("mode", ["sync", "async"])
@pytest.mark.parametrize("factory", ["create", "get", "list"])
def test_any_registered_handle_factory_rejects_false_absence(monkeypatch, hidden_handle, mode, factory):
    from fi import AsyncFutureAGIClient, FutureAGIClient
    hidden_handle(mode)
    cls = AsyncFutureAGIClient if mode == "async" else FutureAGIClient
    monkeypatch.setattr(cls, "deployments", property(lambda _: SimpleNamespace(**{factory: lambda: None})), raising=False)
    with pytest.raises(pytest.fail.Exception, match="DID NOT RAISE"):
        offerings.test_unavailable_declarations_do_not_hide_registered_python_methods(monkeypatch)


@pytest.mark.parametrize("mode", ["sync", "async"])
@pytest.mark.parametrize("root,factories", [("Unknown", ("get",)), ("Deployment", ())])
def test_unknown_handle_or_missing_factory_inventory_fails_closed(monkeypatch, hidden_handle, mode, root, factories):
    hidden_handle(mode, root, factories)
    with pytest.raises(ValueError, match="public handle fixture required"):
        offerings.test_unavailable_declarations_do_not_hide_registered_python_methods(monkeypatch)
