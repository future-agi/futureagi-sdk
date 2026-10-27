__version__ = "0.6.14"  # x-release-please-version

# Allow sibling `fi.*` packages (notably `fi.evals` shipped from the
# ai-evaluation repo) to extend this namespace when both are installed.
from pkgutil import extend_path

__path__ = extend_path(__path__, __name__)

from fi.annotations import Annotation, BulkAnnotationResponse
from fi.queues import (
    AddItemsResponse,
    AnnotationLabel,
    AnnotationQueue,
    ExportToDatasetResponse,
    ImportAnnotationsResponse,
    QueueAgreement,
    QueueAnalytics,
    QueueDetail,
    QueueItem,
    QueueProgress,
    Score,
)


def __getattr__(name):
    # `fi.Client` / `fi.AsyncClient` load fi.platform (httpx + the generated models) on first
    # use, so `import fi` stays as cheap as before for the existing modules.
    if name in ("Client", "AsyncClient"):
        from fi import platform

        return getattr(platform, name)
    raise AttributeError(f"module 'fi' has no attribute {name!r}")


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
    "Client",
    "AsyncClient",
]
