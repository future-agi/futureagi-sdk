"""NOT-OFFERED must inspect real handles, not a missing test fixture."""
import asyncio
import copy
import json
import re
from types import SimpleNamespace

import pytest

from . import test_contract_offerings as offerings
from ._contract_public import unavailable_python_paths
from ._gates_support import REPO


INVENTORY = json.loads((REPO / "tests/fixtures/contracts/operations.json").read_text())
RUN_WRAPPERS = [
    (row, {**wrapper, "py": path})
    for row in INVENTORY["operations"] if row.get("wrappers")
    for wrapper, path in zip(row["wrappers"], unavailable_python_paths(row))
    if path.startswith("Run.")
]


@pytest.fixture
def declared_absent(monkeypatch):
    def declare(row, wrapper, mode, remove_spelling):
        row = copy.deepcopy(row)
        wrapper = copy.deepcopy(wrapper)
        if remove_spelling:
            wrapper.pop("py")
            wrapper["not_offered"] = {"py": {
                "status": "NOT-OFFERED", "reason": "Unavailable", "owner": "runs",
            }}
        row["wrappers"] = [wrapper]
        row.pop("public_wrappers", None)
        generated = {"operations": [row], "not_offered": {"py_sync": [], "py_async": []}}
        generated["not_offered"]["py_" + mode] = [{"id": row["id"]}]
        monkeypatch.setattr(offerings, "module", lambda _: SimpleNamespace(generate=lambda: generated))
        return row
    return declare


@pytest.mark.parametrize("mode", ["sync", "async"])
@pytest.mark.parametrize("remove_spelling", [False, True], ids=["namespace", "language"])
@pytest.mark.parametrize("row,wrapper", RUN_WRAPPERS, ids=[w["py"] for _, w in RUN_WRAPPERS])
def test_not_offered_rejects_every_live_run_method(monkeypatch, declared_absent, row, wrapper, mode, remove_spelling):
    row = declared_absent(row, wrapper, mode, remove_spelling)
    if hidden_console(row, mode):
        offerings.test_unavailable_declarations_do_not_hide_registered_python_methods(monkeypatch)
        return
    # Run.identity is a public property, not a method. A registered non-callable
    # value must reject the absence declaration too, with the exact path named.
    rejection = "DID NOT RAISE|public method is not callable: " + re.escape(wrapper["py"])
    with pytest.raises((pytest.fail.Exception, TypeError), match=rejection):
        offerings.test_unavailable_declarations_do_not_hide_registered_python_methods(monkeypatch)


@pytest.fixture
def tree_absence(declared_absent):
    row, wrapper = next((r, w) for r, w in RUN_WRAPPERS if w["py"] == "Run.tree")
    return lambda mode: declared_absent(row, wrapper, mode, True)


def hidden_console(row, mode):
    if not row.get("public_absence"):
        return False
    from ._contract_runtime import Runtime
    from ._console_absence import assert_console_absent
    async def run():
        subject = Runtime(row, mode, lambda _: pytest.fail("absence must not request"))
        try:
            assert_console_absent(subject)
        finally:
            await subject.close()
    asyncio.run(run())
    return True


def run_types(mode):
    if mode == "async":
        from fi.agents.runs._async_client import AsyncRuns
        from fi.agents.runs._handles._async_client import AsyncRun
        return AsyncRuns, AsyncRun
    from fi.agents.runs._client import Runs
    from fi.agents.runs._handles._client import Run
    return Runs, Run


@pytest.mark.parametrize("mode", ["sync", "async"])
def test_not_offered_accepts_absent_method_on_real_handle(monkeypatch, tree_absence, mode):
    row = tree_absence(mode)
    if hidden_console(row, mode):
        offerings.test_unavailable_declarations_do_not_hide_registered_python_methods(monkeypatch)
        return
    _, run = run_types(mode)
    monkeypatch.delattr(run, "tree")
    offerings.test_unavailable_declarations_do_not_hide_registered_python_methods(monkeypatch)


@pytest.mark.parametrize("mode", ["sync", "async"])
def test_missing_fixture_factory_does_not_prove_handle_absence(monkeypatch, tree_absence, mode):
    row = tree_absence(mode)
    if hidden_console(row, mode):
        offerings.test_unavailable_declarations_do_not_hide_registered_python_methods(monkeypatch)
        return
    runs, _ = run_types(mode)
    # Other public factories can still return Run handles. Losing the fixture's
    # factory is a setup failure, not proof that every handle factory is absent.
    monkeypatch.delattr(runs, "get")
    with pytest.raises(AttributeError, match="get"):
        offerings.test_unavailable_declarations_do_not_hide_registered_python_methods(monkeypatch)


@pytest.mark.parametrize("mode", ["sync", "async"])
@pytest.mark.parametrize("missing", ["fixture", "python_fixture"])
def test_missing_handle_fixture_is_not_public_absence(monkeypatch, tree_absence, mode, missing):
    row = tree_absence(mode)
    if hidden_console(row, mode):
        offerings.test_unavailable_declarations_do_not_hide_registered_python_methods(monkeypatch)
        return
    if missing == "fixture":
        row["handle_fixtures"].pop("Run")
    else:
        row["handle_fixtures"]["Run"].pop("py")
    with pytest.raises(ValueError, match="public handle fixture required"):
        offerings.test_unavailable_declarations_do_not_hide_registered_python_methods(monkeypatch)


@pytest.mark.parametrize("mode", ["sync", "async"])
def test_factory_implementation_errors_are_not_public_absence(monkeypatch, tree_absence, mode):
    row = tree_absence(mode)
    if hidden_console(row, mode):
        offerings.test_unavailable_declarations_do_not_hide_registered_python_methods(monkeypatch)
        return
    runs, _ = run_types(mode)
    calls = []
    def broken_factory(self, *args, **kwargs):
        calls.append(self)
        raise AttributeError("factory implementation failed")
    monkeypatch.setattr(runs, "get", broken_factory)
    with pytest.raises(AttributeError, match="factory implementation failed"):
        offerings.test_unavailable_declarations_do_not_hide_registered_python_methods(monkeypatch)
    assert len(calls) == 1
