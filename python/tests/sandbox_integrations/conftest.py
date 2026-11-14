"""Setup for every sandbox integration test: each frozen-OpenAPI mock server answers the exec route as the
sandbox service does, with a 400 for an absolute ``cwd`` (see ``_strict_exec``), so an integration that
sends a wrong folder fails here."""

from __future__ import annotations

import pytest

from ._strict_exec import enforce_everywhere


@pytest.fixture(autouse=True)
def _exec_folder_rule(monkeypatch):
    enforce_everywhere(monkeypatch)
