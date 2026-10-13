from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

try:
    __version__ = version("futureagi")
except PackageNotFoundError:
    pyproject = Path(__file__).resolve().parents[1] / "pyproject.toml"
    __version__ = "unknown"
    for line in pyproject.read_text().splitlines():
        stripped = line.strip()
        if stripped.startswith("version = "):
            __version__ = stripped.split("=", 1)[1].strip().strip('"').strip("'")
            break
__versions__ = __version__

# Allow sibling fi.* packages to extend this namespace.
from pkgutil import extend_path

__path__ = extend_path(__path__, __name__)

from fi.queues import (
    AnnotationQueue,
    AnnotationLabel,
    QueueDetail,
    QueueItem,
    QueueProgress,
    QueueAnalytics,
    QueueAgreement,
    Score,
    AddItemsResponse,
    ExportToDatasetResponse,
    ImportAnnotationsResponse,
)
from fi.annotations import Annotation, BulkAnnotationResponse
from fi.futureagi_client import FutureAGIAPIError, FutureAGIClient

__all__ = [
    "__version__",
    "__versions__",
    "AnnotationQueue",
    "AnnotationLabel",
    "QueueDetail",
    "QueueItem",
    "QueueProgress",
    "QueueAnalytics",
    "QueueAgreement",
    "Score",
    "AddItemsResponse",
    "ExportToDatasetResponse",
    "ImportAnnotationsResponse",
    "Annotation",
    "BulkAnnotationResponse",
    "FutureAGIClient",
    "FutureAGIAPIError",
]
