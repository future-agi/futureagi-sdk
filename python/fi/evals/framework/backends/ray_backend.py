"""
Ray backend for distributed computing.

Provides distributed task execution using Ray for batch evaluations.
Requires: pip install 'ray[default]'
"""

import logging
import threading
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, TypeVar

from .base import Backend, BackendConfig, TaskHandle, TaskStatus
from ._utils import RAY

T = TypeVar("T")
logger = logging.getLogger(__name__)


@dataclass
class RayConfig(BackendConfig):
    """
    Configuration for Ray backend.

    Attributes:
        address: Ray cluster address ('auto', 'local', or specific address)
        num_cpus: Default CPUs per task (None = auto)
        num_gpus: Default GPUs per task
        memory: Memory limit per task in bytes (None = auto)
        runtime_env: Runtime environment for tasks
        namespace: Ray namespace for isolation
        ignore_reinit_error: Ignore error if Ray already initialized
        log_to_driver: Send task logs to driver
        max_retries: Max retries for failed tasks
        retry_exceptions: Whether to retry on exceptions
    """

    address: str = "auto"
    num_cpus: Optional[float] = None
    num_gpus: float = 0.0
    memory: Optional[int] = None
    runtime_env: Optional[Dict[str, Any]] = None
    namespace: Optional[str] = None
    ignore_reinit_error: bool = True
    log_to_driver: bool = True
    max_retries: int = 3
    retry_exceptions: bool = True


from ._ray_backend_ray_backend_init_ray import _RayBackendInitRayMethods
from ._ray_backend_ray_backend_get_batch_results import _RayBackendGetBatchResultsMethods

class RayBackend(_RayBackendInitRayMethods, _RayBackendGetBatchResultsMethods, Backend):
    """
    Ray backend for distributed computing.

    Uses Ray for distributed task execution across a cluster.
    Optimized for batch processing with auto-scaling.

    Example:
        config = RayConfig(
            address="auto",  # Connect to existing cluster
            num_cpus=2.0,
            num_gpus=0.5,
        )
        backend = RayBackend(config)

        handle = backend.submit(my_eval_func, args=(input_data,))
        result = backend.get_result(handle)

        # Or batch submission
        handles = backend.submit_batch([
            (eval_func, (data1,), {}, None),
            (eval_func, (data2,), {}, None),
        ])

    Note:
        Ray will start a local cluster if none exists when address='auto'.
    """

    name: str = "ray"

    def __init__(self, config: Optional[RayConfig] = None):
        """
        Initialize Ray backend.

        Args:
            config: Ray configuration

        Raises:
            ImportError: If ray is not installed
        """
        RAY.require()

        self.config = config or RayConfig()
        self._initialized = False
        self._handles: Dict[str, TaskHandle] = {}
        self._object_refs: Dict[str, Any] = {}
        self._lock = threading.Lock()

        self._init_ray()
