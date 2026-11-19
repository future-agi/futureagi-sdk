"""KubernetesBackend setup kubernetes operations."""
from __future__ import annotations

from fi.evals.framework.backends.kubernetes_backend import (
    Any, Callable, Dict, Optional, T, TaskHandle, TaskStatus,
)


class _KubernetesBackendSetupKubernetesMethods:
    __slots__ = ()

    def _setup_kubernetes(self) -> None:
        """Load kubeconfig and create API clients."""
        from fi.evals.framework.backends.kubernetes_backend import (logger)
        from kubernetes import client, config

        if self.config.in_cluster is True:
            config.load_incluster_config()
        elif self.config.in_cluster is False:
            config.load_kube_config(
                config_file=self.config.kubeconfig_path,
                context=self.config.context,
            )
        else:
            # Auto-detect: try in-cluster first, fall back to kubeconfig
            try:
                config.load_incluster_config()
            except config.ConfigException:
                config.load_kube_config(
                    config_file=self.config.kubeconfig_path,
                    context=self.config.context,
                )

        self._batch_api = client.BatchV1Api()
        self._core_api = client.CoreV1Api()
        logger.info(
            f"Kubernetes backend initialized (namespace={self.config.namespace})"
        )


    def _make_job_name(self, task_id: str) -> str:
        """
        Generate a DNS-1123 compliant Job name.

        The name is ``{job_prefix}{uuid_hex[:12]}``, lowercased and
        stripped of any characters that are not lowercase alphanumeric
        or hyphens. The total length is capped at 63 characters.
        """
        from fi.evals.framework.backends.kubernetes_backend import (re, uuid)
        short_id = uuid.uuid4().hex[:12]
        raw = f"{self.config.job_prefix}{short_id}"
        # DNS-1123: lowercase, alphanumeric and hyphens only
        name = re.sub(r"[^a-z0-9-]", "", raw.lower())
        # Must start/end with alphanumeric
        name = name.strip("-")
        return name[:63]


    def _build_job_manifest(
        self, job_name: str, serialized_payload: str
    ) -> Any:
        """Build a V1Job manifest for the given payload."""
        from fi.evals.framework.backends.kubernetes_backend import (
            Any, EVAL_PAYLOAD_ENV, RUNNER_COMMAND,
        )
        from kubernetes import client

        labels = {"app": "fi-eval", "job-name": job_name}
        if self.config.labels:
            labels.update(self.config.labels)

        annotations = self.config.annotations or {}

        # Resource requirements
        resources = client.V1ResourceRequirements(
            requests={
                "cpu": self.config.cpu_request,
                "memory": self.config.memory_request,
            },
            limits={
                "cpu": self.config.cpu_limit,
                "memory": self.config.memory_limit,
            },
        )

        container = client.V1Container(
            name="eval-runner",
            image=self.config.image,
            image_pull_policy=self.config.image_pull_policy,
            command=RUNNER_COMMAND,
            env=[
                client.V1EnvVar(
                    name=EVAL_PAYLOAD_ENV, value=serialized_payload
                ),
            ],
            resources=resources,
        )

        # Image pull secrets
        image_pull_secrets = None
        if self.config.image_pull_secrets:
            image_pull_secrets = [
                client.V1LocalObjectReference(name=s)
                for s in self.config.image_pull_secrets
            ]

        pod_spec = client.V1PodSpec(
            containers=[container],
            restart_policy="Never",
            service_account_name=self.config.service_account_name,
            image_pull_secrets=image_pull_secrets,
        )

        template = client.V1PodTemplateSpec(
            metadata=client.V1ObjectMeta(labels=labels, annotations=annotations),
            spec=pod_spec,
        )

        job_spec = client.V1JobSpec(
            template=template,
            backoff_limit=self.config.backoff_limit,
            active_deadline_seconds=self.config.active_deadline_seconds,
            ttl_seconds_after_finished=self.config.ttl_seconds_after_finished,
        )

        job = client.V1Job(
            api_version="batch/v1",
            kind="Job",
            metadata=client.V1ObjectMeta(
                name=job_name,
                namespace=self.config.namespace,
                labels=labels,
                annotations=annotations,
            ),
            spec=job_spec,
        )

        return job


    def submit(
        self,
        fn: Callable[..., T],
        args: tuple = (),
        kwargs: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> TaskHandle[T]:
        """
        Submit a task as a Kubernetes Job.

        The function and its arguments are serialized with cloudpickle,
        base64-encoded, and passed to the container as an env var.

        Args:
            fn: The function to execute
            args: Positional arguments
            kwargs: Keyword arguments
            context: Trace context (stored in metadata)

        Returns:
            TaskHandle to track the task
        """
        from fi.evals.framework.backends.kubernetes_backend import (
            Any, Callable, Dict, Optional, T, TaskHandle, TaskStatus, logger, serialize_task, uuid,
        )
        kwargs = kwargs or {}
        task_id = str(uuid.uuid4())
        job_name = self._make_job_name(task_id)

        handle = TaskHandle(
            task_id=task_id,
            backend_name=self.name,
            metadata={
                "function": fn.__name__ if hasattr(fn, "__name__") else str(fn),
                "context": context,
                "job_name": job_name,
                "namespace": self.config.namespace,
            },
        )
        handle._status = TaskStatus.PENDING

        with self._lock:
            self._handles[task_id] = handle
            self._job_names[task_id] = job_name

        try:
            serialized = serialize_task(fn, args, kwargs)

            # Build and create the Job
            job_manifest = self._build_job_manifest(job_name, serialized)
            self._batch_api.create_namespaced_job(
                namespace=self.config.namespace,
                body=job_manifest,
            )

            with self._lock:
                handle._status = TaskStatus.RUNNING

            logger.debug(
                f"Submitted task {task_id} as Job {job_name} "
                f"in namespace {self.config.namespace}"
            )

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
        Get the result of a Kubernetes Job by polling until completion.

        Args:
            handle: The task handle from submit()
            timeout: Maximum seconds to wait

        Returns:
            The task result

        Raises:
            TimeoutError: If timeout exceeded
            RuntimeError: If the Job failed
            ValueError: If task is unknown
        """
        from fi.evals.framework.backends.kubernetes_backend import (
            Optional, T, TaskHandle, TaskStatus, time,
        )
        timeout = timeout or self.config.timeout_seconds

        with self._lock:
            job_name = self._job_names.get(handle.task_id)

        if job_name is None:
            raise ValueError(f"Unknown task: {handle.task_id}")

        deadline = time.monotonic() + timeout
        while True:
            status = self._poll_job_status(job_name)

            if status == TaskStatus.COMPLETED:
                result = self._read_job_result(job_name)
                with self._lock:
                    if handle.task_id in self._handles:
                        self._handles[handle.task_id]._status = TaskStatus.COMPLETED
                        self._handles[handle.task_id]._result = result
                return result

            if status == TaskStatus.FAILED:
                error_msg = f"Job {job_name} failed"
                # Try to read logs for error details
                try:
                    self._read_job_result(job_name)
                except RuntimeError as re_err:
                    error_msg = str(re_err)
                except Exception:
                    pass
                with self._lock:
                    if handle.task_id in self._handles:
                        self._handles[handle.task_id]._status = TaskStatus.FAILED
                        self._handles[handle.task_id]._error = error_msg
                raise RuntimeError(error_msg)

            if time.monotonic() > deadline:
                with self._lock:
                    if handle.task_id in self._handles:
                        self._handles[handle.task_id]._status = TaskStatus.TIMEOUT
                raise TimeoutError(
                    f"Task {handle.task_id} timed out after {timeout}s"
                )

            time.sleep(self.config.poll_interval)


    def _poll_job_status(self, job_name: str) -> TaskStatus:
        """Poll the K8s API for the Job's current status."""
        from fi.evals.framework.backends.kubernetes_backend import (TaskStatus)
        job = self._batch_api.read_namespaced_job_status(
            name=job_name,
            namespace=self.config.namespace,
        )
        return self._map_job_status(job.status)
