"""Published model inputs must preserve values, not merely bind **kwargs."""
import importlib
import json
from pathlib import Path
import sys
import warnings

import pytest

FIXTURE = json.loads((Path(__file__).parent / 'data/compat_futureagi_0_6_13.json').read_text())
ALIASES = [(target.rsplit('.', 1)[-1], field, details['input_name'])
           for target, spec in FIXTURE['classes'].items() if target.startswith('fi.queues.types.')
           for field, details in spec['fields'].items() if details['input_name'] != field]
BULK = {
    'annotationsCreated': 'annotations_created', 'annotationsUpdated': 'annotations_updated',
    'notesCreated': 'notes_created', 'succeededCount': 'succeeded_count',
    'errorsCount': 'errors_count', 'warningsCount': 'warnings_count',
}


@pytest.fixture(autouse=True)
def fresh_warning_registry(monkeypatch):
    # Reset once-per-process state between independent tests, never within a test.
    import fi.annotations.types
    module = sys.modules.get('fi._compat_fields')
    if module is not None:
        monkeypatch.setattr(module, '_seen', set())


def sample(field):
    if field in ('requires_review',):
        return True
    if field in ('annotations_required', 'reservation_timeout_minutes', 'item_count',
                 'completed_count', 'in_progress', 'rows_created'):
        return 17
    if field in ('progress_pct', 'overall_agreement'):
        return 12.5
    if field in ('annotator_stats', 'annotator_performance', 'per_label', 'annotator_pairs'):
        return [{'test': 17}]
    if field in ('label_distribution', 'status_breakdown'):
        return {'test': 17}
    return 'legacy-value'


@pytest.mark.parametrize('name,field,alias', ALIASES, ids=[f'{c}.{a}' for c, _, a in ALIASES])
def test_legacy_queue_alias_populates_field_and_warns_once(name, field, alias):
    cls = getattr(importlib.import_module('fi.queues.types'), name)
    value = sample(field)
    payload = {'id': 'q', 'name': 'queue', alias: value, 'future_server_field': 42}
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always', DeprecationWarning)
        first = cls(**payload)
        second = cls.model_validate_json(json.dumps(payload))
        assert getattr(first, field) == value
        assert getattr(second, field) == value
        assert first.model_extra['future_server_field'] == 42
    assert len(caught) == 1
    assert caught[0].category is DeprecationWarning
    assert alias in str(caught[0].message) and field in str(caught[0].message)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always', DeprecationWarning)
        modern = cls(id='q', name='queue', **{field: value})
        assert getattr(modern, field) == value
    assert not caught


@pytest.mark.parametrize('old,new', BULK.items())
def test_bulk_old_construction_and_read_preserve_data_and_warn_once(old, new):
    from fi.annotations.types import BulkAnnotationResponse
    payload = {'message': 'ok', **{key: i for i, key in enumerate(BULK, 1)}}
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always', DeprecationWarning)
        result = BulkAnnotationResponse(**payload, ignored='still ignored')
        other = BulkAnnotationResponse.model_validate_json(json.dumps(payload))
        assert getattr(result, old) == getattr(result, new) == payload[old]
        assert getattr(other, old) == payload[old]
        assert not hasattr(result, 'ignored')
    matching = [w for w in caught if old in str(w.message)]
    assert len(matching) == 1
    assert matching[0].category is DeprecationWarning
    assert new in str(matching[0].message)


@pytest.mark.parametrize('old,new', BULK.items())
def test_bulk_modern_construction_is_silent_until_old_attribute_used(old, new):
    from fi.annotations.types import BulkAnnotationResponse
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always', DeprecationWarning)
        result = BulkAnnotationResponse(message='ok', **{key: i for i, key in enumerate(BULK.values(), 1)})
        assert getattr(result, new) >= 1
        assert not caught
        assert getattr(result, old) == getattr(result, new)
        assert getattr(result, old) == getattr(result, new)
    assert len(caught) == 1
    assert old in str(caught[0].message) and new in str(caught[0].message)


def test_legacy_helpers_reexport_current_implementations():
    from fi.datasets.dataset import EvalInfoResponseHandler, EvalTemplate
    from fi.evals.evaluator import EvalInfoResponseHandler as Handler
    from fi.evals.templates import EvalTemplate as Template
    from requests import Response
    assert EvalInfoResponseHandler is Handler
    assert EvalTemplate is Template
    response = Response()
    response.status_code = 200
    response._content = b'{"result": [{"name": "test", "evalId": 1}]}'
    assert Handler.parse(response) == [{'name': 'test', 'evalId': 1}]
    assert Template({'threshold': 1}).config == {'threshold': 1}
    assert callable(Template.validate_config)


def test_shared_alias_warns_once_across_models_and_modern_input_wins():
    from fi.queues.types import QueueDetail, Score
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always', DeprecationWarning)
        queue = QueueDetail(id='q', name='q', createdAt='old', created_at='new')
        score = Score(createdAt='legacy')
    assert queue.created_at == 'new'
    assert score.created_at == 'legacy'
    assert len(caught) == 1
    assert 'created_at' in str(caught[0].message)


def test_bulk_attribute_views_remain_synchronized():
    from fi.annotations.types import BulkAnnotationResponse
    with warnings.catch_warnings():
        warnings.simplefilter('ignore', DeprecationWarning)
        result = BulkAnnotationResponse(message='ok', **dict.fromkeys(BULK, 0))
        result.annotationsCreated = 12
        assert result.annotations_created == 12
        result.annotations_created = 24
        assert result.annotationsCreated == 24


def test_nested_queue_aliases_preserve_extra_policy():
    from fi.queues.types import DefaultQueue
    with pytest.warns(DeprecationWarning, match='item_count'):
        result = DefaultQueue.model_validate({'queue': {'id': 'q', 'name': 'q', 'itemCount': 17, 'future': 3}})
    assert result.queue.item_count == 17
    assert result.queue.model_extra['future'] == 3
