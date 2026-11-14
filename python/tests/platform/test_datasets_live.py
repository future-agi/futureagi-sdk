"""End-to-end against a real backend (FI_BASE_URL, e.g. a local install). No mocks.

Each test creates its own dataset with a unique name and deletes it afterwards.
"""

from __future__ import annotations

import asyncio
import time
import uuid
import warnings

import fi.platform as fi
import pytest
from fi.platform import models


def _wait_for(predicate, timeout: float = 30.0, every: float = 1.0):
    deadline = time.monotonic() + timeout
    while True:
        value = predicate()
        if value or time.monotonic() > deadline:
            return value
        time.sleep(every)


@pytest.fixture
def dataset(client):
    created = client.datasets.create(new_dataset_name=f"sdk-poc-{uuid.uuid4().hex[:8]}")
    yield created
    try:
        client.datasets.delete(dataset_ids=[created.dataset_id])
    except fi.NotFoundError:
        pass


def test_create_returns_typed_model(dataset):
    assert isinstance(dataset, models.DatasetCreateStartedResult)
    assert dataset.dataset_id and dataset.dataset_name.startswith("sdk-poc-")


def test_list_finds_the_new_dataset_across_pages(client, dataset):
    found = _wait_for(lambda: any(d.id == dataset.dataset_id for d in client.datasets.list(page_size=1)))
    assert found, "new dataset not returned by datasets.list()"


def test_search_filters_the_list(client, dataset):
    names = _wait_for(lambda: [d.name for d in client.datasets.list(search_text=dataset.dataset_name)])
    assert names == [dataset.dataset_name]


def test_add_columns_and_rows_then_read_table(client, dataset):
    columns = client.datasets.columns.add(
        dataset.dataset_id,
        new_columns_data=[{"name": "question", "data_type": "text"}, {"name": "answer", "data_type": "text"}],
    )
    assert isinstance(columns, models.DatasetColumnsMutationResult)

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", fi.BetaWarning)
        message = client.datasets.rows.add(
            dataset.dataset_id,
            rows=[
                {"cells": [{"column_name": "question", "value": "What is 2+2?"}, {"column_name": "answer", "value": "4"}]},
                {"cells": [{"column_name": "question", "value": "Capital of France?"}, {"column_name": "answer", "value": "Paris"}]},
            ],
        )
    assert isinstance(message, str)

    table = _wait_for(lambda: (t := client.datasets.get(dataset.dataset_id)) and len(t.table or []) >= 2 and t)
    assert isinstance(table, models.DatasetTableResult)
    assert {c.name for c in table.column_config} >= {"question", "answer"}
    assert len(table.table) == 2


def test_rows_add_is_marked_beta(client, dataset, monkeypatch):
    from fi.platform import _stability

    monkeypatch.setattr(_stability, "_warned", set())  # the warning fires once per process
    client.datasets.columns.add(dataset.dataset_id, new_columns_data=[{"name": "q", "data_type": "text"}])
    with pytest.warns(fi.BetaWarning):
        client.datasets.rows.add(dataset.dataset_id, rows=[{"cells": [{"column_name": "q", "value": "x"}]}])


def test_delete_removes_it(client):
    created = client.datasets.create(new_dataset_name=f"sdk-poc-{uuid.uuid4().hex[:8]}")
    client.datasets.delete(dataset_ids=[created.dataset_id])
    gone = _wait_for(lambda: not any(d.id == created.dataset_id for d in client.datasets.list()))
    assert gone


def test_validation_error_is_typed(client):
    with pytest.raises(fi.BadRequestError) as exc:
        client.datasets.create(new_dataset_name="")
    assert exc.value.status_code == 400


def test_missing_dataset_is_typed(client):
    with pytest.raises((fi.NotFoundError, fi.BadRequestError)) as exc:
        client.datasets.get(str(uuid.uuid4()))
    assert exc.value.status_code in (400, 404)


def test_bad_credentials_are_typed():
    import os

    if not os.environ.get("FI_BASE_URL"):
        pytest.skip("no backend configured")
    with fi.Client(api_key="wrong", secret_key="wrong") as bad, pytest.raises((fi.AuthenticationError, fi.PermissionDeniedError)):
        bad.datasets.list().first_page()


def test_async_client_same_api(client, dataset):
    async def run():
        async with fi.AsyncClient() as aclient:
            return [d.id async for d in aclient.datasets.list(search_text=dataset.dataset_name)]

    ids = _wait_for(lambda: asyncio.run(run()))
    assert ids == [dataset.dataset_id]
