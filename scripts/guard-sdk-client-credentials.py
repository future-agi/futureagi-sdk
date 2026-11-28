"""Keep the token of the generated Python ``AuthenticatedClient`` off plain http.

The SDK refuses credentials over http:// to a Future AGI host, to another non-loopback host without
``FI_ALLOW_INSECURE_HTTP=1``, and through a proxy (``fi._core.http_security``). This post-hook gives the
generated ``client.py`` the same check on either httpx client it builds before that client is kept: a client built
with no transport, proxy or mounts of the caller's sends plain http direct with the environment's proxy variables off,
as the SDK's own clients do, and a proxy of the caller's is refused. Each client it builds also removes the
token header, ``Authorization``, ``Cookie``, ``X-Api-Key`` and ``X-Secret-Key`` from a request to an origin other than
``base_url``'s, such as a followed redirect. ``AuthenticatedClient`` leaves out of the caller's headers each header
named like the token header, ``Authorization``, ``Cookie``, ``X-Api-Key`` or ``X-Secret-Key`` in any case, by a
``str`` or a ``bytes`` name, whether they come to it through its ``headers``, ``attrs.evolve`` or ``with_headers``
(on an httpx client it has built too), and sends its own token once, under the token header. Each client the unauthenticated ``Client`` builds
removes ``Authorization``, ``Cookie``, ``X-Api-Key`` and ``X-Secret-Key`` from a request to another origin the same
way; a client of the caller's set through ``set_httpx_client`` or ``set_async_httpx_client`` sends as the caller
built it.

It fails closed. A file with none of the guard in it gets the whole guard; a file that holds the whole guard, as this
hook writes it on a generated file, passes as it is. Any other file (the guard in part, in a comment only, a builder
without the check, a third httpx builder, the token written into ``self._headers``) makes it exit non-zero with the
reasons and leaves the file as it was.

The guarded file is also judged by its structure (``structure_problems``), as code around the guard text can send the
token past the check: a guard name bound other than by its import, code at module level other than imports and
classes, an httpx client built or an httpx request made outside the two builders, ``httpx.Client`` read without a
call, ``.token`` read outside the two builders, or an attribute or module reached by a computed name (``getattr`` or
``setattr`` with a computed name or one naming an attribute of the client, ``vars``, dunder attributes,
``str.format``) makes it exit non-zero with the reasons.
"""

from __future__ import annotations

import ast
import builtins
from pathlib import Path
import sys

IMPORT_AFTER = "from attrs import define, evolve, field\n"
IMPORT = (
    "\nfrom fi._core.http_security import (\n"
    "    httpx_client_proxied,\n"
    "    httpx_client_sdk_built,\n"
    "    require_secure_credentials_url,\n"
    ")\n"
    "from fi._core.proxy_routing import SdkDirectAsyncTransport, SdkDirectTransport\n"
)
FIELD = '    auth_header_name: str = "Authorization"\n'
# The caller's request ``event_hooks`` with ``hook`` run after them, and the test of a request to an origin other than
# ``base_url``'s: the same text in the request hook of ``Client`` and of ``AuthenticatedClient``.
HOOKS = (
    '        hooks = dict(self._httpx_args.get("event_hooks") or {})\n'
    '        hooks["request"] = [*hooks.get("request", ()), hook]\n'
)
OFF_ORIGIN = (
    '        ports = {"http": 80, "https": 443}\n'
    "        base, url = httpx.URL(self._base_url), request.url\n"
    "        if (url.scheme, url.host, url.port or ports.get(url.scheme)) != (\n"
    "            base.scheme,\n"
    "            base.host,\n"
    "            base.port or ports.get(base.scheme),\n"
    "        ):\n"
)
METHOD = (
    '''
    def _token_httpx_args(self, direct: type, hook: Any) -> dict[str, Any]:
        """The caller's ``httpx_args`` with ``hook`` run after the caller's own request ``event_hooks``; with no
        transport, proxy or mounts of the caller's, plain http goes direct with the environment's proxy variables off,
        as the SDK's own clients send it (``fi._core.proxy_routing``)"""
'''
    + HOOKS
    + '''        httpx_args = {**self._httpx_args, "event_hooks": hooks}
        if any(httpx_args.get(name) for name in ("transport", "proxy", "mounts")):
            return httpx_args
        return {**httpx_args, "mounts": {"http://": direct()}}

    def _drop_token_off_origin(self, request: httpx.Request) -> None:
        """Remove the token header, ``Authorization``, ``Cookie``, ``X-Api-Key`` and ``X-Secret-Key`` from a request to
        an origin other than ``base_url``'s (scheme, host or port differ), such as the target of a followed redirect:
        httpx removes only ``Authorization`` there, and sends the cookies of ``cookies=`` to any host"""
'''
    + OFF_ORIGIN
    + '''            for name in {self.auth_header_name, "Authorization", "Cookie", "X-Api-Key", "X-Secret-Key"}:
                request.headers.pop(name, None)

    def _headers_without_token(self, headers: Any) -> dict[Any, Any]:
        """``headers`` less each credential header: a header named ``auth_header_name``, ``Authorization``, ``Cookie``,
        ``X-Api-Key`` or ``X-Secret-Key`` in any case, by a ``str`` name or a ``bytes`` name (read as latin-1, as httpx
        reads it). httpx sends both of two names that differ in case only, so headers copied from another client (its
        httpx ``headers``, or a dict of them or of their ``.raw`` pairs) would send that client's token, cookie or keys
        next to this client's own token"""
        names = {self.auth_header_name.lower(), "authorization", "cookie", "x-api-key", "x-secret-key"}
        return {
            name: value
            for name, value in headers.items()
            if (name.decode("latin-1") if isinstance(name, bytes) else name).lower() not in names
        }

    async def _drop_token_off_origin_async(self, request: httpx.Request) -> None:
        """The request event hook of the ``httpx.AsyncClient``; see ``_drop_token_off_origin``"""
        self._drop_token_off_origin(request)

    def _refuse_plain_http_token(self, client: httpx.Client | httpx.AsyncClient) -> None:
        """Refuse the token over plain http the way the rest of the SDK does (``fi._core.http_security``): a client
        built here sends it to loopback direct, a proxy of the caller's transport, proxy or mounts is refused, and so
        is a remote host the environment's proxy variables route"""
        built = httpx_client_sdk_built(client, self._base_url)
        require_secure_credentials_url(
            self._base_url,
            setting="base_url",
            caller_proxied=not built and httpx_client_proxied(client, self._base_url),
        )
'''
)
CLIENT_FIELD = "    _async_client: httpx.AsyncClient | None = field(default=None, init=False)\n"
CLIENT_METHOD = (
    '''
    def _off_origin_httpx_args(self, hook: Any) -> dict[str, Any]:
        """The caller's ``httpx_args`` with ``hook`` run after the caller's own request ``event_hooks``"""
'''
    + HOOKS
    + '''        return {**self._httpx_args, "event_hooks": hooks}

    def _drop_credentials_off_origin(self, request: httpx.Request) -> None:
        """Remove ``Authorization``, ``Cookie``, ``X-Api-Key`` and ``X-Secret-Key`` from a request to an origin other
        than ``base_url``'s (scheme, host or port differ), such as the target of a followed redirect: httpx removes
        only ``Authorization`` there, and sends the cookies of ``cookies=`` to any host. A client of the caller's
        (``set_httpx_client``, ``set_async_httpx_client``) sends as the caller built it"""
'''
    + OFF_ORIGIN
    + '''            for name in ("Authorization", "Cookie", "X-Api-Key", "X-Secret-Key"):
                request.headers.pop(name, None)

    async def _drop_credentials_off_origin_async(self, request: httpx.Request) -> None:
        """The request event hook of the ``httpx.AsyncClient``; see ``_drop_credentials_off_origin``"""
        self._drop_credentials_off_origin(request)
'''
)
AUTHENTICATED = "class AuthenticatedClient"
TOKEN = '                f"{self.prefix} {self.token}" if self.prefix else self.token\n'
SHARED_HEADERS = "            self._headers[self.auth_header_name] = (\n" + TOKEN + "            )\n"
OPEN = "                base_url=self._base_url,\n                cookies=self._cookies,\n"
ARGS = "                **self._httpx_args,\n            )\n"
# Each builder sends a headers dict of its own: the caller's ``headers`` and a dict shared between clients through
# ``evolve`` stay as passed, so two clients built at the same time each send their own token.
BUILDS = tuple(
    (
        SHARED_HEADERS + f"            self.{name} = httpx.{kind}(\n" + OPEN + "                headers=self._headers,\n",
        f"            httpx_args = self._token_httpx_args({direct}, self.{hook})\n"
        "            headers = {\n                **self._headers_without_token(self._headers),\n                self.auth_header_name: (\n    "
        + TOKEN
        + "                ),\n            }\n"
        f"            client = httpx.{kind}(\n" + OPEN + "                headers=headers,\n",
        ARGS + f"        return self.{name}\n",
        "                **httpx_args,\n            )\n"
        f"            self._refuse_plain_http_token(client)\n            self.{name} = client\n        return self.{name}\n",
    )
    for name, kind, direct, hook in (
        ("_client", "Client", "SdkDirectTransport", "_drop_token_off_origin"),
        ("_async_client", "AsyncClient", "SdkDirectAsyncTransport", "_drop_token_off_origin_async"),
    )
)

# ``with_headers`` on a built ``AuthenticatedClient``: (generated update of the built httpx client, the update with the
# caller's credential headers left out).
WITH_HEADERS = tuple(
    (
        f"            self.{name}.headers.update(headers)\n",
        f"            self.{name}.headers.update(self._headers_without_token(headers))\n",
    )
    for name in ("_client", "_async_client")
)

# The two builders of ``Client``: (generated end, end with the request hook).
CLIENT_BUILDS = tuple(
    (
        ARGS + f"        return self.{name}\n",
        f"                **self._off_origin_httpx_args(self.{hook}),\n            )\n        return self.{name}\n",
    )
    for name, hook in (
        ("_client", "_drop_credentials_off_origin"),
        ("_async_client", "_drop_credentials_off_origin_async"),
    )
)

# Names that only the guard brings into the file: a file that holds any of them is checked as a guarded file.
GUARD_NAMES = (
    "fi._core.http_security",
    "fi._core.proxy_routing",
    "SdkDirect",
    "_token_httpx_args",
    "_drop_token_off_origin",
    "_headers_without_token",
    "_refuse_plain_http_token",
    "_off_origin_httpx_args",
    "_drop_credentials_off_origin",
    "require_secure_credentials_url",
    "httpx_client_proxied",
    "httpx_client_sdk_built",
)
BUILDERS = (("get_httpx_client", "httpx.Client("), ("get_async_httpx_client", "httpx.AsyncClient("))

# The structure of the guarded file (``structure_problems``): the imports it may hold, each bound once, by that
# import alone; the httpx names it may call, and where; the names it may not call or read at all.
GUARD_IMPORTS = {
    "fi._core.http_security": frozenset(
        ("httpx_client_proxied", "httpx_client_sdk_built", "require_secure_credentials_url")
    ),
    "fi._core.proxy_routing": frozenset(("SdkDirectAsyncTransport", "SdkDirectTransport")),
}
MODULE_IMPORTS = frozenset(("ssl", "httpx"))
FROM_IMPORTS = {"attrs": frozenset(("define", "evolve", "field")), "typing": None, **GUARD_IMPORTS}
# ``httpx.<name>`` called outside an annotation, and the builder each must be called in (None: any function).
HTTPX_CALLS = {"Client": "get_httpx_client", "AsyncClient": "get_async_httpx_client", "URL": None}
DYNAMIC_ACCESS = frozenset(("getattr", "setattr", "delattr", "hasattr"))
OPAQUE_NAMES = frozenset(
    ("vars", "globals", "locals", "eval", "exec", "compile", "__import__", "type", "object", "super", "open")
)
CONTEXT_METHODS = frozenset(("__enter__", "__exit__", "__aenter__", "__aexit__"))
# Attributes of the client that hold or send the token, besides the fields and methods of the file's classes.
TOKEN_ATTRIBUTES = frozenset(("token", "prefix", "auth_header_name", "headers", "_headers", "_httpx_args"))
ANNOTATION_NODES = (ast.Name, ast.Attribute, ast.Constant, ast.Subscript, ast.Tuple, ast.List, ast.BinOp, ast.BitOr)
ANNOTATION_NODES += (ast.Load, ast.Index) if hasattr(ast, "Index") else (ast.Load,)
BUILTIN_NAMES = frozenset(dir(builtins))


class Refused(Exception):
    """The file is not one this hook can guard or accept as guarded"""


class _Structure(ast.NodeVisitor):
    """Collect why a parsed guarded file does not have the structure ``structure_problems`` checks"""

    def __init__(self, tree: ast.Module) -> None:
        self.problems: list[str] = []
        self.parents: dict[ast.AST, ast.AST] = {}
        self.annotations: set[ast.AST] = set()
        self.functions: list[str] = []
        self.classes: list[str] = []
        self.httpx_builds: dict[str, int] = {}
        self.bound: dict[str, int] = {}
        self.attributes = set(TOKEN_ATTRIBUTES)
        self.typing_names: set[str] = set()
        for node in ast.walk(tree):
            for child in ast.iter_child_nodes(node):
                self.parents[child] = node
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                self.attributes.add(node.name)
            if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                self.attributes.add(node.target.id)
            annotations = []
            if isinstance(node, ast.arg):
                annotations.append(node.annotation)
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                annotations.append(node.returns)
            elif isinstance(node, ast.AnnAssign):
                annotations.append(node.annotation)
            for annotation in annotations:
                if annotation is None:
                    continue
                for part in ast.walk(annotation):
                    self.annotations.add(part)
                    if not isinstance(part, ANNOTATION_NODES) or (
                        isinstance(part, ast.BinOp) and not isinstance(part.op, ast.BitOr)
                    ):
                        self.refuse(part, f"an annotation holds {type(part).__name__}; an annotation names types only")

    def refuse(self, node: ast.AST, reason: str) -> None:
        self.problems.append(f"line {getattr(node, 'lineno', '?')}: {reason}")

    def bind(self, node: ast.AST, name: str, by_import: bool = False) -> None:
        if name in BUILTIN_NAMES:
            self.refuse(node, f"it binds the builtin name {name}")
        protected = name in MODULE_IMPORTS or any(name in names for names in GUARD_IMPORTS.values())
        if protected and not by_import:
            self.refuse(node, f"it shadows {name}, which the guard calls as imported")
        self.bound[name] = self.bound.get(name, 0) + 1

    def check_module(self, tree: ast.Module) -> None:
        for statement in tree.body:
            docstring = isinstance(statement, ast.Expr) and isinstance(statement.value, ast.Constant)
            if not isinstance(statement, (ast.Import, ast.ImportFrom, ast.ClassDef)) and not docstring:
                kind = type(statement).__name__
                self.refuse(statement, f"a module-level {kind} statement; the guarded client holds imports and classes")
        self.visit(tree)
        for module, names in GUARD_IMPORTS.items():
            for name in sorted(names):
                if self.bound.get(name) != 1:
                    self.problems.append(f"{name} is bound {self.bound.get(name, 0)} times; the guard imports it once")
        for name in sorted(MODULE_IMPORTS):
            if self.bound.get(name, 0) > 1:
                self.problems.append(f"{name} is bound {self.bound[name]} times; the generated file imports it once")

    def visit_Import(self, node: ast.Import) -> None:
        if not isinstance(self.parents.get(node), ast.Module):
            self.refuse(node, "an import inside a function or class")
        for alias in node.names:
            if alias.name not in MODULE_IMPORTS or alias.asname:
                imports = ", ".join(sorted(MODULE_IMPORTS))
                self.refuse(node, f"it imports {alias.name}; the generated client imports {imports}")
            self.bind(node, (alias.asname or alias.name).partition(".")[0], by_import=True)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if not isinstance(self.parents.get(node), ast.Module):
            self.refuse(node, "an import inside a function or class")
        allowed = FROM_IMPORTS.get(node.module or "", frozenset()) if not node.level else frozenset()
        guard_import = node.module in GUARD_IMPORTS
        if node.module == "typing":
            self.typing_names.update(alias.asname or alias.name for alias in node.names)
        for alias in node.names:
            fits = allowed is None or alias.name in allowed
            if not fits or alias.asname or alias.name == "*":
                self.refuse(node, f"it imports {alias.name} from {node.module}, which the guarded client does not")
            self.bind(node, alias.asname or alias.name, by_import=guard_import)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.bind(node, node.name)
        if node.bases or node.keywords:
            self.refuse(node, f"class {node.name} has bases or keywords; the generated classes have none")
        for decorator in node.decorator_list:
            if not (isinstance(decorator, ast.Name) and decorator.id == "define"):
                self.refuse(decorator, f"class {node.name} has a decorator other than define")
        members: set[str] = set()
        for statement in node.body:
            docstring = isinstance(statement, ast.Expr) and isinstance(statement.value, ast.Constant)
            simple_field = isinstance(statement, ast.AnnAssign) and isinstance(statement.target, ast.Name)
            method = isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef))
            if not (docstring or simple_field or method):
                self.refuse(statement, f"class {node.name} holds a {type(statement).__name__} statement")
            member = statement.name if method else statement.target.id if simple_field else None
            if member is not None and member in members:
                self.refuse(statement, f"class {node.name} defines {member} twice; the later one replaces the first")
            members.add(member)
        self.classes.append(node.name)
        self.generic_visit(node)
        self.classes.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        self.bind(node, node.name)
        if node.decorator_list:
            self.refuse(node, f"{node.name} has a decorator; the generated methods have none")
        self.functions.append(node.name)
        self.generic_visit(node)
        self.functions.pop()

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_Lambda(self, node: ast.Lambda) -> None:
        self.functions.append("<lambda>")
        self.generic_visit(node)
        self.functions.pop()

    def visit_arg(self, node: ast.arg) -> None:
        self.bind(node, node.arg)
        self.generic_visit(node)

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
        if node.name:
            self.bind(node, node.name)
        self.generic_visit(node)

    def visit_Global(self, node: ast.Global | ast.Nonlocal) -> None:
        self.refuse(node, f"a {type(node).__name__.lower()} statement; the generated client has none")

    visit_Nonlocal = visit_Global

    def generic_visit(self, node: ast.AST) -> None:
        if type(node).__name__ in ("Match", "TryStar"):
            self.refuse(node, f"a {type(node).__name__} statement; the generated client has none")
        super().generic_visit(node)

    def called(self, node: ast.AST) -> bool:
        parent = self.parents.get(node)
        return isinstance(parent, ast.Call) and parent.func is node

    def visit_Name(self, node: ast.Name) -> None:
        if not isinstance(node.ctx, ast.Load):
            self.bind(node, node.id)
            return
        if node in self.annotations:
            return
        parent = self.parents.get(node)
        if node.id.startswith("__"):
            self.refuse(node, f"it reads {node.id}")
        elif node.id in OPAQUE_NAMES:
            self.refuse(node, f"it reads {node.id}, which reaches attributes and modules by a name it computes")
        elif node.id in DYNAMIC_ACCESS:
            self.check_dynamic_access(node)
        elif node.id == "ssl" or node.id in self.typing_names:
            self.refuse(node, f"it reads {node.id} outside an annotation")
        elif node.id == "httpx" and not isinstance(parent, ast.Attribute):
            self.refuse(node, "it reads the httpx module itself; the guarded client reads httpx.<name> only")

    def check_dynamic_access(self, node: ast.Name) -> None:
        call = self.parents.get(node)
        if not self.called(node) or not isinstance(call, ast.Call):
            self.refuse(node, f"it passes {node.id} around rather than calling it with a literal name")
            return
        name = call.args[1] if len(call.args) > 1 and not call.keywords else None
        if not (isinstance(name, ast.Constant) and isinstance(name.value, str)):
            self.refuse(node, f"it calls {node.id} with a computed attribute name")
        elif name.value in self.attributes or name.value.startswith("__"):
            self.refuse(node, f"it calls {node.id} on {name.value!r}, an attribute of the client the guard covers")

    def visit_Attribute(self, node: ast.Attribute) -> None:
        self.generic_visit(node)
        if node in self.annotations:
            return
        if node.attr.startswith("__") and node.attr not in CONTEXT_METHODS:
            self.refuse(node, f"it reads .{node.attr}")
        if node.attr in ("format", "format_map"):
            self.refuse(node, f"it calls .{node.attr}, which reads attributes by a name in a string")
        if not isinstance(node.ctx, ast.Load):
            on_name = isinstance(node.value, ast.Name) and node.value.id != "self"
            if on_name or node.attr in self.attributes - {"_client", "_async_client"}:
                self.refuse(node, f"it assigns or deletes .{node.attr} on {ast.unparse(node.value)}")
        if node.attr == "token":
            builder = self.functions[-1:] in (["get_httpx_client"], ["get_async_httpx_client"])
            on_self = isinstance(node.value, ast.Name) and node.value.id == "self"
            if not (builder and on_self and self.classes == ["AuthenticatedClient"]):
                self.refuse(node, "it reads .token outside the token header of the two AuthenticatedClient builders")
        if isinstance(node.value, ast.Name) and node.value.id == "httpx":
            self.check_httpx(node)

    def check_httpx(self, node: ast.Attribute) -> None:
        name = f"httpx.{node.attr}"
        if node.attr not in HTTPX_CALLS:
            self.refuse(node, f"it uses {name} outside an annotation; the guarded client calls httpx.Client,"
                        " httpx.AsyncClient and httpx.URL only")
            return
        if not self.called(node):
            self.refuse(node, f"it reads {name} without calling it, so it can be called under another name")
            return
        builder = HTTPX_CALLS[node.attr]
        if builder is None:
            return
        if self.functions != [builder] or len(self.classes) != 1:
            self.refuse(node, f"it calls {name} outside {builder}, so the client it builds skips the guard")
            return
        key = f"{self.classes[0]}.{builder}"
        self.httpx_builds[key] = self.httpx_builds.get(key, 0) + 1
        if self.httpx_builds[key] > 1:
            self.refuse(node, f"{key} calls {name} more than once")


def structure_problems(source: str) -> list[str]:
    """Why the structure of ``source`` lets a request carry the token past the guard; empty when it does not

    The guard text alone does not keep the token behind the check: other code in the file can shadow the guard
    call, replace a guard method, build or call an httpx client the guard does not see, or read the token by a name it
    computes. ``source`` passes when it imports only what the guarded client imports, each guard name bound by its
    import alone; it holds only classes at module level; ``httpx.Client`` and ``httpx.AsyncClient`` are called in
    their builders only and no other httpx request path is used; ``.token`` is read in the two builders only; and no
    code reaches an attribute or module by a computed name (``getattr``, ``setattr``, ``vars``, dunder attributes,
    ``str.format``)."""
    try:
        tree = ast.parse(source)
    except SyntaxError as error:
        return [f"it does not parse as Python: {error}"]
    structure = _Structure(tree)
    structure.check_module(tree)
    return structure.problems


def guard(source: str) -> str:
    """The generated ``source`` with the whole guard; ``Refused`` when an anchor is missing or repeated"""
    head, marker, tail = source.partition(AUTHENTICATED)
    checks = [(source, IMPORT_AFTER), (tail, FIELD)]
    checks += [(tail, text) for build in BUILDS for text in (build[0], build[2])]
    checks += [(tail, update) for update, _ in WITH_HEADERS]
    checks += [(head, CLIENT_FIELD)] + [(head, end) for end, _ in CLIENT_BUILDS]
    for text, anchor in checks:
        if text.count(anchor) != 1:
            raise Refused(f"expected one {anchor.strip()!r} in the generated AuthenticatedClient file")
    head = head.replace(CLIENT_FIELD, CLIENT_FIELD + CLIENT_METHOD)
    for end, hooked in CLIENT_BUILDS:
        head = head.replace(end, hooked)
    tail = tail.replace(FIELD, FIELD + METHOD)
    for start, local, end, checked in BUILDS:
        tail = tail.replace(start, local).replace(end, checked)
    for update, filtered in WITH_HEADERS:
        tail = tail.replace(update, filtered)
    return (head + marker + tail).replace(IMPORT_AFTER, IMPORT_AFTER + IMPORT)


def unguard(source: str) -> str:
    """``source`` with each part of the guard put back as generated, for a ``source`` that holds each part once"""
    head, marker, tail = source.partition(AUTHENTICATED)
    head = head.replace(CLIENT_FIELD + CLIENT_METHOD, CLIENT_FIELD)
    for end, hooked in CLIENT_BUILDS:
        head = head.replace(hooked, end)
    tail = tail.replace(FIELD + METHOD, FIELD)
    for start, local, end, checked in BUILDS:
        tail = tail.replace(local, start).replace(checked, end)
    for update, filtered in WITH_HEADERS:
        tail = tail.replace(filtered, update)
    return (head + marker + tail).replace(IMPORT_AFTER + IMPORT, IMPORT_AFTER)


def guard_problems(source: str) -> list[str]:
    """Why ``source`` does not hold the whole guard as this hook writes it; empty when it does"""
    head, marker, tail = source.partition(AUTHENTICATED)
    if not marker:
        return [f"there is no {AUTHENTICATED}"]
    problems = []
    if head.count(CLIENT_FIELD + CLIENT_METHOD) != 1:
        problems.append(
            "Client does not hold _off_origin_httpx_args and _drop_credentials_off_origin as this hook writes them"
        )
    for (name, call), (_, hooked) in zip(BUILDERS, CLIENT_BUILDS):
        if head.count(call) != 1 or head.count(hooked) != 1:
            problems.append(
                f"Client.{name} does not build one {call} with _drop_credentials_off_origin in its request event hooks"
            )
    if source.count(IMPORT_AFTER + IMPORT) != 1:
        problems.append("the import of fi._core.http_security and fi._core.proxy_routing is missing or altered")
    if tail.count(FIELD + METHOD) != 1:
        problems.append(
            "AuthenticatedClient does not hold _token_httpx_args, _drop_token_off_origin, _headers_without_token and"
            " _refuse_plain_http_token (with its require_secure_credentials_url check) as this hook writes them"
        )
    for (name, call), (_, local, _, checked) in zip(BUILDERS, BUILDS):
        if tail.count(call) != 1:
            problems.append(f"AuthenticatedClient has {tail.count(call)} {call} builders; the guard covers one")
        if tail.count(local) != 1 or tail.count(checked) != 1:
            problems.append(
                f"{name} does not build its {call} with the token in a headers dict of its own and run"
                " self._refuse_plain_http_token(client) before keeping it"
            )
    for (_, call), (update, filtered) in zip(BUILDERS, WITH_HEADERS):
        if tail.count(filtered) != 1 or update in tail:
            problems.append(
                "AuthenticatedClient.with_headers does not leave the caller's credential headers out of the built"
                f" {call[:-1]} through _headers_without_token"
            )
    if "self._headers[" in tail:
        problems.append("AuthenticatedClient writes into self._headers; each builder sends a headers dict of its own")
    if tail.count("self.token") != len(BUILDS) * TOKEN.count("self.token"):
        problems.append("AuthenticatedClient reads self.token outside the token header of its two builders")
    return problems + structure_problems(source)


def checked_source(source: str) -> str:
    """The guarded ``source``: the whole guard added to a generated file, or a guarded file as it is"""
    if not any(name in source for name in GUARD_NAMES):
        result = guard(source)
        problems = guard_problems(result)
    else:
        result = source
        problems = guard_problems(source)
        if problems:
            named = ", ".join(name for name in GUARD_NAMES if name in source)
            problems.insert(0, f"it holds the guard in part or in a comment only (it names {named})")
    if not problems:
        generated = unguard(result)
        if any(name in generated for name in GUARD_NAMES) or guard(generated) != result:
            problems.append("it holds the guard with other text around it than this hook writes on a generated file")
    if problems:
        raise Refused("; ".join(problems))
    return result


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: guard-sdk-client-credentials.py CLIENT")
    path = Path(sys.argv[1])
    source = path.read_text()
    try:
        result = checked_source(source)
    except Refused as refused:
        raise SystemExit(f"guard-sdk-client-credentials.py: refusing {path}: {refused}") from None
    if result != source:
        path.write_text(result)

if __name__ == "__main__":
    main()
