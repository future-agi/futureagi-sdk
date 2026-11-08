"""KubernetesBackend map job status operations."""
from __future__ import annotations

from fi.evals.framework.backends.kubernetes_backend import (Any, Dict, List, TaskHandle, TaskStatus)


class _KubernetesBackendMapJobStatusMethods:
    __slots__ = ()

    def _map_job_status(self, status: Any) -> TaskStatus:
        """Map a V1JobStatus object to TaskStatus."""
        from fi.evals.framework.backends.kubernetes_backend import (Any, TaskStatus)
        # Check conditions first (Complete / Failed)
        if status.conditions:
            for condition in status.conditions:
                if condition.type == "Complete" and condition.status == "True":
                    return TaskStatus.COMPLETED
                if condition.type == "Failed" and condition.status == "True":
                    return TaskStatus.FAILED

        # If pods are still active, the job is running
        if status.active and status.active > 0:
            return TaskStatus.RUNNING

        # Succeeded / failed counts
        if status.succeeded and status.succeeded > 0:
            return TaskStatus.COMPLETED
        if status.failed and status.failed > 0:
            return TaskStatus.FAILED

        return TaskStatus.PENDING


    def _read_job_result(self, job_name: str) -> Any:
        """
        Read the result from the Job's pod logs.

        Uses :func:`_container.parse_result_from_logs` to extract the
        JSON result printed by the runner script.
        """
        from fi.evals.framework.backends.kubernetes_backend import (Any, parse_result_from_logs)
        from kubernetes.client.rest import ApiException

        # Find pods belonging to this Job
        label_selector = f"job-name={job_name}"
        pods = self._core_api.list_namespaced_pod(
            namespace=self.config.namespace,
            label_selector=label_selector,
        )

        if not pods.items:
            raise RuntimeError(f"No pods found for Job {job_name}")

        pod_name = pods.items[0].metadata.name

        log_kwargs = {"name": pod_name, "namespace": self.config.namespace}
        if self.config.log_tail_lines is not None:
            log_kwargs["tail_lines"] = self.config.log_tail_lines

        try:
            # _preload_content=False prevents the K8s client from
            # auto-deserializing JSON log lines into Python objects
            resp = self._core_api.read_namespaced_pod_log(
                **log_kwargs, _preload_content=False
            )
            logs = resp.data.decode("utf-8")
        except ApiException as e:
            raise RuntimeError(f"Failed to read logs for pod {pod_name}: {e}")

        return parse_result_from_logs(logs)


    def get_status(self, handle: TaskHandle) -> TaskStatus:
        """
        Get current status of a Kubernetes Job.

        Returns cached terminal status if available, otherwise polls K8s.

        Args:
            handle: The task handle

        Returns:
            Current TaskStatus
        """
        from fi.evals.framework.backends.kubernetes_backend import (TaskHandle, TaskStatus)
        with self._lock:
            if handle.task_id in self._handles:
                cached = self._handles[handle.task_id]._status
                if cached in (
                    TaskStatus.COMPLETED,
                    TaskStatus.FAILED,
                    TaskStatus.CANCELLED,
                    TaskStatus.TIMEOUT,
                ):
                    return cached

            job_name = self._job_names.get(handle.task_id)

        if job_name is None:
            return TaskStatus.FAILED

        try:
            status = self._poll_job_status(job_name)
            with self._lock:
                if handle.task_id in self._handles:
                    self._handles[handle.task_id]._status = status
            return status
        except Exception:
            return TaskStatus.FAILED


    def cancel(self, handle: TaskHandle) -> bool:
        """
        Cancel a Kubernetes Job.

        Deletes the Job with foreground propagation policy so
        associated pods are terminated immediately.

        Args:
            handle: The task handle

        Returns:
            True if cancelled, False otherwise
        """
        from fi.evals.framework.backends.kubernetes_backend import (TaskHandle, TaskStatus, logger)
        from kubernetes.client.rest import ApiException

        with self._lock:
            job_name = self._job_names.get(handle.task_id)

        if job_name is None:
            return False

        try:
            from kubernetes import client

            self._batch_api.delete_namespaced_job(
                name=job_name,
                namespace=self.config.namespace,
                body=client.V1DeleteOptions(
                    propagation_policy="Foreground",
                ),
            )

            with self._lock:
                if handle.task_id in self._handles:
                    self._handles[handle.task_id]._status = TaskStatus.CANCELLED

            logger.debug(f"Cancelled Job {job_name}")
            return True

        except ApiException as e:
            logger.warning(f"Failed to cancel Job {job_name}: {e}")
            return False


    def submit_batch(
        self,
        tasks: List[tuple],
    ) -> List[TaskHandle]:
        """
        Submit multiple tasks as Kubernetes Jobs.

        Submits tasks sequentially (each creates an independent K8s Job).

        Args:
            tasks: List of (function, args, kwargs, context) tuples

        Returns:
            List of TaskHandles
        """
        from fi.evals.framework.backends.kubernetes_backend import (List, TaskHandle)
        handles = []
        for fn, args, kwargs, context in tasks:
            handle = self.submit(fn, args, kwargs or {}, context)
            handles.append(handle)
        return handles


    def shutdown(self, wait: bool = True) -> None:
        """
        Shutdown the Kubernetes backend.

        Args:
            wait: If False, cancels all pending/running tasks
        """
        from fi.evals.framework.backends.kubernetes_backend import (TaskHandle, TaskStatus, logger)
        if not wait:
            with self._lock:
                pending_tasks = [
                    (tid, jn)
                    for tid, jn in self._job_names.items()
                    if tid in self._handles
                    and self._handles[tid]._status
                    in (TaskStatus.PENDING, TaskStatus.RUNNING)
                ]

            for task_id, _job_name in pending_tasks:
                try:
                    handle = TaskHandle(task_id=task_id, backend_name=self.name)
                    self.cancel(handle)
                except Exception:
                    pass

        logger.info("Kubernetes backend shut down")


    def get_job_logs(self, handle: TaskHandle) -> Dict[str, str]:
        """
        Get raw logs for all pods of a Job.

        Args:
            handle: The task handle

        Returns:
            Dict mapping pod name to log text

        Raises:
            ValueError: If task is unknown
        """
        from fi.evals.framework.backends.kubernetes_backend import (Dict, TaskHandle)
        from kubernetes.client.rest import ApiException

        with self._lock:
            job_name = self._job_names.get(handle.task_id)

        if job_name is None:
            raise ValueError(f"Unknown task: {handle.task_id}")

        label_selector = f"job-name={job_name}"
        pods = self._core_api.list_namespaced_pod(
            namespace=self.config.namespace,
            label_selector=label_selector,
        )

        result: Dict[str, str] = {}
        for pod in pods.items:
            pod_name = pod.metadata.name
            try:
                logs = self._core_api.read_namespaced_pod_log(
                    name=pod_name,
                    namespace=self.config.namespace,
                )
                result[pod_name] = logs
            except ApiException as e:
                result[pod_name] = f"<error reading logs: {e}>"

        return result


    def get_stats(self) -> dict:
        """
        Get Kubernetes backend statistics.

        Returns:
            Dictionary with task counts and config info
        """
        from fi.evals.framework.backends.kubernetes_backend import (TaskStatus)
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

        return {
            "namespace": self.config.namespace,
            "image": self.config.image,
            "pending_tasks": pending,
            "running_tasks": running,
            "completed_tasks": completed,
            "failed_tasks": failed,
            "total_tasks": len(self._handles),
        }
