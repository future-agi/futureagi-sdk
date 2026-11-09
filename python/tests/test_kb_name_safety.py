"""Name selection and per-operation uploads use mocked transports only."""

from unittest.mock import MagicMock, call, patch

import pytest

from fi.kb.client import KnowledgeBase
from fi.kb.types import KnowledgeBaseConfig
from fi.utils.errors import SDKException
from tests.core import _egress


BASE_URL = "https://example.test"
KB_URL = BASE_URL + "/model-hub/knowledge-base/"
EXACT_ID = "00000000-0000-0000-0000-000000000001"
OTHER_ID = "00000000-0000-0000-0000-000000000002"
OPERATIONS = ["construct", "update", "delete_files", "delete"]


def _config(name, kb_id=EXACT_ID):
    return KnowledgeBaseConfig(id=kb_id, name=name, files=[])


def _response(method, result):
    response = MagicMock()
    response.status_code = 200
    response.url = KB_URL
    response.request.method = method
    response.json.return_value = {"status": True, "result": result}
    return response


@pytest.fixture(autouse=True)
def no_egress(monkeypatch, tmp_path):
    _egress.install(monkeypatch, tmp_path)
    yield
    _egress.assert_no_attempts()


@pytest.fixture
def clients():
    opened = []

    def make(kb_name=None):
        client = KnowledgeBase(
            kb_name=kb_name,
            fi_api_key="synthetic-api",
            fi_secret_key="synthetic-secret",
            fi_base_url=BASE_URL,
        )
        opened.append(client)
        return client

    yield make
    for client in opened:
        client.close()


def _operate(operation, client, clients):
    if operation == "construct":
        return clients("product_docs")
    if operation == "update":
        return client.update_kb("product_docs", new_name="renamed")
    if operation == "delete_files":
        return client.delete_files_from_kb(["manual.txt"], kb_name="product_docs")
    return client.delete_kb(kb_names=["product_docs"])


@pytest.mark.parametrize("operation", OPERATIONS)
@pytest.mark.parametrize(
    "names",
    [[], ["product_docs_archive"], ["PRODUCT_DOCS"], ["product_docs", "product_docs"]],
    ids=["missing", "substring", "different_case", "ambiguous"],
)
def test_name_operations_reject_nonunique_exact_targets(clients, operation, names):
    client = clients()
    # An existing target must not become a fallback for an explicit bad name.
    client.kb = _config("unrelated", OTHER_ID)
    candidates = [_config(name, kb_id) for name, kb_id in zip(names, [EXACT_ID, OTHER_ID])]
    with (
        patch.object(KnowledgeBase, "list_kbs", return_value=candidates) as lookup,
        patch.object(KnowledgeBase, "request") as request,
        patch("requests.patch", return_value=_response("PATCH", {})) as update,
    ):
        with pytest.raises(SDKException):
            _operate(operation, client, clients)

    lookup.assert_called_once_with("product_docs")
    request.assert_not_called()
    update.assert_not_called()
    assert str(client.kb.id) == OTHER_ID


@pytest.mark.parametrize("operation", OPERATIONS)
def test_name_operations_select_exact_match_after_substring(clients, operation):
    client = clients()
    exact = _config("product_docs")
    with (
        patch.object(
            KnowledgeBase,
            "list_kbs",
            return_value=[_config("product_docs_archive", OTHER_ID), exact],
        ) as lookup,
        patch.object(KnowledgeBase, "request") as request,
        patch("requests.patch", return_value=_response("PATCH", {})) as update,
    ):
        result = _operate(operation, client, clients)

    lookup.assert_called_once_with("product_docs")
    if operation == "construct":
        assert result.kb is exact
        request.assert_not_called()
        update.assert_not_called()
    elif operation == "update":
        assert update.call_args.kwargs["json"]["kb_id"] == EXACT_ID
        request.assert_not_called()
    else:
        payload = request.call_args.kwargs["config"].json
        assert payload == (
            {"kb_ids": [EXACT_ID]}
            if operation == "delete"
            else {"kb_id": EXACT_ID, "file_names": ["manual.txt"]}
        )
        update.assert_not_called()


def test_id_deletion_does_not_resolve_names(clients):
    client = clients()
    with (
        patch.object(client, "list_kbs") as lookup,
        patch.object(client, "request") as request,
    ):
        assert client.delete_kb(kb_ids=EXACT_ID) is client

    lookup.assert_not_called()
    assert request.call_args.kwargs["config"].json == {"kb_ids": [EXACT_ID]}


def _upload(client, operation, path, *, fail=False):
    client.kb = _config("product_docs")
    method = "POST" if operation == "create" else "PATCH"
    response = _response(method, {"kb_id": EXACT_ID, "kb_name": "product_docs"})
    if fail:
        response.json.return_value = {"status": False, "result": "Upload rejected"}
    sent = []

    def capture(**kwargs):
        parts = kwargs["files"]
        assert len(parts) == 1
        field, (name, handle, content_type) = parts[0]
        assert (field, name, content_type) == ("file", path.name, "text/plain")
        assert handle.read() == path.read_bytes()
        sent.append(handle)
        return response

    with (
        patch.object(client, "list_kbs", return_value=[client.kb]),
        patch("requests.post" if operation == "create" else "requests.patch", side_effect=capture),
    ):
        if fail:
            with pytest.raises(SDKException, match="Upload rejected"):
                getattr(client, operation + "_kb")("product_docs", file_paths=[str(path)])
        else:
            assert getattr(client, operation + "_kb")("product_docs", file_paths=[str(path)]) is client
    assert len(sent) == 1
    assert sent[0].closed


@pytest.mark.parametrize("previous_operation", ["create", "update"])
@pytest.mark.parametrize("target_name", ["product_docs", "other_docs"])
@pytest.mark.parametrize("file_arguments", [{}, {"file_paths": []}], ids=["omitted", "empty"])
@pytest.mark.parametrize("remove_previous_file", [False, True], ids=["retained", "removed"])
def test_rename_does_not_reuse_previous_upload(
    clients, tmp_path, previous_operation, target_name, file_arguments, remove_previous_file
):
    client = clients()
    document = tmp_path / "manual.txt"
    document.write_text("Original document")
    _upload(client, previous_operation, document)
    if remove_previous_file:
        document.unlink()
    target_id = EXACT_ID if target_name == "product_docs" else OTHER_ID

    with (
        patch.object(client, "list_kbs", return_value=[_config(target_name, target_id)]) as lookup,
        patch("requests.patch", return_value=_response("PATCH", {"name": "renamed"})) as update,
    ):
        assert client.update_kb(target_name, new_name="renamed", **file_arguments) is client

    kwargs = update.call_args.kwargs
    assert "files" not in kwargs
    assert "data" not in kwargs
    assert kwargs["json"] == {"kb_id": target_id, "name": "renamed"}
    assert client.kb.name == "renamed"
    assert str(client.kb.id) == target_id
    lookup.assert_called_once_with(target_name)


@pytest.mark.parametrize("previous_operation", ["create", "update"])
def test_rename_does_not_reuse_rejected_upload(clients, tmp_path, previous_operation):
    client = clients()
    document = tmp_path / "manual.txt"
    document.write_text("Rejected document")
    _upload(client, previous_operation, document, fail=True)

    with (
        patch.object(client, "list_kbs", return_value=[client.kb]),
        patch("requests.patch", return_value=_response("PATCH", {})) as update,
    ):
        client.update_kb("product_docs", new_name="renamed")

    assert "files" not in update.call_args.kwargs
    assert update.call_args.kwargs["json"] == {"kb_id": EXACT_ID, "name": "renamed"}


@pytest.mark.parametrize("previous_operation", ["create", "update"])
def test_update_uploads_only_explicit_new_files(clients, tmp_path, previous_operation):
    client = clients()
    previous = tmp_path / "previous.txt"
    previous.write_text("Previous document")
    _upload(client, previous_operation, previous)
    current = tmp_path / "current.txt"
    current.write_text("Current document")
    # The helper checks the filename, bytes, content type and closed handle.
    _upload(client, "update", current)


@pytest.mark.parametrize("ambiguous", [False, True], ids=["missing", "ambiguous"])
@pytest.mark.parametrize("invalid_first", [False, True], ids=["invalid_last", "invalid_first"])
@pytest.mark.parametrize("include_ids", [False, True], ids=["names_only", "names_and_ids"])
def test_delete_batch_rejects_any_unresolved_name_before_mutation(
    clients, ambiguous, invalid_first, include_ids
):
    client = clients()
    cached = client.kb = _config("product_docs")
    bad_candidates = (
        [_config("uncertain"), _config("uncertain", OTHER_ID)] if ambiguous else []
    )
    names = ["uncertain", "product_docs"] if invalid_first else ["product_docs", "uncertain"]

    def candidates(name):
        return [cached] if name == "product_docs" else bad_candidates

    with (
        patch.object(client, "list_kbs", side_effect=candidates),
        patch.object(client, "request") as request,
    ):
        with pytest.raises(SDKException, match="uncertain") as caught:
            client.delete_kb(kb_names=names, kb_ids=OTHER_ID if include_ids else None)

    assert ("Multiple" if ambiguous else "not found") in str(caught.value)
    request.assert_not_called()
    assert client.kb is cached


def test_delete_batch_resolves_all_names_before_one_request(clients):
    client = clients()
    first = client.kb = _config("product_docs")
    second = _config("other_docs", OTHER_ID)
    lookups = {first.name: first, second.name: second}
    looked_up = []

    def candidates(name):
        looked_up.append(name)
        return [lookups[name]]

    def delete(**kwargs):
        assert looked_up == ["product_docs", "other_docs"]
        assert kwargs["config"].json == {"kb_ids": [EXACT_ID, OTHER_ID]}

    with (
        patch.object(client, "list_kbs", side_effect=candidates) as lookup,
        patch.object(client, "request", side_effect=delete) as request,
    ):
        assert client.delete_kb(kb_names=["product_docs", "other_docs"]) is client

    assert lookup.call_args_list == [call("product_docs"), call("other_docs")]
    request.assert_called_once()
    assert client.kb is None


@pytest.mark.parametrize(
    "names",
    [[], ["product_docs_archive"], ["PRODUCT_DOCS"], ["product_docs", "product_docs"]],
    ids=["missing", "substring", "different_case", "ambiguous"],
)
def test_cached_update_rejects_nonunique_current_name(clients, names):
    cached = _config("product_docs")
    with patch.object(KnowledgeBase, "list_kbs", return_value=[cached]):
        client = clients("product_docs")
    candidates = [_config(name, kb_id) for name, kb_id in zip(names, [EXACT_ID, OTHER_ID])]

    with (
        patch.object(client, "list_kbs", return_value=candidates) as lookup,
        patch("requests.patch", return_value=_response("PATCH", {})) as update,
    ):
        with pytest.raises(SDKException, match="product_docs"):
            client.update_kb("product_docs", new_name="renamed")

    lookup.assert_called_once_with("product_docs")
    update.assert_not_called()
    assert client.kb is cached
    assert (str(cached.id), cached.name) == (EXACT_ID, "product_docs")


def test_cached_update_selects_current_owner_of_reused_name(clients):
    cached = _config("product_docs")
    with patch.object(KnowledgeBase, "list_kbs", return_value=[cached]):
        client = clients("product_docs")
    current = _config("product_docs", OTHER_ID)

    with (
        patch.object(
            client, "list_kbs", return_value=[_config("product_docs_archive"), current]
        ) as lookup,
        patch("requests.patch", return_value=_response("PATCH", {"name": "renamed"})) as update,
    ):
        assert client.update_kb("product_docs", new_name="renamed") is client

    assert update.call_args.kwargs["json"] == {"kb_id": OTHER_ID, "name": "renamed"}
    lookup.assert_called_once_with("product_docs")
    assert client.kb is current
    assert (str(cached.id), cached.name) == (EXACT_ID, "product_docs")


def test_cached_id_deletion_without_names_still_uses_cached_target(clients):
    client = clients()
    client.kb = _config("product_docs")
    with (
        patch.object(client, "list_kbs") as lookup,
        patch.object(client, "request") as request,
    ):
        assert client.delete_kb() is client

    lookup.assert_not_called()
    assert request.call_args.kwargs["config"].json == {"kb_ids": [EXACT_ID]}
    assert client.kb is None
