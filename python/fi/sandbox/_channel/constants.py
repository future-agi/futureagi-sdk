"""Every wire value of the sandbox channel, in one place (the channel contract's own).

A message is one binary WebSocket message holding one frame: ``[type u8][stream u32 big-endian]
[payload]``, the payload at most :data:`MAX_PAYLOAD_BYTES`. Stream 0 is the socket; a client picks
any other id when it opens an exec stream."""

from __future__ import annotations

#: What follows the sandbox's own route (``.../sandboxes/{id}``) to mint a data token (60 s, single use).
TOKEN_SUFFIX = "/channel/token"
#: The operator's switch: exactly ``0`` turns the channel off (the token route then answers 404).
KILL_SWITCH_ENV = "OMEGA_WORKSPACE_SANDBOX_CHANNEL"

#: The subprotocol the server answers, and the prefix of the one that carries the token.
SUBPROTOCOL = "omega.channel.v1"
TOKEN_PROTOCOL_PREFIX = "omega.token."

HEADER_BYTES = 5
MAX_PAYLOAD_BYTES = 65536
MAX_MESSAGE_BYTES = HEADER_BYTES + MAX_PAYLOAD_BYTES
#: The windows the server states in ``hello`` and ``started`` (credit is counted in bytes).
OUTPUT_WINDOW_BYTES = 262144
STDIN_WINDOW_BYTES = 32768
MAX_STREAMS = 8
#: ``exec``'s argv: 1 to 512 strings.
MAX_ARGV = 512
#: The one exec stream this client opens on a socket.
EXEC_STREAM_ID = 1

# Server to client.
HELLO = 0x80
STDOUT = 0x81
STDERR = 0x82
EXIT = 0x83
ERROR = 0x84
WINDOW_TO_CLIENT = 0x85  # grants the client more stdin bytes
STARTED = 0x86
# Client to server.
EXEC = 0x01
STDIN = 0x02
STDIN_EOF = 0x03
WINDOW_TO_SERVER = 0x04  # grants the server more output bytes
CANCEL = 0x05

#: Application close codes, with the contract's stable reasons.
CLOSE_ACCESS_REVOKED = 4401
CLOSE_SANDBOX_GONE = 4404
CLOSE_EMERGENCY_STOP = 4409
CLOSE_SANDBOX_HIBERNATED = 4410
CLOSE_SANDBOX_FROZEN = 4411
CLOSE_SERVER_STOPPING = 1001
CLOSE_REASONS = {
    CLOSE_ACCESS_REVOKED: "access_revoked",
    CLOSE_SANDBOX_GONE: "sandbox_gone",
    CLOSE_EMERGENCY_STOP: "emergency_stop",
    CLOSE_SANDBOX_HIBERNATED: "sandbox_hibernated",
    CLOSE_SANDBOX_FROZEN: "sandbox_frozen",
    CLOSE_SERVER_STOPPING: "server_stopping",
}

#: The HTTP status a stream ``error`` frame's code stands for (the contract's codes).
STREAM_ERROR_STATUS = {
    "validation": 400,
    "conflict": 409,
    "rate_limited": 429,
    "not_found": 404,
    "emergency_stopped": 409,
    "internal": 500,
}

#: Output the reader has consumed is granted back to the server in steps of this size (or at once
#: when nothing is left buffered), so credit follows consumption.
GRANT_STEP_BYTES = OUTPUT_WINDOW_BYTES // 4

#: How long the connection and the closing handshake may take, in seconds.
OPEN_TIMEOUT_SECONDS = 30
CLOSE_TIMEOUT_SECONDS = 3
