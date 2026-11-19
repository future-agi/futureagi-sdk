"""The ``futureagi-webhooks`` receiver distribution: the same verify code as
``fi.webhooks.verify``, importable with only the standard library and without the SDK.

The end-to-end run builds its wheel and installs it into a fresh virtualenv that has no ``futureagi``; these unit tests
check the source tree: the byte-identical copy, the metadata, and the vectors in an interpreter that cannot see ``fi``.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

from ._stdlib import IS_STDLIB

PY = Path(__file__).resolve().parents[2]
DIST = PY / "futureagi-webhooks"
CONF = Path(__file__).resolve().parent / "conformance"


def test_the_receiver_module_is_a_byte_identical_copy_of_fi_webhooks_verify():
    src = (PY / "fi" / "webhooks" / "verify.py").read_bytes()
    copy = (DIST / "futureagi_webhooks" / "_verify.py").read_bytes()
    assert hashlib.sha256(copy).hexdigest() == hashlib.sha256(src).hexdigest(), (
        "copy python/fi/webhooks/verify.py to python/futureagi-webhooks/futureagi_webhooks/_verify.py"
    )


def test_the_distribution_declares_no_dependency_and_one_package():
    text = (DIST / "pyproject.toml").read_text()
    deps = text.split("[tool.poetry.dependencies]")[1].split("[")[0].strip().splitlines()
    assert deps == ['python = ">=3.9"']
    assert 'name = "futureagi-webhooks"' in text and '{ include = "futureagi_webhooks" }' in text
    assert (DIST / "futureagi_webhooks" / "py.typed").exists()


def test_the_vectors_pass_without_the_sdk_on_the_path():
    """A fresh ``-I`` interpreter with only the standard library and the distribution's folder on sys.path (no
    site-packages, no editable installs): ``fi`` is not importable."""
    code = IS_STDLIB + f"""
import base64, json, sys, importlib.util
before = set(sys.modules)
sys.path[:] = [p for p in sys.path if p.startswith(sys.base_prefix) and 'site-packages' not in p]
sys.path.insert(0, {str(DIST)!r})
assert importlib.util.find_spec('fi') is None, 'fi is importable'
import futureagi_webhooks as w
cases = json.load(open({str(CONF / 'signing.json')!r}))['verify']
bad = [c['id'] for c in cases
       if w.verify_result(c['secret'], c['headers'], base64.b64decode(c['body_bytes_b64']), now=c['now']) != c['expected']]
mods = sorted(m.split('.')[0] for m in set(sys.modules) - before)
third = sorted({{m for m in mods if not is_stdlib(m) and m != 'futureagi_webhooks'}})
print(json.dumps({{'cases': len(cases), 'bad': bad, 'third_party': third}}))
"""
    out = subprocess.run([sys.executable, "-I", "-c", code], capture_output=True, text=True, check=True)
    result = json.loads(out.stdout)
    assert result == {"cases": 20, "bad": [], "third_party": []}
