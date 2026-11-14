"""The namespace startup guard has exact, exclusive wheel ownership."""
from __future__ import annotations

import csv
import io
import re
import zipfile

import pytest

from test_namespace_ownership import gate, ownership, wheel


GUARD_PATHS = (
    "_futureagi_namespace_guard.py",
    "futureagi_namespace_guard.pth",
)
UNOWNED_PATHS = (
    "root.py",
    "arbitrary.pth",
    "_futureagi_namespace_guard.py.bak",
    "_futureagi_namespace_guard.pyi",
    "_futureagi_namespace_guard_extra.py",
    "_futureagi_namespace_guard.py/child.py",
    "futureagi_namespace_guard.pth.bak",
    "futureagi_namespace_guard_extra.pth",
    "futureagi_namespace_guard.pth/child.py",
    "unrelated/_futureagi_namespace_guard.py",
    "unrelated/futureagi_namespace_guard.pth",
)
EXCLUDED_PATHS = ("fi/alk/__init__.py", "fi/cli/main.py", "fi/agentcc.py")
COMPANIONS = (
    ("agent-learning-kit", "0.4.0", "fi/alk/__init__.py"),
    ("agentcc", "2.0.0", "agentcc/__init__.py"),
    ("fi-instrumentation-otel", "1.1.0", "fi_instrumentation/__init__.py"),
    ("traceai-openai", "0.1.10", "traceai_openai/__init__.py"),
)


@pytest.fixture
def guard_payload():
    # These bytes are archived and hashed only, never imported or executed.
    return {
        "fi/__init__.py": b"# sdk fixture\n",
        GUARD_PATHS[0]: b"def install():\n    pass\n",
        GUARD_PATHS[1]: b"import _futureagi_namespace_guard; _futureagi_namespace_guard.install()\n",
    }


def test_manifest_assigns_exact_guard_paths_to_futureagi():
    rules = ownership.manifest()
    assert rules["distributions"]["futureagi"]["paths"] == ["fi/", *GUARD_PATHS]
    assert rules["distributions"]["futureagi"]["excludes"] == ["fi/alk/"]
    assert rules["forbidden_paths"] == ["fi/cli/", "fi/agentcc.py"]
    assert rules["forbidden_console_scripts"] == ["fi"]


@pytest.mark.parametrize("path", GUARD_PATHS)
def test_futureagi_owns_each_exact_guard_path(path):
    assert ownership.owns("futureagi", path, ownership.manifest())


@pytest.mark.parametrize("path", GUARD_PATHS)
@pytest.mark.parametrize("name", [name for name, _, _ in COMPANIONS] + [
    "ai-evaluation", "unknown", "futureagi-extra",
])
def test_other_distributions_cannot_own_guard_paths(name, path):
    assert not ownership.owns(name, path, ownership.manifest())


@pytest.mark.parametrize("path", UNOWNED_PATHS + EXCLUDED_PATHS)
def test_futureagi_cannot_own_guard_lookalikes_or_excluded_paths(path):
    assert not ownership.owns("futureagi", path, ownership.manifest())


def test_wheel_record_accepts_both_exact_guard_paths(tmp_path, guard_payload):
    target = wheel(tmp_path, version="0.8.0", payload=guard_payload)
    result = gate.wheel_record(target)
    assert result["name"] == "futureagi"
    assert result["version"] == "0.8.0"
    assert set(result["paths"]) == set(guard_payload) | {
        "futureagi-0.8.0.dist-info/METADATA",
        "futureagi-0.8.0.dist-info/WHEEL",
        "futureagi-0.8.0.dist-info/RECORD",
    }


def test_guard_wheel_and_supported_companions_have_disjoint_ownership(tmp_path, guard_payload):
    sdk = wheel(tmp_path, version="0.8.0", payload=guard_payload)
    companions = [
        wheel(tmp_path, name, version, {path: b"# companion fixture\n"})
        for name, version, path in COMPANIONS
    ]
    result = gate.check_combination([sdk, *companions])
    assert result["status"] == "PASS"
    assert len(result["wheels"]) == 1 + len(COMPANIONS)
    for path in GUARD_PATHS:
        assert [item["name"] for item in result["wheels"] if path in item["paths"]] == ["futureagi"]


@pytest.mark.parametrize("path", UNOWNED_PATHS + EXCLUDED_PATHS)
def test_guard_wheel_rejects_additional_unowned_paths(tmp_path, guard_payload, path):
    # Check the offending member first so a guard ownership error cannot mask it.
    target = wheel(tmp_path, version="0.8.0", payload={path: b"# unowned\n", **guard_payload})
    with pytest.raises(ValueError, match="^" + re.escape(f"unowned runtime path: futureagi: {path}") + "$"):
        gate.check_combination([target])


@pytest.mark.parametrize("path", GUARD_PATHS)
@pytest.mark.parametrize("name,version,owned_path", COMPANIONS, ids=[item[0] for item in COMPANIONS])
def test_companion_wheel_cannot_ship_guard_paths(tmp_path, guard_payload, name, version, owned_path, path):
    target = wheel(tmp_path, name, version, {
        path: guard_payload[path], owned_path: b"# companion fixture\n",
    })
    with pytest.raises(ValueError, match="^" + re.escape(f"unowned runtime path: {name}: {path}") + "$"):
        gate.check_combination([target])


@pytest.mark.parametrize("path", GUARD_PATHS)
@pytest.mark.parametrize("mutation", ["digest", "size", "missing-row", "duplicate-row"])
def test_tampered_guard_record_is_rejected(tmp_path, guard_payload, path, mutation):
    # Digest and size checks must reach the tampered member before any other guard.
    target = wheel(tmp_path, version="0.8.0", payload={path: guard_payload[path], **guard_payload})
    with zipfile.ZipFile(target) as archive:
        files = {member: archive.read(member) for member in archive.namelist()}
    record = "futureagi-0.8.0.dist-info/RECORD"
    rows = list(csv.reader(io.StringIO(files[record].decode("utf-8"))))
    row = next(row for row in rows if row[0] == path)
    if mutation == "digest":
        row[1] = "sha256=" + "A" * 43
    elif mutation == "size":
        row[2] = str(int(row[2]) + 1)
    elif mutation == "missing-row":
        rows.remove(row)
    else:
        rows.append(row.copy())
    output = io.StringIO()
    csv.writer(output).writerows(rows)
    files[record] = output.getvalue().encode("utf-8")
    with zipfile.ZipFile(target, "w") as archive:
        for member, data in files.items():
            archive.writestr(member, data)
    error = (f"RECORD content mismatch: {path}" if mutation in {"digest", "size"}
             else "RECORD does not enumerate archive members exactly once")
    with pytest.raises(ValueError, match="^" + re.escape(error) + "$"):
        gate.check_combination([target])
