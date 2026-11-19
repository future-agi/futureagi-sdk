"""Global published alias round trips plus queue-specific compatibility controls.

The shared inventory is archive-derived across ALL model classes, despite this
file's historical queue name. No client or archive code is executed.
"""
import json
import warnings

import pytest

from fi import _compat_fields
from fi.queues import types
from test_published_alias_roundtrip_guard import (
    ALIASES, ARCHIVE_SHA256, FIXTURE, MODELS, assert_alias_roundtrip, dump, resolve_model,
)


@pytest.fixture(autouse=True)
def fresh_warning_registry(monkeypatch):
    monkeypatch.setattr(_compat_fields, '_seen', set())


def test_pinned_alias_inventory_is_complete():
    assert FIXTURE['archive_sha256'] == ARCHIVE_SHA256
    # Independent whole-fixture cross-check: a new model alias anywhere becomes
    # a runtime parameter. Historical counts/names never define the scope.
    assert set(ALIASES) == {
        (target, field, details['output_name_by_alias'])
        for target, spec in FIXTURE['classes'].items() if spec['field_kind'] == 'model'
        for field, details in spec['fields'].items()
        if details['input_name'] != field or details['output_name_by_alias'] != field
    }


@pytest.mark.parametrize('format', ['dict', 'json'])
@pytest.mark.parametrize('name,field,output_name', ALIASES,
                         ids=[f'{c}.{f}' for c, f, _ in ALIASES])
def test_all_published_alias_outputs_and_canonical_defaults(name, field, output_name, format):
    cls = resolve_model(name)
    spec = FIXTURE['classes'][name]
    assert spec['fields'][field]['output_name_by_alias'] == output_name
    # Both nonempty and falsy values; both accepted input spellings. The very
    # same guard is challenged by non-queue mutants in the generative tests.
    for falsy in (False, True):
        caught = assert_alias_roundtrip(cls, spec, field, format, falsy)
        # Only explicit legacy inputs warn: 0.7.0 output stays canonical, even
        # for by_alias dumps. The guard supplies required fields plus this field;
        # the second loop is silent. Derive the expectation from the frozen input
        # contract, not live inheritance or the implementation's alias metadata.
        expected_warnings = set() if falsy else {
            f"{details['input_name']} is deprecated; use {canonical_field} instead."
            for canonical_field, details in spec['fields'].items()
            if details['input_name'] != canonical_field
            and (details['required'] or canonical_field == field)}
        assert len(caught) == len(expected_warnings)
        assert {str(w.message) for w in caught} == expected_warnings
        assert all(w.category is DeprecationWarning for w in caught)


@pytest.mark.parametrize('format', ['dict', 'json'])
def test_nested_default_queue_serializes_without_changing_labels_or_extras(format):
    payload = {'queue': {'id': 'q', 'name': 'queue', 'itemCount': 0,
                         'requiresReview': False, 'future': {'rawKey': 1}},
               'labels': [{'labelId': 'untouched'}], 'created': False, 'outer_extra': []}
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always', DeprecationWarning)
        model = types.DefaultQueue.model_validate_json(json.dumps(payload))
        canonical = dump(model, format, exclude_unset=True)
        assert canonical == dump(model, format, by_alias=False, exclude_unset=True)
        assert canonical['queue']['item_count'] == 0
        assert canonical['queue']['requires_review'] is False
        expected = {**payload, 'queue': {'id': 'q', 'name': 'queue', 'item_count': 0,
                                       'requires_review': False, 'future': {'rawKey': 1}}}
        assert dump(model, format, by_alias=True, exclude_unset=True) == expected
        assert dump(types.DefaultQueue.model_validate(payload), format, by_alias=True,
                    exclude_unset=True) == expected
    assert len(caught) == 2
    assert all(w.category is DeprecationWarning for w in caught)


@pytest.mark.parametrize('format', ['dict', 'json'])
def test_none_include_exclude_unset_and_defaults_keep_field_name_semantics(format):
    model = types.QueueDetail(id='q', name='queue', item_count=None, requires_review=False,
                              annotations_required=0, future=None)
    assert dump(model, format, by_alias=True, include={'item_count'}) == {'item_count': None}
    assert dump(model, format, by_alias=False, include={'item_count'}) == {'item_count': None}
    assert dump(model, format, by_alias=True, include={'item_count'}, exclude_none=True) == {}
    for options in ({'exclude_none': True}, {'exclude_defaults': True}):
        result = dump(model, format, by_alias=True, exclude={'future'}, **options)
        assert result == {'id': 'q', 'name': 'queue', 'requires_review': False, 'annotations_required': 0}
    result = dump(model, format, by_alias=True, exclude_unset=True, exclude={'annotations_required'})
    assert result == {'id': 'q', 'name': 'queue', 'requires_review': False, 'item_count': None, 'future': None}
    progress = types.QueueProgress(in_progress=0)
    assert dump(progress, format, by_alias=True, exclude_unset=True) == {'in_progress': 0}
    assert dump(progress, format, by_alias=True, exclude_defaults=True) == {}


@pytest.mark.parametrize('format', ['dict', 'json'])
def test_conflicting_inputs_keep_canonical_field_precedence_and_allowed_extras(format):
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always', DeprecationWarning)
        model = types.QueueDetail(id='q', name='queue', item_count=0, itemCount=9, future=False)
        assert model.item_count == 0
        assert model.model_extra == {'itemCount': 9, 'future': False}
        expected = {'id': 'q', 'name': 'queue', 'item_count': 0, 'itemCount': 9, 'future': False}
        assert dump(model, format, exclude_unset=True) == expected
        assert dump(model, format, by_alias=False, exclude_unset=True) == expected
        # Exclude the preserved extra by its original name, not the canonical
        # field. No validator/serializer is allowed to silently discard extras.
        assert dump(model, format, by_alias=True, exclude_unset=True, exclude={'itemCount'}) == {
            'id': 'q', 'name': 'queue', 'item_count': 0, 'future': False}
    assert len(caught) == 1


def test_alias_collision_retains_native_pydantic_extra_serialization():
    with pytest.warns(DeprecationWarning, match='item_count'):
        model = types.QueueDetail(id='q', name='queue', item_count=0, itemCount=9)
    # With extra='allow', the unused alias survives independently of the 0.7.0
    # canonical field. Neither JSON nor dictionary serialization loses a value.
    pairs = json.loads(model.model_dump_json(by_alias=True, exclude_unset=True), object_pairs_hook=list)
    assert [value for key, value in pairs if key == 'itemCount'] == [9]
    assert [value for key, value in pairs if key == 'item_count'] == [0]
    assert model.model_dump(by_alias=True, exclude_unset=True) == {
        'id': 'q', 'name': 'queue', 'item_count': 0, 'itemCount': 9}
    assert model.item_count == 0


@pytest.mark.parametrize('name', MODELS)
def test_schema_output_aliases_are_opt_in_and_validation_schema_is_unchanged(name):
    cls = resolve_model(name)
    canonical = set(cls.model_fields)
    output_names = {field: alias for owner, field, alias in ALIASES if owner == name}
    assert set(cls.model_json_schema()['properties']) == canonical
    assert set(cls.model_json_schema(mode='validation', by_alias=True)['properties']) == canonical
    assert set(cls.model_json_schema(mode='serialization', by_alias=False)['properties']) == canonical
    assert set(cls.model_json_schema(mode='serialization', by_alias=True)['properties']) == {
        output_names.get(field, field) for field in canonical}
