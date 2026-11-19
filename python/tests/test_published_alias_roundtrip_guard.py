"""All-model alias inventory and runtime guard, rooted in published wheel AST data.

The fixture generator owns serialization_alias > alias > field-name precedence.
Live annotations supply test values ONLY, never the expected output names. No
namespace, class-name or historical-count allowlist bounds the runtime cases.
"""
import importlib
import json
from pathlib import Path
import sys
import types
from typing import Any, Union, get_args, get_origin
import warnings

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, create_model
import pytest


from compat_model_contracts import load_model_contracts

# Legacy inputs remain accepted; output names follow the published 0.7.0 models.
FIXTURE = load_model_contracts()
ARCHIVE_SHA256 = 'bbbc8ee96802bd6310c1dd29f9b43c32fda1cd55d4277de7d2f432d59a9e11c6'


def published_models(fixture):
    """Validate the entire class inventory before selecting model fields.

    NamedTuples and ordinary/dependency classes are explicitly distinguished by
    the generator. Missing/unknown kinds or incomplete model metadata are errors,
    not a reason to silently omit a model from alias coverage.
    """
    models = {}
    for target, spec in fixture['classes'].items():
        kind, fields = spec['field_kind'], spec['fields']
        assert kind in (None, 'namedtuple', 'model'), f'{target}: unsupported field kind {kind!r}'
        if kind is None:
            assert not fields, f'{target}: unclassified fields'
        if kind != 'model':
            continue
        outputs = []
        for field, details in fields.items():
            assert isinstance(details['input_name'], str), f'{target}.{field}: unsupported input name'
            assert isinstance(details['output_name_by_alias'], str), f'{target}.{field}: unsupported output name'
            assert type(details['required']) is bool, f'{target}.{field}: unsupported required metadata'
            outputs.append(details['output_name_by_alias'])
        assert len(set(outputs)) == len(outputs), f'{target}: colliding published output names'
        models[target] = spec
    return models


def published_aliases(fixture):
    # Include validation-only aliases too, even when output remains canonical.
    return [(target, field, details['output_name_by_alias'])
            for target, spec in published_models(fixture).items()
            for field, details in spec['fields'].items()
            if details['input_name'] != field or details['output_name_by_alias'] != field]


def resolve_model(target):
    module, separator, name = target.rpartition('.')
    assert separator and name, f'{target}: unsupported model target'
    cls = getattr(importlib.import_module(module), name)
    assert isinstance(cls, type) and issubclass(cls, BaseModel), f'{target}: not a Pydantic model'
    return cls


def sample_value(annotation, falsy=False):
    """Small typed value factory; unsupported cases fail closed, never skip.

    Optional selects its non-None type so an aliased field is exercised with a
    real value rather than passing vacuously on its default. New constrained or
    model-valued cases must extend this factory with explicit successful controls.
    """
    origin, args = get_origin(annotation), get_args(annotation)
    if origin in (Union, types.UnionType):
        non_none = [arg for arg in args if arg is not type(None)]
        assert len(non_none) == 1, f'Unsupported sample annotation: {annotation!r}'
        return sample_value(non_none[0], falsy)
    if annotation is Any:
        return 0 if falsy else 17
    if annotation is str:
        return '' if falsy else 'published-value'
    if annotation is bool:
        return not falsy
    if annotation is int:
        return 0 if falsy else 17
    if annotation is float:
        return 0.0 if falsy else 12.5
    if origin is list and len(args) == 1:
        # Resolve the item even for empty controls: unsupported types cannot hide.
        item = sample_value(args[0])
        return [] if falsy else [item]
    if origin is dict and len(args) == 2:
        key, value = sample_value(args[0]), sample_value(args[1])
        return {} if falsy else {key: value}
    raise AssertionError(f'Unsupported sample annotation: {annotation!r}')


def dump(model, format, **options):
    assert format in ('dict', 'json'), f'Unsupported serialization format: {format}'
    if format == 'json':
        return json.loads(model.model_dump_json(**options))
    return model.model_dump(**options)


def assert_alias_roundtrip(cls, spec, field, format, falsy=False, *, fixture=FIXTURE):
    """The SAME runtime assertions serve published cases and synthetic mutants.

    No construct(), skips, alias normalization or fallback to current output
    metadata. Required fields come from the archive; invalid values and newly
    required runtime fields raise rather than reducing the enumerated scope.
    Returned warnings let the queue controls retain their exact once-only pin.
    """
    fields = spec['fields']
    assert fields.keys() <= cls.model_fields.keys(), f'{cls.__name__}: missing published fields'
    value = sample_value(cls.model_fields[field].annotation, falsy)
    payload = {name: sample_value(cls.model_fields[name].annotation)
               for name, details in fields.items() if details['required']}
    payload[field] = value
    extra = 'future_server_field'
    # The generator adds **extra_data for archived extra='allow'. Do not use
    # current config to decide coverage: losing that policy must fail the guard.
    allows_extra = any(p['kind'] == 'VAR_KEYWORD'
                       for p in fixture['signatures'][spec['constructor']])
    if allows_extra:
        assert extra not in fields and all(extra != d['output_name_by_alias'] for d in fields.values())
        payload[extra] = 0
    with warnings.catch_warnings(record=True) as output_warnings:
        warnings.simplefilter('always', DeprecationWarning)
        canonical = cls.model_validate(payload)
        assert getattr(canonical, field) == value, f'{cls.__name__}.{field}: canonical input lost'
        default = dump(canonical, format)
        assert default == dump(canonical, format, by_alias=False)
        assert default[field] == value
        output_name = fields[field]['output_name_by_alias']
        if output_name != field:
            assert output_name not in default
        aliased = dump(canonical, format, by_alias=True)
        assert output_name in aliased, f'{cls.__name__}.{field}: missing published output {output_name!r}'
        assert aliased[output_name] == value, f'{cls.__name__}.{field}: published output value changed'
        if output_name != field:
            assert field not in aliased, f'{cls.__name__}.{field}: canonical name leaked into published output'
        # Exact names for the whole dump, including optional/defaulted fields.
        # New fields/extras remain additive; no output-name oracle comes from cls.
        expected = {fields[key]['output_name_by_alias'] if key in fields else key: val
                    for key, val in default.items()}
        assert aliased == expected, f'{cls.__name__}: published output differs from archive names'
        if extra in payload:
            assert default.get(extra) == aliased.get(extra) == 0, f'{cls.__name__}: published extra field lost'
        assert not output_warnings  # Output selection must remain silent.
    with warnings.catch_warnings(record=True) as input_warnings:
        warnings.simplefilter('always', DeprecationWarning)
        restored = (cls.model_validate_json(json.dumps(aliased)), cls.model_validate(aliased))
        for model in restored:
            assert getattr(model, field) == value, f'{cls.__name__}.{field}: round-trip field value lost'
            assert dump(model, format, by_alias=True) == aliased
            assert dump(model, format) == default
        # Input and output names can differ. Exercise the archive's accepted
        # input spelling independently instead of treating output as its proxy.
        published_input = {fields[key]['input_name'] if key in fields else key: val
                           for key, val in payload.items()}
        for model in (cls.model_validate(published_input),
                      cls.model_validate_json(json.dumps(published_input))):
            assert getattr(model, field) == value, f'{cls.__name__}.{field}: published input value lost'
            assert dump(model, format, by_alias=True) == aliased
            assert dump(model, format) == default
    return input_warnings


ALIASES = published_aliases(FIXTURE)
MODELS = sorted({target for target, _, _ in ALIASES})


def test_global_inventory_is_pinned_and_has_runtime_cases():
    assert FIXTURE['archive_sha256'] == ARCHIVE_SHA256
    assert ALIASES, 'Empty alias inventory would make the runtime guard vacuous'
    # Do not cap this at a historical count or namespace. Every discovered row
    # becomes a dictionary AND JSON runtime case in test_queue_serialization_compat.
    assert len(ALIASES) == len({(target, field) for target, field, _ in ALIASES})
    for target in MODELS:
        cls = resolve_model(target)
        assert Path(sys.modules[cls.__module__].__file__).resolve().is_relative_to(
            Path(__file__).resolve().parents[1] / 'fi')


@pytest.fixture
def nonqueue_fixture():
    # Synthetic archive is parsed as data, not imported or executed. Include a
    # private base/public re-export, inherited alias and a distinct input/output.
    from test_compat_fixture_generator import GENERATOR, make_wheel

    return GENERATOR.generate_python(make_wheel({
        'fi/__init__.py': 'from .reports import Report as PublishedReport\n',
        'fi/_report_base.py': '''
from pydantic import BaseModel, ConfigDict, Field
class ReportBase(BaseModel):
    model_config = ConfigDict(extra='allow')
    inherited: int = Field(0, alias='inheritedValue')
''',
        'fi/reports.py': '''
from ._report_base import ReportBase
from pydantic import Field
class Report(ReportBase):
    identity: str
    value: int = Field(alias='legacyValue', validation_alias='incomingValue', serialization_alias='publishedValue')
''',
    }))


def install_report(monkeypatch, output_name='publishedValue'):
    base = create_model(
        'ReportBase', __config__=ConfigDict(populate_by_name=True, extra='allow'),
        inherited=(int, Field(0, validation_alias=AliasChoices('inherited', 'inheritedValue'),
                              serialization_alias='inheritedValue')),
    )
    cls = create_model(
        'Report', __base__=base, identity=(str, ...),
        value=(int, Field(validation_alias=AliasChoices('value', 'incomingValue', 'publishedValue'),
                          serialization_alias=output_name)),
    )
    base_module = types.ModuleType('fi._report_base')
    base_module.ReportBase = base
    monkeypatch.setitem(sys.modules, 'fi._report_base', base_module)
    module = types.ModuleType('fi.reports')
    module.Report = cls
    module.ReportBase = base
    monkeypatch.setitem(sys.modules, 'fi.reports', module)
    return resolve_model('fi.reports.Report')


def test_discovery_includes_nonqueue_inherited_and_reexported_aliases(nonqueue_fixture):
    rows = published_aliases(nonqueue_fixture)
    assert ('fi.reports.Report', 'value', 'publishedValue') in rows
    assert ('fi.reports.Report', 'inherited', 'inheritedValue') in rows
    assert ('fi._report_base.ReportBase', 'inherited', 'inheritedValue') in rows
    assert len(rows) == 3  # Synthetic shape, never a published inventory bound.
    assert nonqueue_fixture['modules']['fi']['PublishedReport']['target'] == 'fi.reports.Report'
    expanded = {'classes': {**FIXTURE['classes'], **nonqueue_fixture['classes']}}
    assert set(published_aliases(expanded)) == set(ALIASES) | set(rows)


@pytest.mark.parametrize('format', ['dict', 'json'])
@pytest.mark.parametrize('falsy', [False, True])
def test_same_guard_accepts_nonqueue_roundtrips(nonqueue_fixture, monkeypatch, format, falsy):
    install_report(monkeypatch)
    for target, field, _ in published_aliases(nonqueue_fixture):
        cls = resolve_model(target)
        assert not assert_alias_roundtrip(cls, nonqueue_fixture['classes'][target], field, format,
                                          falsy, fixture=nonqueue_fixture)


@pytest.mark.parametrize('format', ['dict', 'json'])
@pytest.mark.parametrize('wrong_output', ['value', 'incomingValue'])
def test_same_guard_rejects_nonqueue_output_mutants(nonqueue_fixture, monkeypatch, format,
                                                  wrong_output, record_property):
    cls = install_report(monkeypatch, wrong_output)
    spec = nonqueue_fixture['classes']['fi.reports.Report']
    # Setup and input validation succeed. Only the intended output assertion is
    # accepted as mutation proof, not an import/setup/validation error.
    assert cls(identity='report', incomingValue=17).value == 17
    with pytest.raises(AssertionError, match="missing published output 'publishedValue'") as rejected:
        assert_alias_roundtrip(cls, spec, 'value', format, fixture=nonqueue_fixture)
    record_property('mutation', f'{format}: output={wrong_output}')
    record_property('rejection', str(rejected.value))


@pytest.mark.parametrize('format', ['dict', 'json'])
def test_same_guard_rejects_broken_roundtrip_after_correct_output(nonqueue_fixture, monkeypatch, format):
    cls = install_report(monkeypatch)
    # Output metadata remains correct but published input no longer populates the
    # field. A default hides missing-required validation errors, not the guard.
    cls.model_fields['value'].validation_alias = AliasChoices('value', 'incomingValue')
    cls.model_fields['value'].default = 0
    cls.model_rebuild(force=True)
    with pytest.raises(AssertionError, match='round-trip field value lost'):
        assert_alias_roundtrip(cls, nonqueue_fixture['classes']['fi.reports.Report'], 'value', format,
                               fixture=nonqueue_fixture)


@pytest.mark.parametrize('format', ['dict', 'json'])
def test_guard_does_not_drop_extra_coverage_when_runtime_config_changes(nonqueue_fixture, monkeypatch, format):
    cls = install_report(monkeypatch)
    cls.model_config['extra'] = 'ignore'
    cls.model_rebuild(force=True)
    with pytest.raises(AssertionError, match='published extra field lost'):
        assert_alias_roundtrip(cls, nonqueue_fixture['classes']['fi.reports.Report'], 'value', format,
                               fixture=nonqueue_fixture)


@pytest.mark.parametrize('broken', [
    {'field_kind': 'unknown', 'fields': {}},
    {'field_kind': None, 'fields': {'value': {}}},
    {'field_kind': 'model', 'fields': {'value': {'input_name': 'value', 'required': True}}},
    {'field_kind': 'model', 'fields': {'value': {'input_name': 'value', 'required': True,
                                              'output_name_by_alias': ['bad']}}},
])
def test_discovery_fails_closed_on_unsupported_metadata(broken):
    with pytest.raises((AssertionError, KeyError)):
        published_aliases({'classes': {'fi.reports.Unknown': broken}})


def test_resolver_fails_closed_on_nonmodel(monkeypatch):
    module = types.ModuleType('fi.reports')
    module.Report = object
    monkeypatch.setitem(sys.modules, 'fi.reports', module)
    with pytest.raises(AssertionError, match='not a Pydantic model'):
        resolve_model('fi.reports.Report')


@pytest.mark.parametrize('required', [False, True])
def test_guard_fails_closed_on_unsupported_field_or_required_value(nonqueue_fixture, monkeypatch, required):
    cls = install_report(monkeypatch)
    spec = nonqueue_fixture['classes']['fi.reports.Report']
    unsupported = 'identity' if required else 'value'
    cls.model_fields[unsupported].annotation = object
    with pytest.raises(AssertionError, match='Unsupported sample annotation'):
        assert_alias_roundtrip(cls, spec, 'value', 'dict', fixture=nonqueue_fixture)
