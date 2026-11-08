"""``judge()``'s HTTP call, with a bounded retry of a 429 or 5xx answer.

Wave 2d judges each part of the CRITERIA in its own request, so a row makes one call per part, and a run makes parts x
its concurrency calls at once. Before this, one part's 429 made the whole row an error score ("judge HTTP 429").

- **What is retried:** a 429 (rate limited) and any 5xx (the provider overloaded or failing). Nothing else: a 4xx is
  the request's own fault, so it is an error score at once, naming the status.
- **How long it waits:** what the answer asks, ``retry-after-ms`` (OpenAI) or ``Retry-After`` (seconds or an HTTP
  date), capped at ``RETRY_WAIT_CAP_S``; without either, 1, 2, then 4 seconds.
- **How often:** at most ``MAX_RETRIES`` times per call. After that the last answer is returned, and the caller makes
  it an error score naming the status and the retries.
"""

from __future__ import annotations

import asyncio
import email.utils
import time
from typing import Any, Optional

import httpx

from fi.experiments import _debug

MAX_RETRIES = 3
RETRY_WAIT_CAP_S = 30.0
_sleep = asyncio.sleep  # the tests replace it, so they never wait


def retryable(status: int) -> bool:
    return status == 429 or status >= 500


def retry_wait(resp: httpx.Response, attempt: int) -> float:
    """Seconds to wait before retry ``attempt`` (1-based): the answer's own ask, capped, or 1, 2, 4 s."""
    wait: Optional[float] = None
    ms = resp.headers.get("retry-after-ms")
    if ms:
        try:
            wait = float(ms) / 1000.0
        except ValueError:
            wait = None
    after = resp.headers.get("retry-after")
    if wait is None and after:
        try:
            wait = float(after)
        except ValueError:
            try:
                when = email.utils.parsedate_to_datetime(after)
                wait = when.timestamp() - time.time()
            except (TypeError, ValueError, IndexError, OverflowError):
                wait = None
    if wait is None or wait != wait:  # missing, unreadable or NaN: back off
        wait = float(2 ** (attempt - 1))
    return min(max(wait, 0.0), RETRY_WAIT_CAP_S)


async def post(http: httpx.AsyncClient, url: str, body: dict[str, Any], key: str) -> tuple[httpx.Response, int]:
    """``(the last answer, retries made)``: one POST, retried while it answers 429 or 5xx, at most MAX_RETRIES times."""
    attempt = 0
    while True:
        resp = await http.post(url, json=body, headers={"Authorization": f"Bearer {key}"})
        _debug.http("judge POST", url, resp.status_code, attempt)  # --verbose: host and path only
        if not retryable(resp.status_code) or attempt >= MAX_RETRIES:
            return resp, attempt
        attempt += 1
        await _sleep(retry_wait(resp, attempt))
