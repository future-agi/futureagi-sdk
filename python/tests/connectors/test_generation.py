"""Contract pin, facade parity and removable-feature generation gates."""
import hashlib
import importlib
import inspect
import json
import re
import subprocess

import pytest

from tests.connectors.surface import ROOT, FEATURES, SURFACE, NAMESPACES, enabled


def test_pinned_contract_and_generated_output():
    sources = json.loads((ROOT / "openapi/connectors/source.json").read_text())
    for source in sources.values():
        assert re.fullmatch(r"sha256:[0-9a-f]{64}", source.get("source_digest", ""))
        assert source["source_label"]
        assert "commit" not in source
        assert hashlib.sha256((ROOT / source["slice"]).read_bytes()).hexdigest() == source["slice_sha256"]
    subprocess.run(["node", str(ROOT / "scripts/connectors/generate.mjs"), "--check"], check=True)


def test_language_twins_and_signatures_are_complete():
    mapping = json.loads((ROOT / "openapi/connectors/wrapper-map.json").read_text())["operations"]
    expected = {name: (feature, "client." + path) for feature, methods in SURFACE.items() for name, path in methods.items()}
    assert {name for name, row in mapping.items() if row.get("feature")} == set(expected)
    seen = set()
    for name, row in mapping.items():
        if name not in expected or not enabled(expected[name][0]):
            assert "methods" not in row
            assert row["unwrapped"] and row["languages"] == {"py": "NOT-OFFERED", "ts": "NOT-OFFERED"}
            continue
        feature, path = expected[name]
        assert row["feature"] == feature
        assert "unwrapped" not in row
        assert len(row["methods"]) == 1
        for method in row["methods"]:
            py, ts = method["py"], method["ts"]
            assert py == path
            assert py not in seen
            seen.add(py)
            assert re.sub(r"(?<=[a-z0-9])([A-Z])", r"_\1", ts).lower() == py
            _, ns, *parts = py.split(".")
            module = importlib.import_module(f"fi.{ns}")
            cls = "SyncLogs" if parts[0] == "sync_logs" else ns.title()
            sync, async_ = (getattr(getattr(module, prefix + cls), parts[-1]) for prefix in ("", "Async"))
            assert inspect.iscoroutinefunction(async_)
            assert not inspect.iscoroutinefunction(sync)
            assert inspect.signature(sync) == inspect.signature(async_)
            assert list(inspect.signature(sync).parameters)[1:] == [a for a in method["py_args"] if a != "*"]
            assert sync.__doc__ and async_.__doc__
    assert len(seen) == sum(len(methods) for feature, methods in SURFACE.items() if enabled(feature))


@pytest.mark.parametrize("namespace,feature", NAMESPACES.items())
def test_modules_remain_small_or_are_absent(namespace, feature):
    file = ROOT / f"python/fi/{namespace}/__init__.py"
    if not enabled(feature):
        assert not file.exists()
        with pytest.raises(ModuleNotFoundError, match=f"fi.{namespace}"):
            importlib.import_module(f"fi.{namespace}")
    else:
        text = file.read_text()
        assert len(text.splitlines()) <= 400
        assert text.endswith("\n") and not text.endswith("\n\n")
        assert not re.search(r"[\"']/workspace/|[\"']/integrations/", text)
        for dependency in re.findall(r"^from (fi\.[^ ]+) import", text, re.M):
            assert dependency.startswith(("fi._core.", "fi.generated."))


@pytest.mark.parametrize("feature", FEATURES)
def test_policy_modules_match_feature_state(feature):
    module = f"fi.generated.platform.connectors.{feature}"
    if not enabled(feature):
        assert not (ROOT / f"python/fi/generated/platform/connectors/{feature}.py").exists()
        with pytest.raises(ModuleNotFoundError, match=module):
            importlib.import_module(module)
    else:
        operations = importlib.import_module(module).OPERATIONS
        assert set(operations) == set(SURFACE[feature])
        if feature in ("mcp_core", "oauth_connect", "credential_reads"):
            for op in operations.values():
                assert not op.idempotent
                assert not op.human_only
                assert op.retry_class == ("http-idempotent" if op.method in ("GET", "PUT", "DELETE") else "unsafe")
                if feature == "credential_reads":
                    assert op.method == "GET"
