"""
Kubernetes backend for cloud-native job execution.

Provides distributed task execution using Kubernetes Jobs.
Each task is submitted as a K8s Job that runs a container which
deserializes and executes the function, then writes JSON results to stdout.

Requires: pip install kubernetes cloudpickle
"""

import logging
import re
import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, TypeVar

from .base import Backend, BackendConfig, TaskHandle, TaskStatus
from ._utils import KUBERNETES
from ._container import (
    DEFAULT_IMAGE,
    EVAL_PAYLOAD_ENV,
    RUNNER_COMMAND,
    RUNNER_SCRIPT,
    parse_result_from_logs,
    serialize_task,
)

T = TypeVar("T")
logger = logging.getLogger(__name__)


@dataclass
class KubernetesConfig(BackendConfig):
    """
    Configuration for Kubernetes backend.

    A pre-built eval runner Dockerfile is provided at
    ``fi/evals/framework/backends/Dockerfile.eval-runner``.
    Build it with::

        docker build -f Dockerfile.eval-runner -t fi-eval-runner:latest .

    Then pass ``image="fi-eval-runner:latest"`` (or your registry path).

    Attributes:
        namespace: Kubernetes namespace for Jobs
        image: Container image (must have cloudpickle installed)
        cpu_request: CPU request per Job pod
        cpu_limit: CPU limit per Job pod
        memory_request: Memory request per Job pod
        memory_limit: Memory limit per Job pod
        job_prefix: Prefix for Job names (DNS-1123 compliant)
        backoff_limit: Number of retries for failed Jobs
        active_deadline_seconds: Maximum seconds a Job may run
        ttl_seconds_after_finished: Seconds to keep finished Jobs before cleanup
        service_account_name: K8s service account for the Job pod
        image_pull_secrets: Names of image pull secrets
        image_pull_policy: Image pull policy (Always, IfNotPresent, Never)
        kubeconfig_path: Path to kubeconfig file (None = auto-detect)
        context: Kubeconfig context to use (None = current context)
        in_cluster: Force in-cluster config loading
        labels: Extra labels to apply to Jobs
        annotations: Extra annotations to apply to Jobs
        poll_interval: Seconds between status polls
        log_tail_lines: Number of log lines to tail (None = all)
    """

    namespace: str = "default"
    image: str = "fi-eval-runner:latest"
    cpu_request: str = "500m"
    cpu_limit: str = "1"
    memory_request: str = "512Mi"
    memory_limit: str = "2Gi"
    job_prefix: str = "eval-"
    backoff_limit: int = 0
    active_deadline_seconds: int = 600
    ttl_seconds_after_finished: int = 300
    service_account_name: Optional[str] = None
    image_pull_secrets: Optional[List[str]] = None
    image_pull_policy: str = "IfNotPresent"
    kubeconfig_path: Optional[str] = None
    context: Optional[str] = None
    in_cluster: Optional[bool] = None
    labels: Optional[Dict[str, str]] = None
    annotations: Optional[Dict[str, str]] = None
    poll_interval: float = 2.0
    log_tail_lines: Optional[int] = None


from ._kubernetes_backend_kubernetes_backend_setup_kubernetes import _KubernetesBackendSetupKubernetesMethods
from ._kubernetes_backend_kubernetes_backend_map_job_status import _KubernetesBackendMapJobStatusMethods

class KubernetesBackend(
    _KubernetesBackendSetupKubernetesMethods,
    _KubernetesBackendMapJobStatusMethods,
    Backend,
):
    """
    Kubernetes backend for cloud-native job execution.

    Submits evaluation tasks as Kubernetes Jobs. Each task is serialized
    with cloudpickle, base64-encoded, and passed to the container as an env var.
    Results are read from pod logs as JSON.

    Example:
        config = KubernetesConfig(
            namespace="evaluations",
            image="my-eval-image:latest",
            cpu_request="1",
            memory_limit="4Gi",
        )
        backend = KubernetesBackend(config)

        handle = backend.submit(my_eval_func, args=(input_data,))
        result = backend.get_result(handle)

        # Or batch submission
        handles = backend.submit_batch([
            (eval_func, (data1,), {}, None),
            (eval_func, (data2,), {}, None),
        ])

    Note:
        Requires a running Kubernetes cluster. Uses in-cluster config
        when running inside a pod, or falls back to kubeconfig for local dev.
    """

    name: str = "kubernetes"

    def __init__(self, config: Optional[KubernetesConfig] = None):
        """
        Initialize Kubernetes backend.

        Args:
            config: Kubernetes configuration

        Raises:
            ImportError: If kubernetes package is not installed
        """
        KUBERNETES.require()

        self.config = config or KubernetesConfig()
        self._batch_api: Optional[Any] = None
        self._core_api: Optional[Any] = None
        self._handles: Dict[str, TaskHandle] = {}
        self._job_names: Dict[str, str] = {}
        self._lock = threading.Lock()

        self._setup_kubernetes()
