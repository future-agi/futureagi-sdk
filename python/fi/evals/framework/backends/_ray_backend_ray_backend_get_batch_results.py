"""RayBackend get batch results operations."""
from __future__ import annotations

from fi.evals.framework.backends.ray_backend import (List, Optional, T, TaskHandle)


class _RayBackendGetBatchResultsMethods:
    __slots__ = ()

    def get_batch_results(
        self,
        handles: List[TaskHandle],
        timeout: Optional[float] = None,
    ) -> List[T]:
        """
        Get results for multiple tasks efficiently.

        Uses ray.get() on multiple object refs for better performance.

        Args:
            handles: List of task handles
            timeout: Maximum seconds to wait for all results

        Returns:
            List of results in same order as handles
        """
        from fi.evals.framework.backends.ray_backend import (
            List, Optional, T, TaskHandle, TaskStatus,
        )
        import ray

        timeout = timeout or self.config.timeout_seconds

        with self._lock:
            object_refs = [
                self._object_refs.get(h.task_id)
                for h in handles
            ]

        # Filter out None refs
        valid_refs = [(h, ref) for h, ref in zip(handles, object_refs) if ref is not None]

        if not valid_refs:
            return [None] * len(handles)

        try:
            refs_only = [ref for _, ref in valid_refs]
            results = ray.get(refs_only, timeout=timeout)

            # Update handles and build result list
            result_map = {}
            for (handle, _), result in zip(valid_refs, results):
                with self._lock:
                    if handle.task_id in self._handles:
                        self._handles[handle.task_id]._status = TaskStatus.COMPLETED
                        self._handles[handle.task_id]._result = result
                result_map[handle.task_id] = result

            return [result_map.get(h.task_id) for h in handles]

        except ray.exceptions.GetTimeoutError:
            for handle in handles:
                with self._lock:
                    if handle.task_id in self._handles:
                        if self._handles[handle.task_id]._status == TaskStatus.RUNNING:
                            self._handles[handle.task_id]._status = TaskStatus.TIMEOUT
            raise TimeoutError(f"Batch get timed out after {timeout}s")


    def shutdown(self, wait: bool = True) -> None:
        """
        Shutdown the Ray backend.

        Args:
            wait: Whether to wait for pending tasks
        """
        from fi.evals.framework.backends.ray_backend import (logger)
        import ray

        if self._initialized:
            if not wait:
                # Cancel all pending tasks
                with self._lock:
                    for task_id, object_ref in self._object_refs.items():
                        try:
                            ray.cancel(object_ref, force=True)
                        except Exception:
                            pass

            ray.shutdown()
            self._initialized = False
            logger.info("Ray backend shut down")


    def get_cluster_resources(self) -> dict:
        """
        Get available cluster resources.

        Returns:
            Dictionary with CPU, GPU, memory info
        """
        import ray

        resources = ray.cluster_resources()
        available = ray.available_resources()

        return {
            "total": resources,
            "available": available,
            "used": {
                k: resources.get(k, 0) - available.get(k, 0)
                for k in resources
            },
        }


    def get_stats(self) -> dict:
        """
        Get Ray backend statistics.

        Returns:
            Dictionary with task and resource stats
        """
        from fi.evals.framework.backends.ray_backend import (TaskStatus)
        with self._lock:
            pending = len([
                h for h in self._handles.values()
                if h._status == TaskStatus.PENDING
            ])
            running = len([
                h for h in self._handles.values()
                if h._status == TaskStatus.RUNNING
            ])
            completed = len([
                h for h in self._handles.values()
                if h._status == TaskStatus.COMPLETED
            ])
            failed = len([
                h for h in self._handles.values()
                if h._status == TaskStatus.FAILED
            ])

        stats = {
            "address": self.config.address,
            "pending_tasks": pending,
            "running_tasks": running,
            "completed_tasks": completed,
            "failed_tasks": failed,
            "total_tasks": len(self._handles),
        }

        try:
            resources = self.get_cluster_resources()
            stats["cluster_resources"] = resources
        except Exception:
            pass

        return stats
