// ---------------------------------------------------------------------------
// Where the client's base URL comes from
// ---------------------------------------------------------------------------

/** The base URL when neither the argument nor the environment names one: a local gateway. */
export const DEFAULT_BASE_URL = "http://localhost:8090";

/** A process environment variable, or "" where there is no process (browsers, edge runtimes). */
export function readEnv(name: string): string {
  if (typeof process === "undefined" || !process || !process.env) return "";
  return process.env[name] ?? "";
}

/**
 * The gateway origin from a base URL: trailing slashes and one
 * trailing "/v1" are dropped, so `https://gw/v1/` and `https://gw` both
 * reach `https://gw/v1/chat/completions`. FA's management API and the
 * Console hand out `<origin>/v1`, the form the OpenAI SDKs take; every
 * resource path here already starts with /v1. Matches fi.gateway's
 * normalize_base_url (Python).
 */
export function normalizeBaseUrl(baseUrl: string): string {
  let url = baseUrl.replace(/\/+$/, "");
  if (url.endsWith("/v1")) url = url.slice(0, -"/v1".length).replace(/\/+$/, "");
  return url;
}

// ---------------------------------------------------------------------------
// The key and the base URL from the environment
// ---------------------------------------------------------------------------
//
// - Key: the apiKey option, then FI_GATEWAY_API_KEY, then AGENTCC_API_KEY.
//   With none, no Authorization header is sent (as in 1.x).
// - Base URL: the baseUrl option, then FI_GATEWAY_BASE_URL, then
//   AGENTCC_BASE_URL, then http://localhost:8090.
// - An empty value falls through to the next source, as in 1.x (`||`).
// - With both names set to different values the FI_GATEWAY_* one wins and
//   one console.warn names the two (names only, never values).
// - FI_API_KEY, FI_SECRET_KEY and FI_PLATFORM_TOKEN are never read as a key.
//   The gateway also reads x-api-key as a virtual-key location, so a gateway
//   key equal to FI_API_KEY or FI_SECRET_KEY is refused: the Future AGI key
//   pair must never be sent to the gateway. fi.gateway (Python) applies the
//   same order and guard.

export const KEY_ENV = ["FI_GATEWAY_API_KEY", "AGENTCC_API_KEY"] as const;
export const URL_ENV = ["FI_GATEWAY_BASE_URL", "AGENTCC_BASE_URL"] as const;
const FI_KEY_PAIR = ["FI_API_KEY", "FI_SECRET_KEY"] as const;
const KEY_PAGE = "the Keys page of the Agent Command Center in the Future AGI Console";

/** The first non-empty variable of names ("" if none); warns once when two differ. */
export function fromEnv(names: readonly string[]): string {
  const present = names.map((name) => [name, readEnv(name)] as const).filter(([, value]) => value !== "");
  if (present.length === 0) return "";
  if (new Set(present.map(([, value]) => value)).size > 1) {
    console.warn(`${present[0][0]} and ${present[1][0]} are both set to different values; using ${present[0][0]}`);
  }
  return present[0][1];
}

/** Raise when the gateway key is the Future AGI key pair from the environment. */
export function guardFiKeyPair(apiKey: string, makeError: (message: string) => Error): void {
  for (const name of FI_KEY_PAIR) {
    const value = readEnv(name);
    if (value && apiKey === value) {
      throw makeError(
        `The gateway key equals ${name} from the environment. @future-agi/sdk/gateway ` +
          "authenticates with a gateway virtual key and never sends the Future AGI API key pair; " +
          `create a virtual key on ${KEY_PAGE} and pass it as apiKey or FI_GATEWAY_API_KEY.`,
      );
    }
  }
}

/** The gateway virtual key ("" when none is set; then no Authorization header is sent). */
export function resolveApiKey(apiKey: string | undefined, makeError: (message: string) => Error): string {
  const resolved = apiKey || fromEnv(KEY_ENV);
  if (resolved) guardFiKeyPair(resolved, makeError);
  return resolved;
}

/** The gateway origin, normalised (see normalizeBaseUrl). */
export function resolveBaseUrl(baseUrl: string | undefined): string {
  return normalizeBaseUrl(baseUrl || fromEnv(URL_ENV) || DEFAULT_BASE_URL);
}
