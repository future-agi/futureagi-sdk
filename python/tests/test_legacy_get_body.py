"""Regression tests for the prepared requests on the legacy Python transport."""

import json
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

import pytest
from requests import Response
from requests_futures.sessions import FuturesSession

from fi.api.auth import HttpClient
from fi.api.types import HttpMethod, RequestConfig


URL = "https://example.invalid/items"


def prepare(method, *, round_trip=False, **kwargs):
    config = RequestConfig(method=method, url=URL, retry_attempts=1, **kwargs)
    if round_trip:
        config = RequestConfig.model_validate(config.model_dump())
    with FuturesSession() as session, patch.object(session, "send", return_value=Response()) as send:
        session.trust_env = False
        client = HttpClient(base_url=URL, session=session)
        client.request(config)
        send.assert_called_once()
        return send.call_args.args[0]


@pytest.mark.parametrize("body", [{}, {"json": None}, {"json": {}}], ids=["omitted", "none", "empty"])
@pytest.mark.parametrize("round_trip", [False, True])
def test_get_without_json_keeps_query_in_url(body, round_trip):
    request = prepare(
        HttpMethod.GET,
        round_trip=round_trip,
        params={"tag": ["a+b", "x y"], "custom/key": "a&b"},
        **body,
    )
    assert request.body is None
    assert parse_qs(urlsplit(request.url).query) == {"tag": ["a+b", "x y"], "custom/key": ["a&b"]}


def test_nonempty_explicit_get_json_is_preserved():
    body = {"explicit": True}
    assert json.loads(prepare(HttpMethod.GET, json=body).body) == body


@pytest.mark.parametrize("kwargs, expected", [({}, {}), ({"json": {"value": 1}}, {"value": 1})])
def test_post_json_is_unchanged(kwargs, expected):
    assert json.loads(prepare(HttpMethod.POST, **kwargs).body) == expected
