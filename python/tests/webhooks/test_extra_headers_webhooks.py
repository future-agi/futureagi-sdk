"""FI_EXTRA_HEADERS in fi.webhooks: the clients take extra_headers= and send them to their server only."""

from __future__ import annotations

import pytest

from fi._extra_headers import ENV_VAR, ExtraHeadersError

# a made-up value, low entropy on purpose (never a real token)
TOKEN = "fake-identity-token-" + "x" * 12
VALUE = f"Bearer {TOKEN}"


@pytest.fixture(autouse=True)
def _no_setting(monkeypatch):
    monkeypatch.delenv(ENV_VAR, raising=False)


def test_webhooks_client_takes_extra_headers():
    from fi.webhooks import Webhooks

    with Webhooks(base_url="http://platform.test", extra_headers={"X-Team": "t"}) as wh:
        assert wh._auth.extra.for_url("http://platform.test/x") == {"X-Team": "t"}
        assert wh._auth.extra.for_url("https://receiver.test/hook") == {}
    with pytest.raises(ExtraHeadersError):
        Webhooks(base_url="http://platform.test", extra_headers={"Authorization": "x"})
