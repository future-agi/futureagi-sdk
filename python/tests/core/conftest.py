import pytest

from tests.core import _egress


@pytest.fixture(autouse=True)
def _no_egress(monkeypatch, tmp_path):
    _egress.install(monkeypatch, tmp_path)
    yield
    _egress.assert_no_attempts()


@pytest.fixture
def anyio_backend():
    return "asyncio"
