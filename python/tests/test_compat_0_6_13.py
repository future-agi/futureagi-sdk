"""Published-wheel pins: additive source changes must preserve existing callers.

Regenerate only from the published archive with scripts/compat/gen_compat_fixture.py.
These tests never instantiate clients, execute API calls, or import wheel code.
Third-party imports are availability pins; the wheel's own AST supplies signatures.
"""
import importlib
import inspect
import json
from pathlib import Path
import sys

import pytest


from compat_model_contracts import load_model_contracts

# Keep legacy imports/signatures, but do not restore pre-0.7.0 output contracts.
FIXTURE = load_model_contracts()
P = inspect.Parameter
POSITIONAL = (P.POSITIONAL_ONLY, P.POSITIONAL_OR_KEYWORD)
NAMES = [(module, name, spec) for module, names in FIXTURE['modules'].items()
         for name, spec in names.items()]
CALLABLES = []
METHODS = []
FIELDS = []
for module, name, spec in NAMES:
    if spec['kind'] == 'function':
        CALLABLES.append((module, name, None, 'function', spec['target']))
    elif spec['kind'] == 'class':
        cls = FIXTURE['classes'][spec['target']]
        if cls['constructor']:
            CALLABLES.append((module, name, None, 'constructor', cls['constructor']))
        for method, details in cls['methods'].items():
            METHODS.append((module, name, method, details['kind']))
            if details['kind'] != 'property' and details['signature'] is not None:
                CALLABLES.append((module, name, method, details['kind'], details['signature']))
        for field, details in cls.get('fields', {}).items():
            FIELDS.append((module, name, field, cls['field_kind'], details))


def assert_compatible(old, current, label):
    """Keep old positional slots, keywords, optionality and variadic calls.

    New keyword-only parameters cannot require old callers to supply new data.
    Every formerly valid minimal call must still bind unchanged. Defaults' values
    and annotations are not pinned; neither are dependency-only signatures.
    """
    params = list(current.parameters.values())
    positional = [p for p in params if p.kind in POSITIONAL]
    old_pos = [p for p in old if p['kind'] in ('POSITIONAL_ONLY', 'POSITIONAL_OR_KEYWORD')]
    assert [p.name for p in positional[:len(old_pos)]] == [p['name'] for p in old_pos], (
        f'{label}: published positional parameters changed order or were removed; '
        f"expected {[p['name'] for p in old_pos]}, got {current}"
    )
    by_name = current.parameters
    has_kwargs = any(p.kind == P.VAR_KEYWORD for p in params)
    for previous in old:
        name, kind = previous['name'], previous['kind']
        if kind in ('VAR_POSITIONAL', 'VAR_KEYWORD'):
            assert any(p.kind.name == kind for p in params), f'{label}: lost {kind}'
            continue
        now = by_name.get(name)
        if kind in ('POSITIONAL_OR_KEYWORD', 'KEYWORD_ONLY'):
            assert (now is not None and now.kind in (P.POSITIONAL_OR_KEYWORD, P.KEYWORD_ONLY)) or has_kwargs, (
                f'{label}: no longer accepts keyword {name}'
            )
        if now is not None and not previous['required']:
            assert now.default is not P.empty or now.kind in (P.VAR_KEYWORD, P.VAR_POSITIONAL), (
                f'{label}: formerly optional {name} is now required'
            )
    # Bind the published minimal call WITHOUT supplying any new arguments.
    # This catches newly required parameters, including keyword-only additions.
    args = [object() for p in old_pos if p['required']]
    kwargs = {p['name']: object() for p in old if p['kind'] == 'KEYWORD_ONLY' and p['required']}
    try:
        current.bind(*args, **kwargs)
    except TypeError as error:
        pytest.fail(f'{label}: published minimal call no longer binds: {error}')


@pytest.mark.parametrize('module', FIXTURE['modules'])
def test_published_module_imports(module):
    imported = importlib.import_module(module)
    source_root = Path(__file__).resolve().parents[1] / 'fi'
    assert Path(imported.__file__).resolve().is_relative_to(source_root), (
        f'{module} came from an installed distribution instead of current source'
    )


@pytest.mark.parametrize('module,name,spec', NAMES, ids=[f'{m}.{n}' for m, n, _ in NAMES])
def test_published_name_exists(module, name, spec, monkeypatch):
    imported = importlib.import_module(module)
    if spec.get('context') == 'interactive':
        # logging.handler only existed when sys.ps1 was set in 0.6.13.
        with monkeypatch.context() as patch:
            patch.setattr(sys, 'ps1', '>>> ', raising=False)
            importlib.reload(imported)
            try:
                assert hasattr(imported, name), f'{module}.{name}: published interactive name missing'
            finally:
                imported.logger.handlers.clear()
        importlib.reload(imported)
    else:
        if spec.get('context') == 'optional-import':
            # The baseline export exists with these optional dependencies present.
            # Never skip the pin: this lane provides them (fi.evals now ships).
            for dependency in spec['requires']:
                importlib.import_module(dependency)
        assert hasattr(imported, name), f'{module}.{name}: published name missing'
    if spec['kind'] == 'class':
        assert inspect.isclass(getattr(imported, name)), f'{module}.{name}: no longer a class'


@pytest.mark.parametrize('module,name,method,kind', METHODS,
                         ids=[f'{m}.{n}.{a}' for m, n, a, _ in METHODS])
def test_published_method_exists(module, name, method, kind):
    cls = getattr(importlib.import_module(module), name)
    # getattr/hasattr deliberately include the MRO: SDKException and
    # MissingAuthError moved to private implementation modules in 0.7.0.
    assert hasattr(cls, method), f'{module}.{name}.{method}: published method missing'
    if kind == 'property':
        assert isinstance(inspect.getattr_static(cls, method), property), (
            f'{module}.{name}.{method}: no longer a property'
        )
    else:
        assert callable(getattr(cls, method)), f'{module}.{name}.{method}: no longer callable'


@pytest.mark.parametrize('module,name,field,kind,details', FIELDS,
                         ids=[f'{m}.{n}.{f}' for m, n, f, _, _ in FIELDS])
def test_published_generated_field_exists(module, name, field, kind, details):
    cls = getattr(importlib.import_module(module), name)
    label = f'{module}.{name}.{field}'
    if kind == 'model':
        # Pydantic fields are instance attributes, not class descriptors. Its
        # metadata lets us pin them without creating clients or running validators.
        assert field in cls.model_fields, f'{label}: published model field missing'
        current = cls.model_fields[field]
        alias = current.validation_alias or current.alias
        accepted = {alias} if isinstance(alias, str) else set()
        if hasattr(alias, 'choices'):
            accepted.update(a for a in alias.choices if isinstance(a, str))
        if alias is None or cls.model_config.get('populate_by_name') or cls.model_config.get('validate_by_name'):
            accepted.add(field)
        assert details['input_name'] in accepted, f'{label}: published input alias no longer accepted'
    else:
        assert field in cls._fields and hasattr(cls, field), f'{label}: published tuple field missing'


def assert_serialization_name(cls, field, details):
    """Use the archive's output oracle, never its accepted input spelling."""
    current = cls.model_fields[field]
    output_name = current.serialization_alias
    if output_name is None:
        output_name = field
    assert output_name == details['output_name_by_alias'], (
        f'{cls.__name__}.{field}: published by_alias output name changed; '
        f"expected {details['output_name_by_alias']!r}, got {output_name!r}"
    )


@pytest.mark.parametrize('module,name,field,details',
                         [(m, n, f, d) for m, n, f, k, d in FIELDS if k == 'model'],
                         ids=[f'{m}.{n}.{f}' for m, n, f, k, _ in FIELDS if k == 'model'])
def test_published_model_serialization_name(module, name, field, details):
    cls = getattr(importlib.import_module(module), name)
    assert_serialization_name(cls, field, details)


@pytest.mark.parametrize('module,name,method,kind,signature', CALLABLES,
                         ids=[f'{m}.{n}' + (f'.{a}' if a else '') for m, n, a, _, _ in CALLABLES])
def test_published_signature_compatible(module, name, method, kind, signature):
    obj = getattr(importlib.import_module(module), name)
    if method is not None:
        descriptor = inspect.getattr_static(obj, method)
        obj = getattr(obj, method)
        if kind == 'class':
            assert inspect.ismethod(obj) and inspect.isclass(obj.__self__), (
                f'{module}.{name}.{method}: no longer a class-bound method'
            )
        elif kind == 'static':
            assert isinstance(descriptor, staticmethod), f'{module}.{name}.{method}: no longer static'
        current = inspect.signature(obj)
        if inspect.isfunction(obj) and not isinstance(descriptor, staticmethod):
            current = current.replace(parameters=list(current.parameters.values())[1:])
    else:
        current = inspect.signature(obj)
    label = f'{module}.{name}' + (f'.{method}' if method else '')
    assert_compatible(FIXTURE['signatures'][signature], current, label)


def _baseline(function):
    return [{'name': p.name, 'kind': p.kind.name, 'required': p.default is P.empty
             and p.kind not in (P.VAR_KEYWORD, P.VAR_POSITIONAL)}
            for p in inspect.signature(function).parameters.values()]


@pytest.mark.parametrize('before,after', [
    (lambda a, b=None: None, lambda a, b=None, c=None: None),
    (lambda a: None, lambda a, *, c=None: None),
    (lambda a, /: None, lambda a: None),
    (lambda *, a=None: None, lambda **kwargs: None),
    (lambda a, *args, **kwargs: None, lambda a, *args, **kwargs: None),
])
def test_signature_checker_accepts_compatible_additions(before, after):
    assert_compatible(_baseline(before), inspect.signature(after), 'synthetic')


@pytest.mark.parametrize('before,after,reason', [
    (lambda a, b=None: None, lambda b, a=None: None, 'changed order'),
    (lambda a, b=None: None, lambda a: None, 'removed'),
    (lambda a: None, lambda *, a: None, 'positional'),
    (lambda a: None, lambda a, /: None, 'keyword'),
    (lambda a=None: None, lambda a: None, 'formerly optional'),
    (lambda a: None, lambda a, b: None, 'minimal call'),
    (lambda a: None, lambda a, *, c: None, 'minimal call'),
    (lambda *, a=None: None, lambda: None, 'keyword'),
    (lambda *args: None, lambda: None, 'VAR_POSITIONAL'),
    (lambda **kwargs: None, lambda: None, 'VAR_KEYWORD'),
])
def test_signature_checker_rejects_breaking_changes(before, after, reason):
    with pytest.raises((AssertionError, pytest.fail.Exception), match=reason):
        assert_compatible(_baseline(before), inspect.signature(after), 'synthetic')


def test_property_pin_rejects_replacement_with_plain_method(monkeypatch):
    class Published:
        def value(self):
            return 1

    monkeypatch.setattr(sys.modules[__name__], 'SyntheticPropertyOwner', Published, raising=False)
    with pytest.raises(AssertionError, match='property'):
        test_published_method_exists(__name__, 'SyntheticPropertyOwner', 'value', 'property')


def test_property_pin_accepts_inherited_descriptor(monkeypatch):
    class Parent:
        @property
        def value(self):
            return 1

    class Child(Parent):
        pass

    monkeypatch.setattr(sys.modules[__name__], 'SyntheticPropertyOwner', Child, raising=False)
    test_published_method_exists(__name__, 'SyntheticPropertyOwner', 'value', 'property')


def test_namedtuple_pin_rejects_removed_positional_constructor(monkeypatch):
    from fi.utils.types import Embedding

    signature = FIXTURE['classes']['fi.utils.types.Embedding']['constructor']
    assert signature is not None
    monkeypatch.setattr(Embedding, '__new__', staticmethod(lambda cls: tuple.__new__(cls)))
    with pytest.raises(AssertionError, match='positional parameters'):
        test_published_signature_compatible('fi.utils.types', 'Embedding', None, 'constructor', signature)


def test_inherited_dependency_pin_rejects_shadowed_method(monkeypatch):
    from fi.utils.logging import CustomLogFormatter

    assert 'formatTime' in FIXTURE['classes']['fi.utils.logging.CustomLogFormatter']['methods']
    monkeypatch.setattr(CustomLogFormatter, 'formatTime', None)
    with pytest.raises(AssertionError, match='no longer callable'):
        test_published_method_exists('fi.utils.logging', 'CustomLogFormatter', 'formatTime', 'instance')


def test_model_field_pin_rejects_alias_loss_even_with_extra_kwargs(monkeypatch):
    from pydantic import BaseModel, ConfigDict

    class Model(BaseModel):
        model_config = ConfigDict(extra='allow')
        value: int = 0

    monkeypatch.setattr(sys.modules[__name__], 'SyntheticModel', Model, raising=False)
    # Binding alone accepts any keyword, but it no longer populates the old field.
    inspect.signature(Model).bind(legacyValue=1)
    with pytest.raises(AssertionError, match='input alias no longer accepted'):
        test_published_generated_field_exists(__name__, 'SyntheticModel', 'value', 'model',
                                              {'input_name': 'legacyValue'})


def test_model_field_pin_rejects_attribute_rename(monkeypatch):
    from pydantic import BaseModel

    class Model(BaseModel):
        annotations_created: int

    monkeypatch.setattr(sys.modules[__name__], 'SyntheticModel', Model, raising=False)
    with pytest.raises(AssertionError, match='published model field missing'):
        test_published_generated_field_exists(__name__, 'SyntheticModel', 'annotationsCreated', 'model',
                                              {'input_name': 'annotationsCreated'})
