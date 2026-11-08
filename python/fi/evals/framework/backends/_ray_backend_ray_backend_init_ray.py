"""RayBackend init ray operations."""
from __future__ import annotations

from fi.evals.framework.backends.ray_backend import (
    Any, Callable, Dict, List, Optional, T, TaskHandle, TaskStatus,
)


class _RayBackendInitRayMethods:
    __slots__ = ()

    def _init_ray(self) -> None:
        """Initialize Ray runtime."""
        from fi.evals.framework.backends.ray_backend import (logger)
        import ray

        init_kwargs = {
            "ignore_reinit_error": self.config.ignore_reinit_error,
            "log_to_driver": self.config.log_to_driver,
        }

        if self.config.address:
            init_kwargs["address"] = self.config.address

        if self.config.namespace:
            init_kwargs["namespace"] = self.config.namespace

        if self.config.runtime_env:
            init_kwargs["runtime_env"] = self.config.runtime_env

        ray.init(**init_kwargs)
        self._initialized = True
        logger.info(f"Ray initialized with address={self.config.address}")


    def submit(
        self,
        fn: Callable[..., T],
        args: tuple = (),
        kwargs: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> TaskHandle[T]:
        """
        Submit a task to Ray.

        Args:
            fn: The function to execute
            args: Positional arguments
            kwargs: Keyword arguments
            context: Trace context (stored in metadata)

        Returns:
            TaskHandle to track the task
        """
        from fi.evals.framework.backends.ray_backend import (
            Any, Callable, Dict, Optional, T, TaskHandle, TaskStatus, logger, uuid,
        )
        import ray

        kwargs = kwargs or {}
        task_id = str(uuid.uuid4())

        # Create handle
        handle = TaskHandle(
            task_id=task_id,
            backend_name=self.name,
            metadata={
                "function": fn.__name__ if hasattr(fn, "__name__") else str(fn),
                "context": context,
                "num_cpus": self.config.num_cpus,
                "num_gpus": self.config.num_gpus,
            },
        )
        handle._status = TaskStatus.PENDING

        with self._lock:
            self._handles[task_id] = handle

        try:
            # Create Ray remote function with resources
            remote_options = {
                "max_retries": self.config.max_retries,
                "retry_exceptions": self.config.retry_exceptions,
            }

            if self.config.num_cpus is not None:
                remote_options["num_cpus"] = self.config.num_cpus

            if self.config.num_gpus > 0:
                remote_options["num_gpus"] = self.config.num_gpus

            if self.config.memory is not None:
                remote_options["memory"] = self.config.memory

            # Create remote function and submit
            remote_fn = ray.remote(**remote_options)(fn)
            object_ref = remote_fn.remote(*args, **kwargs)

            with self._lock:
                self._object_refs[task_id] = object_ref
                handle._status = TaskStatus.RUNNING

            logger.debug(f"Submitted task {task_id} to Ray")

        except Exception as e:
            handle._status = TaskStatus.FAILED
            handle._error = str(e)
            logger.error(f"Failed to submit task {task_id}: {e}")

        return handle


    def get_result(
        self,
        handle: TaskHandle[T],
        timeout: Optional[float] = None,
    ) -> T:
        """
        Get the result of a Ray task.

        Args:
            handle: The task handle from submit()
            timeout: Maximum seconds to wait

        Returns:
            The task result

        Raises:
            TimeoutError: If timeout exceeded
            Exception: If task failed
        """
        from fi.evals.framework.backends.ray_backend import (Optional, T, TaskHandle, TaskStatus)
        import ray

        timeout = timeout or self.config.timeout_seconds

        with self._lock:
            object_ref = self._object_refs.get(handle.task_id)

        if object_ref is None:
            raise ValueError(f"Unknown task: {handle.task_id}")

        try:
            result = ray.get(object_ref, timeout=timeout)

            with self._lock:
                if handle.task_id in self._handles:
                    self._handles[handle.task_id]._status = TaskStatus.COMPLETED
                    self._handles[handle.task_id]._result = result

            return result

        except ray.exceptions.GetTimeoutError:
            with self._lock:
                if handle.task_id in self._handles:
                    self._handles[handle.task_id]._status = TaskStatus.TIMEOUT
            raise TimeoutError(f"Task {handle.task_id} timed out after {timeout}s")

        except Exception as e:
            with self._lock:
                if handle.task_id in self._handles:
                    self._handles[handle.task_id]._status = TaskStatus.FAILED
                    self._handles[handle.task_id]._error = str(e)
            raise


    def get_status(self, handle: TaskHandle) -> TaskStatus:
        """
        Get current status of a Ray task.

        Args:
            handle: The task handle

        Returns:
            Current TaskStatus
        """
        from fi.evals.framework.backends.ray_backend import (TaskHandle, TaskStatus)
        import ray

        with self._lock:
            if handle.task_id in self._handles:
                cached_status = self._handles[handle.task_id]._status
                if cached_status in (TaskStatus.COMPLETED, TaskStatus.FAILED,
                                     TaskStatus.CANCELLED, TaskStatus.TIMEOUT):
                    return cached_status

            object_ref = self._object_refs.get(handle.task_id)

        if object_ref is None:
            return TaskStatus.FAILED

        # Check if task is ready (completed)
        ready, _ = ray.wait([object_ref], timeout=0)
        if ready:
            # Task is done, check if it succeeded
            try:
                ray.get(object_ref, timeout=0)
                return TaskStatus.COMPLETED
            except Exception:
                return TaskStatus.FAILED

        return TaskStatus.RUNNING


    def cancel(self, handle: TaskHandle) -> bool:
        """
        Cancel a Ray task.

        Args:
            handle: The task handle

        Returns:
            True if cancelled, False otherwise
        """
        from fi.evals.framework.backends.ray_backend import (TaskHandle, TaskStatus, logger)
        import ray

        with self._lock:
            object_ref = self._object_refs.get(handle.task_id)

        if object_ref is None:
            return False

        try:
            ray.cancel(object_ref, force=True)

            with self._lock:
                if handle.task_id in self._handles:
                    self._handles[handle.task_id]._status = TaskStatus.CANCELLED

            logger.debug(f"Cancelled task {handle.task_id}")
            return True

        except Exception as e:
            logger.warning(f"Failed to cancel task {handle.task_id}: {e}")
            return False


    def submit_batch(
        self,
        tasks: List[tuple],
    ) -> List[TaskHandle]:
        """
        Submit multiple tasks efficiently to Ray.

        Uses Ray's ability to schedule multiple tasks in parallel.

        Args:
            tasks: List of (function, args, kwargs, context) tuples

        Returns:
            List of TaskHandles
        """
        from fi.evals.framework.backends.ray_backend import (List, TaskHandle, TaskStatus, uuid)
        import ray

        handles = []
        refs_to_submit = []

        # Prepare all tasks
        for fn, args, kwargs, context in tasks:
            kwargs = kwargs or {}
            task_id = str(uuid.uuid4())

            handle = TaskHandle(
                task_id=task_id,
                backend_name=self.name,
                metadata={
                    "function": fn.__name__ if hasattr(fn, "__name__") else str(fn),
                    "context": context,
                },
            )
            handle._status = TaskStatus.PENDING
            handles.append(handle)

            with self._lock:
                self._handles[task_id] = handle

            # Create remote function
            remote_options = {
                "max_retries": self.config.max_retries,
            }
            if self.config.num_cpus is not None:
                remote_options["num_cpus"] = self.config.num_cpus
            if self.config.num_gpus > 0:
                remote_options["num_gpus"] = self.config.num_gpus

            remote_fn = ray.remote(**remote_options)(fn)
            refs_to_submit.append((task_id, remote_fn, args, kwargs))

        # Submit all tasks
        for task_id, remote_fn, args, kwargs in refs_to_submit:
            try:
                object_ref = remote_fn.remote(*args, **kwargs)
                with self._lock:
                    self._object_refs[task_id] = object_ref
                    self._handles[task_id]._status = TaskStatus.RUNNING
            except Exception as e:
                with self._lock:
                    self._handles[task_id]._status = TaskStatus.FAILED
                    self._handles[task_id]._error = str(e)

        return handles
