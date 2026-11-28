"""The channel's wire constants, frame codec, typed close errors and the dependency that carries
it. The values here are written out from the channel contract (the fake server holds its own copy),
so a wrong constant in the SDK fails against them."""

from __future__ import annotations

import struct
from pathlib import Path

import pytest

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10
    import tomli as tomllib


def test_constants_are_the_contracts_one_module():
    from fi.sandbox._channel import constants as c

    assert (c.SUBPROTOCOL, c.TOKEN_PROTOCOL_PREFIX) == ("omega.channel.v1", "omega.token.")
    assert (c.MAX_PAYLOAD_BYTES, c.OUTPUT_WINDOW_BYTES, c.STDIN_WINDOW_BYTES, c.MAX_STREAMS) == (
        65536, 262144, 32768, 8)
    assert c.HEADER_BYTES == 5
    assert (c.HELLO, c.STARTED, c.STDOUT, c.STDERR, c.EXIT, c.ERROR, c.WINDOW_TO_CLIENT) == (
        0x80, 0x86, 0x81, 0x82, 0x83, 0x84, 0x85)
    assert (c.EXEC, c.STDIN, c.STDIN_EOF, c.WINDOW_TO_SERVER, c.CANCEL) == (0x01, 0x02, 0x03, 0x04, 0x05)
    assert c.CLOSE_REASONS == {
        4401: "access_revoked", 4404: "sandbox_gone", 4409: "emergency_stop",
        4410: "sandbox_hibernated", 4411: "sandbox_frozen", 1001: "server_stopping",
    }
    assert c.TOKEN_SUFFIX == "/channel/token"


def test_frame_codec_round_trips_and_rejects_short_and_large_messages():
    from fi.sandbox._channel import constants as c
    from fi.sandbox._channel.protocol import decode, encode
    from fi.sandbox.errors import ChannelProtocolError

    message = encode(c.STDIN, 7, b"\x00\xffabc")
    assert message == b"\x02" + struct.pack(">I", 7) + b"\x00\xffabc"
    assert decode(message) == (c.STDIN, 7, b"\x00\xffabc")
    assert decode(encode(c.STDIN_EOF, 7)) == (c.STDIN_EOF, 7, b"")
    for bad in (b"", b"\x01\x00\x00\x00", b"\x81" + b"\x00" * 4 + b"x" * (c.MAX_PAYLOAD_BYTES + 1)):
        with pytest.raises(ChannelProtocolError):
            decode(bad)
    with pytest.raises(ChannelProtocolError):
        encode(c.STDIN, 1, b"x" * (c.MAX_PAYLOAD_BYTES + 1))


@pytest.mark.parametrize("code,reason,name", [
    (4401, "access_revoked", "ChannelAccessRevokedError"),
    (4404, "sandbox_gone", "ChannelSandboxGoneError"),
    (4409, "emergency_stop", "ChannelEmergencyStopError"),
    (4410, "sandbox_hibernated", "ChannelSandboxHibernatedError"),
    (4411, "sandbox_frozen", "ChannelSandboxFrozenError"),
    (1001, "server_stopping", "ChannelServerStoppingError"),
])
def test_each_close_code_has_a_typed_error_in_the_public_namespace(code, reason, name):
    import fi.sandbox as sandbox
    from fi.sandbox import errors

    cls = getattr(sandbox, name)
    assert cls is getattr(errors, name) and name in sandbox.__all__
    assert issubclass(cls, errors.ChannelClosedError) and issubclass(cls, errors.SandboxError)
    made = errors.channel_closed(code, "")
    assert type(made) is cls and made.close_code == code and made.reason == reason
    assert reason in str(made) or reason.replace("_", " ") in str(made)
    assert errors.channel_closed(code, "server words").server_reason == "server words"


def test_an_unlisted_close_code_is_the_base_class():
    from fi.sandbox import errors

    made = errors.channel_closed(1011, "boom")
    assert type(made) is errors.ChannelClosedError and made.close_code == 1011


def test_public_names_for_the_stream_handles():
    import fi.sandbox as sandbox

    for name in ("ExecStream", "AsyncExecStream", "ExecChunk", "ChannelClosedError", "ChannelProtocolError"):
        assert name in sandbox.__all__ and hasattr(sandbox, name), name


def test_websockets_is_a_core_dependency_not_an_extra():
    project = Path(__file__).resolve().parents[2] / "pyproject.toml"
    with project.open("rb") as stream:
        data = tomllib.load(stream)["tool"]["poetry"]
    requirement = data["dependencies"]["websockets"]
    assert isinstance(requirement, str), "websockets must be unconditional"
    assert requirement.lstrip("^~>=").startswith("16") or ">=16" in requirement
    assert all("websockets" not in members for members in data["extras"].values())
