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

    def _tracked(self, iterator: Any) -> Any:
        try:
            for chunk in iterator:
                if self._closed:
                    return
                yield self._note(chunk)
        except Exception as exc:
            self._error = exc if isinstance(exc, StreamError) else StreamError(f"Stream interrupted: {exc}")
            raise self._error from exc if self._error is not exc else None
        finally:
            try:
                if not self._closed:
                    self._closed = True
                    self._response.close()
            finally:
                self._notify_finish()

    async def _atracked(self, iterator: Any) -> Any:
        try:
            async for chunk in iterator:
                if self._closed:
                    return
                yield self._note(chunk)
        except Exception as exc:
            self._error = exc if isinstance(exc, StreamError) else StreamError(f"Stream interrupted: {exc}")
            raise self._error from exc if self._error is not exc else None
        finally:
            try:
                if not self._closed:
                    self._closed = True
                    await self._response.aclose()
            finally:
                self._notify_finish()
