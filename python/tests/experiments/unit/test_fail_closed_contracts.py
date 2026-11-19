"""the fail-closed contract, no network, no model, no server:

- **S6:** ``futureagi-py doctor`` imports and instruments each installed tracing add-on in a subprocess; a broken one is
  reported as BROKEN with its error (a doctor problem, exit 3), never as "installed". Two broken shapes
  (``fixtures/broken_instrumentor``): ``traceai_instrumentfake`` imports and fails inside ``instrument()``, the real
  F3 shape of traceAI-anthropic 0.1.10 with anthropic 1.x (e2e tracing regression); ``traceai_brokenfake`` fails on import.
- **Explicit ``instrument=[...]``** naming a broken add-on is refused (``InstrumentorBrokenError``, exit 3) before
  any request, both shapes; ``'auto'`` still runs on without it (``test_instrument_failures.py``).
- **Resume with changed params** is refused with a message saying how to start a new run instead: the same CLI
  command without ``--resume`` (secrets redacted), or the same call without ``resume=``.
"""

import json
import sys
import types
from pathlib import Path

import pytest

from fi import experiments
from fi.experiments.errors import InstrumentorBrokenError, UsageError
from tests.experiments.unit.cli_helpers import cli
from tests.experiments.unit.contract_server import ContractServer, client_for

BROKEN = Path(__file__).parent / "fixtures" / "broken_instrumentor"
ROWS = [{"id": "a", "q": 1}, {"id": "b", "q": 2}]


@pytest.fixture
def instrument(monkeypatch):
    from fi.experiments._tracing import instrument as inst

    monkeypatch.setattr(inst, "_done", {})
    monkeypatch.setattr(inst, "_failed", {})
    monkeypatch.setattr(inst, "_probed_ok", set())
    monkeypatch.setattr(inst, "python_supported", lambda: True)
    return inst


def _broken_anthropic(monkeypatch, inst):
    """traceAI-anthropic installed but unimportable (the recorded FW-16bL-TA implementation failure)."""
    monkeypatch.syspath_prepend(str(BROKEN))
    sys.modules.pop("traceai_brokenfake", None)
    monkeypatch.setitem(inst.INSTRUMENTORS, "anthropic",
                        ("traceai_brokenfake", "AnthropicInstrumentor", "traceAI-anthropic"))


def _instrument_fails(monkeypatch, inst):
    """traceAI-anthropic installed, importable, and failing inside instrument() (the real F3 shape, tracing regression)."""
    monkeypatch.syspath_prepend(str(BROKEN))
    sys.modules.pop("traceai_instrumentfake", None)
    monkeypatch.setitem(inst.INSTRUMENTORS, "anthropic",
                        ("traceai_instrumentfake", "AnthropicInstrumentor", "traceAI-anthropic"))


# ---- S6: doctor imports and instruments each installed add-on in a subprocess -------------------------


def test_the_probe_runs_instrument_in_the_child_and_reports_where_it_failed(monkeypatch, tmp_path):
    pytest.importorskip("opentelemetry.sdk")  # the child instruments against its own TracerProvider (absent on 3.14)
    from fi.experiments._tracing.probe import probe_imports

    (tmp_path / "fi_test_good_instr.py").write_text(
        "class GoodInstrumentor:\n    def instrument(self, tracer_provider=None):\n"
        "        assert type(tracer_provider).__name__ == 'TracerProvider'\n")
    monkeypatch.syspath_prepend(str(BROKEN))
    monkeypatch.syspath_prepend(str(tmp_path))
    got = probe_imports({"inst": ("traceai_instrumentfake", "AnthropicInstrumentor"),
                         "good": ("fi_test_good_instr", "GoodInstrumentor"),
                         "import": ("traceai_brokenfake", "AnthropicInstrumentor")})
    assert got["inst"].ok is False and got["inst"].stage == "instrument"
    assert got["inst"].error.startswith("ModuleNotFoundError: No module named 'fi_test_absent_provider'")
    assert got["inst"].why().startswith("instrument() raised ModuleNotFoundError")
    assert got["good"].ok is True and got["good"].instrumented is True
    assert got["import"].ok is False and got["import"].stage == "import"
    assert "traceai_instrumentfake" not in sys.modules and "fi_test_good_instr" not in sys.modules  # child only


def test_doctor_reports_an_add_on_that_fails_in_instrument_as_broken_and_exits_3(monkeypatch, instrument):
    pytest.importorskip("opentelemetry.sdk")
    _instrument_fails(monkeypatch, instrument)
    code, out, err = cli("doctor", "--offline")
    line = next(ln for ln in out.splitlines() if ln.startswith("Instrument traceAI-anthropic"))
    assert "BROKEN: installed and it imports, but instrument() fails (ModuleNotFoundError: No module named " in line
    assert "installed (imports" not in line and code == 3, (out, err)


def test_doctor_says_imports_instruments_for_a_working_add_on(monkeypatch, instrument, tmp_path):
    pytest.importorskip("opentelemetry.sdk")
    (tmp_path / "fi_test_good_instr2.py").write_text(
        "class GoodInstrumentor:\n    def instrument(self, tracer_provider=None):\n        pass\n")
    monkeypatch.syspath_prepend(str(tmp_path))
    monkeypatch.setitem(instrument.INSTRUMENTORS, "openai", ("fi_test_good_instr2", "GoodInstrumentor", "traceAI-openai"))
    code, out, _ = cli("doctor", "--offline")
    line = next(ln for ln in out.splitlines() if ln.split()[:2] == ["Instrument", "traceAI-openai"])  # not -agents
    assert line.endswith("installed (imports, instruments)") and "BROKEN" not in line


def test_an_explicit_list_naming_an_add_on_that_fails_in_instrument_is_refused_before_any_request(monkeypatch,
                                                                                                  instrument):
    """The real F3 shape: before wave 2c's probe it was refused only when tracing started, after the dataset
    version and the server run were made."""
    pytest.importorskip("opentelemetry.sdk")
    _instrument_fails(monkeypatch, instrument)
    server = ContractServer()
    with pytest.raises(InstrumentorBrokenError) as info:
        experiments.run(experiments.dataset(ROWS, name="support-cases"), lambda row: "ok", client=client_for(server),
                        instrument=["anthropic"], progress=False)
    message = str(info.value)
    assert "traceAI-anthropic is installed but fails to load (instrument() raised ModuleNotFoundError" in message
    assert "nothing was sent" in message
    assert server.requests == []
    assert "traceai_instrumentfake" not in sys.modules  # probed in a child, never instrumented here


def test_a_working_explicit_add_on_is_probed_once_per_process(monkeypatch, instrument, tmp_path):
    from fi.experiments._tracing import probe as probe_mod

    calls = []
    real = probe_mod.probe_imports
    monkeypatch.setattr(probe_mod, "probe_imports", lambda targets, **kw: calls.append(dict(targets)) or real(targets, **kw))
    (tmp_path / "fi_test_good_instr3.py").write_text(
        "class GoodInstrumentor:\n    def instrument(self, tracer_provider=None):\n        pass\n")
    monkeypatch.syspath_prepend(str(tmp_path))
    monkeypatch.setitem(instrument.INSTRUMENTORS, "openai", ("fi_test_good_instr3", "GoodInstrumentor", "traceAI-openai"))
    instrument.refuse_broken_explicit(["openai"], True)
    instrument.refuse_broken_explicit(["openai"], True)
    assert calls == [{"openai": ("fi_test_good_instr3", "GoodInstrumentor")}]


def test_the_probe_reports_a_broken_add_on_with_its_import_error_and_a_good_one_as_importing(monkeypatch):
    from fi.experiments._tracing.probe import probe_imports

    monkeypatch.syspath_prepend(str(BROKEN))
    got = probe_imports({"broken": ("traceai_brokenfake", "AnthropicInstrumentor"), "good": ("json", "JSONDecoder"),
                         "no-class": ("json", "NoSuchInstrumentor")})
    assert got["broken"].ok is False
    assert got["broken"].error.startswith("ModuleNotFoundError: No module named 'fi_test_absent_provider'")
    assert got["good"].ok is True and got["good"].error is None
    assert got["no-class"].ok is False and got["no-class"].error.startswith("AttributeError")
    assert "traceai_brokenfake" not in sys.modules  # imported in the child only: this process is untouched


def test_the_probe_reports_a_hanging_import_as_broken(tmp_path, monkeypatch):
    from fi.experiments._tracing.probe import probe_imports

    (tmp_path / "fi_test_slow_import.py").write_text("import time\ntime.sleep(30)\nclass X: pass\n")
    monkeypatch.syspath_prepend(str(tmp_path))
    got = probe_imports({"slow": ("fi_test_slow_import", "X")}, timeout_s=1.0)
    assert got["slow"].ok is False and "did not finish within 1 s" in got["slow"].error


def test_doctor_reports_a_broken_add_on_as_broken_never_installed_and_exits_3(monkeypatch, instrument):
    _broken_anthropic(monkeypatch, instrument)
    code, out, err = cli("doctor", "--offline")
    line = next(ln for ln in out.splitlines() if ln.startswith("Instrument traceAI-anthropic"))
    assert "BROKEN: installed, but importing it fails (ModuleNotFoundError: No module named " in line
    assert "'fi_test_absent_provider'" in line and "installed (imports)" not in line
    assert "--instrument / instrument=[...] naming 'anthropic' is refused" in line
    assert code == 3, (out, err)
    code, out, _ = cli("doctor", "--offline", "--json")
    problems = json.loads(out)["sections"]["experiments"]["problems"]
    assert code == 3 and any("traceAI-anthropic" in p and "BROKEN" in p for p in problems)


def test_doctor_says_installed_only_when_the_import_works(monkeypatch, instrument):
    monkeypatch.setitem(instrument.INSTRUMENTORS, "openai", ("json", "JSONDecoder", "traceAI-openai"))
    monkeypatch.setitem(instrument.INSTRUMENTORS, "anthropic", ("fi_test_not_there_at_all", "X", "traceAI-anthropic"))
    code, out, _ = cli("doctor", "--offline")
    lines = {ln.split()[1]: ln for ln in out.splitlines() if ln.startswith("Instrument ")}
    assert lines["traceAI-openai"].endswith("installed (imports)")
    assert lines["traceAI-anthropic"].endswith("not installed")
    assert "BROKEN" not in out


# ---- an explicit instrument=[...] naming a broken add-on is refused ----------------------------------


def test_an_explicit_list_naming_a_broken_add_on_is_refused_before_any_request(monkeypatch, instrument):
    pytest.importorskip("opentelemetry.sdk")
    _broken_anthropic(monkeypatch, instrument)
    server = ContractServer()
    with pytest.raises(InstrumentorBrokenError) as info:
        experiments.run(experiments.dataset(ROWS, name="support-cases"), lambda row: "ok", client=client_for(server),
                        instrument=["anthropic"], progress=False)
    message = str(info.value)
    assert "names 'anthropic', and traceAI-anthropic is installed but fails to load (ModuleNotFoundError" in message
    assert "nothing was sent" in message and "drop 'anthropic' from --instrument" in message
    assert info.value.get_error_code() == "INSTRUMENTOR_BROKEN" and info.value.exit_code == 3
    assert server.requests == []


def test_the_refusal_holds_on_a_later_run_in_the_same_process(monkeypatch, instrument):
    pytest.importorskip("opentelemetry.sdk")
    _broken_anthropic(monkeypatch, instrument)
    auto = experiments.run(ROWS, lambda row: "ok", upload=False, progress=False, instrument="auto")  # warns, runs
    assert auto.items[0].status == "completed"
    with pytest.raises(InstrumentorBrokenError):
        experiments.run(ROWS, lambda row: "ok", upload=False, progress=False, instrument=["anthropic"])


def test_a_failure_inside_instrument_is_refused_for_an_explicit_list(monkeypatch, instrument):
    pytest.importorskip("opentelemetry.sdk")  # the router needs it (absent on 3.14, TA-1)
    from fi.experiments._tracing.routing import RoutingTracerProvider

    bad = types.ModuleType("fake_bad_instr")

    class Bad:
        def instrument(self, tracer_provider):
            raise AttributeError("'NoneType' object has no attribute 'create'")

    bad.Bad = Bad
    monkeypatch.setitem(sys.modules, "fake_bad_instr", bad)
    monkeypatch.setitem(instrument.INSTRUMENTORS, "fake-bad", ("fake_bad_instr", "Bad", "traceAI-fakebad"))
    with pytest.raises(InstrumentorBrokenError, match="it stopped before its first trial"):
        instrument.apply(RoutingTracerProvider(), instrument.InstrumentPlan(enable=["fake-bad"], explicit=True))


def test_the_cli_refuses_instrument_naming_a_broken_add_on_with_exit_3(monkeypatch, instrument, tmp_path):
    pytest.importorskip("opentelemetry.sdk")
    _broken_anthropic(monkeypatch, instrument)
    (tmp_path / "agent.py").write_text("def task(row):\n    return 'ok'\n")
    (tmp_path / "rows.jsonl").write_text("\n".join(json.dumps(r) for r in ROWS) + "\n")
    code, out, err = cli("run", "agent.py:task", "--dataset", "rows.jsonl", "--no-upload", "--instrument",
                         "anthropic")  # a file path: a cached module named agent from another test never answers
    assert code == 3 and "traceAI-anthropic is installed but fails to load" in err


def test_a_missing_add_on_in_an_explicit_list_is_still_named_not_refused(monkeypatch, instrument):
    pytest.importorskip("opentelemetry.sdk")
    monkeypatch.setitem(instrument.INSTRUMENTORS, "anthropic", ("fi_test_not_there_at_all", "X", "traceAI-anthropic"))
    result = experiments.run(ROWS, lambda row: "ok", upload=False, progress=False, instrument=["anthropic"])
    assert result.items[0].status == "completed"


# ---- resume with changed params says how to start a new run -------------------------------------------


def _local(params, **kw):
    return experiments.run(ROWS, lambda row: "ok", upload=False, progress=False, trace=False, params=params, **kw)


def test_a_resume_with_changed_params_says_how_to_start_a_new_run_in_python():
    first = _local({"model": "m1"})
    with pytest.raises(UsageError) as info:
        _local({"model": "m2"}, resume=first.run_id)
    message = str(info.value)
    assert '"m2"' in message and "the run has \"m1\"" in message and "nothing was sent" in message
    assert "start a new run instead: call run() / log_results() again without resume=" in message
    assert f"run {first.run_id}'s results stay as they are" in message


def test_the_new_run_line_is_the_command_without_resume_with_secrets_hidden():
    from fi.experiments._resume_params import new_run_how

    fake = "plain-fake-value-" + "no-shape-0042"
    line = new_run_how(["run", "agent:task", "--dataset", "rows.jsonl", "--resume", "r-1", "--param",
                        "api" + "_key=" + fake, "--model", "m2"])
    assert line.startswith("run the same command without --resume (it shows api_key as [redacted]")
    assert line.endswith("futureagi-py run agent:task --dataset rows.jsonl --param 'api_key=[redacted]' --model m2")
    assert fake not in line and "--resume" not in line.split(": ", 1)[1]
    assert new_run_how(["run", "a:b", "--resume=r-1"]).endswith(": futureagi-py run a:b")
