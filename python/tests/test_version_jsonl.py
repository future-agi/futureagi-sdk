import hashlib
import json
from pathlib import Path

import httpx
import pytest

from fi.datasets.version_jsonl import decode_version_jsonl, encode_version_jsonl
from tests.test_dataset_experiment_lifecycle import client_for


def _version(dataset="11111111-1111-4111-8111-111111111111"):
    return {
        "id": "22222222-2222-4222-8222-222222222222",
        "dataset": dataset,
        "parent_version": None,
        "description": "portable",
        "metadata": {"source": "fixture", "nullable": None},
        "source_revision": "git:abc",
        "content_hash": "a" * 64,
        "item_count": 2,
    }


def _items():
    return [
        {
            "example_id": "44444444-4444-4444-8444-444444444444",
            "external_id": "case-2",
            "input": ["text", None],
            "expected": None,
            "metadata": {"nested": None},
            "source_trace_id": "trace",
            "source_span_id": "span",
            "content_hash": "b" * 64,
            "legacy_row": None,
        },
        {
            "example_id": "33333333-3333-4333-8333-333333333333",
            "external_id": "case-1",
            "input": {"answer": False},
            "expected": 0,
            "metadata": {"split": "eval"},
            "source_trace_id": "",
            "source_span_id": "",
            "content_hash": "c" * 64,
            "legacy_row": None,
        },
    ]


def test_encode_is_deterministic_and_decode_preserves_complete_payload():
    first = encode_version_jsonl(_version(), _items())
    second = encode_version_jsonl(_version(), list(reversed(_items())))
    assert first == second
    assert decode_version_jsonl(first, _version()["dataset"]).items[0].to_dict()[
        "input"
    ] in ({"answer": False}, ["text", None])


def test_archive_checksum_covers_exact_case_lines():
    archive = encode_version_jsonl(_version(), _items())
    header, *records = archive.splitlines()
    parsed = json.loads(header)
    assert (
        parsed["records_sha256"]
        == hashlib.sha256(("\n".join(records) + "\n").encode()).hexdigest()
    )


@pytest.mark.parametrize(
    "mutate",
    [
        lambda text: text.replace('"format_version":1', '"format_version":2'),
        lambda text: text.replace("case-1", "case-2"),
        lambda text: text.replace("\n", "\n\n", 1),
    ],
)
def test_decode_rejects_invalid_archive_before_create(mutate):
    archive = encode_version_jsonl(_version(), _items())
    with pytest.raises(ValueError):
        decode_version_jsonl(mutate(archive), _version()["dataset"])


def test_legacy_row_policy_is_explicit_and_cross_dataset_safe():
    items = _items()
    items[0]["legacy_row"] = "55555555-5555-4555-8555-555555555555"
    archive = encode_version_jsonl(_version(), items)
    with pytest.raises(ValueError, match="legacy_row"):
        decode_version_jsonl(archive, "66666666-6666-4666-8666-666666666666")
    dropped = decode_version_jsonl(
        archive, "66666666-6666-4666-8666-666666666666", legacy_rows="drop"
    )
    assert all("legacy_row_id" not in item.to_dict() for item in dropped.items)
    preserved = decode_version_jsonl(
        archive, _version()["dataset"], legacy_rows="preserve"
    )
    assert any(
        item.to_dict().get("legacy_row_id") == "55555555-5555-4555-8555-555555555555"
        for item in preserved.items
    )


def test_empty_and_oversized_archives_are_refused():
    with pytest.raises(ValueError):
        encode_version_jsonl({**_version(), "item_count": 0}, [])
    archive = encode_version_jsonl(_version(), _items())
    with pytest.raises(ValueError):
        decode_version_jsonl(archive + "x" * (10 * 1024 * 1024), _version()["dataset"])


def test_shared_archive_is_byte_deterministic_and_preserves_every_portable_field():
    archive = (
        Path(__file__).parents[2]
        / "tests/fixtures/dataset-experiments/version-portability.jsonl"
    ).read_text()
    assert encode_version_jsonl(_version(), _items()) == archive
    body = decode_version_jsonl(
        archive, _version()["dataset"], parent_version_id=_version()["id"]
    ).to_dict()
    assert body == {
        "items": [
            {
                key: item[key]
                for key in item
                if key not in {"content_hash", "legacy_row"}
            }
            for item in sorted(_items(), key=lambda item: item["example_id"])
        ],
        "description": _version()["description"],
        "metadata": _version()["metadata"],
        "source_revision": _version()["source_revision"],
        "parent_version_id": _version()["id"],
    }


@pytest.mark.parametrize("late_failure", [False, True])
def test_export_fetches_complete_pages_and_returns_no_partial_archive(late_failure):
    calls = []

    def handler(request):
        index = len(calls)
        calls.append(request)
        assert request.method == "GET"
        assert dict(request.url.params) == {"limit": "500", "offset": str(index)}
        if late_failure and index == 1:
            return httpx.Response(403, json={"status": False, "detail": "hidden"})
        return httpx.Response(
            200,
            json={
                "status": True,
                "result": {
                    "version": _version(),
                    "items": [_items()[index]],
                    "limit": 500,
                    "offset": index,
                    "has_more": index == 0,
                },
            },
        )

    with client_for(handler) as client:
        if late_failure:
            with pytest.raises(Exception, match="403"):
                client.datasets.versions.export_jsonl(
                    _version()["dataset"], _version()["id"]
                )
        else:
            assert client.datasets.versions.export_jsonl(
                _version()["dataset"], _version()["id"]
            ) == encode_version_jsonl(_version(), _items())
    assert len(calls) == 2


@pytest.mark.parametrize("payload,expected_calls", [("bad\n", 0), ("valid", 1)])
def test_import_validates_before_its_single_post(payload, expected_calls):
    calls = []
    archive = (
        encode_version_jsonl(_version(), _items()) if payload == "valid" else payload
    )

    def handler(request):
        calls.append(request)
        assert request.method == "POST"
        assert (
            json.loads(request.content)
            == decode_version_jsonl(archive, _version()["dataset"]).to_dict()
        )
        raise httpx.ReadTimeout("response lost", request=request)

    with client_for(handler) as client, pytest.raises((ValueError, httpx.ReadTimeout)):
        client.datasets.versions.import_jsonl(_version()["dataset"], archive)
    assert len(calls) == expected_calls


@pytest.mark.parametrize(
    "change",
    [
        {"input": None},
        {"metadata": []},
        {"example_id": "invalid"},
        {"external_id": 123},
        {"source_trace_id": None},
        {"legacy_row": "invalid"},
        {"source_span_id": "x" * 256},
        {"expected": float("nan")},
    ],
)
def test_export_rejects_invalid_payloads(change):
    items = _items()
    items[0].update(change)
    with pytest.raises(ValueError):
        encode_version_jsonl(_version(), items)


def test_malformed_line_and_exact_case_bound():
    archive = encode_version_jsonl(_version(), _items())
    with pytest.raises(ValueError, match="line 2"):
        decode_version_jsonl(
            archive.splitlines()[0] + "\nnot json\n", _version()["dataset"]
        )
    from uuid import UUID

    items = [
        {
            **_items()[0],
            "example_id": str(UUID(int=index + 1)),
            "external_id": str(index),
        }
        for index in range(10_000)
    ]
    bounded = encode_version_jsonl({**_version(), "item_count": len(items)}, items)
    assert len(decode_version_jsonl(bounded, _version()["dataset"]).items) == 10_000
    with pytest.raises(ValueError, match="10000"):
        encode_version_jsonl(
            {**_version(), "item_count": 10_001}, items + [_items()[1]]
        )
