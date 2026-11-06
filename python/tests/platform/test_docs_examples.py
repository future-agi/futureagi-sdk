"""The generated reference's Python examples bind to the real client (python/consumer/docs_examples.py)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "python" / "consumer"))

import docs_examples  # noqa: E402

REFERENCE = ROOT / "docs" / "sdk-reference"


def test_every_python_example_binds_to_the_real_method_signature() -> None:
    problems = docs_examples.check(REFERENCE)
    assert not problems, "\n".join(problems)


def test_the_checker_catches_a_wrong_keyword_and_a_missing_method(
    tmp_path: Path,
) -> None:
    (tmp_path / "bad.mdx").write_text(
        "<CodeGroup>\n```python Python\nresult = client.datasets.get(dataset_id=1, nope=2)\n```\n</CodeGroup>\n"
        "<CodeGroup>\n```python Python\nresult = client.datasets.frobnicate()\n```\n</CodeGroup>\n"
        "<CodeGroup>\n```python Python\nfrom fi.platform import NoSuchError\n```\n</CodeGroup>\n"
        '<Expandable title="Signature">\n```python Python\nclient.datasets.get(\n    dataset_id: str,\n    *,\n)\n```\n</Expandable>\n'
    )
    problems = docs_examples.check(tmp_path)
    assert any("nope" in p for p in problems)
    assert any("frobnicate" in p for p in problems)
    assert any("import example fails" in p for p in problems)
