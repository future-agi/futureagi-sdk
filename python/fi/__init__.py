__version__ = "0.0.1"

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

__all__ = [
    "__version__",
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
]
