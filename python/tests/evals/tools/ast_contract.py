"""Source contracts for compatibility-preserving method extractions (no optional imports)."""
import ast
import copy
import hashlib
import json
from pathlib import Path


def _canonical(node):
    if isinstance(node, ast.AST):
        return [type(node).__name__, {key: _canonical(value) for key, value in ast.iter_fields(node)
                                     if not (key == "type_params" and not value)}]
    if isinstance(node, list):
        return [_canonical(value) for value in node]
    if node is not None and not isinstance(node, (str, int, float, bool)):
        return {"literal_type": type(node).__name__, "value": repr(node)}
    return node


def node_digest(node):
    # ast.dump changed its empty-field formatting across supported interpreter versions.
    return hashlib.sha256(json.dumps(_canonical(node), sort_keys=True).encode()).hexdigest()


def function_digest(node, facade=None):
    """Hash executable statements and signature, omitting docs and extraction-only imports."""
    node = copy.deepcopy(node)
    if (node.body and isinstance(node.body[0], ast.Expr)
            and isinstance(node.body[0].value, ast.Constant)
            and isinstance(node.body[0].value.value, str)):
        node.body.pop(0)
    if facade:
        node.body = [n for n in node.body if not (isinstance(n, ast.ImportFrom) and n.module == facade)]
    return node_digest(node)


def class_digest(node):
    node = copy.deepcopy(node)
    node.body = [n for n in node.body if not isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    node.bases = [base for base in node.bases if not (isinstance(base, ast.Name)
                  and base.id.startswith('_') and base.id.endswith('Methods'))]
    if (node.body and isinstance(node.body[0], ast.Expr)
            and isinstance(node.body[0].value, ast.Constant)
            and isinstance(node.body[0].value.value, str)):
        node.body.pop(0)
    return node_digest(node)


def assignments(tree):
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    yield target.id, node
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            yield node.target.id, node


def functions(tree):
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            yield None, node
        elif isinstance(node, ast.ClassDef):
            for method in node.body:
                if isinstance(method, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    yield node.name, method


def resolve_definition(root, path, name, seen=None):
    """Resolve a public name through explicit relative re-exports without importing its module."""
    seen = set() if seen is None else seen
    identity = (path, name)
    if identity in seen:
        raise ValueError(f"circular re-export: {identity}")
    seen.add(identity)
    tree = ast.parse((root / path).read_text())
    for key, node in assignments(tree):
        if key == name:
            return path, node
    for node in tree.body:
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            return path, node
        if isinstance(node, ast.ImportFrom) and node.module:
            for alias in node.names:
                if (alias.asname or alias.name) == name:
                    if node.level == 1:
                        target = str(Path(path).parent / (node.module.replace('.', '/') + '.py'))
                    elif node.level == 0 and node.module.startswith('fi.'):
                        target = node.module.replace('.', '/') + '.py'
                    else:
                        continue
                    return resolve_definition(root, target, alias.name, seen)
    raise KeyError(identity)


def resolve_method(root, path, owner, name):
    path, cls = resolve_definition(root, path, owner)
    for node in cls.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            return node
    for base in cls.bases:
        if isinstance(base, ast.Name) and base.id.startswith('_') and base.id.endswith('Methods'):
            try:
                return resolve_method(root, path, base.id, name)
            except KeyError:
                pass
    raise KeyError((path, owner, name))
