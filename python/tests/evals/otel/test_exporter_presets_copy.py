"""Each read of an exporter preset is a separate configuration: headers one caller adds stay with that caller."""

import uuid

import pytest

from fi.evals.otel import EXPORTER_PRESETS as PACKAGE_PRESETS
from fi.evals.otel.config import EXPORTER_PRESETS, ExporterConfig, get_exporter_preset

NAMES = ["jaeger", "zipkin", "datadog", "honeycomb", "grafana_tempo", "arize"]


def runtime_marker() -> str:
    return f"preset-marker-{uuid.uuid4().hex}"


@pytest.mark.parametrize("name", NAMES)
def test_headers_added_to_one_preset_read_stay_with_it(name):
    first = get_exporter_preset(name)
    marker = runtime_marker()
    first.headers["x-honeycomb-team"] = marker
    first.options["dataset"] = marker
    first.endpoint = f"http://127.0.0.1:1/{marker}"

    second = get_exporter_preset(name)
    assert second is not first
    assert second.headers == {} and second.headers is not first.headers
    assert second.options == {}
    assert marker not in str(second.endpoint)
    assert EXPORTER_PRESETS[name].headers == {}
    assert marker not in repr(EXPORTER_PRESETS[name])


@pytest.mark.parametrize("name", NAMES)
def test_a_preset_read_from_the_mapping_is_a_copy(name):
    marker = runtime_marker()
    EXPORTER_PRESETS[name].headers["x-api-key"] = marker
    assert EXPORTER_PRESETS[name] is not EXPORTER_PRESETS[name]
    assert EXPORTER_PRESETS[name].headers == {}
    assert get_exporter_preset(name).headers == {}


def test_no_preset_carries_headers():
    assert sorted(EXPORTER_PRESETS) == sorted(NAMES)
    for name, preset in EXPORTER_PRESETS.items():
        assert isinstance(preset, ExporterConfig)
        assert preset.headers == {}, name


def test_the_mapping_is_read_only():
    with pytest.raises(TypeError):
        EXPORTER_PRESETS["custom"] = ExporterConfig(type=EXPORTER_PRESETS["arize"].type)
    assert "custom" not in EXPORTER_PRESETS
    assert PACKAGE_PRESETS is EXPORTER_PRESETS


def test_an_unknown_name_lists_the_presets():
    with pytest.raises(ValueError, match="honeycomb"):
        get_exporter_preset("unknown")
