// Where the gateway client reads its settings from.
//
// The gateway authenticates with its own virtual keys (`sk-agentcc-*`), so it has its own
// variables; the `AGENTCC_*` names still work for existing @future-agi/sdk/gateway users.

function env(name: string): string {
  return (typeof process !== "undefined" ? process.env?.[name] : undefined) || "";
}

export function envApiKey(): string {
  return env("FI_GATEWAY_API_KEY") || env("AGENTCC_API_KEY");
}

export function envBaseUrl(): string {
  return env("FI_GATEWAY_URL") || env("AGENTCC_BASE_URL");
}

/**
 * Resources add `/v1/...` themselves, so an OpenAI-style `.../v1` base URL (the control plane
 * and the agentcc README both show one) would call `/v1/v1/...`.
 */
export function cleanBaseUrl(url: string): string {
  const trimmed = (url || "").replace(/\/+$/, "");
  return trimmed.endsWith("/v1") ? trimmed.slice(0, -"/v1".length) : trimmed;
}
