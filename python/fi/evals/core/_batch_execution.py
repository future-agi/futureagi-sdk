"""Waitable view of every execution returned by an asynchronous batch."""
from __future__ import annotations

from typing import Sequence

from ..execution import Execution


class BatchExecution(Execution):
    """An Execution whose result list follows submission order.

    ``executions`` holds individually waitable handles and ``ids`` exposes their
    resumable server IDs. The aggregate ``id`` is a display label, not a server
    ID; resume individual jobs with ``Evaluator.get_execution``. A batch only
    becomes terminal after every job completes or fails, even if one fails early.
    """

    def __init__(self, executions: Sequence[Execution]):
        if not executions:
            raise ValueError("A batch execution requires at least one execution")
        self.executions = tuple(executions)
        super().__init__(id="batch:" + ",".join(self.ids), kind="eval_batch")

    @property
    def ids(self) -> list[str]:
        return [execution.id for execution in self.executions]

    def refresh(self) -> BatchExecution:
        for execution in self.executions:
            if not execution.is_done():
                execution.refresh()
        failures = [execution for execution in self.executions if execution.status == "failed"]
        if all(execution.is_done() for execution in self.executions):
            self.status = "failed" if failures else "completed"
        elif all(execution.status == "pending" for execution in self.executions):
            self.status = "pending"
        else:
            self.status = "processing"
        self.result = [execution.result for execution in self.executions]
        self.error_message = "; ".join(
            f"{execution.id}: {execution.error_message or 'Evaluation failed'}"
            for execution in failures
        ) or None
        return self
