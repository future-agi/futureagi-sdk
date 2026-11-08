from __future__ import annotations

import json

import pytest
from fi.context.lock import (
    InstallationError,
    SourceBundle,
    canonical_json,
    manifest_digest,
)
from fi.context.materialize import validate_bundle
from test_materializer import bundle


@pytest.mark.parametrize(
    "mount",
    ["skills/refunds", "skills/refunds//", "skills/Refunds/", "skills/refunds/extra/"],
)
def test_descriptor_mount_is_exact_not_silently_normalized(mount):
    source = bundle()
    files = dict(source.files)
    descriptor = json.loads(files[".futureagi/context.json"])
    descriptor["links"][0]["mount"] = mount
    files[".futureagi/context.json"] = canonical_json(descriptor)
    source = SourceBundle(
        identity=source.identity.model_copy(update={"digest": manifest_digest(files)}),
        lease=source.lease,
        files=files,
    )
    with pytest.raises(InstallationError) as failure:
        validate_bundle(source)
    assert failure.value.code == "integrity_failure"


def test_compiled_file_limit_includes_descriptor_and_root():
    valid = bundle(
        linked=False, extra={f"references/{i}.md": b"Reference" for i in range(198)}
    )
    assert len(valid.files) == 200
    validate_bundle(valid)
    with pytest.raises(ValueError):
        bundle(
            linked=False, extra={f"references/{i}.md": b"Reference" for i in range(199)}
        )


@pytest.mark.parametrize(
    "paths",
    [
        ("references/A.md", "references/a.md"),
        ("references/é.md", "references/é.md"),
        ("references/item", "references/item/nested.md"),
    ],
)
def test_cross_platform_path_collisions_fail_before_materialization(paths):
    with pytest.raises(InstallationError) as failure:
        bundle(linked=False, extra={p: b"Reference" for p in paths})
    assert failure.value.code == "path_collision"
