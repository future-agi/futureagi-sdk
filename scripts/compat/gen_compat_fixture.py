#!/usr/bin/env python3
"""Pin published APIs without importing or extracting either published archive.

Run with the SDK development environment's Python 3.10+ and -I::

    python -I scripts/compat/gen_compat_fixture.py --wheel /path/to/pub.whl \
        --typescript-tarball /path/to/future-agi-sdk-0.1.2.tgz

SDK definitions, signatures and generated constructor fields come ONLY from the
wheel AST. No default expressions, decorators or wheel imports are executed.
Inherited dependency methods are availability pins, inventoried from explicitly
allowlisted installed dependencies/stdlib (versions recorded in the fixture),
not invented signatures or imports of the current SDK. Regenerate in the same
environment for byte-identical output; JSON mappings and export lists are sorted.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import importlib
import importlib.metadata
import inspect
import json
from pathlib import Path
import platform
import subprocess
import tarfile
import zipfile


FUNCTIONS = (ast.FunctionDef, ast.AsyncFunctionDef)
BINDINGS = (ast.Assign, ast.AnnAssign, ast.Import, ast.ImportFrom, ast.ClassDef, *FUNCTIONS)
REPO = Path(__file__).resolve().parents[2]
# Never let archive contents choose arbitrary modules to import, especially fi.
# These are the external providers of public classes/bases in the 0.6.13 wheel.
EXTERNAL_MODULES = {
    'abc': None, 'builtins': None, 'collections': None, 'collections.abc': None,
    'concurrent.futures': None, 'datetime': None, 'enum': None, 'logging': None,
    'queue': None, 'threading': None, 'typing': None,
    'pydantic': 'pydantic', 'requests': 'requests',
    'requests.exceptions': 'requests', 'requests_futures.sessions': 'requests-futures',
    'tqdm': 'tqdm',
}


def parameters(node, drop_receiver=False, class_name=None):
    """An annotation-independent signature; default expressions are never run."""
    args = node.args
    positional = [*args.posonlyargs, *args.args]
    defaults = [None] * (len(positional) - len(args.defaults)) + list(args.defaults)
    result = []
    for index, (arg, default) in enumerate(zip(positional, defaults)):
        result.append({
            "name": arg.arg,
            "kind": "POSITIONAL_ONLY" if index < len(args.posonlyargs) else "POSITIONAL_OR_KEYWORD",
            "required": default is None,
            **({"default": ast.unparse(default)} if default is not None else {}),
        })
    if drop_receiver:
        result = result[1:]
    if args.vararg:
        result.append({"name": args.vararg.arg, "kind": "VAR_POSITIONAL", "required": False})
    for arg, default in zip(args.kwonlyargs, args.kw_defaults):
        result.append({
            "name": arg.arg, "kind": "KEYWORD_ONLY", "required": default is None,
            **({"default": ast.unparse(default)} if default is not None else {}),
        })
    if args.kwarg:
        result.append({"name": args.kwarg.arg, "kind": "VAR_KEYWORD", "required": False})
    if class_name and class_name.lstrip('_'):
        for parameter in result:
            name = parameter['name']
            if name.startswith('__') and not name.endswith('__'):
                parameter['source_name'] = name
                parameter['name'] = f'_{class_name.lstrip("_")}{name}'
    return result


def assignment_names(target):
    if isinstance(target, ast.Name):
        return [target.id]
    if isinstance(target, (ast.Tuple, ast.List)):
        return [name for child in target.elts for name in assignment_names(child)]
    return []


def generate_python(wheel):
    modules, definitions, exports = {}, {}, {}
    with zipfile.ZipFile(wheel) as archive:
        metadata = [n for n in archive.namelist() if n.endswith('.dist-info/METADATA')]
        assert len(metadata) == 1
        assert '\nVersion: 0.6.13\n' in archive.read(metadata[0]).decode()
        for filename in sorted(archive.namelist()):
            if not filename.startswith('fi/') or not filename.endswith('.py'):
                continue
            parts = filename[:-3].split('/')
            package = parts[-1] == '__init__'
            if package:
                parts.pop()
            module = '.'.join(parts)
            # Private definitions still resolve public re-exports and bases.
            modules[module] = {"file": filename, "package": package, "bindings": {},
                               "contexts": {}, "all": None,
                               "tree": ast.parse(archive.read(filename), filename)}

    def import_base(module, node):
        base = node.module or ''
        if node.level:
            package = module.split('.') if modules[module]['package'] else module.split('.')[:-1]
            base = '.'.join(package[:len(package) - node.level + 1] + ([base] if base else []))
        return base

    def bind_statements(module, statements, context=None):
        info = modules[module]
        bindings = info['bindings']

        def bind(name, target):
            if context and name in bindings and bindings[name] != target:
                raise ValueError(f'Ambiguous conditional bindings in {module}: {name}')
            bindings[name] = target
            if context:
                info['contexts'][name] = context

        for node in statements:
            if isinstance(node, (ast.ClassDef, *FUNCTIONS)):
                target = f'{module}.{node.name}'
                bind(node.name, target)
                definitions[target] = (module, node)
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    bind(alias.asname or alias.name.split('.')[0],
                         alias.name if alias.asname else alias.name.split('.')[0])
            elif isinstance(node, ast.ImportFrom):
                base = import_base(module, node)
                for alias in node.names:
                    if alias.name == '*':
                        raise ValueError(f'Unresolved star import in {module}')
                    bind(alias.asname or alias.name, f'{base}.{alias.name}')
            elif isinstance(node, (ast.Assign, ast.AnnAssign)):
                targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                for target in targets:
                    for name in assignment_names(target):
                        if name == '__all__':
                            info['all'] = ast.literal_eval(node.value)
                        bind(name, f'{module}.{name}')
            elif isinstance(node, ast.If) and ast.unparse(node.test) == 'TYPE_CHECKING':
                bind_statements(module, node.orelse, context)
            elif isinstance(node, ast.If) and ast.unparse(node.test) == "hasattr(sys, 'ps1')":
                bind_statements(module, node.body, {'context': 'interactive'})
                bind_statements(module, node.orelse, context)
            elif isinstance(node, ast.Try):
                for handler in node.handlers:
                    types = handler.type.elts if isinstance(handler.type, ast.Tuple) else [handler.type]
                    if not all(isinstance(t, ast.Name) and t.id in ('ImportError', 'ModuleNotFoundError') for t in types):
                        raise ValueError(f'Unresolved try bindings in {module}:{node.lineno}')
                requires = sorted({import_base(module, child) for child in node.body
                                   if isinstance(child, ast.ImportFrom)} |
                                  {alias.name for child in node.body if isinstance(child, ast.Import)
                                   for alias in child.names})
                optional = {'context': 'optional-import', 'requires': requires}
                bind_statements(module, node.body, optional)
                bind_statements(module, node.orelse, optional)
                for handler in node.handlers:
                    bind_statements(module, handler.body, optional)
                bind_statements(module, node.finalbody, context)
            elif any(isinstance(child, BINDINGS) for child in ast.walk(node)):
                # Never silently lose names in a new/unknown control-flow form.
                raise ValueError(f'Unresolved control-flow bindings in {module}:{node.lineno}')

    for module, info in modules.items():
        bind_statements(module, info['tree'].body)

    def resolve(target, seen=()):
        if target in seen:
            raise ValueError(f'Circular alias: {target}')
        mod, _, name = target.rpartition('.')
        other = modules.get(mod, {}).get('bindings', {}).get(name, target)
        return resolve(other, (*seen, target)) if other != target else target

    def resolve_base(module, base):
        if isinstance(base, ast.Subscript):
            base = base.value
        first, *rest = ast.unparse(base).split('.')
        return resolve('.'.join([modules[module]['bindings'].get(first, first), *rest]))

    dependency_versions = {}

    def external_object(target):
        if '.' not in target:
            target = 'builtins.' + target
        for prefix in sorted(EXTERNAL_MODULES, key=len, reverse=True):
            if not target.startswith(prefix + '.'):
                continue
            obj = importlib.import_module(prefix)
            distribution = EXTERNAL_MODULES[prefix]
            if distribution:
                dependency_versions[distribution] = importlib.metadata.version(distribution)
            for part in target[len(prefix) + 1:].split('.'):
                obj = getattr(obj, part, None)
            return obj
        return None

    signatures, classes = {}, {}

    def external_class_info(target):
        if target in classes:
            return classes[target]
        # typing.NamedTuple is a factory; its generated instances inherit tuple.
        obj = tuple if target == 'typing.NamedTuple' else external_object(target)
        if not inspect.isclass(obj):
            raise ValueError(f'Unresolved external base: {target}')
        methods = {}
        for name in sorted(set(dir(obj)) | {n for base in obj.__mro__ for n in vars(base)}):
            if name.startswith('_'):
                continue
            descriptor = inspect.getattr_static(obj, name)
            kind = ('property' if isinstance(descriptor, property) else
                    'static' if isinstance(descriptor, staticmethod) else
                    'class' if isinstance(descriptor, classmethod) else 'instance')
            # Inspect descriptors without invoking them (Enum.name, for example,
            # deliberately raises on class access despite existing on instances).
            value = descriptor.__func__ if isinstance(descriptor, (staticmethod, classmethod)) else descriptor
            if kind == 'property' or callable(value):
                methods[name] = {'kind': kind, 'signature': None, 'owner': target}
        classes[target] = {'methods': methods, 'constructor': None,
                           'external_bases': [], 'fields': {}, 'field_kind': None,
                           'source': 'dependency-availability'}
        return classes[target]

    def mro(target):
        if target not in definitions:
            return [target]
        module, node = definitions[target]
        bases = [resolve_base(module, b) for b in node.bases]
        sequences = [mro(b)[:] for b in bases] + [bases[:]]
        result = [target]
        while any(sequences):
            sequences = [s for s in sequences if s]
            candidate = next((s[0] for s in sequences if not any(s[0] in other[1:] for other in sequences)), None)
            if candidate is None:
                raise ValueError(f'Inconsistent MRO: {target}')
            result.append(candidate)
            for sequence in sequences:
                if sequence[0] == candidate:
                    sequence.pop(0)
        return result

    def generated_fields(ancestors, field_kind):
        fields, config = {}, {}
        for ancestor in reversed(ancestors):
            if ancestor not in definitions:
                continue
            module, node = definitions[ancestor]
            for child in node.body:
                # Pydantic ConfigDict/Config settings affect the call signature.
                if field_kind == 'model' and isinstance(child, ast.Assign):
                    if any(isinstance(t, ast.Name) and t.id == 'model_config' for t in child.targets):
                        if isinstance(child.value, ast.Call) and resolve_base(module, child.value.func) == 'pydantic.ConfigDict':
                            config.update({kw.arg: ast.literal_eval(kw.value) for kw in child.value.keywords})
                        elif isinstance(child.value, ast.Dict):
                            config.update(ast.literal_eval(child.value))
                        else:
                            raise ValueError(f'Unresolved model_config: {ancestor}')
                if field_kind == 'model' and isinstance(child, ast.ClassDef) and child.name == 'Config':
                    for setting in child.body:
                        if isinstance(setting, ast.Assign):
                            for name in assignment_names(setting.targets[0]):
                                config[name] = ast.literal_eval(setting.value)
                if not isinstance(child, ast.AnnAssign) or not isinstance(child.target, ast.Name):
                    continue
                name = child.target.id
                if name.startswith('_') or name == 'model_config':
                    continue
                if resolve_base(module, child.annotation) == 'typing.ClassVar':
                    continue
                default, input_name, output_name_by_alias = child.value, name, name
                factory = None
                if field_kind == 'model' and isinstance(default, ast.Call) and resolve_base(module, default.func) == 'pydantic.Field':
                    options = {kw.arg: kw.value for kw in default.keywords}
                    # Pydantic resolves these independently: validation_alias never
                    # supplies an output name. Explicit None falls back to alias;
                    # an empty string is still a valid serialization alias.
                    aliases = {key: ast.literal_eval(options[key]) if key in options else None
                               for key in ('alias', 'validation_alias', 'serialization_alias')}
                    alias = aliases['validation_alias']
                    if alias is None:
                        alias = aliases['alias']
                    if alias is not None:
                        input_name = alias
                        if not isinstance(input_name, str) or not input_name.isidentifier():
                            raise ValueError(f'Unsupported field alias: {ancestor}.{name}')
                    output_alias = aliases['serialization_alias']
                    if output_alias is None:
                        output_alias = aliases['alias']
                    if output_alias is not None:
                        if not isinstance(output_alias, str):
                            raise ValueError(f'Unsupported serialization alias: {ancestor}.{name}')
                        output_name_by_alias = output_alias
                    factory = options.get('default_factory')
                    default = default.args[0] if default.args else options.get('default')
                required = factory is None and (default is None or
                            isinstance(default, ast.Constant) and default.value is Ellipsis)
                fields[name] = {'input_name': input_name, 'required': required,
                                **({'output_name_by_alias': output_name_by_alias} if field_kind == 'model' else {}),
                                **({'default': ast.unparse(factory), 'default_factory': True} if factory is not None else
                                   {'default': ast.unparse(default)} if not required else {})}
        return fields, config

    def class_info(target):
        if target in classes:
            return classes[target]
        module, node = definitions[target]
        ancestors = mro(target)
        methods, constructor, external_bases = {}, None, []
        # Only a wheel ancestor's own declarations participate at its C3 slot.
        for ancestor in reversed(ancestors[1:]):
            if ancestor not in definitions:
                external_bases.append(ancestor)
                inherited = external_class_info(ancestor)
            else:
                inherited = class_info(ancestor)
            methods.update({name: method for name, method in inherited['methods'].items()
                            if method['owner'] == ancestor})
            if inherited['constructor'] and inherited['constructor'].rsplit('.', 1)[0] == ancestor:
                constructor = inherited['constructor']
        for method in node.body:
            if not isinstance(method, FUNCTIONS):
                continue
            if method.name.startswith('_') and method.name not in ('__init__', '__new__', '__str__', '__repr__'):
                continue
            decorators = [ast.unparse(d) for d in method.decorator_list]
            kind = 'property' if 'property' in decorators else (
                'static' if 'staticmethod' in decorators else (
                    'class' if 'classmethod' in decorators or (
                        method.args.args and method.args.args[0].arg == 'cls'
                        and any(d.startswith('field_validator(') for d in decorators)
                    ) else 'instance'))
            key = f'{target}.{method.name}'
            signatures[key] = parameters(method, drop_receiver=kind != 'static', class_name=node.name)
            if method.name in ('__init__', '__new__'):
                if constructor != f'{target}.__new__':
                    constructor = key
            else:
                methods[method.name] = {"kind": kind, "signature": key, "owner": target}
        field_kind = ('model' if 'pydantic.BaseModel' in ancestors else
                      'namedtuple' if 'typing.NamedTuple' in ancestors else None)
        fields, config = generated_fields(ancestors, field_kind) if field_kind else ({}, {})
        if field_kind:
            # The field declarations define generated public call signatures even
            # though the wheel contains no explicit __init__ / __new__ function.
            if constructor and not constructor.endswith('.__generated_constructor__'):
                raise ValueError(f'Explicit and generated constructor need resolution: {target}')
            constructor = f'{target}.__generated_constructor__'
            signatures[constructor] = [
                {'name': field['input_name'],
                 'kind': 'KEYWORD_ONLY' if field_kind == 'model' else 'POSITIONAL_OR_KEYWORD',
                 'required': field['required'],
                 **({'default': field['default']} if not field['required'] else {})}
                for field in fields.values()
            ]
            if field_kind == 'model' and config.get('extra') == 'allow':
                signatures[constructor].append({'name': 'extra_data', 'kind': 'VAR_KEYWORD', 'required': False})
        elif constructor is None and not external_bases:
            # Plain wheel classes without a constructor use object()'s empty call.
            constructor = f'{target}.__generated_constructor__'
            signatures[constructor] = []
        classes[target] = {"methods": methods, "constructor": constructor,
                           "external_bases": sorted(set(external_bases)),
                           "field_kind": field_kind, "fields": fields, "source": 'wheel-ast'}
        return classes[target]

    for module, info in modules.items():
        if any(p.startswith('_') for p in module.split('.')):
            continue
        names = info['all'] if info['all'] is not None else [n for n in info['bindings'] if not n.startswith('_')]
        exports[module] = {}
        for name in sorted(names):
            target = resolve(info['bindings'][name])
            kind = 'name'
            if target in definitions:
                _, node = definitions[target]
                if isinstance(node, ast.ClassDef):
                    kind = 'class'
                    class_info(target)
                else:
                    kind = 'function'
                    signatures[target] = parameters(node)
            elif inspect.isclass(external_object(target)):
                kind = 'class'
                external_class_info(target)
            exports[module][name] = {"kind": kind, "target": target, **info['contexts'].get(name, {})}

    return {
        "distribution": "futureagi", "version": "0.6.13",
        "archive_sha256": hashlib.sha256(wheel.read_bytes()).hexdigest(),
        "signature_scope": "Wheel AST definitions and generated model/NamedTuple constructors, including re-exports and inherited SDK methods. Dependency methods are availability pins only.",
        "dependency_inventory_environment": {"python": platform.python_version(),
                                              "distributions": dependency_versions},
        "modules": exports, "classes": classes, "signatures": signatures,
    }


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--wheel', type=Path, required=True)
    parser.add_argument('--typescript-tarball', type=Path)
    parser.add_argument('--python-output', type=Path, default=REPO / 'python/tests/data/compat_futureagi_0_6_13.json')
    parser.add_argument('--typescript-output', type=Path, default=REPO / 'typescript/futureagi/src/__tests__/compat-0.1.2.json')
    parser.add_argument('--types-output', type=Path, default=REPO / 'typescript/futureagi/test/compat-0.1.2.types.ts')
    args = parser.parse_args()
    write_json(args.python_output, generate_python(args.wheel))
    if args.typescript_tarball:
        with tarfile.open(args.typescript_tarball) as archive:
            files = {m.name: archive.extractfile(m).read().decode() for m in archive.getmembers()
                     if m.isfile() and (m.name.endswith('.d.ts') or m.name == 'package/package.json')}
        subprocess.run(
            ['node', str(Path(__file__).with_name('gen_ts_compat_fixture.cjs')),
             str(args.typescript_output), str(args.types_output)],
            input=json.dumps({"files": files, "archive_sha256": hashlib.sha256(args.typescript_tarball.read_bytes()).hexdigest()}),
            text=True, check=True,
        )


if __name__ == '__main__':
    main()
