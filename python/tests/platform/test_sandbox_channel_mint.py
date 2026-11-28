"""Minting a channel token and the errors of the mint and of the upgrade, through the SDK's
sandbox errors (sync and async). The fake server follows the channel contract."""

from __future__ import annotations

import pytest
from fi.sandbox import (
    AuthenticationError,
    ConflictError,
    NotFoundError,
    PermissionDeniedError,
    RateLimitError,
    UnavailableError,
)

from ._channel_fake import OTHER_SBX
from ._channel_support import (  # noqa: F401
    SBX,
    FakeChannel,
    async_sandbox,
    channel_fixture,
    sync_sandbox,
)


def test_mint_posts_an_empty_body_and_returns_the_channel(channel):
    sbx, core = sync_sandbox(channel)
    reply = sbx._sandboxes.commands.channel_token(SBX)
    core.shared.close()
    info = reply["channel"]
    assert reply["schemaVersion"] == "omega-workspace-sandboxes/v2"
    assert info["token"].startswith("sct_") and len(info["token"]) == 4 + 43
    assert info["transport"]["protocols"] == ["omega.channel.v1", "omega.token." + info["token"]]
    assert info["url"] == f"ws://127.0.0.1:{channel.port}/workspace/sandboxes/{SBX}/channel"
    assert info["limits"]["outputWindowBytes"] == 262144 and info["limits"]["stdinWindowBytes"] == 32768
    (seen,) = channel.mints
    assert seen["sandbox"] == SBX and seen["headers"]["authorization"].startswith("Bearer ")
    assert seen["body"] in (b"", b"{}")


@pytest.mark.asyncio
async def test_mint_async(channel):
    sbx, core = async_sandbox(channel)
    reply = await sbx._sandboxes.commands.channel_token(SBX)
    await core.shared.aclose()
    assert reply["channel"]["token"].startswith("sct_")


def _open(channel, sandbox_id=SBX):
    sbx, core = sync_sandbox(channel, sandbox_id)
    try:
        return sbx.commands.exec_stream(["true"])
    finally:
        core.shared.close()


def test_403_is_permission_denied(tmp_path):
    with FakeChannel(tmp_path, sandboxes=(SBX, OTHER_SBX), forbidden=(OTHER_SBX,)) as server:
        with pytest.raises(PermissionDeniedError) as caught:
            _open(server, OTHER_SBX)
    assert caught.value.status == 403 and caught.value.code == "role_forbidden"


def test_404_for_an_unknown_sandbox_names_the_switch(channel):
    with pytest.raises(NotFoundError) as caught:
        _open(channel, "sbx_" + "z" * 24)
    assert caught.value.status == 404
    assert "switched off" in str(caught.value)


def test_404_while_the_operator_switch_is_off_says_so(tmp_path):
    with FakeChannel(tmp_path, enabled=False) as server:
        with pytest.raises(NotFoundError) as caught:
            _open(server)
    text = str(caught.value)
    assert "switched off by the operator" in text and "OMEGA_WORKSPACE_SANDBOX_CHANNEL" in text
    assert not server.upgrades


def test_409_channel_remote_unsupported_is_a_clear_conflict(tmp_path):
    with FakeChannel(tmp_path, remote_unsupported=True) as server:
        with pytest.raises(ConflictError) as caught:
            _open(server)
    text = str(caught.value)
    assert caught.value.status == 409
    assert "sandbox host" in text and "commands.run" in text
    assert not server.upgrades


def test_401_at_the_mint_is_authentication_failed(channel, monkeypatch):
    from fi.sandbox import Sandbox, Sandboxes
    from fi.sandbox._connection import SandboxConnection

    core = SandboxConnection(environ={"OMEGA_BASE_URL": channel.base_url,
                                      "FUTUREAGI_OMEGA_API_KEY": "wrong-token"}).core()
    with pytest.raises(AuthenticationError):
        Sandbox(Sandboxes(core), {"id": SBX}).commands.exec_stream(["true"])
    core.shared.close()


@pytest.mark.parametrize("status,code,detail,cls", [
    (429, "rate_limited", {}, RateLimitError),
    (503, "sandboxes_unavailable", {"reason": "external_origin_required"}, UnavailableError),
    (409, "emergency_stopped", {}, ConflictError),
])
def test_other_mint_refusals_keep_their_classes(tmp_path, status, code, detail, cls):
    with FakeChannel(tmp_path, mint_error=(status, code, detail)) as server:
        with pytest.raises(cls) as caught:
            _open(server)
    assert caught.value.status == status


def test_401_token_invalid_at_the_upgrade_is_authentication_failed(channel):
    channel.token_ttl = -1  # every token is already expired when it is redeemed
    with pytest.raises(AuthenticationError) as caught:
        _open(channel)
    assert "token_invalid" in (caught.value.code or "") or "token" in str(caught.value).lower()
    assert channel.refusals == [(401, "token_invalid")]


@pytest.mark.asyncio
async def test_async_404_names_the_switch(tmp_path):
    with FakeChannel(tmp_path, enabled=False) as server:
        sbx, core = async_sandbox(server)
        with pytest.raises(NotFoundError) as caught:
            await sbx.commands.exec_stream(["true"])
        await core.shared.aclose()
    assert "switched off by the operator" in str(caught.value)


def test_a_bad_argv_is_refused_before_any_request(channel):
    from fi.sandbox import ConfigurationError

    sbx, core = sync_sandbox(channel)
    for argv in ([], "ls -la", ["ls", 3], [""], ["-rf"], ["a\x00b"], ["x"] * 513):
        with pytest.raises(ConfigurationError) as caught:
            sbx.commands.exec_stream(argv)
        assert caught.value.code == "invalid_argv"
    core.shared.close()
    assert channel.mints == []
