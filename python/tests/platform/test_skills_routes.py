"""The live suites skip Skills only when the product has no Skills routes at all: Django's own 404
page for GET /model-hub/skills/. Every other answer runs the Skills tests or fails."""

from __future__ import annotations

import sys
from pathlib import Path

import httpx
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))  # the shared helper, under any import mode

from _skills_routes import SKILLS_PROBE, skills_served_by  # noqa: E402
from fi.platform._errors import error_from_response  # noqa: E402

DJANGO_404 = "<!doctype html><title>Not Found</title><h1>Not Found</h1>"


class Answering:
    def __init__(self, status, content, content_type):
        self.status, self.content, self.content_type, self.calls = status, content, content_type, []

    def request(self, method, path):
        self.calls.append((method, path))
        if self.status < 400:
            return {"results": []}
        response = httpx.Response(self.status, content=self.content.encode(),
                                  headers={"content-type": self.content_type},
                                  request=httpx.Request(method, "http://product" + path))
        raise error_from_response(response)


def test_only_djangos_404_page_means_no_skills_routes():
    client = Answering(404, DJANGO_404, "text/html; charset=utf-8")
    assert skills_served_by(client) is False
    assert client.calls == [("GET", SKILLS_PROBE)]


@pytest.mark.parametrize("status, content, content_type", [
    (200, "", "application/json"),
    (403, '{"status": false, "detail": "Skills are not enabled"}', "application/json"),
    (401, '{"detail": "Authentication credentials were not provided."}', "application/json"),
    (500, DJANGO_404, "text/html"),
])
def test_any_other_answer_means_the_routes_exist(status, content, content_type):
    assert skills_served_by(Answering(status, content, content_type)) is True


@pytest.mark.parametrize("content, content_type", [
    ('{"detail": "Not found."}', "application/json"),
    ('"Not found"', "application/json"),
    ("Not Found", "text/plain"),
])
def test_a_404_that_is_not_djangos_page_fails(content, content_type):
    with pytest.raises(AssertionError, match="not Django's page"):
        skills_served_by(Answering(404, content, content_type))


def test_transport_failures_propagate():
    class Down:
        def request(self, method, path):
            raise httpx.ConnectError("connection refused")

    with pytest.raises(httpx.ConnectError):
        skills_served_by(Down())
