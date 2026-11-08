"""F2 (reports/WAVE1.md section, e2e FW-16bL-TA implementation): an installed instrumentor that fails to import or to
instrument never stops the run. It is warned about once per process, named with both installed versions
and the way to switch it off in the run header and the run summary, recorded in
``result.metadata["tracing"]`` and on each trial's root span (so an uploaded trace says why), and the
run goes on traced by everything else. No network, no model, no server."""

import sys
import types
import warnings
from pathlib import Path

import pytest

pytest.importorskip("opentelemetry.sdk")  # trace=True needs it (absent on 3.14, TA-1)

from fi import experiments  # noqa: E402

BROKEN = Path(__file__).parent / "fixtures" / "broken_instrumentor"


@pytest.fixture
def instrument(monkeypatch):
    from fi.experiments._tracing import instrument as inst

    monkeypatch.setattr(inst, "_done", {})
    monkeypatch.setattr(inst, "_failed", {}, raising=False)  # raising=False: the same file runs on the pre-fix head
    monkeypatch.setattr(inst, "python_supported", lambda: True)
    return inst


def _broken_anthropic(monkeypatch, inst):
    """traceAI-anthropic installed but unimportable (the recorded FW-16bL-TA implementation failure), and the
    anthropic client library present, so ``instrument='auto'`` turns it on."""
    monkeypatch.syspath_prepend(str(BROKEN))
    sys.modules.pop("traceai_brokenfake", None)
    monkeypatch.setitem(inst.INSTRUMENTORS, "anthropic",
                        ("traceai_brokenfake", "AnthropicInstrumentor", "traceAI-anthropic"))
    real = inst._installed
    monkeypatch.setattr(inst, "_installed", lambda m: m == "anthropic" or (m != "openai" and real(m)))


def test_an_instrumentor_that_fails_to_import_does_not_stop_the_run(monkeypatch, capsys, instrument):
    _broken_anthropic(monkeypatch, instrument)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        result = experiments.run([{"id": "a", "q": 1}, {"id": "b", "q": 2}], lambda row: "ok", upload=False,
                                 progress=True)
    assert [i.status for i in result.items] == ["completed", "completed"]
    assert all(i.trace_id for i in result.items)  # the run is still traced (root spans), only anthropic is off
    why = result.metadata["tracing"]["failed_instrumentors"]["traceAI-anthropic"]
    assert why.startswith("ModuleNotFoundError: No module named 'fi_test_absent_provider'")
    out = capsys.readouterr().err
    header = next(ln for ln in out.splitlines() if ln.startswith("Tracing  "))
    assert "traceAI-anthropic failed to load (ModuleNotFoundError" in header
    assert "to stop loading it, pass --instrument / instrument=[...] without 'anthropic'" in header
    summary = out[out.index("Done     "):]
    assert "Tracing  traceAI-anthropic failed to load (ModuleNotFoundError" in summary
    assert "spans are off for this run" in summary
    ours = [w for w in caught if "traceAI-anthropic failed to load" in str(w.message)]
    assert len(ours) == 1 and issubclass(ours[0].category, RuntimeWarning)


def test_the_failure_is_warned_once_per_process_and_reported_on_every_run(monkeypatch, capsys, instrument):
    _broken_anthropic(monkeypatch, instrument)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        first = experiments.run([{"q": 1}], lambda row: "ok", upload=False, progress=False)
        second = experiments.run([{"q": 1}], lambda row: "ok", upload=False, progress=False)
    assert first.items[0].status == second.items[0].status == "completed"
    assert "traceAI-anthropic" in second.metadata["tracing"]["failed_instrumentors"]
    assert sum("traceAI-anthropic failed to load" in str(w.message) for w in caught) == 1
    assert "anthropic" in instrument._failed and "anthropic" not in instrument._done


def test_warnings_as_errors_do_not_stop_the_run_either(monkeypatch, instrument):
    _broken_anthropic(monkeypatch, instrument)
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        result = experiments.run([{"q": 1}], lambda row: "ok", upload=False, progress=False)
    assert result.items[0].status == "completed"
    assert "traceAI-anthropic" in result.metadata["tracing"]["failed_instrumentors"]


def test_an_instrumentor_whose_instrument_call_raises_is_skipped_and_others_still_apply(monkeypatch, instrument):
    from fi.experiments._tracing.routing import RoutingTracerProvider

    bound = []
    good, bad = types.ModuleType("fake_good_instr"), types.ModuleType("fake_bad_instr")

    class Good:
        def instrument(self, tracer_provider):
            bound.append(tracer_provider)

    class Bad:
        def instrument(self, tracer_provider):
            raise AttributeError("'NoneType' object has no attribute 'create'")

    good.Good, bad.Bad = Good, Bad
    monkeypatch.setitem(sys.modules, "fake_good_instr", good)
    monkeypatch.setitem(sys.modules, "fake_bad_instr", bad)
    monkeypatch.setitem(instrument.INSTRUMENTORS, "fake-bad", ("fake_bad_instr", "Bad", "traceAI-fakebad"))
    monkeypatch.setitem(instrument.INSTRUMENTORS, "fake-good", ("fake_good_instr", "Good", "traceAI-fakegood"))
    the_plan = instrument.InstrumentPlan(enable=["fake-bad", "fake-good"])
    with warnings.catch_warnings(record=True):
        warnings.simplefilter("always")
        applied = instrument.apply(RoutingTracerProvider(), the_plan)
    assert applied == ["fake-good"] and len(bound) == 1
    assert the_plan.enable == ["fake-good"]
    assert the_plan.failed == [("fake-bad", "AttributeError: 'NoneType' object has no attribute 'create'")]
    assert "traceAI-fakebad failed to load (AttributeError" in the_plan.header()
    assert "traceAI-fakegood on" in the_plan.header()



def test_the_failure_line_names_both_versions_and_how_to_switch_it_off(monkeypatch, instrument):
    """Regression coverage: "reinstall: pip install traceAI-anthropic" reinstalls the same 0.1.10, which cannot load with
    anthropic 1.x. The line names both installed versions (the recorded FW-16bL-TA venv) and the opt-out."""
    versions = {"traceAI-anthropic": "0.1.10", "anthropic": "1.17.0", "traceAI-langchain": "0.1.5",
                "langchain-core": "1.0.3"}
    monkeypatch.setattr(instrument, "_version", versions.get)
    line = instrument.failure_line("anthropic", "ModuleNotFoundError: No module named 'anthropic.resources.completions'")
    assert line.startswith("traceAI-anthropic failed to load (ModuleNotFoundError: No module named 'anthropic.resources")
    assert "Installed: traceAI-anthropic 0.1.10 with anthropic 1.17.0." in line
    assert ("install a traceAI-anthropic release that supports anthropic 1.17.0, or pin anthropic to a version "
            "traceAI-anthropic 0.1.10 supports") in line
    assert "pass --instrument / instrument=[...] without 'anthropic'" in line
    assert "pip install traceAI-anthropic" not in line  # reinstalling the same version does nothing
    # the framework instrumentors keep their futureagi extra, where reinstalling can help
    lc = instrument.failure_line("langchain", "ImportError: x")
    assert 'reinstall a compatible version: pip install "futureagi[langchain]"' in lc
    assert "Installed: traceAI-langchain 0.1.5 with langchain-core 1.0.3." in lc


def test_the_trial_root_span_names_the_failed_instrumentor(monkeypatch, instrument):
    """Regression coverage: result.metadata is local; the uploaded trace says why its provider spans are missing."""
    from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

    from fi.experiments._tracing.export import exporter_factory
    from fi.experiments._upload_session import UploadSession
    from tests.experiments.unit.contract_server import ContractServer, client_for

    _broken_anthropic(monkeypatch, instrument)
    mem = InMemorySpanExporter()

    def factory(self, **kw):
        creds = self.client.auth
        return exporter_factory(base_url=self.base_url, api_key=creds.api_key, secret_key=creds.secret_key,
                                inner=mem, **kw)

    monkeypatch.setattr(UploadSession, "exporter_factory", factory)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        result = experiments.run(experiments.dataset([{"question": "q1", "expected": "ok"}], name="t-instrument"), lambda row: "ok",
                                 [], client=client_for(ContractServer()), progress=False, trace=True)
    assert result.items[0].status == "completed"
    [root] = [s for s in mem.get_finished_spans() if s.name == "experiment.trial"]
    [failed] = root.attributes["fi.experiment.tracing.failed_instrumentors"]
    assert failed.startswith("traceAI-anthropic: ModuleNotFoundError: No module named 'fi_test_absent_provider'")
