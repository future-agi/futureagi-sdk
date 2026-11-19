"""
Celery backend for distributed task execution.

Provides distributed task execution using Celery with Redis/RabbitMQ.
Requires: pip install 'celery[redis]'
"""

import logging
import threading
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, TypeVar

from .base import Backend, BackendConfig, TaskHandle, TaskStatus
from ._utils import CELERY

T = TypeVar("T")
logger = logging.getLogger(__name__)


@dataclass
class CeleryConfig(BackendConfig):
    """
    Configuration for Celery backend.

    Attributes:
        broker_url: Message broker URL (Redis/RabbitMQ)
        result_backend: Result backend URL
        task_queue: Queue name for tasks
        task_priority: Default task priority (0-9, higher = more priority)
        task_serializer: Serialization format ('json', 'pickle')
        result_serializer: Result serialization format
        task_acks_late: Acknowledge tasks after execution
        task_reject_on_worker_lost: Reject tasks if worker dies
        task_track_started: Track when tasks start executing
        worker_prefetch_multiplier: Number of tasks to prefetch
    """

    broker_url: str = "redis://localhost:6379/0"
    result_backend: str = "redis://localhost:6379/1"
    task_queue: str = "eval_tasks"
    task_priority: int = 0
    task_serializer: str = "cloudpickle"
    result_serializer: str = "cloudpickle"
    task_acks_late: bool = True
    task_reject_on_worker_lost: bool = True
    task_track_started: bool = True
    worker_prefetch_multiplier: int = 1


from ._celery_backend_celery_backend_setup_celery import _CeleryBackendSetupCeleryMethods
from ._celery_backend_celery_backend_shutdown import _CeleryBackendShutdownMethods

class CeleryBackend(_CeleryBackendSetupCeleryMethods, _CeleryBackendShutdownMethods, Backend):
    """
    Celery backend for distributed task execution.

    Uses Celery for distributed task execution across multiple workers.
    Integrates with existing Celery infrastructure (Redis, RabbitMQ).

    Example:
        config = CeleryConfig(
            broker_url="redis://localhost:6379/0",
            result_backend="redis://localhost:6379/1",
            task_queue="eval_tasks",
        )
        backend = CeleryBackend(config)

        handle = backend.submit(my_eval_func, args=(input_data,))
        result = backend.get_result(handle)

    Note:
        Requires Celery workers to be running to execute tasks.
        Start workers with: celery -A your_app worker -Q eval_tasks
    """

    name: str = "celery"

    def __init__(self, config: Optional[CeleryConfig] = None):
        """
        Initialize Celery backend.

        Args:
            config: Celery configuration

        Raises:
            ImportError: If celery is not installed
        """
        CELERY.require()

        self.config = config or CeleryConfig()
        self._app: Optional[Any] = None
        self._task: Optional[Any] = None
        self._handles: Dict[str, TaskHandle] = {}
        self._async_results: Dict[str, Any] = {}
        self._lock = threading.Lock()

        self._setup_celery()
