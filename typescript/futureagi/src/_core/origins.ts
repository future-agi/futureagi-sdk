/**
 * The platform origin, its credential and the host guard; the twin of Python's
 * `fi._core.origins`. TypeScript has no saved login, so an origin's source is `argument`, `env` or
 * `derived`.
 *
 * - The key pair comes from **one** place, as Python's resolver takes it: when `apiKey` or `secretKey` is
 *   given, both are the arguments; otherwise both are `FI_API_KEY` / `FI_SECRET_KEY`. A half pair is
 *   `CredentialsMissingError`; the other half is never taken from the environment (so "the same source
 *   as the keys" below always names one source for both keys).
 * - The origin is `platformBaseUrl`, else `FI_PLATFORM_BASE_URL`, else derived as `{baseUrl}/omega/api`.
 * - Keys mode: `X-Api-Key` / `X-Secret-Key`, plus `X-Workspace-Id` / `X-Organization-Id` when set (when
 *   neither is set no selector is sent and the server uses the key's own workspace).
 * - Bearer mode (self-hosted EE): `Authorization: Bearer <platformToken>`, plus `X-Omega-Workspace` /
 *   `X-Omega-Org`; the transport's key headers are removed. A token with an explicit key pair throws
 *   `MixedCredentialsError`.
 * - The guard (keys mode): allowed when derived, from the same source as the keys, or HTTPS in the
 *   `futureagi.com` zone or HTTP(S) on loopback; else `HostNotAllowedError` unless
 *   `allowCustomPlatformUrl` / `FI_ALLOW_CUSTOM_PLATFORM_URL=1`, which warns once per origin.
 * - Non-loopback HTTP: keys remain compatible with a deprecation warning; Bearer requires
 *   `allowInsecureHttp` / `FI_ALLOW_INSECURE_HTTP=1`. Mixed credentials still fail first.
 */

import { CredentialsMissingError, HostNotAllowedError, MixedCredentialsError, PlatformNotConfiguredError } from "./errors";
import { checkHttpSecurity, isInsecureHttp, isLoopback, resetHttpWarnings } from "./http-security";

export const PLATFORM_PATH = "/omega/api";
const ZONE = "futureagi.com";
const warned = new Set<string>();
// Raw-string rules, the same in Python's fi._core.origins (tests/fixtures/platform-origins): the WHATWG
// URL parser and httpx disagree on these inputs, so neither parser decides them.
const SCHEME_AUTHORITY = /^[A-Za-z][A-Za-z0-9+.-]*:\/\/([^/?#]*)/u;
const DOTS = /[.\u3002\uff0e\uff61]/gu; // the separators IDNA maps to "."
const OCTET = "(25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9])";
const IPV4 = new RegExp(`^${OCTET}(\\.${OCTET}){3}$`, "u");
const NUMERIC_LABEL = /^(0[xX][0-9a-fA-F]*|\p{Nd}+)$/u;

/** What makes `raw` unusable before a parser sees it: a space, a control character or a backslash
 * anywhere; no `scheme://` or an empty host; a percent sign in the host. */
function rawProblem(raw: string): string | undefined {
  for (const ch of raw) {
    const code = ch.codePointAt(0) ?? 0;
    if (code <= 0x20 || code === 0x7f || ch === "\\") return "must not contain spaces, control characters or a backslash";
  }
  const match = SCHEME_AUTHORITY.exec(raw);
  if (match === null || match[1] === "") return "must be an absolute https:// URL (or http:// to loopback)";
  if (match[1]!.includes("%")) return "must not percent-encode its host";
  return undefined;
}

/** A host whose last label is a number is an IPv4 address to the WHATWG parser (`127.1`, `2130706433`,
 * `0x7f.1`), which `URL` silently rewrites; only the canonical dotted quad is accepted, as in Python. */
function ipv4Problem(raw: string): string | undefined {
  const authority = SCHEME_AUTHORITY.exec(raw)?.[1] ?? "";
  let host = authority.slice(authority.lastIndexOf("@") + 1);
  if (host.startsWith("[")) return undefined;
  host = host.replace(/:[0-9]*$/u, "").replace(DOTS, ".");
  if (host.endsWith(".")) host = host.slice(0, -1);
  const last = host.slice(host.lastIndexOf(".") + 1);
  if (!NUMERIC_LABEL.test(last) || IPV4.test(host)) return undefined;
  return "must write an IPv4 address as four decimal numbers (like 127.0.0.1)";
}

export type Source = "argument" | "env" | "derived" | "none";

/** What the client was given, before resolution. */
export interface PlatformInputs {
  readonly apiKey?: string;
  readonly secretKey?: string;
  readonly baseUrl?: string;
  readonly platformBaseUrl?: string;
  readonly workspaceId?: string;
  readonly organizationId?: string;
  readonly platformToken?: string;
  readonly allowCustomPlatformUrl?: boolean;
  readonly allowInsecureHttp?: boolean;
}

/** The resolved origin and what every request to it carries. */
export interface PlatformOrigin {
  readonly url: URL;
  readonly base: string;
  readonly mode: "keys" | "bearer";
  readonly source: Source;
  readonly headers: Readonly<Record<string, string>>;
  readonly secrets: readonly string[];
  readonly custom: boolean;
}

type Env = Readonly<Record<string, string | undefined>>;

export function processEnv(): Env {
  return (globalThis as { process?: { env?: Env } }).process?.env ?? {};
}

function pick(arg: string | undefined, env: Env, name: string): [string | undefined, Source] {
  if (arg) return [arg, "argument"];
  if (env[name]) return [env[name], "env"];
  return [undefined, "none"];
}

/** The workspace and organization selector headers: argument, then environment; an empty value is unset. */
export function selectorHeaders(
  inputs: Pick<PlatformInputs, "workspaceId" | "organizationId">,
  env: Env = processEnv(),
): Record<string, string> {
  const headers: Record<string, string> = {};
  const [workspaceId] = pick(inputs.workspaceId, env, "FI_WORKSPACE_ID");
  const [organizationId] = pick(inputs.organizationId, env, "FI_ORGANIZATION_ID");
  if (workspaceId !== undefined) headers["X-Workspace-Id"] = workspaceId;
  if (organizationId !== undefined) headers["X-Organization-Id"] = organizationId;
  return headers;
}

/** The key pair from one place: both arguments when either is given, else both environment variables. */
function pickPair(inputs: PlatformInputs, env: Env): [string | undefined, string | undefined, Source] {
  if (inputs.apiKey || inputs.secretKey) return [inputs.apiKey || undefined, inputs.secretKey || undefined, "argument"];
  if (env.FI_API_KEY || env.FI_SECRET_KEY) return [env.FI_API_KEY || undefined, env.FI_SECRET_KEY || undefined, "env"];
  return [undefined, undefined, "none"];
}

/** The sentence a half pair adds: the environment's other half is not paired with an argument. */
function halfPairNote(keySource: Source, apiKey: string | undefined, secretKey: string | undefined, env: Env): string {
  if (keySource !== "argument") return "";
  const unpaired = [!apiKey && env.FI_API_KEY ? "FI_API_KEY" : "", !secretKey && env.FI_SECRET_KEY ? "FI_SECRET_KEY" : ""].filter(Boolean);
  if (unpaired.length === 0) return "";
  return (
    ` The key pair comes from one place: ${unpaired.join(" and ")} in the environment is not paired with ` +
    `${apiKey ? "an apiKey" : "a secretKey"} argument; pass both arguments or set both variables.`
  );
}

export function parseOrigin(raw: string): URL {
  const problem = rawProblem(raw);
  if (problem !== undefined) throw new PlatformNotConfiguredError(`FI_PLATFORM_BASE_URL ${problem}`, "invalid_platform_url");
  let url: URL;
  try {
    url = new URL(raw);
  } catch {
    throw new PlatformNotConfiguredError("FI_PLATFORM_BASE_URL is not a valid URL", "invalid_platform_url");
  }
  if ((url.protocol !== "https:" && url.protocol !== "http:") || url.hostname === "") {
    throw new PlatformNotConfiguredError(
      "FI_PLATFORM_BASE_URL must be an absolute https:// URL (or http:// to loopback)",
      "invalid_platform_url",
    );
  }
  if (url.username !== "" || url.password !== "") {
    throw new PlatformNotConfiguredError(
      `FI_PLATFORM_BASE_URL must not contain a user name or password (host ${url.host})`,
      "invalid_platform_url",
    );
  }
  if (url.search !== "" || url.hash !== "" || raw.includes("?") || raw.includes("#")) {
    throw new PlatformNotConfiguredError("FI_PLATFORM_BASE_URL must not contain a query or a fragment", "invalid_platform_url");
  }
  const ipv4 = ipv4Problem(raw);
  if (ipv4 !== undefined) throw new PlatformNotConfiguredError(`FI_PLATFORM_BASE_URL ${ipv4}`, "invalid_platform_url");
  return url;
}

/** HTTPS in the Future AGI zone, or HTTP(S) on loopback. `URL` gives the ASCII (punycode) host. */
export function hostAllowed(url: URL): boolean {
  const host = url.hostname.toLowerCase().replace(/\.$/u, "");
  if (isLoopback(url)) return true;
  return url.protocol === "https:" && (host === ZONE || host.endsWith(`.${ZONE}`));
}

/** Decide the origin and credential for platform requests, or throw before anything is sent. */
export function resolvePlatformOrigin(inputs: PlatformInputs, env: Env = processEnv()): PlatformOrigin {
  const [apiKey, secretKey, keySource] = pickPair(inputs, env);
  const baseUrl = (inputs.baseUrl ?? env.FI_BASE_URL ?? "https://api.futureagi.com").replace(/\/+$/u, "");
  const [explicit, explicitSource] = pick(inputs.platformBaseUrl, env, "FI_PLATFORM_BASE_URL");
  const source: Source = explicit === undefined ? "derived" : explicitSource;
  const raw = (explicit ?? `${baseUrl}${PLATFORM_PATH}`).replace(/\/+$/u, "");
  const url = parseOrigin(raw);
  const [workspaceId] = pick(inputs.workspaceId, env, "FI_WORKSPACE_ID");
  const [organizationId] = pick(inputs.organizationId, env, "FI_ORGANIZATION_ID");
  const [token, tokenSource] = pick(inputs.platformToken, env, "FI_PLATFORM_TOKEN");
  if (token !== undefined) {
    if (apiKey !== undefined || secretKey !== undefined) {
      throw new MixedCredentialsError(
        `both FI_PLATFORM_TOKEN (a self-host Bearer token, from ${tokenSource}) and an API key pair (from ${keySource}) are set; pass one or the other`,
        "mixed_credentials",
      );
    }
    checkHttpSecurity(url, "bearer", inputs.allowInsecureHttp ??
      ["1", "true", "yes"].includes((env.FI_ALLOW_INSECURE_HTTP ?? "").trim().toLowerCase()));
    const headers: Record<string, string> = { Authorization: `Bearer ${token}` };
    if (workspaceId !== undefined) headers["X-Omega-Workspace"] = workspaceId;
    if (organizationId !== undefined) headers["X-Omega-Org"] = organizationId;
    return { url, base: raw, mode: "bearer", source, headers, secrets: [token], custom: false };
  }
  if (!apiKey || !secretKey) {
    throw new CredentialsMissingError(
      `No ${[!apiKey ? "FI_API_KEY" : "", !secretKey ? "FI_SECRET_KEY" : ""].filter(Boolean).join(" and ")} for ${raw}. ` +
        "Pass apiKey/secretKey or set FI_API_KEY and FI_SECRET_KEY; for a self-hosted Omega EE, set FI_PLATFORM_TOKEN instead." +
        halfPairNote(keySource, apiKey, secretKey, env),
    );
  }
  const exempt = source === "derived" || source === keySource;
  let custom = false;
  if (!exempt && !hostAllowed(url)) {
    const flag =
      inputs.allowCustomPlatformUrl ?? ["1", "true", "yes"].includes((env.FI_ALLOW_CUSTOM_PLATFORM_URL ?? "").trim().toLowerCase());
    if (!flag) {
      const why = url.protocol === "http:" ? "plain http to a host that is not loopback" : "outside the Future AGI zone";
      throw new HostNotAllowedError(
        `refusing to send your API keys (from ${keySource}) to ${url.host} (${why}); the platform origin came from ${source}, not from ` +
          "the same place as the keys. Pass allowCustomPlatformUrl: true or set FI_ALLOW_CUSTOM_PLATFORM_URL=1 if you trust it",
        "host_not_allowed",
      );
    }
    custom = true;
    // HTTP gets the single canonical-origin cleartext warning below, not a second custom-host warning.
    if (!isInsecureHttp(url) && !warned.has(url.href)) {
      warned.add(url.href);
      console.warn(`futureagi: sending your keys to ${url.host}, outside the Future AGI zone, because allowCustomPlatformUrl is set.`);
    }
  }
  checkHttpSecurity(url, "keys");
  const headers: Record<string, string> = { "X-Api-Key": apiKey, "X-Secret-Key": secretKey };
  if (workspaceId !== undefined) headers["X-Workspace-Id"] = workspaceId;
  if (organizationId !== undefined) headers["X-Organization-Id"] = organizationId;
  return { url, base: raw, mode: "keys", source, headers, secrets: [apiKey, secretKey], custom };
}

/** Test seam: forget which origins were warned about. */
export function resetWarnings(): void {
  warned.clear();
  resetHttpWarnings();
}
