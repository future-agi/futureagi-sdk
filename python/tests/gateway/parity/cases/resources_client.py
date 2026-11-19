"""Client-level cases: module helpers (health_check, check_valid_key), an
injected http client, and closing a client (close, aclose, the context managers)."""

from __future__ import annotations

from .._fixtures import MSG, ok
from .._runner import BASE_URL, KEY, Case, exercises

BOTH = ("sync", "async")
CHAT = {"model": "gpt-4o-mini", "messages": MSG}


def _health(ctx, **kwargs):
    return ctx.T.health_check(api_key=KEY, base_url=BASE_URL, **kwargs)


def cases() -> list[Case]:
    return [
        Case("resource.health_check", "resources", _health, replies=[ok("health")]),
        Case(
            "resource.health_check.model",
            "resources",
            lambda c: _health(c, model="gpt-4o-mini"),
            replies=[ok("chat_completion")],
        ),
        Case(
            "resource.health_check.error",
            "resources",
            _health,
            replies=[{"status": 404, "text": "404 page not found"}],
        ),
        Case(
            "resource.health_check.no_url",
            "resources",
            lambda c: c.T.health_check(api_key=KEY),
        ),
        Case(
            "resource.check_valid_key",
            "resources",
            lambda c: c.T.check_valid_key(KEY, BASE_URL),
            replies=[ok("models_list")],
        ),
        Case(
            "resource.check_valid_key.401",
            "resources",
            lambda c: c.T.check_valid_key(KEY, BASE_URL),
            replies=[{"status": 401, "json": {"error": {"message": "bad key"}}}],
        ),
        Case(
            "resource.http_client",
            "resources",
            _explicit_http_client,
            replies=[ok("chat_completion")],
        ),
        Case(
            "resource.close_and_context",
            "resources",
            _close_and_context,
            BOTH,
            replies=[ok("chat_completion")],
        ),
        Case(
            "resource.close",
            "resources",
            _close_then_call,
            BOTH,
            replies=[ok("chat_completion"), ok("chat_completion")],
        ),
    ]


@exercises("close")
def _explicit_http_client(ctx):
    import httpx

    with httpx.Client(headers={"x-from-http-client": "1"}) as http:
        client = ctx.client(http_client=http, max_retries=0)
        result = ctx.call(
            client, "chat.completions.create", model="gpt-4o-mini", messages=MSG
        )
        client.close()
        return {"result": result, "http_client_closed": http.is_closed}


def _close_and_context(ctx):
    """`with` / `async with`: the client is itself, and leaving closes it."""
    manager = ctx.client(max_retries=0)
    client = ctx.enter(manager)
    result = ctx.call(client, "chat.completions.create", **CHAT)
    shown = repr(client)
    ctx.exit(manager)
    return {"result": result, "repr": shown}


@exercises("close", "aclose")
def _close_then_call(ctx):
    """close() / aclose(), then a request on the closed client."""
    client = ctx.client(max_retries=0)
    first = ctx.call(client, "chat.completions.create", **CHAT)
    ctx.call(client, "aclose" if ctx.mode == "async" else "close")
    after = ctx.attempt(lambda: ctx.call(client, "chat.completions.create", **CHAT))
    return {"first": first, "after_close": after}


