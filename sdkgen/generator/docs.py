"""Emit the platform SDK reference for docs.futureagi.com from the contract + catalog.

One MDX page per top-level resource (nested resources are sections on it), one response-models
page per product area, an overview page, and the sidebar group as `navigation.json`. The pages
use the docs site's components (`ParamField`, `ResponseField`, `CodeGroup`, ...), which its MDX
pipeline imports automatically. The docs repository (future-agi/docs) copies the output into
`src/pages/docs/sdk/reference/` with `scripts/sync-sdk-reference.mjs`; nothing here is edited by
hand.
"""

from __future__ import annotations

import json
import re

from . import python as py
from . import typescript as ts
from .catalog import (
    Op,
    Param,
    class_name,
    is_file,
    is_json_value,
    is_method_field,
    model_refs,
    namespace_tree,
)

SITE_PATH = "/docs/sdk/reference"
NAV_GROUP = "Platform SDK Reference"
INDEX_FILE = "index.mdx"
NAV_FILE = "navigation.json"

# The sidebar groups resources by product area, in this order. A resource missing here lands
# under "Other" so a new catalog resource never breaks the build; place it deliberately after.
AREAS: list[tuple[str, list[str]]] = [
    ("Account", ["account", "workspaces", "usage"]),
    ("Datasets & evals", ["datasets", "evals", "experiments", "optimizations"]),
    ("Prompts", ["prompts"]),
    (
        "Observability",
        [
            "projects",
            "traces",
            "spans",
            "sessions",
            "dashboards",
            "error_clusters",
            "alerts",
        ],
    ),
    ("Annotation", ["annotation_queues", "annotations", "scores"]),
    ("Simulation", ["agents", "simulation"]),
    ("Knowledge bases", ["knowledge_bases", "file_knowledge_bases"]),
    ("Gateway", ["gateway", "models", "provider_keys"]),
]
OTHER_AREA = "Other"


# --------------------------------------------------------------------------- #
# Text helpers
# --------------------------------------------------------------------------- #


def md(text: str) -> str:
    """Plain text for MDX: no JSX or expression starts, one line."""
    text = " ".join(str(text).split())
    return text.replace("{", "\\{").replace("}", "\\}").replace("<", "\\<")


def yaml_str(text: str) -> str:
    return json.dumps(" ".join(str(text).split()))


def slug(text: str) -> str:
    """The id the docs site gives a heading (github-slugger)."""
    text = text.lower()
    text = re.sub(r"[^\w\- ]", "", text)
    return text.replace(" ", "-")


def title_of(ns: tuple[str, ...]) -> str:
    return " ".join(ns[0].split("_")).capitalize()


def page_name(ns: tuple[str, ...]) -> str:
    return ns[0].replace("_", "-")


def page_href(ns: tuple[str, ...]) -> str:
    return f"{SITE_PATH}/{page_name(ns)}"


def area_slug(area: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", area.lower()).strip("-")


def models_page_name(area: str) -> str:
    return f"{area_slug(area)}-models"


def models_href(area: str) -> str:
    return f"{SITE_PATH}/{models_page_name(area)}"


def dotted(ns: tuple[str, ...], lang: str) -> str:
    return (
        ".".join(ns) if lang == "python" else ".".join(ts.ts_attr(part) for part in ns)
    )


def doc_type(schema: dict | None, *, for_input: bool) -> str:
    """A language-neutral type for the parameter and field tables."""
    if not schema:
        return "any"
    if is_file(schema):
        return "file[]" if schema.get("type") == "array" else "file"
    if is_json_value(schema):
        return "any JSON value"
    if "$ref" in schema:
        return "object" if for_input else class_name(schema["$ref"])
    kind = schema.get("type")
    if kind == "array":
        return f"{doc_type(schema.get('items'), for_input=for_input)}[]"
    if kind == "object" and not for_input and not schema.get("properties"):
        return "any"
    return {
        "string": "string",
        "integer": "integer",
        "number": "number",
        "boolean": "boolean",
        "object": "object",
    }.get(kind, "any")


# --------------------------------------------------------------------------- #
# Areas and model homes
# --------------------------------------------------------------------------- #


def areas_of(roots: list[tuple[str, ...]]) -> list[tuple[str, list[tuple[str, ...]]]]:
    """[(area title, [resource namespaces in that area])], in sidebar order, non-empty areas only."""
    placed: set[str] = set()
    out: list[tuple[str, list[tuple[str, ...]]]] = []
    for area, names in AREAS:
        members = [(name,) for name in names if (name,) in roots]
        placed.update(names)
        if members:
            out.append((area, members))
    rest = [root for root in roots if root[0] not in placed]
    if rest:
        out.append((OTHER_AREA, rest))
    return out


def _model_homes(
    spec: dict,
    tree: dict[tuple[str, ...], list[Op]],
    areas: list[tuple[str, list[tuple[str, ...]]]],
) -> dict[str, str]:
    """Which models page documents each response model: the first area (in sidebar order) that reaches it."""
    homes: dict[str, str] = {}
    for area, members in areas:
        ops = [op for ns, group in tree.items() for op in group if (ns[0],) in members]
        for name in model_refs(spec, [op.returns for op in ops if op.returns]):
            homes.setdefault(name, area)
    return homes


def _model_link(name: str, homes: dict[str, str], here: str | None) -> str:
    home = homes[name]
    anchor = f"#{slug(name)}"
    return f"[`{name}`]({anchor if home == here else models_href(home) + anchor})"


# --------------------------------------------------------------------------- #
# Examples and signatures
# --------------------------------------------------------------------------- #


def _example_value(p: Param, lang: str, definitions: dict) -> str:
    return _example_for(p.name, p.schema or {}, lang, definitions, depth=0)


def _example_for(
    name: str, schema: dict, lang: str, definitions: dict, depth: int
) -> str:
    """A value that type-checks against `schema` in both SDKs.

    A `$ref` is resolved before the shape is chosen, so an object-valued field is
    shown as an object literal of its required fields (or, when nothing is
    required, its first enum field, which is usually the one a user sets), never
    as a placeholder string the compiler rejects.
    """
    if is_file(schema):
        return '"path/to/file"'
    if "$ref" in schema and depth < 3:
        target = definitions.get(class_name(schema["$ref"]), {})
        props = target.get("properties", {})
        chosen = [n for n in target.get("required", []) if n in props]
        if not chosen:
            chosen = [n for n, prop in props.items() if prop.get("enum")][:1]
        fields = [
            (n, _example_for(n, props[n], lang, definitions, depth + 1)) for n in chosen
        ]
        if not fields:
            return "{}"
        if lang == "python":
            return "{" + ", ".join(f"{json.dumps(n)}: {v}" for n, v in fields) + "}"
        return "{ " + ", ".join(f"{ts.prop_key(n)}: {v}" for n, v in fields) + " }"
    if schema.get("enum"):
        return json.dumps(schema["enum"][0])
    kind = schema.get("type")
    if is_json_value(schema) or kind == "string" or not kind:
        return json.dumps(f"your-{name.replace('_', '-')}")
    if kind == "integer":
        return "1"
    if kind == "number":
        return "1.0"
    if kind == "boolean":
        return "True" if lang == "python" else "true"
    if kind == "array":
        return "[]"
    return "{}"


def _placeholder(p: Param) -> str:
    """A path argument's example value: `"your-dataset-id"`."""
    return json.dumps(f"your-{py.arg_name(p).replace('_', '-')}")


def real_description(name: str, description: str | None) -> str:
    """drf-yasg fills in the field name as the description ("Source id"); that says nothing, so drop it."""
    if not description:
        return ""
    words = " ".join(description.lower().replace("_", " ").split()).rstrip(".")
    return "" if words == name.lower().replace("_", " ") else description


def _example_params(op: Op) -> list[Param]:
    page_params = {op.pagination["page_param"]} if op.pagination else set()
    return [
        p
        for p in op.params
        if p.location != "path" and p.name not in page_params and p.required
    ]


def python_example(op: Op, definitions: dict) -> str:
    call = f"client.{dotted(op.namespace, 'python')}.{op.method_name}"
    args = [_placeholder(p) for p in op.params_in("path")]
    args += [
        f"{py.arg_name(p)}={_example_value(p, 'python', definitions)}"
        for p in _example_params(op)
    ]
    if len(args) > 2:
        call = f"{call}(\n" + "".join(f"    {a},\n" for a in args) + ")"
    else:
        call = f"{call}({', '.join(args)})"
    if op.pagination:
        return f"for item in {call}:\n    print(item)"
    return f"result = {call}"


def typescript_example(op: Op, definitions: dict) -> str:
    call = f"client.{dotted(op.namespace, 'typescript')}.{ts.ts_method(op)}"
    args = [_placeholder(p) for p in op.params_in("path")]
    fields = [
        f"{ts.prop_key(p.name)}: {_example_value(p, 'typescript', definitions)}"
        for p in _example_params(op)
    ]
    if len(fields) > 1:
        args.append("{\n" + "".join(f"  {f},\n" for f in fields) + "}")
    elif fields:
        args.append("{ " + fields[0] + " }")
    call = f"{call}({', '.join(args)})"
    if op.pagination:
        return f"for await (const item of {call}) {{\n  console.log(item);\n}}"
    return f"const result = await {call};"


def python_signature(op: Op) -> str:
    """The generated method as a user reads it: `client.datasets.get(dataset_id: str, *, ...) -> Model`."""
    args, _ = py._signature(op)
    ret, _ = py._return_annotation(op, is_async=False)
    body = "".join(f"    {a},\n" for a in args[1:])  # drop `self`
    return (
        f"client.{dotted(op.namespace, 'python')}.{op.method_name}(\n{body}) -> {ret}"
    )


def typescript_signature(op: Op) -> str:
    interface, fields = ts._params_interface(op)
    args = [f"{ts.ts_arg(p)}: string" for p in op.params_in("path")]
    if fields:
        optional = "" if any(p.required for p in fields) else " = {}"
        args.append(f"params: {ts.ts_params_type(op)}{optional}")
    args.append("options?: RequestOptions")
    line = f"client.{dotted(op.namespace, 'typescript')}.{ts.ts_method(op)}({', '.join(args)}): {ts._return_type(op)}"
    if not interface:
        return line
    # Drop the doc comments that only restate the field name ("/** Source id */").
    kept = []
    lines = interface.rstrip().splitlines()
    for i, text in enumerate(lines):
        comment = text.strip()
        if comment.startswith("/**") and comment.endswith("*/") and i + 1 < len(lines):
            field = lines[i + 1].strip().split("?")[0].split(":")[0].strip('"')
            if not real_description(field, comment[3:-2].strip()):
                continue
        kept.append(text)
    return f"{line}\n\n" + "\n".join(kept)


# --------------------------------------------------------------------------- #
# Method and model sections
# --------------------------------------------------------------------------- #


def _returns(op: Op, homes: dict[str, str]) -> str:
    returns = op.returns or {}
    if op.decode == "text":
        return "The response body as text."
    if op.decode == "auto":
        return "The decoded JSON when the response is JSON, else the body as text."
    if "$ref" in returns:
        item = _model_link(class_name(returns["$ref"]), homes, None)
    elif returns.get("type") == "array" and "$ref" in returns.get("items", {}):
        item = f"A list of {_model_link(class_name(returns['items']['$ref']), homes, None)}"
    elif not returns:
        return "The decoded response. The contract does not describe its shape, so it is untyped."
    else:
        item = f"`{doc_type(returns, for_input=False)}`"
    if op.pagination:
        return f"A pager of {item} items: iterate it, or call `to_list()` (Python) / `toArray()` (TypeScript)."
    return f"{item}."


def _param_field(p: Param) -> str:
    kind = {"path": "path", "query": "query", "body": "body"}[p.location]
    attrs = [f'{kind}="{p.name}"', f'type="{doc_type(p.schema, for_input=True)}"']
    attrs.append("required" if p.required else "optional")
    schema = p.schema or {}
    if "enum" in schema:
        attrs.append(f"enum={{{json.dumps([str(v) for v in schema['enum']])}}}")
    text = md(real_description(p.name, p.description))
    if p.location == "path" and not text:
        text = f"Positional argument `{py.arg_name(p)}`."
    if not text:
        return f"<ParamField {' '.join(attrs)} />\n"
    return f"<ParamField {' '.join(attrs)}>\n  {text}\n</ParamField>\n"


def _method_section(op: Op, homes: dict[str, str], definitions: dict) -> str:
    out = [f"### {op.id}\n\n", f"{md(op.description)}\n\n"]
    out.append(f'<ApiEndpoint method="{op.method}" path="{op.path}" />\n\n')
    facts = []
    if op.pagination:
        facts.append(
            f"**Paginated**: returns a pager ([how pagination works]({SITE_PATH}#pagination))"
        )
    if op.multipart:
        facts.append(
            "**Multipart upload**: file parameters take a path, bytes or an open file"
        )
    mcp = op.surfaces.get("mcp")
    if mcp:
        facts.append(f"**MCP tool**: `{mcp['name']}`")
    if facts:
        out.append(" · ".join(facts) + "\n\n")
    stability = op.surfaces["sdk"]["stability"]
    if stability == "beta":
        out.append(
            "<Warning>\n  **Beta.** This method may change without notice; calling it emits a one-time warning.\n</Warning>\n\n"
        )
    elif stability == "deprecated":
        out.append(
            "<Warning>\n  **Deprecated.** This method will be removed in a future release.\n</Warning>\n\n"
        )
    out.append(
        "<CodeGroup>\n\n```python Python\n"
        + python_example(op, definitions)
        + "\n```\n\n```typescript TypeScript\n"
        + typescript_example(op, definitions)
        + "\n```\n\n</CodeGroup>\n\n"
    )
    out.append(
        '<Expandable title="Signature">\n\n```python Python\n'
        + python_signature(op)
        + "\n```\n\n```typescript TypeScript\n"
        + typescript_signature(op)
        + "\n```\n\n</Expandable>\n\n"
    )
    page_params = {op.pagination["page_param"]} if op.pagination else set()
    params = [p for p in op.params if p.name not in page_params]
    params.sort(
        key=lambda p: ({"path": 0, "query": 1, "body": 2}[p.location], not p.required)
    )
    out.append("#### Parameters\n\n")
    if params:
        out.append("".join(_param_field(p) for p in params))
    else:
        out.append("This method takes no parameters beyond the per-call `options`.\n")
    if op.pagination:
        out.append(
            f"\nThe pager sends `{op.pagination['page_param']}` itself; pass `{op.pagination['size_param']}` to change the page size.\n"
            if op.pagination.get("size_param")
            else f"\nThe pager sends `{op.pagination['page_param']}` itself.\n"
        )
    out.append(f"\n#### Returns\n\n{_returns(op, homes)}\n\n")
    return "".join(out)


# --------------------------------------------------------------------------- #
# Pages
# --------------------------------------------------------------------------- #


def _first_sentence(text: str) -> str:
    text = " ".join(text.split())
    match = re.match(r"(.+?[.!?])(\s|$)", text)
    return match.group(1) if match else text


def _frontmatter(title: str, description: str) -> str:
    return (
        f"---\ntitle: {yaml_str(title)}\ndescription: {yaml_str(description)}\n---\n\n"
    )


def resource_page(
    tree: dict[tuple[str, ...], list[Op]],
    root: tuple[str, ...],
    area: str,
    homes: dict[str, str],
    definitions: dict,
) -> str:
    namespaces = [root] + sorted(ns for ns in tree if ns[0] == root[0] and ns != root)
    ops = [
        op for ns in namespaces for op in sorted(tree[ns], key=lambda o: o.method_name)
    ]
    names = [op.id for op in ops]
    listed = ", ".join(names[:6]) + (
        f" and {len(names) - 6} more" if len(names) > 6 else ""
    )
    description = f"Reference for client.{root[0]} in the Future AGI Python and TypeScript SDKs: {listed}."
    out = [_frontmatter(title_of(root), description)]
    nested = [f"`client.{dotted(ns, 'python')}`" for ns in namespaces[1:]]
    out.append(
        f"`client.{dotted(root, 'python')}` on `fi.Client` (Python) and `client.{dotted(root, 'typescript')}` on `Client` from `@future-agi/sdk` (TypeScript)"
        + (f", with the nested resources {', '.join(nested)}" if nested else "")
        + f". The models these methods return are on [{area} response models]({models_href(area)}); "
        f"how arguments, pagination, errors and strict mode work is in the [overview]({SITE_PATH}).\n\n"
    )
    # Tables sit in a bounded scroller (<div class="sdk-ref-table">, styled by the docs
    # site) so a long identifier scrolls inside the table instead of widening a phone page.
    out.append(
        '## Methods\n\n<div class="sdk-ref-table">\n\n| Method | Description |\n|---|---|\n'
    )
    for op in ops:
        summary = md(_first_sentence(op.description)).replace("|", "\\|")
        out.append(f"| [`{op.id}`](#{slug(op.id)}) | {summary} |\n")
    out.append("\n</div>\n\n")
    for ns in namespaces:
        out.append(f"## client.{dotted(ns, 'python')}\n\n")
        if ns != root:
            out.append(f"TypeScript: `client.{dotted(ns, 'typescript')}`.\n\n")
        for op in sorted(tree[ns], key=lambda o: o.method_name):
            out.append(_method_section(op, homes, definitions))
    return "".join(out).rstrip() + "\n"


def _field_cell(spec: dict, name: str, homes: dict[str, str], here: str) -> str:
    """Every field of a model as `name: type`, model types linked to their row."""
    props = spec["definitions"][name].get("properties", {})
    if not props:
        return "No fields are described in the contract."
    cells = []
    for field, prop in props.items():
        kind = "any" if is_method_field(prop) else doc_type(prop, for_input=False)
        ref = prop.get("$ref") or (
            prop.get("items", {}).get("$ref") if prop.get("type") == "array" else None
        )
        if ref and class_name(ref) in homes:
            link = _model_link(class_name(ref), homes, here)
            suffix = "[]" if prop.get("type") == "array" else ""
            cells.append(f"`{field}:` {link}{suffix}")
        else:
            cells.append(f"`{field}: {kind}`")
    return ", ".join(cells).replace("|", "\\|")


def models_page(
    spec: dict, area: str, members: list[tuple[str, ...]], homes: dict[str, str]
) -> str:
    names = sorted(name for name, home in homes.items() if home == area)
    resources = ", ".join(f"`client.{m[0]}`" for m in members)
    title = f"{area} response models"
    description = f"The {len(names)} response models returned by the {area.lower()} resources of the Future AGI Python and TypeScript SDKs, with every field and its type."
    out = [_frontmatter(title, description)]
    out.append(
        f"The models returned by {resources}, importable from `fi.platform.models` (Python) and `@future-agi/sdk/platform/models` (TypeScript). "
        "Types are language-neutral: `string[]` is a Python `list[str]` and a TypeScript `string[]`, and a type named after another model links to that model. "
        "Parsing is tolerant by default: a response that leaves a field out or adds one never breaks a call. "
        f"In Python, `Client(strict_responses=True)` rejects a response that misses a field the contract requires (see the [overview]({SITE_PATH}#strict-mode)); TypeScript has no strict mode.\n\n"
    )
    out.append(
        '## Models\n\n<div class="sdk-ref-table">\n\n| Model | Fields |\n|---|---|\n'
    )
    for name in names:
        definition = spec["definitions"][name]
        label = f'<span id="{slug(name)}">`{name}`</span>'
        if definition.get("description"):
            label += "<br/>" + md(definition["description"]).replace("|", "\\|")
        out.append(f"| {label} | {_field_cell(spec, name, homes, area)} |\n")
    out.append("\n</div>\n")
    return "".join(out).rstrip() + "\n"


def index_page(
    tree: dict[tuple[str, ...], list[Op]],
    areas: list[tuple[str, list[tuple[str, ...]]]],
) -> str:
    total = sum(len(group) for group in tree.values())
    roots = [root for _, members in areas for root in members]
    out = [
        _frontmatter(
            "Platform SDK reference",
            "Every method of the Future AGI platform client in Python and TypeScript: the client, conventions for arguments, pagination, errors and strict mode, and one page per resource.",
        )
    ]
    out.append(
        "<TLDR>\n"
        "- One client, every API: `fi.Client` (Python, `pip install futureagi`) and `Client` from `@future-agi/sdk` (TypeScript)\n"
        f"- {total} methods across {len(roots)} resources, generated from the API contract; each page lists parameters, return types and the REST endpoint\n"
        "- Omitted arguments are not sent, `None` / `null` is; list calls return pagers; HTTP errors raise typed exceptions\n"
        "</TLDR>\n\n"
    )
    out.append(
        "The platform client is generated from the Future AGI API contract, so every REST operation has one method with the same name in Python and TypeScript. "
        "This reference is generated from the same source as the SDKs. For narrative guides, see the [SDK overview](/docs/sdk).\n\n"
        "## The client\n\n"
        "Credentials come from the constructor or from the environment: `FI_API_KEY`, `FI_SECRET_KEY`, and optionally `FI_BASE_URL` and `FI_WORKSPACE_ID`.\n\n"
        "<CodeGroup>\n\n"
        "```python Python\n"
        "from fi import Client\n\n"
        "client = Client()  # or Client(api_key=..., secret_key=..., base_url=...)\n"
        "for dataset in client.datasets.list():\n"
        "    print(dataset.name)\n"
        "```\n\n"
        "```typescript TypeScript\n"
        'import { Client } from "@future-agi/sdk";\n\n'
        "const client = new Client(); // or new Client({ apiKey, secretKey, baseUrl })\n"
        "for await (const dataset of client.datasets.list()) {\n"
        "  console.log(dataset.name);\n"
        "}\n"
        "```\n\n"
        "</CodeGroup>\n\n"
        "Python also ships `AsyncClient` with the same methods, awaited (`await client.datasets.get(...)`, `async for` over pagers).\n\n"
        '<ParamField name="api_key / apiKey" type="string" optional>\n  Defaults to `FI_API_KEY`.\n</ParamField>\n'
        '<ParamField name="secret_key / secretKey" type="string" optional>\n  Defaults to `FI_SECRET_KEY`.\n</ParamField>\n'
        '<ParamField name="base_url / baseUrl" type="string" optional>\n  Defaults to `FI_BASE_URL`, then `https://api.futureagi.com`.\n</ParamField>\n'
        '<ParamField name="workspace_id / workspaceId" type="string" optional>\n  Defaults to `FI_WORKSPACE_ID`. Sent as `X-Workspace-Id`.\n</ParamField>\n'
        '<ParamField name="timeout" type="number" optional>\n  Per-request timeout: seconds in Python (default 60), milliseconds in TypeScript (default 60000).\n</ParamField>\n'
        '<ParamField name="max_retries / maxRetries" type="integer" optional>\n  Default 2. Retries 429 on every call, and timeouts and 5xx on calls that are safe to repeat.\n</ParamField>\n'
        '<ParamField name="default_headers / defaultHeaders" type="object" optional>\n  Sent with every request.\n</ParamField>\n'
        '<ParamField name="strict_responses" type="boolean" optional>\n  Python only. Reject a response that misses a field the contract marks required (see Strict mode).\n</ParamField>\n'
        '<ParamField name="http_client / fetch" type="object" optional>\n  Python: an `httpx.Client` (or `httpx.AsyncClient`) to use instead of the SDK\'s own. TypeScript: a replacement for the global `fetch`.\n</ParamField>\n\n'
        "## Conventions\n\n"
        "### Arguments\n\n"
        "Path parameters are positional; every other parameter is a keyword argument in Python and a field of the `params` object in TypeScript. "
        "An argument you leave out is not sent. Passing `None` (Python) or `null` (TypeScript) sends `null`, which clears a nullable field. "
        "In Python the omitted-argument sentinel is `fi.platform.NOT_GIVEN`.\n\n"
        "A `PATCH` is always a partial update: send only the fields you want to change.\n\n"
        "Fields the contract does not describe yet go through the escape hatches: `extra_query=` and `extra_body=` in Python, `options.extraQuery` and `options.extraBody` in TypeScript.\n\n"
        "### Per-call options\n\n"
        "Every method accepts `options` (`fi.platform.RequestOptions` / `RequestOptions`) with `headers`, `timeout` and `max_retries` / `maxRetries` overrides for that one call.\n\n"
        "### Pagination\n\n"
        "A method marked *paginated* returns a pager instead of a list and fetches pages as you iterate. "
        "Python `SyncPager` / `AsyncPager`: iterate, or `first_page()` for one `Page` (`items`, `number`, `raw`), or `to_list(limit=None)`. "
        "TypeScript `Pager`: `for await`, or `firstPage()`, or `toArray(limit?)`.\n\n"
        "### Responses\n\n"
        "Responses are parsed into models (`fi.platform.models` / `@future-agi/sdk/platform/models`), documented on the response-models page of each area below. "
        "Parsing is tolerant: a field the backend leaves out is `None` / `undefined`, an extra field is kept. "
        "The backend's `{status, result}` envelope is unwrapped for you.\n\n"
        "### Strict mode\n\n"
        "`Client(strict_responses=True)` (Python) raises `ResponseValidationError` when a response misses a field the contract marks required. "
        "Use it in tests to catch contract drift; leave it off in production.\n\n"
        "### Errors\n\n"
        "HTTP errors raise a subclass of `APIError` with `status_code` / `status`, `body`, `detail` and `request_id` / `requestId`. "
        "Import the error classes from `fi.platform` (Python) and from **`@future-agi/sdk/platform`** (TypeScript): the package root does not export them, "
        "and its `RateLimitError` is an older, unrelated class that an `instanceof` check against platform errors never matches.\n\n"
        "<CodeGroup>\n```python Python\nfrom fi.platform import APIError, NotFoundError, RateLimitError\n```\n\n"
        '```typescript TypeScript\nimport { APIError, NotFoundError, RateLimitError } from "@future-agi/sdk/platform";\n```\n</CodeGroup>\n\n'
        '<div class="sdk-ref-table">\n\n| Status | Error |\n|---|---|\n'
        "| 400 | `BadRequestError` |\n| 401 | `AuthenticationError` |\n| 402 | `PaymentRequiredError` |\n| 403 | `PermissionDeniedError` |\n"
        "| 404 | `NotFoundError` |\n| 409 | `ConflictError` |\n| 422 | `UnprocessableEntityError` |\n| 429 | `RateLimitError` |\n| 5xx | `InternalServerError` |\n\n</div>\n\n"
        "Network failures raise `APIConnectionError`. All of them extend `FutureAGIError`.\n\n"
        "### Stability\n\n"
        "A method marked **Beta** may change without notice; the first call emits a `BetaWarning` (Python) or a console warning (TypeScript).\n\n"
        "### Any endpoint\n\n"
        "`client.request(method, path, ...)` calls any endpoint under the base URL with the client's authentication, retries and error handling, for operations this reference does not list yet.\n\n"
        "## Resources\n\n"
    )
    for area, members in areas:
        out.append(f"### {area}\n\n<CardGroup cols={{2}}>\n")
        for root in members:
            count = sum(len(tree[ns]) for ns in tree if ns[0] == root[0])
            out.append(
                f'  <Card title="{title_of(root)}" href="{page_href(root)}">\n    `client.{root[0]}`: {count} method{"s" if count != 1 else ""}.\n  </Card>\n'
            )
        out.append(
            f'  <Card title="Response models" href="{models_href(area)}">\n    What the {area.lower()} methods return.\n  </Card>\n'
        )
        out.append("</CardGroup>\n\n")
    return "".join(out).rstrip() + "\n"


def navigation(areas: list[tuple[str, list[tuple[str, ...]]]]) -> str:
    """The sidebar group: Overview, then one sub-heading per product area with its resources and models page."""
    items: list[dict] = [{"title": "Overview", "href": SITE_PATH}]
    for area, members in areas:
        children = [
            {"title": title_of(root), "href": page_href(root)} for root in members
        ]
        children.append({"title": "Response models", "href": models_href(area)})
        items.append({"title": area, "items": children})
    return (
        json.dumps({"group": NAV_GROUP, "icon": "code", "items": items}, indent=2)
        + "\n"
    )


def emit_pages(spec: dict, ops: list[Op]) -> dict[str, str]:
    """{file name: text} for every reference page plus the navigation fragment."""
    tree = namespace_tree(
        ops
    )  # parents without methods of their own are present, with an empty list
    roots = sorted(ns for ns in tree if len(ns) == 1)
    areas = areas_of(roots)
    homes = _model_homes(spec, tree, areas)
    out = {INDEX_FILE: index_page(tree, areas), NAV_FILE: navigation(areas)}
    for area, members in areas:
        for root in members:
            out[f"{page_name(root)}.mdx"] = resource_page(
                tree, root, area, homes, spec.get("definitions", {})
            )
        out[f"{models_page_name(area)}.mdx"] = models_page(spec, area, members, homes)
    return out
