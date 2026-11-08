"""Supplemental namespaces cannot replace or diverge from certified operations."""
from dataclasses import replace
import json
from pathlib import Path

import pytest

from fi._core.connector_policy import OPERATIONS as CONNECTORS
from fi._core.transport import PlatformShared
from fi.generated.platform.policy import OPERATIONS as PLATFORM


READS = {"platform.credentials.bindings", "platform.credentials.get", "platform.credentials.list"}


def test_generated_overlap_is_exact_and_equal():
    root = Path(__file__).resolve().parents[3]
    features = json.loads((root / "openapi/connectors/features.json").read_text())
    overlap = PLATFORM.keys() & CONNECTORS.keys()
    assert overlap == (READS if features["credential_reads"] else set())
    shared = PlatformShared(lambda: None, table=PLATFORM, supplemental_table=CONNECTORS)
    for name in overlap:
        assert CONNECTORS[name] == PLATFORM[name]
        assert shared.operation(name) is PLATFORM[name]
    for name in PLATFORM:
        assert shared.operation(name) is PLATFORM[name]
    for name in CONNECTORS.keys() - PLATFORM.keys():
        assert shared.operation(name) is CONNECTORS[name]


@pytest.mark.parametrize("lazy", [False, True])
def test_equal_overlap_keeps_certified_object(lazy):
    name, certified = next(iter(PLATFORM.items()))
    duplicate = replace(certified)
    assert duplicate == certified and duplicate is not certified
    shared = PlatformShared(lambda: None, table=None if lazy else PLATFORM,
                            supplemental_table={name: duplicate})
    assert shared.operation(name) is certified


@pytest.mark.parametrize("lazy", [False, True])
def test_divergent_overlap_is_rejected_before_origin_or_transport(lazy):
    name, certified = next(iter(PLATFORM.items()))
    divergent = replace(certified, path=certified.path + "/different")
    resolved = []
    shared = PlatformShared(lambda: resolved.append(True), table=None if lazy else PLATFORM,
                            supplemental_table={name: divergent})
    with pytest.raises(ValueError, match="Divergent supplemental operation"):
        shared.operation(name)
    assert resolved == []
    assert shared._http is None and shared._ahttp is None
