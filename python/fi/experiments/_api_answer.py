"""One run-create or ingest POST, its HTTP status read before its body is parsed.

The generated client parses every answer as JSON before anything looks at its status (each operation's
``_parse_response`` calls ``response.json()`` for every status, error statuses included). So a page written by
whatever stands in front of the API (a gateway, proxy, load balancer or web app) surfaced as a bare
``json.JSONDecodeError`` that carries no status. Here the operation's own ``_get_kwargs`` builds the request, the
platform client's httpx client sends it (its auth and its retrying transport included), and the answer is read in
this order:

- not JSON: :class:`NonJSONAnswerError`, with the status, the page's ``<title>`` and what to do. The caller retries
  only a 429 or a 5xx, i.e. a server that is down, restarting or overloaded behind its gateway (an HTML 502 page
  while it restarts). Any other status stops the run at once: a proxy's 413 body limit, an auth proxy's 401 or 403, a
  404 for a wrong path, a redirect, a web page's 200. Resending the same request would get the same page;
- JSON with a status outside 2xx: ``FutureAGIAPIError(status, <that JSON>)``, as the platform client raises it;
- JSON with a 2xx status: the operation's own parser, then the expected type (the platform client's rule).
"""

from __future__ import annotations

import html
import re
from typing import Any

_TITLE = re.compile(rb"<title[^>]*>(.*?)</title\s*>", re.IGNORECASE | re.DOTALL)


def _page_title(response: Any) -> str:
    """The page's ``<title>`` (printable, one line, at most 120 characters), else the status and its reason."""
    match = _TITLE.search(bytes(response.content[:65536]))
    if match:
        text = html.unescape(match.group(1).decode("utf-8", errors="replace"))
        text = " ".join("".join(ch if ch.isprintable() else " " for ch in text).split())[:120]
        if text:
            return text
    return f"{response.status_code} {getattr(response, 'reason_phrase', '') or ''}".strip()


class NonJSONAnswerError(Exception):
    """A run-create or ingest call was answered by something other than the API: the answer is not JSON, and
    every answer the API itself writes is. ``status_code`` is the HTTP status; only a 429 or a 5xx is retried."""

    def __init__(self, status_code: int, title: str, content_type: str = "", location: str = "") -> None:
        self.status_code = status_code
        self.title = title
        self.content_type = content_type
        self.location = location
        super().__init__(self._text())

    @classmethod
    def from_response(cls, response: Any) -> "NonJSONAnswerError":
        headers = response.headers
        return cls(int(response.status_code), _page_title(response), headers.get("content-type", ""),
                   headers.get("location", ""))

    def _text(self) -> str:
        status, page = self.status_code, f"'{self.title}'"
        if status == 429 or status >= 500:
            return (f"a gateway or proxy answered for the server with its own page ({page}): the server behind it "
                    "is down, restarting or overloaded")
        if status == 413:
            return (f"a proxy in front of the API refused the request as too large ({page}): raise its request "
                    "body limit to at least 2 MiB (nginx: client_max_body_size; ingress-nginx: the "
                    "nginx.ingress.kubernetes.io/proxy-body-size annotation)")
        if status in (401, 403, 407):
            return (f"a proxy in front of the API refused the request before the API saw it ({page}); the API's "
                    "own refusals are JSON. Check that proxy's access rules")
        if status in (404, 405):
            return (f"nothing answers as the API at this address ({page}); check FI_BASE_URL: it must be the "
                    "API's address, not the app's")
        if 300 <= status < 400:
            where = f" to {self.location[:200]}" if self.location else ""
            return (f"the address redirects{where} ({page}); set FI_BASE_URL to the address the API answers on")
        return (f"the answer is a page, not the API's JSON ({page}, {self.content_type or 'no content type'}); "
                "check FI_BASE_URL: it must be the API's address, not the app's")


def post(client: Any, op: Any, expected: type, *path: Any, body: Any) -> Any:
    """``op`` (a generated operation module) for ``client`` (the platform client), read as the module says."""
    from fi.errors import FutureAGIAPIError

    generated = client.generated_client
    response = generated.get_httpx_client().request(**op._get_kwargs(*path, body=body))
    status = int(response.status_code)
    try:
        payload = response.json()
    except ValueError:  # json.JSONDecodeError and UnicodeDecodeError alike
        raise NonJSONAnswerError.from_response(response) from None
    if not 200 <= status < 300:
        raise FutureAGIAPIError(status, payload)
    parsed = op._parse_response(client=generated, response=response)
    if not isinstance(parsed, expected):
        raise FutureAGIAPIError(status, "Unexpected response shape")
    return parsed
