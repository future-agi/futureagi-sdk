"""SDK-level parallel request utilities for batch/multi-model completions.

These are standalone functions (not methods on the client) that use
``concurrent.futures.ThreadPoolExecutor`` for sync variants and ``asyncio``
for async variants.  No gateway changes are required.
"""

from __future__ import annotations

import asyncio
from concurrent.futures import Future, ThreadPoolExecutor, as_completed
from typing import Any

from fi.gateway.types.chat.chat_completion import ChatCompletion

# ---------------------------------------------------------------------------
# Sync: batch_completion
# ---------------------------------------------------------------------------


def batch_completion(
    client: Any,
    model: str,
    messages_list: list[list[dict[str, Any]]],
    max_concurrency: int = 10,
    return_exceptions: bool = False,
    **kwargs: Any,
) -> list[ChatCompletion | Exception]:
    """Send multiple prompts to a single model in parallel.

    Parameters
    ----------
    client:
        A :class:`agentcc.AgentCC` instance.
    model:
        The model identifier (e.g. ``"gpt-4o"``).
    messages_list:
        A list of message lists, where each inner list is a conversation.
    max_concurrency:
        Maximum number of concurrent requests.
    return_exceptions:
        If *True*, failed requests return the exception object in the
        results list instead of raising.  If *False* (the default), the
        first failure is raised immediately (best-effort: other in-flight
        requests may still complete).
    **kwargs:
        Extra keyword arguments forwarded to
        ``client.chat.completions.create()``.

    Returns
    -------
    list[ChatCompletion]
        Results in the **same order** as *messages_list*.
    """
    if not messages_list:
        return []

    results: list[ChatCompletion | Exception | None] = [None] * len(messages_list)

    def _call(index: int, messages: list[dict[str, Any]]) -> tuple[int, ChatCompletion]:
        resp = client.chat.completions.create(model=model, messages=messages, **kwargs)
        return index, resp

    with ThreadPoolExecutor(max_workers=max_concurrency) as executor:
        futures: dict[Future[tuple[int, ChatCompletion]], int] = {}
        for idx, msgs in enumerate(messages_list):
            fut = executor.submit(_call, idx, msgs)
            futures[fut] = idx

        for fut in as_completed(futures):
            idx = futures[fut]
            try:
                _, result = fut.result()
                results[idx] = result
            except Exception as exc:
                if return_exceptions:
                    results[idx] = exc
                else:
                    # Cancel remaining futures best-effort, then raise
                    for other in futures:
                        other.cancel()
                    raise

    return results  # type: ignore[return-value]


# ---------------------------------------------------------------------------
# Async: abatch_completion
# ---------------------------------------------------------------------------


async def abatch_completion(
    client: Any,
    model: str,
    messages_list: list[list[dict[str, Any]]],
    max_concurrency: int = 10,
    return_exceptions: bool = False,
    **kwargs: Any,
) -> list[ChatCompletion | Exception]:
    """Async variant of :func:`batch_completion`.

    Uses ``asyncio.Semaphore`` for concurrency control and
    ``asyncio.gather`` for parallel dispatch.
    """
    if not messages_list:
        return []

    sem = asyncio.Semaphore(max_concurrency)

    async def _call(messages: list[dict[str, Any]]) -> ChatCompletion:
        async with sem:
            return await client.chat.completions.create(model=model, messages=messages, **kwargs)

    tasks = [_call(msgs) for msgs in messages_list]
    return await asyncio.gather(*tasks, return_exceptions=return_exceptions)  # type: ignore[return-value]


# ---------------------------------------------------------------------------
# Sync: batch_completion_models  (race — first success wins)
# ---------------------------------------------------------------------------


def batch_completion_models(
    client: Any,
    models: list[str],
    messages: list[dict[str, Any]],
    max_concurrency: int = 10,
    **kwargs: Any,
) -> ChatCompletion:
    """Send one prompt to multiple models and return the **first** success.

    This is a latency optimisation — all models are queried in parallel and
    the first successful response is returned.  Remaining futures are
    cancelled best-effort.

    Raises the last exception if **all** models fail.
    """
    if not models:
        raise ValueError("models list must not be empty")

    def _call(model: str) -> ChatCompletion:
        return client.chat.completions.create(model=model, messages=messages, **kwargs)

    last_exc: Exception | None = None

    with ThreadPoolExecutor(max_workers=max_concurrency) as executor:
        futures: dict[Future[ChatCompletion], str] = {}
        for model in models:
            fut = executor.submit(_call, model)
            futures[fut] = model

        for fut in as_completed(futures):
            try:
                result = fut.result()
                # Cancel remaining futures best-effort
                for other in futures:
                    if other is not fut:
                        other.cancel()
                return result
            except Exception as exc:
                last_exc = exc

    # All failed
    assert last_exc is not None
    raise last_exc


# ---------------------------------------------------------------------------
# Async: abatch_completion_models  (race — first success wins)
# ---------------------------------------------------------------------------


async def abatch_completion_models(
    client: Any,
    models: list[str],
    messages: list[dict[str, Any]],
    max_concurrency: int = 10,
    **kwargs: Any,
) -> ChatCompletion:
    """Async variant of :func:`batch_completion_models`.

    Uses ``asyncio.wait(return_when=FIRST_COMPLETED)`` and cancels
    remaining tasks after the first success.
    """
    if not models:
        raise ValueError("models list must not be empty")

    sem = asyncio.Semaphore(max_concurrency)

    async def _call(model: str) -> ChatCompletion:
        async with sem:
            return await client.chat.completions.create(model=model, messages=messages, **kwargs)

    pending: set[asyncio.Task[ChatCompletion]] = set()
    for model in models:
        task = asyncio.ensure_future(_call(model))
        pending.add(task)

    last_exc: Exception | None = None

    while pending:
        done, pending = await asyncio.wait(pending, return_when=asyncio.FIRST_COMPLETED)
        for task in done:
            exc = task.exception()
            if exc is None:
                # Success — cancel remaining tasks
                for p in pending:
                    p.cancel()
                # Await cancelled tasks to suppress warnings
                if pending:
                    await asyncio.gather(*pending, return_exceptions=True)
                return task.result()
            last_exc = exc

    assert last_exc is not None
    raise last_exc


# ---------------------------------------------------------------------------
# Sync: batch_completion_models_all
# ---------------------------------------------------------------------------


def batch_completion_models_all(
    client: Any,
    models: list[str],
    messages: list[dict[str, Any]],
    max_concurrency: int = 10,
    return_exceptions: bool = False,
    **kwargs: Any,
) -> list[ChatCompletion | Exception]:
    """Send one prompt to multiple models and return **all** responses.

    Results are returned in the same order as *models*.  Useful for model
    comparison and A/B testing.
    """
    if not models:
        return []

    results: list[ChatCompletion | Exception | None] = [None] * len(models)

    def _call(index: int, model: str) -> tuple[int, ChatCompletion]:
        resp = client.chat.completions.create(model=model, messages=messages, **kwargs)
        return index, resp

    with ThreadPoolExecutor(max_workers=max_concurrency) as executor:
        futures: dict[Future[tuple[int, ChatCompletion]], int] = {}
        for idx, model in enumerate(models):
            fut = executor.submit(_call, idx, model)
            futures[fut] = idx

        for fut in as_completed(futures):
            idx = futures[fut]
            try:
                _, result = fut.result()
                results[idx] = result
            except Exception as exc:
                if return_exceptions:
                    results[idx] = exc
                else:
                    for other in futures:
                        other.cancel()
                    raise

    return results  # type: ignore[return-value]


# ---------------------------------------------------------------------------
# Async: abatch_completion_models_all
# ---------------------------------------------------------------------------


async def abatch_completion_models_all(
    client: Any,
    models: list[str],
    messages: list[dict[str, Any]],
    max_concurrency: int = 10,
    return_exceptions: bool = False,
    **kwargs: Any,
) -> list[ChatCompletion | Exception]:
    """Async variant of :func:`batch_completion_models_all`."""
    if not models:
        return []

    sem = asyncio.Semaphore(max_concurrency)

    async def _call(model: str) -> ChatCompletion:
        async with sem:
            return await client.chat.completions.create(model=model, messages=messages, **kwargs)

    tasks = [_call(m) for m in models]
    return await asyncio.gather(*tasks, return_exceptions=return_exceptions)  # type: ignore[return-value]
