"""A withdrawn Console accounts for exact test modules, never silent deletion."""
from pathlib import Path
import runpy
import shutil

import pytest

GATE = runpy.run_path(str(Path(__file__).resolve().parents[3] / "scripts/packaging/console_composition.py"))


@pytest.fixture
def tree(tmp_path):
    for name, count, _ in GATE["CONSOLE_TESTS"]:
        p = tmp_path / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("".join(f"def test_case_{i}(): pass\n" for i in range(count)) if p.suffix == ".py"
                     else 'test("case", () => {});\n' * count)
    for name in GATE["DELETE_ROOTS"]:
        p = tmp_path / name
        if p.suffix != ".py":
            p.mkdir(parents=True, exist_ok=True)
            (p / "module.txt").write_text("module")
        elif not p.exists():
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text("# generator\n")
    (tmp_path / "test_retained.py").write_text("def test_retained(): pass\n")
    return tmp_path


def remove(tree):
    for name in GATE["DELETE_ROOTS"]:
        path = tree / name
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink()


def test_withdrawn_names_every_absent_module_and_both_counts(tree):
    before = GATE["begin"](tree, "WITHDRAWN")
    remove(tree)
    report = GATE["finish"](tree, before)
    assert [(r["module"], r["test_count"], r["collected_test_count"]) for r in report["identities"]] == list(GATE["CONSOLE_TESTS"])
    assert all(r["status"] == "ABSENT" for r in report["identities"])
    assert report["python_test_declarations"] == 50
    assert report["python_collected_tests"] == 627


def test_d2_keeps_all_seven_modules_unchanged(tree):
    before = GATE["begin"](tree, "D-2")
    report = GATE["finish"](tree, before)
    assert report["deleted_files"] == []
    assert len(report["identities"]) == 7
    assert all(r["status"] == "PRESENT" for r in report["identities"])


@pytest.mark.parametrize("name,_,__", GATE["CONSOLE_TESTS"])
def test_missing_console_module_cannot_be_counted_as_a_hide(tree, name, _, __):
    (tree / name).unlink()
    with pytest.raises(AssertionError, match="Missing Console module"):
        GATE["begin"](tree, "WITHDRAWN")


@pytest.mark.parametrize("mutation", ["missing-deletion", "extra-deletion", "retained-test-change"])
def test_exact_deletion_set_is_enforced(tree, mutation):
    before = GATE["begin"](tree, "WITHDRAWN")
    remove(tree)
    if mutation == "missing-deletion":
        (tree / "scripts/platform/generate-console.py").write_text("# retained\n")
    elif mutation == "extra-deletion":
        (tree / "test_retained.py").unlink()
    else:
        (tree / "test_retained.py").write_text("# deleted assertions\n")
    with pytest.raises(AssertionError):
        GATE["finish"](tree, before)


def test_extra_nested_test_requires_an_explicit_absence_identity(tree):
    (tree / "typescript/futureagi/src/agents/unlisted.test.ts").write_text('test("new", () => {});\n')
    with pytest.raises(AssertionError, match="Unregistered Console test deletion"):
        GATE["begin"](tree, "WITHDRAWN")


def test_changed_declaration_count_is_not_silently_accepted(tree):
    p = tree / GATE["CONSOLE_TESTS"][0][0]
    p.write_text(p.read_text() + "def test_new(): pass\n")
    with pytest.raises(AssertionError, match="Console test declaration count changed"):
        GATE["begin"](tree, "WITHDRAWN")


def test_d2_cannot_remove_a_console_module(tree):
    before = GATE["begin"](tree, "D-2")
    (tree / GATE["CONSOLE_TESTS"][0][0]).unlink()
    with pytest.raises(AssertionError):
        GATE["finish"](tree, before)
