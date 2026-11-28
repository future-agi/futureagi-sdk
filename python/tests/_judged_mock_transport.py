"""An in-process transport that the SDK judges as a direct connection.

A caller's client whose transport is exactly ``httpx.MockTransport`` answers in the process and is not judged (the
0.8.1 rule). The tests that check the plain-http rule, its notice and its refusals through a caller's client use this
subclass instead: it answers in the process as ``MockTransport`` does, and the SDK judges it as it judges a transport
it built to send direct (``_fi_decided_by_environment``), so every rule for a connection applies to it.
"""

from __future__ import annotations

import httpx


class JudgedMockTransport(httpx.MockTransport):
    """``httpx.MockTransport`` that the SDK judges as a direct connection."""

    _fi_decided_by_environment = True
