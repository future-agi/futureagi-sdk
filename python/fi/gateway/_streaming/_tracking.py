"""Released stream accounting/callback hooks, shared by the split stream types."""

from __future__ import annotations

from typing import Any

from fi.gateway._exceptions import StreamError


class StreamTracking:
    def _init_tracking(self, chunk_cls: Any, on_chunk: Any, on_finish: Any) -> None:
        from fi.gateway._streaming._accumulator import ChunkAccumulator
        from fi.gateway.types.chat.chat_completion_chunk import ChatCompletionChunk

        self._on_chunk = on_chunk
        self._on_finish = on_finish
        self._finished = False
        self._error: Exception | None = None
        # Set by the transport for this exchange; never retain its client or key.
        self._composed_names: frozenset[str] = frozenset()
        self._redact_error = getattr(self._response, "_gateway_error_scrubber", None)
        self.usage: Any = None
        self.chunk_count = 0
        self._accumulator = ChunkAccumulator() if chunk_cls is ChatCompletionChunk else None

    @property
    def completion(self) -> Any:
        # The released Stream contract exposes assembled completions for chat only.
        return self._accumulator.build() if self._accumulator is not None else None

    def _note(self, chunk: Any) -> Any:
        self.chunk_count += 1
        response = getattr(chunk, "response", None)
        usage = getattr(chunk, "usage", None) or getattr(response, "usage", None)
        if usage is not None:
            self.usage = usage
        if self._accumulator is not None:
            self._accumulator.add(chunk)
        if self._on_chunk is not None:
            self._on_chunk(chunk)
        return chunk

    def _notify_finish(self) -> None:
        if not self._finished:
            self._finished = True
            if self._on_finish is not None:
                self._on_finish(self, self._error)

    def _scrub_error(self, error: BaseException) -> None:
        from fi.gateway._transport._scrub import scrub_reachable

        if self._redact_error is not None:
            self._redact_error(error)
        scrub_reachable((error,), self._composed_names)

    def _failure(self, exc: Exception) -> StreamError:
        from fi.gateway._retry_policy import _UNKNOWN_DISPATCH_REMEDY

        self._scrub_error(exc)
        error = exc if isinstance(exc, StreamError) else StreamError(f"Stream interrupted: {exc}")
        error.gateway_evidence = self.agentcc.gateway_evidence
        error.request_id = error.gateway_request_id
        # Transport interruptions have no definitive gateway outcome. Apply this
        # before callbacks, including streams with no published lifecycle hooks.
        if not isinstance(exc, StreamError) and error.dispatched == "unknown":
            error.message += " " + _UNKNOWN_DISPATCH_REMEDY
            error.args = (error.message,)
        return error

    def _tracked(self, iterator: Any) -> Any:
        try:
            for chunk in iterator:
                if self._closed:
                    return
                yield self._note(chunk)
        except Exception as exc:
            # Scrub before formatting/wrapping, preserving the original cause/traceback.
            self._error = self._failure(exc)
            raise self._error from exc if self._error is not exc else None
        except BaseException as exc:
            self._scrub_error(exc)
            raise
        finally:
            try:
                if not self._closed:
                    self._closed = True
                    self._response.close()
            except BaseException as exc:
                self._scrub_error(exc)
                raise
            finally:
                self._notify_finish()

    async def _atracked(self, iterator: Any) -> Any:
        try:
            async for chunk in iterator:
                if self._closed:
                    return
                yield self._note(chunk)
        except Exception as exc:
            # Scrub before formatting/wrapping, preserving the original cause/traceback.
            self._error = self._failure(exc)
            raise self._error from exc if self._error is not exc else None
        except BaseException as exc:
            self._scrub_error(exc)
            raise
        finally:
            try:
                if not self._closed:
                    self._closed = True
                    await self._response.aclose()
            except BaseException as exc:
                self._scrub_error(exc)
                raise
            finally:
                self._notify_finish()
