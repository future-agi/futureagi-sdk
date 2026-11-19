"""CeleryBackend shutdown operations."""
from __future__ import annotations


class _CeleryBackendShutdownMethods:
    __slots__ = ()

    def shutdown(self, wait: bool = True) -> None:
        """
        Shutdown the Celery backend.

        Revokes only our tracked tasks, not the entire Celery queue.

        Args:
            wait: Whether to wait for pending tasks
        """
        from fi.evals.framework.backends.celery_backend import (logger)
        if self._app is not None:
            with self._lock:
                task_ids = list(self._async_results.keys())

            for task_id in task_ids:
                try:
                    self._app.control.revoke(task_id, terminate=not wait)
                except Exception:
                    pass

            with self._lock:
                self._handles.clear()
                self._async_results.clear()

            logger.info(f"Celery backend shut down, revoked {len(task_ids)} tasks")


    def get_queue_length(self) -> int:
        """
        Get the number of tasks waiting in the queue.

        Returns:
            Number of pending tasks in the queue
        """
        try:
            with self._app.pool.acquire(block=True) as conn:
                return conn.default_channel.client.llen(self.config.task_queue)
        except Exception:
            return -1


    def get_stats(self) -> dict:
        """
        Get Celery backend statistics.

        Returns:
            Dictionary with queue and worker stats
        """
        from fi.evals.framework.backends.celery_backend import (TaskStatus)
        stats = {
            "queue": self.config.task_queue,
            "broker": self.config.broker_url,
            "pending_tasks": len([
                h for h in self._handles.values()
                if h._status == TaskStatus.PENDING
            ]),
            "running_tasks": len([
                h for h in self._handles.values()
                if h._status == TaskStatus.RUNNING
            ]),
        }

        try:
            stats["queue_length"] = self.get_queue_length()
        except Exception:
            stats["queue_length"] = -1

        return stats
