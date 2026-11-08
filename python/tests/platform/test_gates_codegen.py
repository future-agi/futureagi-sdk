"""Platform codegen gates over committed files, run in CI with no Node and no network.

The scoped spec's pin, the policy table against the spec, the generated types and the import boundary.
The wrapper map and hygiene gates are in their own modules; regenerate-and-diff needs the pinned
generators and runs in ``scripts/platform/check.sh``.
"""

from __future__ import annotations

import hashlib
import os
import subprocess
import sys
import typing
from types import ModuleType

import pytest

from ._feature_scope import OPERATION_COUNT, HTTP_IDEMPOTENT_COUNT, PAGINATED_COUNT, assert_credential_scope
from ._gates_support import (
    PLATFORM,
    REPO,
    SCOPED,
    TS_POLICY,
    guard_sockets,
    operations,
    read_json,
    spec_retry_class,
)


@pytest.fixture(autouse=True)
def no_egress(monkeypatch: pytest.MonkeyPatch) -> None:
    guard_sockets(monkeypatch)


@pytest.fixture(scope="module")
def spec() -> dict[str, typing.Any]:
    return read_json(SCOPED)


#: Every human-only operation of the pinned contract that carries an idempotency key.
HUMAN_ONLY_KEYED = {
    "platform.credentials.create",
    "platform.credentials.revoke",
    "platform.credentials.rotate",
    "platform.approvals.decide",
}
OUT_OF_SCOPE_FAMILIES = (
    "hub.",
    "connectors.",
    "platform.skills.",
    "platform.agentTeams.",
    "platform.audit.",
)


@pytest.fixture(scope="module")
def source() -> dict[str, typing.Any]:
    return read_json(PLATFORM / "source.json")


@pytest.fixture(scope="module")
def policy() -> ModuleType:
    from fi.generated.platform import policy as module

    return module


def test_scoped_spec_matches_its_pin(
    source: dict[str, typing.Any], policy: ModuleType
) -> None:
    digest = hashlib.sha256(SCOPED.read_bytes()).hexdigest()
    assert (
        digest == source["scoped"]["sha256"]
    ), "the scoped spec changed without build-platform-openapi.sh"
    assert policy.CONTRACT["scoped_sha256"] == digest
    assert "source_digest" in source and "source_label" in source
    assert "source_digest" in policy.CONTRACT and "source_label" in policy.CONTRACT
    assert policy.CONTRACT["source_digest"] == source["source_digest"]
    assert policy.CONTRACT["source_label"] == source["source_label"]
    assert source["source_digest"].startswith("sha256:")
    assert "commit" not in source and "commit" not in policy.CONTRACT
    ts = TS_POLICY.read_text(encoding="utf-8")
    assert (
        digest in ts and source["source_digest"] in ts
    ), "policy.gen.ts was not regenerated from this spec"


def test_scope_policy_and_operations_list_agree(
    spec: dict[str, typing.Any], policy: ModuleType
) -> None:
    scope = read_json(PLATFORM / "scope.json")["operations"]
    listed = [
        line.split()[0]
        for line in (PLATFORM / "generated" / "futureagi-platform.operations.txt")
        .read_text()
        .splitlines()
    ]
    assert (
        sorted(scope) == sorted(operations(spec)) == sorted(policy.OPERATIONS) == listed
    )
    assert policy.CONTRACT["operation_count"] == len(scope) == OPERATION_COUNT
    assert_credential_scope(scope)


def test_policy_matches_the_spec_operation_by_operation(
    spec: dict[str, typing.Any], policy: ModuleType
) -> None:
    for name, (method, op) in operations(spec).items():
        entry = policy.OPERATIONS[name]
        idem = op.get("x-omega-idempotency") or {}
        idempotent = op.get("x-omega-idempotent") is True
        assert entry.method == method, name
        assert entry.retry_class == spec_retry_class(method, op), name
        assert entry.idempotent is idempotent, name
        # durable is False only where the contract says so; unstated counts as durable (keyed), and
        # the extras keep the fact that it was unstated, per operation
        assert entry.durable is (
            not idempotent or idem.get("durable") is not False
        ), name
        unstated = idempotent and idem.get("durable") is None
        extras = policy.EXTRAS.get(name, {})
        assert extras.get("durable_unstated", False) is unstated, name
        assert entry.idempotency_key_required is (
            idempotent and idem.get("keyRequired") is True
        ), name
        assert entry.not_found_means_applied is (
            op.get("x-omega-not-found-on-retry-means-applied") is True
        ), name
        assert entry.human_only is False, name
        assert (entry.stream is None) is ("x-omega-stream" not in op), name
        assert (entry.pagination is None) is ("x-omega-pagination" not in op), name
        assert entry.operation_id == op["operationId"], name


def test_policy_counts(policy: ModuleType) -> None:
    counts = policy.CONTRACT["counts"]
    assert counts == {
        "operations": OPERATION_COUNT,
        "keyed": 13,
        "keyed-not-durable": 3,
        "http-idempotent": HTTP_IDEMPOTENT_COUNT,
        "unsafe": 6,
        "idempotent": 16,
        "durable_unstated": 4,
        "streams": 2,
        "paginated": PAGINATED_COUNT,
        "not_found_means_applied": 0,
    }
    names = set(policy.OPERATIONS)
    assert_credential_scope(names)
    assert (
        not names & HUMAN_ONLY_KEYED
    ), "a human-only keyed operation reached the scoped spec"
    assert not [n for n in names if n.startswith(OUT_OF_SCOPE_FAMILIES)]
    assert {
        n for n, e in policy.OPERATIONS.items() if e.retry_class == "keyed-not-durable"
    } == {
        "platform.environments.control",
        "platform.environments.create",
        "platform.environments.revise",
    }
    assert not any(name.startswith("sandboxes.") for name in names)
    assert policy.OPERATIONS["platform.agents.create"].retry_class == "unsafe"
    assert all(not op.not_found_means_applied for op in policy.OPERATIONS.values())
    assert policy.EXTRAS["deployments.rotateAccessToken"]["replay_omits"] == (
        "accessToken",
    )
    unstated = {n for n, e in policy.EXTRAS.items() if e.get("durable_unstated")}
    assert unstated == {
        "platform.agents.draft",
        "platform.agents.rollbackDeployment",
        "platform.schedules.create",
        "platform.schedules.runNow",
    }
    assert len(unstated) == counts["durable_unstated"]
    assert all(policy.OPERATIONS[n].durable is True for n in unstated)
    assert set(policy.KNOWN_EVENTS) == {
        "OmegaRunEventFrame",
        "OmegaDeploymentLogFrame",
    }


def test_generated_types_import_and_resolve() -> None:
    from fi.generated.platform import types as generated

    schemas = read_json(SCOPED)["components"]["schemas"]
    assert set(generated.TITLES) == {node.get("title", key) for key, node in schemas.items()}
    assert len(generated.TITLES) == len(schemas)
    for title in generated.TITLES:
        value = getattr(generated, title)
        if isinstance(value, type) and issubclass(value, dict):
            assert value.__total__ is False, title
            typing.get_type_hints(value)
    for path in (REPO / "python" / "fi" / "generated" / "platform").glob("*.py"):
        assert "Unset" not in path.read_text(encoding="utf-8"), path.name


def _fresh(code: str) -> subprocess.CompletedProcess[str]:
    env = {
        **os.environ,
        "FI_BASE_URL": "http://127.0.0.1:9",
        "FI_PLATFORM_BASE_URL": "http://127.0.0.1:9",
    }
    return subprocess.run(
        [sys.executable, "-c", code],
        cwd=REPO / "python",
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def test_import_boundaries() -> None:
    result = _fresh(
        "import sys, fi\n"
        "assert not [m for m in sys.modules if m.startswith('fi.generated.platform')], 'import fi loaded platform code'\n"
        "import fi.generated.platform.policy, fi.generated.platform.types\n"
        "bad = [m for m in sys.modules if m.startswith(('fi.utils', 'fi.api', 'fi.experiments'))]\n"
        "assert not bad, bad\n"
        "print('ok')\n"
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "ok"
