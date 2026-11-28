"""NonBlockingEvaluator enter operations."""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fi.evals.framework.evaluators.non_blocking import NonBlockingEvaluator


class _NonBlockingEvaluatorEnterMethods:
    __slots__ = ()

    def __enter__(self) -> "NonBlockingEvaluator":
        return self


    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.shutdown(wait=True)
