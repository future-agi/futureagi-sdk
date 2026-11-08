"""Auto-instrumentation: the traceAI instrumentor for the detected framework, plus traceAI-openai /
traceAI-anthropic when their client library is installed (the two with truth rows; groq and
litellm are available by name only). A missing package is named (with its install line) in the run
header and by ``futureagi-py doctor``; it never fails the run. Neither does an installed one that fails
to load or to instrument under ``instrument='auto'`` (F2: traceAI-anthropic 0.1.10 cannot import with
anthropic 1.x): it is warned about once per process, named with both installed versions in the run
header, the run summary and on each trial's root span (``fi.experiment.tracing.failed_instrumentors``, so
an uploaded trace says why its provider spans are missing), and the run goes on without that
instrumentor's spans. **Named explicitly** (``instrument=[...]`` / ``--instrument``), a broken one is
refused with ``InstrumentorBrokenError``: the user asked for its spans by name. Before any request
(``refuse_broken_explicit``) each one named is imported and instrumented in a subprocess (``probe.py``), so an
add-on that imports but fails inside ``instrument()`` (traceAI-anthropic 0.1.10 with anthropic 1.x) is refused
before a dataset version or a server run is made; anything that still fails in this process is refused when
tracing starts. ``futureagi-py doctor`` runs the same probe on each installed one and reports a broken one as
broken, with its error.
Each instrumentor binds to one provider per process, so mixing ``trace=True`` and
``trace=<provider>`` runs is refused.

On Python 3.14+ ``trace=True`` refuses until TA-1 (fi-instrumentation-otel support).
"""

from __future__ import annotations

import importlib
import importlib.util
import sys
import threading
import warnings
from dataclasses import dataclass, field
from typing import Any, Optional, Sequence, Union

from fi.experiments.errors import InstrumentorBrokenError, TracingConflictError, TracingUnsupportedError, UsageError

# name -> (module, instrumentor class, pip package)
INSTRUMENTORS: dict[str, tuple[str, str, str]] = {
    "langchain": ("traceai_langchain", "LangChainInstrumentor", "traceAI-langchain"),
    "openai-agents": ("traceai_openai_agents", "OpenAIAgentsInstrumentor", "traceAI-openai-agents"),
    "openai": ("traceai_openai", "OpenAIInstrumentor", "traceAI-openai"),
    "anthropic": ("traceai_anthropic", "AnthropicInstrumentor", "traceAI-anthropic"),
    "groq": ("traceai_groq", "GroqInstrumentor", "traceAI-groq"),
    "litellm": ("traceai_litellm", "LiteLLMInstrumentor", "traceAI-litellm"),
}
# instrumentor name -> the futureagi extra that installs it (pyproject [tool.poetry.extras]; test_extras.py
# checks the two agree). traceAI-anthropic has no [anthropic] extra on purpose: its only release (0.1.10)
# cannot import with anthropic>=1.0 (F3, e2e FW-16bL-TA), and an extra would resolve the current anthropic and
# install a broken add-on. Its line names the package itself until a traceAI-anthropic release supports
# anthropic 1.x; so do groq and litellm, which have no truth rows.
EXTRAS = {"langchain": "langchain", "openai-agents": "openai-agents", "openai": "openai"}


def install_line(name: str) -> str:
    extra = EXTRAS.get(name)
    return f'pip install "futureagi[{extra}]"' if extra else f"pip install {INSTRUMENTORS[name][2]}"


# instrumentor name -> (the client library, its first major version no release of the add-on works with, why).
# With such a version installed, a missing add-on gets no install line: installing it gives a broken pair (L-SDK2c
# regression coverage; F3: traceAI-anthropic 0.1.10, its only release, fails inside instrument() on anthropic>=1.0).
NO_WORKING_RELEASE = {"anthropic": ("anthropic", 1, "traceAI-anthropic 0.1.10, its only release, fails inside "
                                                   "instrument() on anthropic>=1.0 (F3)")}


def missing_line(name: str) -> str:
    """The run header's words for an add-on that is not installed: what installs it, or, when the installed client
    library is a version no release of the add-on supports, that nothing can be installed yet."""
    pkg = INSTRUMENTORS[name][2]
    known = NO_WORKING_RELEASE.get(name)
    if known is not None:
        lib, major, why = known
        version = _version(lib)
        head = (version or "").split(".", 1)[0]
        if head.isdigit() and int(head) >= major:
            return (f"{pkg} missing, and no release of it works with {lib} {version} yet ({why}): there is nothing "
                    f"to install; {lib} calls are not traced")
    return f"{pkg} missing ({install_line(name)})"


# framework (adapter name) -> instrumentor name
FRAMEWORKS = {"langgraph": "langchain", "langchain": "langchain", "openai_agents": "openai-agents"}
# provider instrumentor -> the client library whose presence turns it on under "auto". Only the
# two with truth rows (FW-16a/b); groq and litellm stay available by name (instrument=[...]) but
# are not turned on automatically until a row checks their class names and spans.
PROVIDER_LIBRARIES = {"openai": "openai", "anthropic": "anthropic"}

_done: dict[str, Any] = {}  # instrumentor name -> the provider it is bound to (once per process)
_failed: dict[str, str] = {}  # instrumentor name -> why it failed to load (tried once per process)
_probed_ok: set[tuple[str, str]] = set()  # (module, class) the subprocess probe imported and instrumented
_lock = threading.Lock()


def _describe(provider: Any) -> str:
    from fi.experiments._tracing.routing import RoutingTracerProvider

    return "the experiments router (trace=True)" if isinstance(provider, RoutingTracerProvider) else (
        f"your provider {type(provider).__name__} (trace=<provider>)")


def _same_sink(bound: Any, new: Any) -> bool:
    """Every router routes by the same context variable, so any two routers are one sink."""
    from fi.experiments._tracing.routing import RoutingTracerProvider

    if isinstance(bound, RoutingTracerProvider) and isinstance(new, RoutingTracerProvider):
        return True
    return bound is new


def python_supported() -> bool:
    return sys.version_info < (3, 14)


def require_supported_python() -> None:
    if not python_supported():
        raise TracingUnsupportedError(
            "fi-instrumentation-otel does not support Python 3.14 yet (TA-1). Run with trace=False "
            "(CLI --no-trace), or use Python 3.10-3.13."
        )


def _installed(module: str) -> bool:
    try:
        return importlib.util.find_spec(module) is not None
    except (ImportError, ValueError):
        return False


@dataclass
class InstrumentPlan:
    enable: list[str] = field(default_factory=list)
    missing: list[tuple[str, str]] = field(default_factory=list)  # (name, pip package)
    failed: list[tuple[str, str]] = field(default_factory=list)  # (name, why): installed, failed to load
    explicit: bool = False  # instrument=[...] named them: a broken one is refused, not warned about

    def header(self) -> str:
        parts = [f"{INSTRUMENTORS[n][2]} on" for n in self.enable]
        parts += [missing_line(name) for name, _ in self.missing]
        parts += [failure_line(name, why) for name, why in self.failed]
        return " · ".join(parts) if parts else "no instrumentors"


# instrumentor name -> the distribution it instruments (to name both versions when it fails)
LIBRARIES = {"langchain": "langchain-core", "openai-agents": "openai-agents", "openai": "openai",
             "anthropic": "anthropic", "groq": "groq", "litellm": "litellm"}


def _version(dist: str) -> Optional[str]:
    try:
        import importlib.metadata

        return importlib.metadata.version(dist)
    except Exception:
        return None


def versions_and_fix(name: str) -> tuple[str, str]:
    """``(both installed versions, what fixes it)`` for an installed instrumentor that fails to load (L-SDK2a
    Regression coverage: reinstalling traceAI-anthropic 0.1.10 does nothing when it cannot load with anthropic 1.x)."""
    pkg, lib = INSTRUMENTORS[name][2], LIBRARIES.get(name, "")
    mine, theirs = _version(pkg), _version(lib) if lib else None
    versions = f"{pkg} {mine or '?'} with {lib} {theirs}" if theirs else f"{pkg} {mine or '?'}"
    fix = (f"reinstall a compatible version: {install_line(name)}" if name in EXTRAS
           else f"install a {pkg} release that supports {lib} {theirs}, or pin {lib} to a version {pkg} "
                f"{mine or '?'} supports"
           if theirs else f"reinstall it: {install_line(name)}")
    return versions, fix


def failure_line(name: str, why: str) -> str:
    """One line for an instrumentor that is installed but failed to load or instrument: both installed
    versions, what fixes it, and how to stop loading it."""
    versions, fix = versions_and_fix(name)
    return (f"{INSTRUMENTORS[name][2]} failed to load ({why}); its spans are off for this run. Installed: {versions}. "
            f"To trace it, {fix}; to stop loading it, pass --instrument / instrument=[...] without {name!r}")


def broken_explicit(name: str, why: str, *, before_requests: bool = True) -> InstrumentorBrokenError:
    """The refusal for a broken instrumentor named in ``instrument=[...]`` / ``--instrument``."""
    versions, fix = versions_and_fix(name)
    pkg = INSTRUMENTORS[name][2]
    when = "nothing was sent" if before_requests else "it stopped before its first trial"
    return InstrumentorBrokenError(
        f"instrument=[...] / --instrument names {name!r}, and {pkg} is installed but fails to load ({why}). You asked "
        f"for its spans by name, so the run is refused rather than run without them; {when}. Installed: "
        f"{versions}. To trace it, {fix}. To run without it, drop {name!r} from --instrument / instrument=[...] "
        "(instrument='auto' runs on without a broken instrumentor and says so)")


def refuse_broken_explicit(instrument: Any, trace: Any) -> None:
    """Before any request: each instrumentor an explicit ``instrument=[...]`` names that is installed must import
    and instrument, checked in a subprocess (``probe.py``; once per process for each one that passes). A broken
    one is refused; a missing one is left to the header."""
    if trace is False or not python_supported() or instrument in (True, False, "auto") or isinstance(instrument, str):
        return
    named = [n for n in dict.fromkeys(instrument or ()) if n in INSTRUMENTORS and _installed(INSTRUMENTORS[n][0])]
    with _lock:
        todo = {n: INSTRUMENTORS[n][:2] for n in named
                if n not in _failed and n not in _done and INSTRUMENTORS[n][:2] not in _probed_ok}
    if todo:
        from fi.experiments._tracing.probe import probe_imports

        probes = probe_imports(todo)
        with _lock:
            for n, probe in probes.items():
                if probe.ok:
                    _probed_ok.add(todo[n])
                else:
                    _failed.setdefault(n, probe.why())
    for name in named:
        if name in _failed:
            raise broken_explicit(name, _failed[name])


def _why(exc: BaseException) -> str:
    text = f"{type(exc).__name__}: {exc}"
    return text if len(text) <= 300 else text[:300] + "…"


def _warn_once(name: str, why: str) -> None:
    try:
        warnings.warn(f"fi.experiments: {failure_line(name, why)}", RuntimeWarning, stacklevel=4)
    except Warning:  # warnings turned into errors (-W error) must not stop the run either
        pass


def plan(framework: Optional[str], instrument: Union[str, Sequence[str], bool]) -> InstrumentPlan:
    out = InstrumentPlan()
    if instrument is False:
        return out
    if instrument is True or instrument == "auto":
        wanted: list[str] = []
        if framework in FRAMEWORKS:
            wanted.append(FRAMEWORKS[framework])
        for name, lib in PROVIDER_LIBRARIES.items():
            if name not in wanted and _installed(lib):
                wanted.append(name)
    elif isinstance(instrument, str):
        raise UsageError(f"instrument= takes 'auto', True/False or a list of names, got {instrument!r}")
    else:
        wanted = list(instrument)
        unknown = [n for n in wanted if n not in INSTRUMENTORS]
        if unknown:
            raise UsageError(f"unknown instrumentor(s) {unknown}; known: {', '.join(INSTRUMENTORS)}")
        out.explicit = True
    for name in wanted:
        module, _, pkg = INSTRUMENTORS[name]
        (out.enable if _installed(module) else out.missing).append(name if _installed(module) else (name, pkg))
    return out


def apply(tracer_provider: Any, the_plan: InstrumentPlan) -> list[str]:
    """Instrument each enabled package once per process against ``tracer_provider``.

    Instrumentors bind to a provider once, so a later run that traces somewhere else would lose
    its framework spans (and ``tool_called`` would score False). That mix is refused."""
    applied: list[str] = []
    with _lock:
        for name in list(the_plan.enable):
            if name in _failed:  # tried and failed earlier in this process: not retried, still reported
                if the_plan.explicit:
                    raise broken_explicit(name, _failed[name], before_requests=False)
                _mark_failed(the_plan, name, _failed[name])
                continue
            if name in _done:
                bound = _done[name]
                if not _same_sink(bound, tracer_provider):
                    raise TracingConflictError(
                        f"{INSTRUMENTORS[name][2]} is already bound to {_describe(bound)} in this process; "
                        f"instrumentors bind once, so a run traced to {_describe(tracer_provider)} would lose "
                        "its framework spans. Use one tracing mode per process: trace=True for every run, or "
                        "the same trace=<provider> for every run (instrument=False skips auto-instrumentation)."
                    )
                continue
            module, cls, _ = INSTRUMENTORS[name]
            try:
                instrumentor = getattr(importlib.import_module(module), cls)()
                instrumentor.instrument(tracer_provider=tracer_provider)
            except Exception as exc:  # F2: a broken instrumentor never stops an 'auto' run
                _failed[name] = _why(exc)
                if the_plan.explicit:  # named explicitly: refused
                    raise broken_explicit(name, _failed[name], before_requests=False) from exc
                _warn_once(name, _failed[name])
                _mark_failed(the_plan, name, _failed[name])
                continue
            _done[name] = tracer_provider
            applied.append(name)
    return applied


def _mark_failed(the_plan: InstrumentPlan, name: str, why: str) -> None:
    if name in the_plan.enable:
        the_plan.enable.remove(name)
    if all(n != name for n, _ in the_plan.failed):
        the_plan.failed.append((name, why))
