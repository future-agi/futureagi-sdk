from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

__version__ = "0.7.0"  # x-release-please-version

# Keep the release-please literal above; installed metadata (or the source
# declaration) remains authoritative for the public version and its legacy alias.
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

# The SDK owns fi.* except fi.alk, which belongs to agent-learning-kit.
# fi.simulate and fi.opt remain SDK clear-error stubs pointing into fi.alk.
# The released fi.platform.Client.simulation resource is separate and retained.
# extend_path lets fi.alk resolve on another sys.path entry, such as an editable checkout.
from pkgutil import extend_path

__path__ = extend_path(__path__, __name__)

# PEP 562 lazy attributes: `import fi` stays cheap, and every name exported before
# still resolves (`from fi import FutureAGIClient` works as it always did).
_LAZY = {
    "Client": "fi.platform",
    "AsyncClient": "fi.platform",
    "AnnotationQueue": "fi.queues",
    "AnnotationLabel": "fi.queues",
    "QueueDetail": "fi.queues",
    "DefaultQueue": "fi.queues",
    "DefaultQueueLabelError": "fi.queues",
    "QueueItem": "fi.queues",
    "QueueProgress": "fi.queues",
    "QueueAnalytics": "fi.queues",
    "QueueAgreement": "fi.queues",
    "Score": "fi.queues",
    "AddItemsResponse": "fi.queues",
    "ExportToDatasetResponse": "fi.queues",
    "ImportAnnotationsResponse": "fi.queues",
    "Annotation": "fi.annotations",
    "BulkAnnotationResponse": "fi.annotations",
    "FutureAGIClient": "fi.futureagi_client",
    "FutureAGIAPIError": "fi.futureagi_client",
    "PaymentRequiredError": "fi.errors",
    "LicenseRequiredError": "fi.errors",
    "ConsoleUnavailableError": "fi.errors",
    "AsyncFutureAGIClient": "fi.futureagi_async_client",
}

__all__ = ["__version__", "__versions__", *_LAZY]


def __getattr__(name: str):
    module_name = _LAZY.get(name)
    if module_name is None:
        raise AttributeError(f"module 'fi' has no attribute {name!r}")
    import importlib

    value = getattr(importlib.import_module(module_name), name)
    globals()[name] = value
    return value


def __dir__():
    return sorted(set(globals()) | set(_LAZY))
