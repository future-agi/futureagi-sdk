"""``Dataset.add_evaluation`` uses this package's own ``fi.evals``: no second package, and no message
that names one."""

from __future__ import annotations

import subprocess
import sys
import uuid
from pathlib import Path

import pytest

from tests.evals import _mock_http

PYTHON = Path(__file__).resolve().parents[2]


def test_the_dataset_module_names_no_other_package() -> None:
    text = (PYTHON / "fi" / "datasets" / "dataset.py").read_text(encoding="utf-8")
    assert "ai-evaluation" not in text and "ai_evaluation" not in text


def test_importing_datasets_warns_about_nothing_and_loads_no_evals_module() -> None:
    code = "import sys, fi.datasets.dataset; print(sorted(m for m in sys.modules if m.startswith('fi.evals')))"
    out = subprocess.run([sys.executable, "-c", code], cwd=PYTHON, capture_output=True, text=True, timeout=120)
    assert out.returncode == 0, out.stderr
    assert out.stdout.strip() == "[]"
    assert "install" not in out.stderr.lower()


def test_add_evaluation_runs_on_this_package(monkeypatch: pytest.MonkeyPatch) -> None:
    from fi.datasets.dataset import Dataset
    from fi.datasets.types import DatasetConfig

    dataset_id = uuid.UUID(int=7)
    routes = {
        ("GET", "/sdk/api/v1/eval/15/"): lambda call: (200, {"status": True, "result": {
            "id": "tmpl-toxicity", "config": {"required_keys": ["output"]}}}),
        ("POST", f"/model-hub/develops/{dataset_id}/add_user_eval/"): lambda call: (200, {"status": True, "result": "ok"}),
    }
    backend = _mock_http.FakeBackend(routes)
    with _mock_http.serve(backend):
        dataset = Dataset(dataset_config=DatasetConfig(id=dataset_id, name="d", model_type="GenerativeLLM"))
        monkeypatch.setattr(dataset, "get_column_id", lambda name: "col-" + name)
        assert dataset.add_evaluation(
            name="tox", eval_template="toxicity", required_keys_to_column_names={"output": "answer"}, model="turing_flash"
        ) is dataset
    posted = [c for c in backend.calls if c["method"] == "POST"]
    assert [c["path"] for c in backend.calls if c["method"] == "GET"] == ["/sdk/api/v1/get-evals/", "/sdk/api/v1/eval/15/"]
    assert posted[0]["json"]["template_id"] == "tmpl-toxicity"
    assert posted[0]["json"]["config"]["mapping"] == {"output": "col-answer"}


def test_add_evaluation_without_an_id_fails_on_the_id_not_on_an_import() -> None:
    from fi.datasets.dataset import Dataset
    from fi.utils.errors import DatasetError

    with pytest.raises(DatasetError, match="configured with an ID"):
        Dataset().add_evaluation(name="x", eval_template="toxicity", required_keys_to_column_names={"output": "a"}, model="m")
