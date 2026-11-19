"""Small parser regressions; no published archive code is ever executed."""
import importlib.util
from io import BytesIO
from pathlib import Path
import zipfile

import pytest


SCRIPT = Path(__file__).resolve().parents[2] / 'scripts/compat/gen_compat_fixture.py'
SPEC = importlib.util.spec_from_file_location('compat_fixture_generator', SCRIPT)
GENERATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GENERATOR)


class MemoryWheel(BytesIO):
    def read_bytes(self):
        return self.getvalue()


def make_wheel(files):
    stream = MemoryWheel()
    with zipfile.ZipFile(stream, 'w') as archive:
        archive.writestr('futureagi-0.6.13.dist-info/METADATA', 'Name: futureagi\nVersion: 0.6.13\n')
        for filename, source in files.items():
            archive.writestr(filename, source)
    stream.seek(0)
    return stream


def test_ast_reexports_all_inheritance_and_signature_kinds():
    wheel = make_wheel({
        'fi/__init__.py': "from .public import Child as Exported\n__all__ = ['Exported']\n",
        'fi/_base.py': '''
class Base:
    def __init__(self, first, /, second=None, *args, flag=True, **kwargs): pass
    def inherited(self, value): pass
    def _private(self): pass
''',
        'fi/public.py': '''
from ._base import Base
from collections import OrderedDict
ALPHA, BETA = 1, 2
class Child(Base):
    @classmethod
    def build(cls, value=None): pass
    @staticmethod
    def normalize(value): pass
    @property
    def size(self): return 1
''',
    })
    fixture = GENERATOR.generate_python(wheel)
    assert list(fixture['modules']['fi']) == ['Exported']
    assert 'fi._base' not in fixture['modules']
    assert fixture['modules']['fi']['Exported'] == {'kind': 'class', 'target': 'fi.public.Child'}
    assert {'ALPHA', 'BETA', 'OrderedDict', 'Base', 'Child'} == set(fixture['modules']['fi.public'])
    cls = fixture['classes']['fi.public.Child']
    assert set(cls['methods']) == {'inherited', 'build', 'normalize', 'size'}
    assert cls['methods']['build']['kind'] == 'class'
    assert cls['methods']['normalize']['kind'] == 'static'
    assert cls['methods']['size']['kind'] == 'property'
    assert cls['constructor'] == 'fi._base.Base.__init__'
    params = fixture['signatures'][cls['constructor']]
    assert [(p['name'], p['kind'], p['required']) for p in params] == [
        ('first', 'POSITIONAL_ONLY', True),
        ('second', 'POSITIONAL_OR_KEYWORD', False),
        ('args', 'VAR_POSITIONAL', False),
        ('flag', 'KEYWORD_ONLY', False),
        ('kwargs', 'VAR_KEYWORD', False),
    ]
    wheel.seek(0)
    assert GENERATOR.generate_python(wheel) == fixture


def test_inherited_method_uses_c3_order_not_depth_first_order():
    wheel = make_wheel({'fi/__init__.py': '''
class Root:
    def method(self, root): pass
class Left(Root): pass
class Right(Root):
    def method(self, right): pass
class Diamond(Left, Right): pass
'''})
    fixture = GENERATOR.generate_python(wheel)
    assert fixture['classes']['fi.Diamond']['methods']['method']['signature'] == 'fi.Right.method'


def test_explicit_new_takes_precedence_over_inherited_init():
    wheel = make_wheel({'fi/__init__.py': '''
class Base:
    def __init__(self, token=None): pass
class Singleton(Base):
    def __new__(cls): pass
'''})
    fixture = GENERATOR.generate_python(wheel)
    assert fixture['classes']['fi.Singleton']['constructor'] == 'fi.Singleton.__new__'
    assert fixture['signatures']['fi.Singleton.__new__'] == []


def test_double_underscore_parameter_names_match_python_compilation():
    wheel = make_wheel({'fi/__init__.py': '''
class Model:
    def model_post_init(self, __context, *, __flag=None): pass
'''})
    fixture = GENERATOR.generate_python(wheel)
    params = fixture['signatures']['fi.Model.model_post_init']
    assert [p['name'] for p in params] == ['_Model__context', '_Model__flag']
    assert [p['source_name'] for p in params] == ['__context', '__flag']


def test_namedtuple_constructor_and_inherited_tuple_methods_are_pinned():
    fixture = GENERATOR.generate_python(make_wheel({'fi/__init__.py': '''
from typing import NamedTuple, Optional, List
class Embedding(NamedTuple):
    vector: List[float]
    data: Optional[str] = None
    link_to_data: Optional[str] = None
'''}))
    cls = fixture['classes']['fi.Embedding']
    assert cls['constructor'] is not None
    params = fixture['signatures'][cls['constructor']]
    assert [(p['name'], p['kind'], p['required']) for p in params] == [
        ('vector', 'POSITIONAL_OR_KEYWORD', True),
        ('data', 'POSITIONAL_OR_KEYWORD', False),
        ('link_to_data', 'POSITIONAL_OR_KEYWORD', False),
    ]
    assert {'count', 'index'} <= cls['methods'].keys()
    assert set(cls['fields']) == {'vector', 'data', 'link_to_data'}


def test_pydantic_constructor_uses_ast_fields_defaults_aliases_and_inheritance():
    fixture = GENERATOR.generate_python(make_wheel({'fi/__init__.py': '''
from pydantic import BaseModel, Field, ConfigDict
from typing import ClassVar
class Parent(BaseModel):
    inherited: str
    overridden: int = 1
class Model(Parent):
    model_config = ConfigDict(extra='allow', populate_by_name=True)
    ignored: ClassVar[str] = 'not a field'
    overridden: int = Field(...)
    annotationsCreated: int
    alias_name: str = Field(alias='aliasName')
    with_default: str = Field('value')
    with_factory: list = Field(default_factory=list)
    optional: str = None
    # The generator must not execute even a default expression.
    unevaluated: str = dangerous_call()
'''}))
    cls = fixture['classes']['fi.Model']
    assert cls['constructor'] is not None
    params = fixture['signatures'][cls['constructor']]
    assert [(p['name'], p['kind'], p['required']) for p in params] == [
        ('inherited', 'KEYWORD_ONLY', True),
        ('overridden', 'KEYWORD_ONLY', True),
        ('annotationsCreated', 'KEYWORD_ONLY', True),
        ('aliasName', 'KEYWORD_ONLY', True),
        ('with_default', 'KEYWORD_ONLY', False),
        ('with_factory', 'KEYWORD_ONLY', False),
        ('optional', 'KEYWORD_ONLY', False),
        ('unevaluated', 'KEYWORD_ONLY', False),
        ('extra_data', 'VAR_KEYWORD', False),
    ]
    assert cls['fields']['alias_name']['input_name'] == 'aliasName'
    assert 'ignored' not in cls['fields']
    assert 'annotationsCreated' in cls['fields']


@pytest.mark.parametrize('options,input_name,output_name', [
    ('', 'value', 'value'),
    ("alias='both'", 'both', 'both'),
    ("validation_alias='inbound'", 'inbound', 'value'),
    ("serialization_alias='outbound'", 'value', 'outbound'),
    ("alias='both', validation_alias='inbound'", 'inbound', 'both'),
    ("alias='both', serialization_alias='outbound'", 'both', 'outbound'),
    ("alias='both', validation_alias='inbound', serialization_alias='outbound'", 'inbound', 'outbound'),
    ("alias='both', validation_alias=None, serialization_alias=None", 'both', 'both'),
    ("alias='both', serialization_alias=''", 'both', ''),
    ("serialization_alias='not-an-identifier'", 'value', 'not-an-identifier'),
])
def test_ast_serialization_alias_precedence_is_independent_of_validation(options, input_name, output_name):
    fixture = GENERATOR.generate_python(make_wheel({'fi/__init__.py': f'''
from pydantic import BaseModel, Field
class Parent(BaseModel):
    value: str = Field('default', {options})
class Child(Parent): pass
'''}))
    for target in ('fi.Parent', 'fi.Child'):
        fields = fixture['classes'][target]['fields']
        assert fields['value']['input_name'] == input_name
        assert fields['value']['output_name_by_alias'] == output_name


def test_generated_pin_rejects_validation_name_used_for_serialization():
    from pydantic import BaseModel, Field
    from test_compat_0_6_13 import assert_serialization_name

    fixture = GENERATOR.generate_python(make_wheel({'fi/__init__.py': '''
from pydantic import BaseModel, Field
class Model(BaseModel):
    value: str = Field('default', alias='both', validation_alias='inbound', serialization_alias='outbound')
'''}))
    details = fixture['classes']['fi.Model']['fields']['value']

    class Correct(BaseModel):
        value: str = Field('default', validation_alias='inbound', serialization_alias='outbound')

    class ValidationOnly(BaseModel):
        value: str = Field('default', validation_alias='inbound')

    class WrongOutput(BaseModel):
        value: str = Field('default', validation_alias='inbound', serialization_alias='inbound')

    assert_serialization_name(Correct, 'value', details)
    for cls in (ValidationOnly, WrongOutput):
        assert cls(inbound='kept').value == 'kept'
        with pytest.raises(AssertionError, match='published by_alias output name changed'):
            assert_serialization_name(cls, 'value', details)


def test_invalid_serialization_alias_fails_instead_of_using_input_name():
    with pytest.raises(ValueError, match='Unsupported serialization alias'):
        GENERATOR.generate_python(make_wheel({'fi/__init__.py': '''
from pydantic import BaseModel, Field
class Model(BaseModel):
    value: str = Field(alias='inbound', serialization_alias=123)
'''}))


def test_external_base_methods_and_public_imported_classes_are_inventoried():
    fixture = GENERATOR.generate_python(make_wheel({'fi/__init__.py': '''
import logging
from pydantic import BaseModel
class Formatter(logging.Formatter):
    def format(self, record): pass
class Child(Formatter): pass
class Model(BaseModel):
    value: str
'''}))
    for target in ('fi.Formatter', 'fi.Child'):
        methods = fixture['classes'][target]['methods']
        assert methods['formatTime']['signature'] is None
        assert methods['formatTime']['kind'] == 'instance'
        assert methods['format']['signature'] == 'fi.Formatter.format'
    assert 'model_dump' in fixture['classes']['fi.Model']['methods']
    assert fixture['modules']['fi']['BaseModel']['kind'] == 'class'
    assert 'model_dump' in fixture['classes']['pydantic.BaseModel']['methods']


def test_external_enum_inventory_does_not_invoke_instance_descriptors():
    fixture = GENERATOR.generate_python(make_wheel({'fi/__init__.py': '''
from enum import Enum
class Choice(str, Enum):
    VALUE = 'value'
'''}))
    assert 'capitalize' in fixture['classes']['fi.Choice']['methods']


def test_unresolved_external_base_fails_instead_of_dropping_methods():
    with pytest.raises(ValueError, match='external base'):
        GENERATOR.generate_python(make_wheel({'fi/__init__.py': '''
from unknown_dependency import Base
class Child(Base): pass
'''}))


def test_optional_import_try_block_is_not_silently_omitted():
    fixture = GENERATOR.generate_python(make_wheel({'fi/__init__.py': '''
try:
    from fi.evals.evaluator import EvalInfoResponseHandler
    from fi.evals.templates import EvalTemplate
except ImportError:
    pass
'''}))
    names = fixture['modules']['fi']
    assert set(names) == {'EvalInfoResponseHandler', 'EvalTemplate'}
    assert names['EvalTemplate']['target'] == 'fi.evals.templates.EvalTemplate'
    assert names['EvalTemplate']['context'] == 'optional-import'
    assert names['EvalTemplate']['requires'] == ['fi.evals.evaluator', 'fi.evals.templates']


def test_unresolved_control_flow_fails_instead_of_losing_public_bindings():
    with pytest.raises(ValueError, match='bindings'):
        GENERATOR.generate_python(make_wheel({'fi/__init__.py': '''
for item in []:
    PUBLIC = item
'''}))


def test_public_string_protocols_are_pinned_through_inheritance():
    fixture = GENERATOR.generate_python(make_wheel({'fi/__init__.py': '''
class Error(Exception):
    def __str__(self): return 'message'
    def __repr__(self): return 'Error()'
    def _private(self): pass
class Child(Error): pass
'''}))
    for target in ('fi.Error', 'fi.Child'):
        methods = fixture['classes'][target]['methods']
        assert methods['__str__']['signature'] == 'fi.Error.__str__'
        assert methods['__repr__']['signature'] == 'fi.Error.__repr__'
        assert '_private' not in methods
