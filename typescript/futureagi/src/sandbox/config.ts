/**
 * The client that `Sandbox.create`, `Sandbox.connect`, `Sandbox.list` and `Sandbox.settings` build: from the
 * environment only. To pass keys, a base URL, a workspace or an organization in
 * code, build a `FutureAGIClient` and call `client.sandboxes.create(...)` / `client.sandboxes.connect(id)`,
 * which return the same `Sandbox` handle.
 *
 * - Base URL: `OMEGA_BASE_URL`. There is no default host: without it, a `PlatformNotConfiguredError` (a
 *   `ConfigurationError`) names `OMEGA_BASE_URL`. Hosted: `https://<gateway-host>/omega/api`; self-hosted EE:
 *   its origin with the port.
 * - Hosted keys: `FI_API_KEY` + `FI_SECRET_KEY`, sent as `X-Api-Key` / `X-Secret-Key`.
 * - Self-host: `FUTUREAGI_OMEGA_API_KEY`, sent as `Authorization: Bearer`. A self-hosted origin that is not
 *   loopback needs the constructor-only `allowCustomBaseUrl: true` of `FutureAGIClient`, so the environment
 *   alone reaches only a loopback EE (OpenAPI servers[1]).
 * - Both modes set: `MixedCredentialsError`, nothing is sent. `OMEGA_OS_API_KEY` is never read.
 * - Scope (OpenAPI info.x-omega-scope-headers): `FI_WORKSPACE_ID` and `FI_ORGANIZATION_ID` (the client's own
 *   variables), sent as `X-Workspace-Id` / `X-Organization-Id` with keys and as `x-omega-workspace` /
 *   `x-omega-org` with a Bearer token.
 * - Sandbox calls refuse plain HTTP to anything but loopback (src/platform/resources/sandboxes.ts).
 */

import { CredentialsMissingError, MixedCredentialsError, PlatformNotConfiguredError } from "../_core/errors";
import { parseOrigin, processEnv, type PlatformOrigin } from "../_core/origins";
import { DEFAULT_STREAM_IDLE_MS, DEFAULT_TIMEOUT_MS, PlatformCore } from "../_core/platform-base";
import { PLATFORM_OPERATIONS } from "../generated/platform/policy.gen";

/** The environment variables `Sandbox.create/connect/list/settings` read. */
export const SANDBOX_ENV = {
  baseUrl: "OMEGA_BASE_URL",
  apiKey: "FI_API_KEY",
  secretKey: "FI_SECRET_KEY",
  bearerToken: "FUTUREAGI_OMEGA_API_KEY",
  workspace: "FI_WORKSPACE_ID",
  organization: "FI_ORGANIZATION_ID",
} as const;

type Env = Readonly<Record<string, string | undefined>>;

const value = (env: Env, name: string): string | undefined => (env[name] ? env[name] : undefined);

/** The origin, credential and scope headers for sandbox calls from the environment, or a configuration error
 * before anything is sent. */
export function resolveSandboxOrigin(env: Env = processEnv()): PlatformOrigin {
  const rawBase = value(env, SANDBOX_ENV.baseUrl);
  if (rawBase === undefined) {
    throw new PlatformNotConfiguredError(
      `No sandbox API base URL: set ${SANDBOX_ENV.baseUrl} (hosted: https://<gateway-host>/omega/api; ` +
        "self-hosted EE: its origin with the port), or pass it to a FutureAGIClient and use client.sandboxes. " +
        "There is no default host.",
      "missing_base_url",
    );
  }
  const apiKey = value(env, SANDBOX_ENV.apiKey);
  const secretKey = value(env, SANDBOX_ENV.secretKey);
  const token = value(env, SANDBOX_ENV.bearerToken);
  if (token !== undefined && (apiKey !== undefined || secretKey !== undefined)) {
    throw new MixedCredentialsError(
      `both a self-hosted Bearer token (${SANDBOX_ENV.bearerToken}) and an API key pair ` +
        `(${SANDBOX_ENV.apiKey}/${SANDBOX_ENV.secretKey}) are set; ` +
        "use one: keys for hosted Future AGI, the token for a self-hosted EE",
      "mixed_credentials",
    );
  }
  if (token === undefined && (apiKey === undefined || secretKey === undefined)) {
    const missing =
      apiKey === undefined && secretKey === undefined
        ? "no credentials"
        : `no ${apiKey === undefined ? SANDBOX_ENV.apiKey : SANDBOX_ENV.secretKey} to pair with ${apiKey === undefined ? SANDBOX_ENV.secretKey : SANDBOX_ENV.apiKey}`;
    throw new CredentialsMissingError(
      `Sandbox calls found ${missing}. Hosted: set ${SANDBOX_ENV.apiKey} and ${SANDBOX_ENV.secretKey}. ` +
        `Self-hosted EE: set ${SANDBOX_ENV.bearerToken}. To pass credentials in code, use a FutureAGIClient and client.sandboxes.`,
    );
  }
  const base = rawBase.replace(/\/+$/u, "");
  let url: URL;
  try {
    url = parseOrigin(base);
  } catch (error) {
    if (!(error instanceof PlatformNotConfiguredError)) throw error;
    throw new PlatformNotConfiguredError(error.message.replace("FI_PLATFORM_BASE_URL", SANDBOX_ENV.baseUrl), error.code);
  }
  const workspace = value(env, SANDBOX_ENV.workspace);
  const organization = value(env, SANDBOX_ENV.organization);
  const headers: Record<string, string> = {};
  if (token !== undefined) {
    headers.Authorization = `Bearer ${token}`;
    if (workspace !== undefined) headers["x-omega-workspace"] = workspace;
    if (organization !== undefined) headers["x-omega-org"] = organization;
  } else {
    headers["X-Api-Key"] = apiKey as string;
    headers["X-Secret-Key"] = secretKey as string;
    if (workspace !== undefined) headers["X-Workspace-Id"] = workspace;
    if (organization !== undefined) headers["X-Organization-Id"] = organization;
  }
  return {
    url,
    base,
    mode: token !== undefined ? "bearer" : "keys",
    source: "env",
    headers,
    secrets: token !== undefined ? [token] : [apiKey as string, secretKey as string],
    custom: false,
  };
}

/** The client the `Sandbox` statics call through, built from the environment (no `allowCustomBaseUrl`). */
export function environmentHost(env: Env = processEnv()): { readonly _platform: PlatformCore } {
  const origin = resolveSandboxOrigin(env);
  const core = new PlatformCore(
    { resolveOrigin: () => origin, origin, table: PLATFORM_OPERATIONS },
    { timeoutMs: DEFAULT_TIMEOUT_MS, streamIdleTimeoutMs: DEFAULT_STREAM_IDLE_MS },
  );
  return { _platform: core };
}
