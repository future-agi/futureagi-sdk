"""A run file's experiments.run(...) calls register in CLI context and run once each."""

import json

from tests.experiments.unit.cli_helpers import cli


RUN_FILE = """
from fi import experiments
CALLS = __import__("pathlib").Path("calls.txt")

def task(row):
    with CALLS.open("a") as fh:
        fh.write(str(row["q"]) + "\\n")
    return row["q"]

experiments.run([{"q": 1}, {"q": 2}], task, upload=False, name="first")
experiments.run([{"q": 3}], task, upload=False, name="second")

if __name__ == "__main__":
    experiments.run([{"q": 4}], task, upload=False, name="main-block")
"""


def test_each_declared_run_runs_once(tmp_path):
    (tmp_path / "run.py").write_text(RUN_FILE)
    code, out, err = cli("run", "run.py", "--json")
    assert code == 0, err
    doc = json.loads(out)
    assert [r["label"] for r in doc["runs"]] == ["first", "second", "main-block"]
    assert sorted((tmp_path / "calls.txt").read_text().split()) == ["1", "2", "3", "4"]


def test_list_filter_and_overlays(tmp_path):
    (tmp_path / "run.py").write_text(RUN_FILE)
    code, out, _ = cli("run", "run.py", "--list")
    assert code == 0 and out.split() == ["first", "second", "main-block"]
    assert not (tmp_path / "calls.txt").exists()
    code, out, err = cli("run", "run.py", "--filter", "sec*", "--trials", "2", "--json")
    assert code == 0, err
    runs = json.loads(out)["runs"]
    assert [r["label"] for r in runs] == ["second"] and runs[0]["summary"]["trials"] == 2


def test_directory_runs_eval_files(tmp_path):
    d = tmp_path / "evals"
    d.mkdir()
    (d / "a_eval.py").write_text("from fi import experiments\nexperiments.run([{'q': 1}], lambda r: 1, upload=False, name='a')\n")
    (d / "eval_b.py").write_text("from fi import experiments\nexperiments.run([{'q': 1}], lambda r: 1, upload=False, name='b')\n")
    (d / "helper.py").write_text("raise SystemExit('must not be imported')\n")
    code, out, err = cli("run", "evals", "--json")
    assert code == 0, err
    assert [r["label"] for r in json.loads(out)["runs"]] == ["a", "b"]


def test_declared_run_result_not_available_at_import(tmp_path):
    (tmp_path / "run.py").write_text(
        "from fi import experiments\nr = experiments.run([{'q': 1}], lambda r: 1, upload=False)\nr.summary()\n")
    code, out, err = cli("run", "run.py")
    assert code != 0 and "declared in a run file" in (err + out)
