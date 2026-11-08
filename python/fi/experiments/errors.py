"""Errors raised by ``fi.experiments``.

Every error class subclasses the SDK's public tree, ``fi.errors`` (root ``FutureAGIError``, which is
``SDKException``), and carries a stable ``get_error_code()`` that maps 1:1 to a CLI exit code and
to the ``--json`` error object. Where one exists, a class also subclasses the matching
``fi.errors`` class, so ``except fi.errors.TransportError`` / ``MissingExtraError`` /
``AuthError`` catch the experiments errors too.

This module imports nothing from ``fi.utils`` or ``fi.api``.
"""

from __future__ import annotations

from typing import Any, Iterable, Optional, Sequence

from fi._credentials import CredentialsMissingError
from fi.errors import AuthError, FutureAGIError, TransportError, describe_transport_error, transport_failure_kind
from fi.errors import MissingExtraError as _MissingExtraError

# CLI exit codes:
# 0 ok · 1 the gate failed (--fail-under / --max-error-rate) · 2 usage error · 3 setup / server
# refused / missing extra · 4 interrupted · 5 the run completed with errors under CI=true.
EXIT_OK, EXIT_GATE, EXIT_USAGE, EXIT_SETUP, EXIT_INTERRUPTED, EXIT_CI_ERRORS = 0, 1, 2, 3, 4, 5


class ExperimentError(FutureAGIError):
    code = "EXPERIMENT_ERROR"
    exit_code = EXIT_SETUP

    def __init__(self, message: Optional[str] = None, cause: Optional[Exception] = None) -> None:
        super().__init__(message, cause)

    def get_message(self) -> str:
        return self.custom_message or self.__class__.__doc__ or self.code

    def get_error_code(self) -> str:
        return self.code

    def to_json(self) -> dict[str, Any]:
        return {"code": self.get_error_code(), "message": str(self), "exit_code": self.exit_code}


class TraceExportWarning(UserWarning):
    """Collector delivery was not confirmed for some spans from an uploaded run."""


class TraceExportError(ExperimentError):
    """The SDK's OTLP exporter failed; run items may already be stored (CLI exit 3)."""

    code = "TRACE_EXPORT_FAILED"

    def __init__(self, run_id: str, endpoint: str, status_code: Optional[int], reason: str) -> None:
        self.run_id, self.endpoint, self.status_code = run_id, endpoint, status_code
        self.reason = reason
        detail = f"HTTP {status_code}" if status_code is not None else reason
        super().__init__(
            f"Run {run_id}: trace export to {endpoint} failed ({detail}); some spans were not confirmed as uploaded. "
            "Run items may already be stored. Check the collector route and connectivity. "
            "For future runs without tracing, set trace=False (CLI --no-trace). "
            "Spans are not journaled: resume does not re-export lost spans."
        )

    def to_json(self) -> dict[str, Any]:
        return {**super().to_json(), "run_id": self.run_id, "endpoint": self.endpoint,
                "status_code": self.status_code, "reason": self.reason}


class UsageError(ExperimentError):
    """The arguments do not describe a valid run."""

    code = "USAGE_ERROR"
    exit_code = EXIT_USAGE


class AmbiguousInputError(UsageError):
    code = "AMBIGUOUS_INPUT"

    def __init__(self, columns: Sequence[str]) -> None:
        self.columns: list[str] = list(columns)
        cols = ", ".join(self.columns)
        super().__init__(
            f"{len(self.columns)} input columns: {cols}. Pass input='{self.columns[0]}' "
            f"(CLI: --input-column {self.columns[0]})."
        )


class AmbiguousDatasetError(UsageError):
    code = "AMBIGUOUS_DATASET"

    def __init__(self, name: str, candidate_ids: Iterable[str]) -> None:
        self.candidate_ids: list[str] = list(candidate_ids)
        super().__init__(
            f"{len(self.candidate_ids)} datasets are named {name!r}: {', '.join(self.candidate_ids)}. "
            "Pass the dataset id instead."
        )


class DatasetNotFoundError(UsageError):
    code = "DATASET_NOT_FOUND"


class UnknownTargetError(UsageError):
    code = "UNKNOWN_TARGET"

    def __init__(self, target: str, kinds: Sequence[str]) -> None:
        self.target = target
        self.kinds: list[str] = list(kinds)
        listed = "\n".join(f"  - {k}" for k in self.kinds)
        super().__init__(f"{target!r} is not a TARGET this version can run. TARGET is one of:\n{listed}")


class SharedStatefulTaskError(UsageError):
    code = "SHARED_STATEFUL_TASK"


class UnmappedEvalKeysError(UsageError):
    code = "UNMAPPED_EVAL_KEYS"

    def __init__(self, template: str, keys: Sequence[str], fix_line: str) -> None:
        self.template = template
        self.keys: list[str] = list(keys)
        self.fix_line = fix_line
        super().__init__(
            f"{template!r} needs {', '.join(self.keys)}, which no column provides. Add:\n  {fix_line}"
        )


class JudgeModelRequiredError(UsageError):
    code = "JUDGE_MODEL_REQUIRED"

    def __init__(self, template: str) -> None:
        self.template = template
        super().__init__(
            f"`{template}` is an LLM-judge template; add `--judge-model M` or set FI_JUDGE_MODEL "
            "(Python: judge_model=...)."
        )


class UndeclaredScoreNameError(UsageError):
    code = "UNDECLARED_SCORE_NAME"


class PlanTooLargeError(UsageError):
    code = "PLAN_TOO_LARGE"
    MAX_ITEMS = 10_000

    def __init__(self, items: int) -> None:
        super().__init__(
            f"{items} trials (rows x trials) is above the server limit of {self.MAX_ITEMS}. "
            "Use --limit N, --rows sample:N, or split the dataset into several runs."
        )


class UnpricedModelError(ExperimentError):
    code = "UNPRICED_MODEL"

    def __init__(self, models: Sequence[str]) -> None:
        self.models: list[str] = list(models)
        names = ", ".join(self.models)
        super().__init__(
            f"max_cost_usd is set but no price is known for {names}. Pass "
            f"limits=Limits(prices={{{self.models[0]!r}: (USD_PER_1M_IN, USD_PER_1M_OUT)}}) "
            f"(CLI: --price {self.models[0]}=IN,OUT)."
        )


class ModelRetiredError(ExperimentError):
    """A provider answered that the model was retired (OpenAI's 404 ``model_not_found`` "has been deprecated",
    Groq's ``model_decommissioned``). The message names the model and quotes the provider; see
    ``fi.experiments._provider_errors``.

    Internal, not in ``__all__``: no run ends with it and no CLI exit code comes from it.
    ``judge()`` turns it into each row's error score, a trial keeps the provider's own exception type with the same
    sentence first in its message, and the run's closing lines say it once per evaluator and per error type. A run
    on a retired model ends as any run with errors does (exit 0, or 5 under ``CI=true``)."""

    code = "MODEL_RETIRED"

    def __init__(self, model: Optional[str], *, status: int, provider_code: Optional[str] = None,
                 provider_message: str = "", provider: Optional[str] = None) -> None:
        from fi.experiments._provider_errors import Retirement, describe

        self.model = model
        self.status = status
        self.provider_code = provider_code
        self.provider_message = provider_message
        self.provider = provider
        super().__init__(describe(Retirement(status, provider_code, provider_message, model), provider))


class CapNotEnforceableError(UsageError):
    code = "CAP_NOT_ENFORCEABLE"


class NotSupportedByServerError(ExperimentError):
    code = "NOT_SUPPORTED_BY_SERVER"

    LOCAL_HINT = "Run with upload=False (CLI --no-upload) to score locally."

    def __init__(self, srv: str, what: str = "", *, hint: Optional[str] = LOCAL_HINT) -> None:
        self.srv = srv
        self.what = what
        detail = f" {what}" if what else ""
        tail = f" {hint}" if hint else ""
        super().__init__(f"This needs server feature {srv}, which the server does not provide yet.{detail}{tail}")


class HostedEvalNeedsServerError(ExperimentError, AuthError):
    code = "HOSTED_EVAL_NEEDS_SERVER"

    def __init__(self, templates: Sequence[str]) -> None:
        self.templates: list[str] = list(templates)
        super().__init__(
            f"{', '.join(self.templates)} run on the hosted eval API, which needs keys. Set "
            "FI_API_KEY and FI_SECRET_KEY, or use local evaluators only."
        )


class ServerUnreachableError(ExperimentError, TransportError):
    """The platform at the base URL did not answer (connection refused, DNS, timeout, reset). Exit 3.

    ``kind`` is :func:`fi.errors.transport_failure_kind`'s: only ``"connect"`` (nothing was sent)
    says "cannot reach ... check FI_BASE_URL"; a timeout or a reset reached the server, and says so
   ."""

    code = "SERVER_UNREACHABLE"

    def __init__(self, base_url: str, reason: str, kind: str = "connect") -> None:
        self.base_url = base_url
        self.reason = reason
        self.kind = kind
        if kind == "timeout":
            message = f"{base_url} did not answer in time ({reason}); retry later, or run with local evaluators only"
        elif kind == "connection":
            message = (f"the connection to {base_url} broke before a response ({reason}); retry, or run "
                       "with local evaluators only")
        else:
            message = f"cannot reach {base_url} ({reason}); check FI_BASE_URL, or run with local evaluators only"
        super().__init__(message)


def server_unreachable(exc: BaseException, base_url: Optional[str] = None) -> ServerUnreachableError:
    """Turn an ``httpx.TransportError`` into :class:`ServerUnreachableError` (no httpx import here)."""
    url, reason = describe_transport_error(exc, base_url)
    err = ServerUnreachableError(url, reason, transport_failure_kind(exc))
    err.__cause__ = exc
    return err


class MissingExtraError(ExperimentError, _MissingExtraError):
    code = "MISSING_EXTRA"

    def __init__(self, extra: str, module: str) -> None:
        super().__init__(f'{module} is not installed. Run: pip install "futureagi[{extra}]"')
        self.extra = extra
        self.module = module
        self.install_hint: Optional[str] = f'pip install "futureagi[{extra}]"'


class RunLockedError(ExperimentError):
    code = "RUN_LOCKED"


class JournalError(ExperimentError):
    code = "JOURNAL_ERROR"


class TracingConflictError(UsageError):
    code = "TRACING_CONFLICT"


class TracingUnsupportedError(ExperimentError):
    code = "TRACING_UNSUPPORTED"


class InstrumentorBrokenError(ExperimentError):
    """An instrumentor named explicitly (``instrument=[...]`` / ``--instrument``) is installed but fails to load
   : refused before any request, since the user asked for its spans by name."""

    code = "INSTRUMENTOR_BROKEN"


class NoRunPageError(ExperimentError):
    """``ExperimentResult.open()`` with no page to open: ``url`` is None, and the message says why (FN-05)."""

    code = "NO_RUN_PAGE"


class RunInterrupted(KeyboardInterrupt):
    """Ctrl-C during a run, raised after the journal is flushed. Never swallowed."""

    code = "INTERRUPTED"
    exit_code = EXIT_INTERRUPTED

    def __init__(self, run_id: str, done: int, total: int) -> None:
        self.run_id = run_id
        self.done = done
        self.total = total
        super().__init__(f"run {run_id} interrupted after {done}/{total} trials; journal flushed")


__all__ = [
    "CredentialsMissingError",
    "ExperimentError",
    "UsageError",
    "AmbiguousInputError",
    "AmbiguousDatasetError",
    "DatasetNotFoundError",
    "UnknownTargetError",
    "SharedStatefulTaskError",
    "UnmappedEvalKeysError",
    "JudgeModelRequiredError",
    "UndeclaredScoreNameError",
    "PlanTooLargeError",
    "UnpricedModelError",
    "CapNotEnforceableError",
    "NotSupportedByServerError",
    "HostedEvalNeedsServerError",
    "ServerUnreachableError",
    "MissingExtraError",
    "RunLockedError",
    "JournalError",
    "TracingConflictError",
    "TracingUnsupportedError",
    "RunInterrupted",
]
