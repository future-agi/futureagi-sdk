"""First local upload writes native rows before its immutable version."""

import uuid

import pytest

from fi import experiments
from fi.errors import FutureAGIAPIError
from fi.experiments._server_dataset import pin_dataset, pin_resumed
from fi.experiments.errors import UsageError
from tests.experiments.unit.contract_server import ContractServer, client_for, err

ROWS = [
    {"id": "case-a", "question": "alpha", "count": 1, "ratio": 1.5, "enabled": True,
     "context": {"tag": "a"}, "choices": ["x"], "expected": {"answer": "yes"}, "metadata": {"group": "a"}},
    {"id": "case-b", "question": "beta", "count": 2, "ratio": 2.5, "enabled": False,
     "context": {"tag": "b"}, "choices": ["y"], "expected": {"answer": "no"}, "metadata": {"group": "b"}},
]


def upload(server, rows=ROWS, name="native-cases", **kwargs):
    return experiments.run(experiments.dataset(rows, name=name, **kwargs), lambda row: "done", [],
                           client=client_for(server), upload=True, trace=False, progress=False)


def posts(server, suffix):
    return [body for method, path, body in server.requests if method == "POST" and path.endswith(suffix)]


def one_post(server, suffix):
    found = posts(server, suffix)
    assert len(found) == 1, f"expected exactly one POST ending in {suffix}"
    return found[0]


def test_upload_adds_columns_before_rows():
    server = ContractServer()
    upload(server)
    columns = one_post(server, "/add_columns/")
    types = {c["name"]: c["data_type"] for c in columns["new_columns_data"]}
    assert types == {"id": "text", "question": "text", "count": "integer", "ratio": "float",
                     "enabled": "boolean", "context": "json", "choices": "array", "expected": "json",
                     "metadata": "json"}
    writes = [path for method, path, _ in server.requests if method == "POST"]
    column_at = next(i for i, p in enumerate(writes) if p.endswith("/add_columns/"))
    rows_at = next(i for i, p in enumerate(writes) if p.endswith("/add_rows/"))
    version_at = next(i for i, p in enumerate(writes) if p.endswith("/versions/"))
    assert column_at < rows_at < version_at


def test_upload_writes_table_rows_with_client_ids():
    server = ContractServer()
    upload(server)
    body = one_post(server, "/add_rows/")
    assert len(body["rows"]) == len(ROWS)
    ids = [r["id"] for r in body["rows"]]
    assert len(set(ids)) == len(ROWS)
    assert all(uuid.UUID(rid).version == 4 for rid in ids)
    for sent, original in zip(body["rows"], ROWS):
        assert {c["column_name"]: c["value"] for c in sent["cells"]} == original
    [dataset] = server.datasets.values()
    assert [r["row_id"] for r in dataset["rows"]] == ids


def test_version_items_point_to_uploaded_rows():
    server = ContractServer()
    result = upload(server)
    rows = one_post(server, "/add_rows/")
    version = one_post(server, "/versions/")
    assert len(version["items"]) == len(ROWS)
    assert "parent_version_id" not in version
    for row, item, original in zip(rows["rows"], version["items"], ROWS):
        assert item["legacy_row_id"] == row["id"]
        assert "example_id" not in item
        assert item["external_id"] == original["id"]
        assert item["expected"] == original["expected"]
        assert item["metadata"] == original["metadata"]
    stored = server.datasets[result.dataset_id]["versions"][0]["items"]
    assert [it["legacy_row"] for it in stored] == [r["id"] for r in rows["rows"]]
    assert [it["example_id"] for it in stored] == [str(uuid.uuid5(uuid.NAMESPACE_URL, r["id"]))
                                                  for r in rows["rows"]]


@pytest.mark.parametrize("status", [400, 429])
def test_refused_rows_leave_no_version(status):
    class RefusedRows(ContractServer):
        def __call__(self, request):
            if request.url.path.endswith("/add_rows/"):
                self.requests.append((request.method, request.url.path, None))
                return err(status, "native rows refused")
            return super().__call__(request)

    server = RefusedRows()
    with pytest.raises(FutureAGIAPIError, match="native rows refused"):
        upload(server)
    assert len(posts(server, "/add_rows/")) == 1
    assert posts(server, "/versions/") == []
    assert posts(server, "/experiment-runs/") == []


def test_unchanged_upload_and_local_resume_add_no_native_writes():
    server = ContractServer()
    client = client_for(server)
    spec = experiments.dataset(ROWS, name="native-cases")
    first = pin_dataset(client, spec)
    first_writes = [(m, p, b) for m, p, b in server.requests if m != "GET"]
    same = pin_dataset(client, spec)
    resumed = pin_resumed(client, spec, dataset_id=first.dataset_id, version_id=first.version_id, name=first.name)
    assert first.version_id == same.version_id == resumed.version_id
    assert [r.id for r in first.rows] == [r.id for r in resumed.rows]
    assert [(m, p, b) for m, p, b in server.requests if m != "GET"] == first_writes
    assert len(posts(server, "/add_rows/")) == 1


def test_name_based_read_preserves_metadata_and_local_reuse():
    server = ContractServer()
    client = client_for(server)
    spec = experiments.dataset(ROWS, name="native-cases")
    first = pin_dataset(client, spec)
    by_name = pin_dataset(client, "native-cases")
    assert by_name.version_id == first.version_id
    assert [r.metadata for r in by_name.rows] == [r.metadata for r in first.rows]
    again = pin_dataset(client, spec)
    assert again.version_id == first.version_id
    assert len(posts(server, "/versions/")) == 1


def test_existing_version_only_dataset_is_not_materialized():
    server = ContractServer()
    did = server.add_dataset("legacy-cases")
    first = upload(server, name="legacy-cases", add_version=True)
    server.requests.clear()
    same = upload(server, name="legacy-cases")
    assert first.dataset_version_id == same.dataset_version_id
    assert server.datasets[did]["rows"] == []
    assert posts(server, "/add_columns/") == posts(server, "/add_rows/") == posts(server, "/versions/") == []


def test_inferred_columns_preserve_nulls_and_promote_numbers():
    server = ContractServer()
    upload(server, [{"question": "a", "number": 1, "empty": None},
                    {"question": "b", "number": 1.5, "empty": None}])
    body = one_post(server, "/add_columns/")
    assert {c["name"]: c["data_type"] for c in body["new_columns_data"]} == {
        "question": "text", "number": "float", "empty": "text"}
    body = one_post(server, "/add_rows/")
    assert all(next(c for c in r["cells"] if c["column_name"] == "empty")["value"] is None for r in body["rows"])


def test_conflicting_column_types_stop_before_native_writes():
    server = ContractServer()
    with pytest.raises(UsageError, match="incompatible"):
        upload(server, [{"question": "a"}, {"question": {"text": "b"}}])
    assert posts(server, "/add_columns/") == posts(server, "/add_rows/") == posts(server, "/versions/") == []


def test_explicit_input_does_not_upload_unselected_columns():
    server = ContractServer()
    upload(server, [{"question": "a", "not_selected": "private-local-only", "answer": "ok"}],
           input="question", expected="answer")
    body = one_post(server, "/add_rows/")
    assert {c["column_name"]: c["value"] for c in body["rows"][0]["cells"]} == {"question": "a", "answer": "ok"}
