/** FA management semantics over the shared policy executor; no service URLs. */
import { apiError } from "./error-map";
import { ConfigurationError, FutureAGIAPIError } from "./errors";
import { parseOrigin, type PlatformOrigin } from "./origins";
import { Page } from "./pagination";
import { PlatformCore } from "./platform-base";
import { APIPromise, type CallMeta } from "./raw";
import { redactValue, scrubValue } from "./redact";

/** Strict-mode warning: the server mutation may already have applied. */
export class GatewayConfigWarningError extends ConfigurationError {}

/** Management requires the personal platform pair, never the model-call key. */
export function managementOrigin(base: string, keys: { apiKey: string; secretKey: string }, selectors: Record<string, string>, token?: string): PlatformOrigin {
  if (token || keys.apiKey.startsWith("sk-agentcc") || keys.secretKey.startsWith("sk-agentcc")) {
    throw new ConfigurationError("Gateway management requires a personal platform key pair", "management_credentials");
  }
  const url = parseOrigin(base);
  return { url, base: url.toString().replace(/\/$/u, ""), mode: "keys", source: "derived", custom: false,
    headers: { "X-Api-Key": keys.apiKey, "X-Secret-Key": keys.secretKey, ...selectors }, secrets: [keys.apiKey, keys.secretKey] };
}

const object = (v: unknown): v is Record<string, unknown> => v !== null && typeof v === "object" && !Array.isArray(v);

function validateBody(name: string, body: unknown): void {
  if (name !== "gateway.keys.update" || !object(body)) return;
  const forbidden = ["user", "owner", "organization", "workspace", "type", "rate_limit_rpm", "rate_limit_tpm", "allowed_ips"];
  const metadata = body.metadata;
  if (forbidden.some(k => k in body) || (object(metadata) && ["rate_limit_rpm", "rate_limit_tpm", "allowed_ips"].some(k => k in metadata))) {
    throw new ConfigurationError("Key ownership and unsupported limits cannot be changed", "unsupported_key_field", name);
  }
}

function mask(value: unknown): unknown {
  if (Array.isArray(value)) return value.map(mask);
  if (object(value)) return Object.fromEntries(Object.entries(value).map(([k, v]) => [k, mask(v)]));
  return value === null ? null : "[REDACTED]";
}

/** Mask even unexpected short or nested credential values returned by older servers. */
export function maskRead(value: unknown): unknown {
  if (Array.isArray(value)) return value.map(maskRead);
  if (!object(value)) return value;
  const sensitive = new Set(["credentials", "encrypted_credentials", "api_key", "secret_key", "key", "token"]);
  return Object.fromEntries(Object.entries(value).map(([k, v]) => [k, sensitive.has(k) ? mask(v) : maskRead(v)]));
}

function requirePersonalKeys(value: unknown): void {
  if (Array.isArray(value)) value.forEach(requirePersonalKeys);
  else if (object(value)) {
    if ("results" in value) requirePersonalKeys(value.results);
    else if ("id" in value && (!value.user || value.type === "system" || value.type === "mcp")) {
      throw new ConfigurationError("The backend returned a non-personal gateway key", "non_personal_gateway_key");
    }
  }
}

/** Scrub decoded string values once, including short secrets, without changing wire keys. */
export function scrubManagementValue(value: unknown, secrets: readonly string[]): unknown {
  return scrubValue(value, secrets, 0, 1, false);
}

function unwrap(value: unknown, name: string, secrets: readonly string[], strict: boolean, meta: CallMeta): unknown {
  if (object(value) && "status" in value) {
    if (value.status === false || value.status === "error" || value.status === "failed") {
      const safe = scrubManagementValue(value, secrets);
      throw apiError(400, redactValue(safe), new Headers(meta.headers), {
        operation: name, body: safe,
        ...(meta.idempotencyKey !== undefined ? { idempotencyKey: meta.idempotencyKey } : {}),
      });
    }
    if (!("result" in value)) throw new FutureAGIAPIError(200, undefined, { code: "invalid_envelope", operation: name });
    value = value.result;
  }
  if (name.startsWith("gateway.keys.")) requirePersonalKeys(value);
  // Interpret server semantics before redaction; credentials can collide with wire field names.
  const hasWarnings = object(value) && Boolean(value.gateway_synced === false || (Array.isArray(value.warnings) && value.warnings.length > 0) || value.gateway_warning);
  if (hasWarnings && strict) throw new GatewayConfigWarningError("The server saved the change with warnings; inspect the result before relying on it.", "gateway_config_warning", name);
  if (name.startsWith("gateway.provider_credentials.") || name.startsWith("gateway.keys.")) value = maskRead(value);
  value = scrubManagementValue(value, secrets);
  // Preserve all wire fields. The explicit flag is available without a console side effect.
  return hasWarnings && object(value) ? { ...value, hasWarnings: true } : value;
}

function pageData(raw: unknown, current: number) {
  if (Array.isArray(raw)) return { items: raw, next: undefined as string | undefined, response: raw };
  if (!object(raw) || !Array.isArray(raw.results)) throw new FutureAGIAPIError(200, undefined, { code: "invalid_page" });
  let next: string | undefined;
  if (typeof raw.next === "string" && raw.next) {
    // A next link only selects a numbered page of the same operation, never a URL.
    try {
      const values = new URL(raw.next, "http://localhost").searchParams.getAll("page");
      const candidate = values.length === 1 && /^\d+$/u.test(values[0]!) ? Number(values[0]) : NaN;
      if (Number.isSafeInteger(candidate) && candidate > current) next = String(candidate);
    } catch { /* Invalid links end the walk. */ }
  } else if (!("next" in raw) && typeof raw.total_pages === "number" && Number.isInteger(raw.total_pages) && raw.total_pages > current) {
    next = String(current + 1);
  }
  return { items: raw.results, next: raw.results.length ? next : undefined, response: raw };
}

/** A shared Page preserving the wire DRF response. */
export class ManagementPage extends Page<Record<string, unknown>> {
  readonly raw: unknown;
  constructor(value: ReturnType<typeof pageData>, private readonly load: (cursor: string) => Promise<ReturnType<typeof pageData>>, private readonly visited: ReadonlySet<string> = new Set()) {
    super(value, { style: "cursor", itemsField: "items", cursorParam: "page", nextCursorField: "next" }, load, undefined, visited);
    this.raw = value.response;
  }
  async nextPage(): Promise<ManagementPage | undefined> {
    if (!this.hasMore || this.nextCursor === undefined) return undefined;
    return new ManagementPage(await this.load(this.nextCursor), this.load, new Set([...this.visited, this.nextCursor]));
  }
}

/** Generated namespaces share the policy executor, retries, errors and response metadata. */
export class ManagementResource {
  constructor(protected readonly core: PlatformCore) {}

  protected call<T>(name: string, path: Record<string, string>, query: Record<string, any>, body: unknown, paged = false, strict = false): APIPromise<T> {
    return new APIPromise(async () => {
      validateBody(name, body);
      const q = { ...query };
      if (paged) q.page ??= 1;
      const request = (wire: Record<string, any>) => this.core.call(name, { path, query: wire, body }, {},
        (data, secrets, meta) => unwrap(data, name, secrets, strict, meta));
      const { data, meta } = await request(q).withResponse();
      if (!paged) return { data: data as T, meta };
      const load = async (cursor: string) => pageData(await request({ ...q, page: Number(cursor) }), Number(cursor));
      return { data: new ManagementPage(pageData(data, Number(q.page)), load) as T, meta };
    });
  }
}
