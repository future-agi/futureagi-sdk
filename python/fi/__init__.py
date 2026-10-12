from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

try:
    __version__ = version("futureagi")
except PackageNotFoundError:
    # Source-tree fallback for environments that import `fi` before installing
    # the package metadata. Read the declared version so it cannot drift.
    pyproject = Path(__file__).resolve().parents[1] / "pyproject.toml"
    __version__ = "unknown"
    for line in pyproject.read_text().splitlines():
        stripped = line.strip()
        if stripped.startswith("version = "):
            __version__ = stripped.split("=", 1)[1].strip().strip('"').strip("'")
            break
__versions__ = __version__

# Allow sibling `fi.*` packages (notably `fi.evals` shipped from the
# ai-evaluation repo) to extend this namespace when both are installed.
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
