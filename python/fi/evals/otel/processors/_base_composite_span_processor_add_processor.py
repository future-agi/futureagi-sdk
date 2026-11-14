"""CompositeSpanProcessor add processor operations."""
from __future__ import annotations

from fi.evals.otel.processors.base import (Any, BaseSpanProcessor, Context, Optional, ReadableSpan)


class _CompositeSpanProcessorAddProcessorMethods:
    __slots__ = ()

    def add_processor(self, processor: BaseSpanProcessor) -> None:
        """Add a processor to the composite."""
        from fi.evals.otel.processors.base import (BaseSpanProcessor)
        self._processors.append(processor)


    def remove_processor(self, processor: BaseSpanProcessor) -> None:
        """Remove a processor from the composite."""
        from fi.evals.otel.processors.base import (BaseSpanProcessor)
        if processor in self._processors:
            self._processors.remove(processor)


    def on_start(
        self,
        span: Any,
        parent_context: Optional[Context] = None,
    ) -> None:
        """Call on_start on all child processors."""
        from fi.evals.otel.processors.base import (Any, Context, Optional, logger)
        if not self.enabled:
            return

        for processor in self._processors:
            try:
                processor.on_start(span, parent_context)
            except Exception as e:
                logger.warning(f"Processor on_start error: {e}")


    def _on_ending(self, span: Any) -> None:
        """Call the span-ending hook on each child processor that has one."""
        from fi.evals.otel.processors.base import (logger)
        if not self.enabled:
            return

        for processor in self._processors:
            hook = getattr(processor, "_on_ending", None)
            if not callable(hook):
                continue
            try:
                hook(span)
            except Exception as e:
                logger.warning(f"Processor _on_ending error: {e}")


    def on_end(self, span: ReadableSpan) -> None:
        """Call on_end on all child processors."""
        from fi.evals.otel.processors.base import (ReadableSpan)
        if not self.enabled:
            return

        if self._parallel:
            self._process_parallel(span)
        else:
            self._process_sequential(span)


    def _process_sequential(self, span: ReadableSpan) -> None:
        """Process span through all processors sequentially."""
        from fi.evals.otel.processors.base import (ReadableSpan, logger)
        for processor in self._processors:
            try:
                if processor.enabled:
                    processor.on_end(span)
            except Exception as e:
                logger.warning(f"Processor on_end error: {e}")


    def _process_parallel(self, span: ReadableSpan) -> None:
        """Process span through all processors in parallel."""
        from fi.evals.otel.processors.base import (
            BaseSpanProcessor, ReadableSpan, ThreadPoolExecutor, logger,
        )
        if self._executor is None:
            self._executor = ThreadPoolExecutor(max_workers=self._max_workers)

        def run_processor(processor: BaseSpanProcessor) -> None:
            try:
                if processor.enabled:
                    processor.on_end(span)
            except Exception as e:
                logger.warning(f"Processor on_end error: {e}")

        futures = [
            self._executor.submit(run_processor, p)
            for p in self._processors
        ]

        # Wait for all to complete
        for future in futures:
            try:
                future.result(timeout=30)
            except Exception as e:
                logger.warning(f"Parallel processor error: {e}")


    def force_flush(self, timeout_millis: int = 30000) -> bool:
        """Force flush all child processors."""
        from fi.evals.otel.processors.base import (logger)
        success = True
        per_processor_timeout = timeout_millis // max(len(self._processors), 1)

        for processor in self._processors:
            try:
                if not processor.force_flush(per_processor_timeout):
                    success = False
            except Exception as e:
                logger.warning(f"Processor force_flush error: {e}")
                success = False

        return success
