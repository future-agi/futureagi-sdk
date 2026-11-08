"""Send-time observations, independent of retained exchange objects."""

import httpx


def wire_snapshot(request: httpx.Request) -> httpx.Request:
    """Copy a request inside a mock transport, before SDK scrubbing runs.

    MockTransport has consumed the request body before calling its handler, so
    reading content here also preserves multipart bytes without re-reading a
    file. The independent Headers object keeps raw duplicate header values.
    """
    return httpx.Request(
        request.method,
        request.url,
        headers=request.headers,
        content=request.content,
        extensions=request.extensions,
    )
