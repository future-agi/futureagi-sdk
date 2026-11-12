/**
 * Test fixture (not shipped API): a mock sandbox API driven by the scoped customer contract
 * (openapi/platform/generated/futureagi-platform.openapi.json). Every request is matched to a contract
 * operation by method and path template and checked against it (path parameter patterns, declared query keys,
 * required headers, the request body's media type and schema); every JSON response, canned or scripted, is
 * checked against the operation's response schema for its status. A violation is recorded in `problems`, never
 * thrown into the SDK (a throw would surface as a connection error); tests assert `problems` is empty.
 * The files routes keep the service's path rule before any answer, scripted or default: a file path is relative to
 * `/workspace`, so an absolute one, a `.` or `..` segment, a backslash or a NUL is answered with a 400 (see
 * `files-path-rule.ts`). No socket is opened.
 */

import { readFileSync } from "node:fs";
import { join } from "node:path";

import { refusedFilePath } from "./files-path-rule";

type Json = Record<string, unknown>;

export const SPEC_PATH = join(__dirname, "..", "..", "..", "..", "..", "openapi", "platform", "generated", "futureagi-platform.openapi.json");
export const BASE = "https://sandbox.test/omega/api";
export const SID = "sbx_" + "a".repeat(24);
export const SID2 = "sbx_" + "b".repeat(24);
export const SNAP = "snap_" + "c".repeat(24);
export const EXEC = "exec_" + "d".repeat(24);
export const AT = "2026-11-11T00:00:00.000Z";

const PATTERNS: Readonly<Record<string, string>> = {
  "^(sbx_[a-f0-9]{24}|agent-task-[A-Za-z0-9._-]{1,120})$": SID,
  "^snap_[a-f0-9]{24}$": SNAP,
  "^exec_[a-f0-9]{24}$": EXEC,
  "^req_[0-9a-f]{32}$": "req_" + "0".repeat(32),
  "^sha256:[a-f0-9]{64}$": "sha256:" + "a".repeat(64),
  "^[a-f0-9]{64}$": "a".repeat(64),
  "^[a-z][a-z0-9-]{1,40}$": "python",
  "^[0-9]+$": "1",
};

let loaded: Json | undefined;
/** The scoped contract, read once. */
export function spec(): Json {
  loaded ??= JSON.parse(readFileSync(SPEC_PATH, "utf8")) as Json;
  return loaded;
}

const isRecord = (v: unknown): v is Json => v !== null && typeof v === "object" && !Array.isArray(v);

function resolve(schema: unknown): Json {
  let node = schema;
  for (let depth = 0; isRecord(node) && typeof node.$ref === "string" && depth < 32; depth += 1) {
    let target: unknown = spec();
    for (const part of node.$ref.replace(/^#\//u, "").split("/")) target = isRecord(target) ? target[part] : undefined;
    node = target;
  }
  return isRecord(node) ? node : {};
}

/** A minimal instance of a schema: required properties only, first alternatives, minimum values. */
export function sampleOf(schema: unknown): unknown {
  const s = resolve(schema);
  if ("const" in s) return s.const;
  if (Array.isArray(s.enum)) return s.enum[0];
  for (const key of ["oneOf", "anyOf"] as const) if (Array.isArray(s[key])) return sampleOf((s[key] as unknown[])[0]);
  let type = Array.isArray(s.type) ? s.type[0] : s.type;
  if (type === undefined && isRecord(s.properties)) type = "object";
  if (type === "object") {
    const props = isRecord(s.properties) ? s.properties : {};
    const out: Json = {};
    for (const key of (s.required as string[] | undefined) ?? []) if (key in props) out[key] = sampleOf(props[key]);
    return out;
  }
  if (type === "array") return Array.from({ length: typeof s.minItems === "number" ? s.minItems : 0 }, () => sampleOf(s.items));
  if (type === "string") {
    if (typeof s.pattern === "string") return PATTERNS[s.pattern] ?? "x";
    if (s.format === "date-time") return AT;
    return "x".repeat(Math.max(1, typeof s.minLength === "number" ? s.minLength : 1));
  }
  if (type === "integer" || type === "number") return typeof s.minimum === "number" ? s.minimum : 0;
  if (type === "boolean") return false;
  return null;
}

function typeOk(type: unknown, v: unknown): boolean {
  switch (type) {
    case "integer": return Number.isInteger(v);
    case "number": return typeof v === "number";
    case "string": return typeof v === "string";
    case "boolean": return typeof v === "boolean";
    case "null": return v === null;
    case "object": return isRecord(v);
    case "array": return Array.isArray(v);
    default: return true;
  }
}

/** Schema violations of `value` (type, required, unknown keys, enum, const, pattern, alternatives, items). */
export function violations(schema: unknown, value: unknown, path = "$"): string[] {
  const s = resolve(schema);
  const out: string[] = [];
  for (const key of ["anyOf", "oneOf"] as const) {
    if (Array.isArray(s[key]) && !(s[key] as unknown[]).some((alt) => violations(alt, value, path).length === 0)) {
      out.push(`${path}: matches no ${key} alternative`);
    }
  }
  for (const alt of (s.allOf as unknown[] | undefined) ?? []) out.push(...violations(alt, value, path));
  if ("const" in s && value !== s.const) out.push(`${path}: is not ${JSON.stringify(s.const)}`);
  if (Array.isArray(s.enum) && !s.enum.includes(value)) out.push(`${path}: ${JSON.stringify(value)} is not in the enum`);
  const types = s.type === undefined ? [] : Array.isArray(s.type) ? s.type : [s.type];
  if (types.length > 0 && !types.some((t) => typeOk(t, value))) return [...out, `${path}: expected ${types.join("|")}`];
  if (typeof value === "string" && typeof s.pattern === "string" && !new RegExp(s.pattern).test(value)) out.push(`${path}: does not match ${s.pattern}`);
  if (isRecord(value) && (types.includes("object") || isRecord(s.properties))) {
    const props = isRecord(s.properties) ? s.properties : {};
    for (const key of (s.required as string[] | undefined) ?? []) if (!(key in value)) out.push(`${path}.${key}: required`);
    for (const [key, item] of Object.entries(value)) {
      if (key in props) out.push(...violations(props[key], item, `${path}.${key}`));
      else if (s.additionalProperties === false) out.push(`${path}.${key}: not in the schema`);
      else if (isRecord(s.additionalProperties)) out.push(...violations(s.additionalProperties, item, `${path}.${key}`));
    }
  }
  if (Array.isArray(value) && s.items !== undefined) value.forEach((item, i) => out.push(...violations(s.items, item, `${path}[${i}]`)));
  return out;
}

/** One sandbox operation of the scoped contract. */
export interface SpecOperation {
  readonly method: string;
  readonly template: string;
  readonly operationId: string;
  /** `<family>.<method>` from `x-omega-sdk`. */
  readonly sdkName: string;
  readonly humanOnly: boolean;
  readonly op: Json;
  readonly matcher: RegExp;
  readonly pathParams: string[];
}

/** Every operation of the `sandboxes` family in the scoped contract. */
export function sandboxOperations(): SpecOperation[] {
  const out: SpecOperation[] = [];
  for (const [template, item] of Object.entries(spec().paths as Json)) {
    for (const [method, op] of Object.entries(item as Json)) {
      if (!isRecord(op) || !isRecord(op["x-omega-sdk"]) || op["x-omega-sdk"].family !== "sandboxes") continue;
      const pathParams: string[] = [];
      const pattern = template.replace(/[.*+?^$()|[\]\\]/gu, "\\$&").replace(/\\?\{([^}]+)\\?\}/gu, (_m, name: string) => {
        pathParams.push(name);
        return name === "path" ? "(.+)" : "([^/]+)";
      });
      out.push({
        method: method.toUpperCase(),
        template,
        operationId: String(op.operationId),
        sdkName: `sandboxes.${String(op["x-omega-sdk"].method)}`,
        humanOnly: op["x-omega-human-only"] === true,
        op,
        matcher: new RegExp(`^${pattern}$`, "u"),
        pathParams,
      });
    }
  }
  // a literal segment wins over a parameter (`/workspace/sandboxes/settings` is not a sandbox id)
  return out.sort((a, b) => a.pathParams.length - b.pathParams.length);
}

function successSchema(op: Json): { status: number; schema?: unknown; media?: string } {
  const responses = op.responses as Json;
  const code = Object.keys(responses).find((c) => c.startsWith("2")) ?? "200";
  const content = (responses[code] as Json).content as Json | undefined;
  const media = content !== undefined ? Object.keys(content)[0] : undefined;
  return { status: Number(code), ...(media !== undefined ? { media, schema: (content![media] as Json).schema } : {}) };
}

function merge(base: unknown, over: unknown): unknown {
  if (!isRecord(base) || !isRecord(over)) return over;
  const out: Json = { ...base };
  for (const [key, value] of Object.entries(over)) out[key] = merge(base[key], value);
  return out;
}

/** What the mock saw for one request. */
export interface MockCall {
  readonly request: Request;
  readonly operation: SpecOperation;
  readonly params: Readonly<Record<string, string>>;
  readonly query: URLSearchParams;
  /** The request body as text ("" when none). */
  readonly text: string;
  /** The JSON request body, when it was JSON. */
  readonly json?: unknown;
}

export type Handler = (call: MockCall) => Response | Promise<Response>;

/** An SSE body from `[event, data, id?]` frames. */
export function sseText(frames: readonly (readonly [string, unknown, string?])[]): string {
  return frames.map(([event, data, id]) => `${id !== undefined ? `id: ${id}\n` : ""}event: ${event}\ndata: ${JSON.stringify(data)}\n\n`).join("");
}

/** A streamed response that sends `chunks` (bytes or text) one by one; `hold` keeps it open until cancelled. */
export function streamed(
  chunks: readonly (string | Uint8Array)[],
  options: { hold?: boolean; fail?: Error; onCancel?: () => void; contentType?: string } = {},
): Response {
  const queue = chunks.map((c) => (typeof c === "string" ? new TextEncoder().encode(c) : c));
  let index = 0;
  const body = new ReadableStream<Uint8Array>({
    pull(controller) {
      if (index < queue.length) {
        controller.enqueue(queue[index]!);
        index += 1;
        return undefined;
      }
      if (options.fail !== undefined) return controller.error(options.fail);
      if (options.hold === true) return new Promise<void>(() => undefined);
      controller.close();
      return undefined;
    },
    cancel() {
      options.onCancel?.();
    },
  });
  return new Response(body, { status: 200, headers: { "content-type": options.contentType ?? "text/event-stream" } });
}

/** A JSON response. */
export const json = (status: number, body?: unknown, headers: Record<string, string> = {}): Response =>
  new Response(body === undefined ? null : JSON.stringify(body), { status, headers: { "content-type": "application/json", ...headers } });

/** A mock sandbox API at `base`, answering from the contract unless a handler is scripted. */
export class SandboxApi {
  readonly calls: MockCall[] = [];
  readonly problems: string[] = [];
  readonly operations = sandboxOperations();
  readonly #scripts = new Map<string, Handler[]>();

  constructor(readonly base: string = BASE) {}

  /** Script the answers for one operation (by operationId); the last one repeats. */
  on(operationId: string, ...handlers: Handler[]): this {
    if (!this.operations.some((o) => o.operationId === operationId)) this.problems.push(`scripted an unknown operation ${operationId}`);
    this.#scripts.set(operationId, handlers);
    return this;
  }

  /** The contract's minimal success body for an operation, with `overrides` merged in. */
  sample(operationId: string, overrides: unknown = {}): unknown {
    const op = this.operations.find((o) => o.operationId === operationId);
    if (op === undefined) throw new Error(`no operation ${operationId}`);
    const { schema } = successSchema(op.op);
    return merge(sampleOf(schema), overrides);
  }

  /** A success response for an operation, from the contract's sample plus `overrides`. */
  ok(operationId: string, overrides: unknown = {}, headers: Record<string, string> = {}): Response {
    const op = this.operations.find((o) => o.operationId === operationId)!;
    return json(successSchema(op.op).status, this.sample(operationId, overrides), headers);
  }

  /** The calls made to one operation. */
  callsTo(operationId: string): MockCall[] {
    return this.calls.filter((c) => c.operation.operationId === operationId);
  }

  readonly fetch: typeof fetch = (async (input: RequestInfo | URL, init?: RequestInit): Promise<Response> => {
    const request = new Request(input as RequestInfo, init);
    const text = request.body === null ? "" : await request.clone().text();
    const url = new URL(request.url);
    if (!request.url.startsWith(`${this.base}/`)) {
      this.problems.push(`request outside the base: ${request.method} ${url.origin}${url.pathname}`);
      return json(599, { code: "mock_outside_base", message: "outside the base" });
    }
    const rawPath = request.url.slice(this.base.length).split("?")[0]!;
    let match: { operation: SpecOperation; values: RegExpExecArray } | undefined;
    for (const operation of this.operations) {
      const values = operation.matcher.exec(rawPath);
      if (operation.method === request.method && values !== null) {
        match = { operation, values };
        break;
      }
    }
    if (match === undefined) {
      this.problems.push(`no contract operation for ${request.method} ${rawPath}`);
      return json(599, { code: "mock_no_operation", message: "no operation" });
    }
    const { operation, values } = match;
    const params: Record<string, string> = {};
    operation.pathParams.forEach((name, i) => {
      params[name] = name === "path" ? values[i + 1]!.split("/").map(decodeURIComponent).join("/") : decodeURIComponent(values[i + 1]!);
    });
    const call: MockCall = { request, operation, params, query: url.searchParams, text, ...this.#body(operation, request, text) };
    this.calls.push(call);
    this.#check(call);
    const script = this.#scripts.get(operation.operationId);
    const used = this.callsTo(operation.operationId).length - 1;
    const handler = script !== undefined && script.length > 0 ? script[Math.min(used, script.length - 1)]! : (c: MockCall) => this.#default(c);
    const response = refusedFilePath(call) ?? (await handler(call));
    await this.#checkResponse(operation, response);
    return response;
  }) as typeof fetch;

  #body(operation: SpecOperation, request: Request, text: string): { json?: unknown } {
    if (!(request.headers.get("content-type") ?? "").startsWith("application/json") || text === "") return {};
    try {
      return { json: JSON.parse(text) };
    } catch {
      this.problems.push(`${operation.operationId}: the JSON body does not parse`);
      return {};
    }
  }

  #check(call: MockCall): void {
    const { operation, request, params, query, text } = call;
    const where = operation.operationId;
    const declared = ((operation.op.parameters as Json[] | undefined) ?? []).map((p) => resolve(p));
    for (const p of declared.filter((d) => d.in === "path")) {
      const schema = resolve(p.schema);
      const value = params[String(p.name)];
      if (value === undefined || value === "") this.problems.push(`${where}: path parameter ${String(p.name)} is empty`);
      else if (typeof schema.pattern === "string" && !new RegExp(schema.pattern).test(value)) {
        this.problems.push(`${where}: path parameter ${String(p.name)}=${value} does not match ${schema.pattern}`);
      }
    }
    const queryNames = new Set(declared.filter((d) => d.in === "query").map((d) => String(d.name)));
    for (const key of query.keys()) if (!queryNames.has(key)) this.problems.push(`${where}: undeclared query key ${key}`);
    for (const p of declared.filter((d) => d.in === "query")) {
      const value = query.get(String(p.name));
      if (value !== null && violations(p.schema, resolve(p.schema).type === "integer" ? Number(value) : value).length > 0) {
        this.problems.push(`${where}: query ${String(p.name)}=${value} violates its schema`);
      }
    }
    for (const p of declared.filter((d) => d.in === "header" && d.required === true)) {
      if (!request.headers.has(String(p.name))) this.problems.push(`${where}: required header ${String(p.name)} is missing`);
    }
    const body = operation.op.requestBody as Json | undefined;
    if (body === undefined) {
      if (text !== "") this.problems.push(`${where}: sent a body the operation does not take`);
      return;
    }
    const content = (body.content ?? {}) as Json;
    const media = Object.keys(content)[0]!;
    const contentType = request.headers.get("content-type") ?? "";
    if (!contentType.startsWith(media)) this.problems.push(`${where}: content-type ${contentType} is not ${media}`);
    if (body.required === true && text === "") this.problems.push(`${where}: the required body is missing`);
    if (media === "application/json" && call.json !== undefined) {
      for (const v of violations((content[media] as Json).schema, call.json)) this.problems.push(`${where} request ${v}`);
    }
  }

  async #checkResponse(operation: SpecOperation, response: Response): Promise<void> {
    const responses = operation.op.responses as Json;
    const declared = (responses[String(response.status)] ?? responses.default) as Json | undefined;
    if (declared === undefined) {
      this.problems.push(`${operation.operationId}: status ${response.status} is not in the contract`);
      return;
    }
    if (!(response.headers.get("content-type") ?? "").startsWith("application/json")) return;
    const text = await response.clone().text();
    if (text === "") return;
    const ref = resolve(declared);
    const schema = ((ref.content as Json | undefined)?.["application/json"] as Json | undefined)?.schema;
    if (schema === undefined) return;
    for (const v of violations(schema, JSON.parse(text))) this.problems.push(`${operation.operationId} ${response.status} response ${v}`);
  }

  #default(call: MockCall): Response {
    const id = call.operation.operationId;
    if (id === "execInWorkspaceSandbox") {
      return streamed([
        sseText([["started", { execId: EXEC, sandboxId: call.params.id }, "1"], ["stdout", { data: "hello\n" }, "2"]]),
        sseText([["exit", { exitCode: 0, timedOut: false, cancelled: false, truncated: false, durationMs: 5, stdoutBytes: 6, stderrBytes: 0 }, "3"]]),
      ]);
    }
    if (id === "downloadWorkspaceSandboxFile") {
      return new Response(new Uint8Array([0, 1, 2, 255]), { status: 200, headers: { "content-type": "application/octet-stream" } });
    }
    const sandboxFor: Record<string, unknown> = { id: call.params.id ?? SID };
    if (id === "restoreWorkspaceSandboxSnapshot") return this.ok(id, { sandbox: { id: SID2, origin: "restored" } });
    if (id === "destroyWorkspaceSandbox") return this.ok(id, { sandbox: { ...sandboxFor, state: "destroyed" } });
    if (id === "hibernateWorkspaceSandbox") return this.ok(id, { sandbox: { ...sandboxFor, state: "hibernated" } });
    const sample = this.sample(id);
    return this.ok(id, isRecord(sample) && "sandbox" in sample ? { sandbox: sandboxFor } : {});
  }
}
