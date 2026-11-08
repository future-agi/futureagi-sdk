// ---------------------------------------------------------------------------
// Options for the stock OpenAI and Vercel AI SDKs, pointed at the gateway.
// Nothing here imports openai, @ai-sdk/openai, langchain or llamaindex: the helpers return plain objects for the
// frameworks' own classes, so the frameworks stay real and no peer is needed.
// ---------------------------------------------------------------------------

import { AgentCCError } from "./errors.js";
import { DEFAULT_BASE_URL, fromEnv, normalizeBaseUrl, resolveApiKey, resolveBaseUrl, URL_ENV } from "./env.js";
import { createHeaders } from "./gateway-config.js";
import type { CreateHeadersOptions, GatewayConfig } from "./gateway-config.js";

const KEY_PAGE = "the Keys page of the Agent Command Center in the Future AGI Console";

function requireKey(apiKey: string | undefined, helper: string, sdk: string): string {
  const key = resolveApiKey(apiKey, (message) => new AgentCCError(message));
  if (!key) {
    throw new AgentCCError(
      `${helper} needs a gateway key: pass apiKey or set FI_GATEWAY_API_KEY (AGENTCC_API_KEY is still read). ` +
        `It always passes one explicitly, because ${sdk} would otherwise send OPENAI_API_KEY to the gateway. ` +
        `Create a virtual key on ${KEY_PAGE}; it is not your FI_API_KEY.`,
    );
  }
  return key;
}

// --- The OpenAI SDK (and LangChain / LlamaIndex, which take its options) ---

/** What {@link openaiOptions} takes: the gateway's key and origin, and the request headers {@link createHeaders} builds. */
export interface OpenAIOptionsInput extends Omit<CreateHeadersOptions, "apiKey"> {
  /** The gateway virtual key; else FI_GATEWAY_API_KEY, then AGENTCC_API_KEY. */
  apiKey?: string;
  /** The gateway origin (a trailing /v1 is accepted); else FI_GATEWAY_BASE_URL, then AGENTCC_BASE_URL, then http://localhost:8090, as the client resolves it. */
  baseUrl?: string;
}

/** `new OpenAI(...)` options: always an explicit key, the gateway's /v1 URL and its headers. */
export interface OpenAIClientOptions {
  apiKey: string;
  baseURL: string;
  /** `x-agentcc-*` headers; OpenAI-Organization and OpenAI-Project are null, so the OpenAI SDK sends neither. */
  defaultHeaders: Record<string, string | null>;
}

/**
 * Options for a stock OpenAI SDK client that talks to the gateway:
 *
 * ```ts
 * import OpenAI from "openai";
 * import { openaiOptions } from "@future-agi/sdk/gateway";
 * const openai = new OpenAI(openaiOptions({ sessionId: "s1" }));
 * // LangChain: new ChatOpenAI({ model: "gpt-4o-mini", apiKey: opts.apiKey, configuration: opts })
 * ```
 *
 * The key resolves as the AgentCC client's does (the FI key pair is refused)
 * and must resolve: without one the OpenAI SDK would read OPENAI_API_KEY and
 * send it to the gateway. OPENAI_ORG_ID / OPENAI_PROJECT_ID are not
 * forwarded. A gateway cache hit answers a streamed request with one JSON
 * body, which the OpenAI SDK's stream does not read; the AgentCC client does.
 */
export function openaiOptions(opts: OpenAIOptionsInput = {}): OpenAIClientOptions {
  const { apiKey, baseUrl, ...headerOptions } = opts;
  const key = requireKey(apiKey, "openaiOptions()", "the OpenAI SDK");
  return {
    apiKey: key,
    baseURL: `${resolveBaseUrl(baseUrl)}/v1`,
    defaultHeaders: { ...createHeaders(headerOptions), "OpenAI-Organization": null, "OpenAI-Project": null },
  };
}

// --- The Vercel AI SDK (createOpenAI from @ai-sdk/openai) ---

/** The settings @agentcc/vercel 1.0's createAgentCC took, so its 2.0 shim passes them on unchanged. */
export interface AgentCCProviderSettings {
  /** The gateway virtual key; else FI_GATEWAY_API_KEY, then AGENTCC_API_KEY. */
  apiKey?: string;
  /** The gateway URL (with or without /v1); else FI_GATEWAY_BASE_URL, then AGENTCC_BASE_URL. There is no default. */
  baseURL?: string;
  /** Additional HTTP headers, merged last. */
  headers?: Record<string, string>;
  /** Gateway config (cache only), sent as x-agentcc-config. */
  config?: GatewayConfig;
  traceId?: string;
  sessionId?: string;
  metadata?: Record<string, unknown>;
  userId?: string;
  /** With cacheTtl, sends x-agentcc-cache-ttl (1.0 also sent `x-agentcc-cache: true`, which the gateway does not read). */
  cacheEnabled?: boolean;
  /** Cache TTL, sent only when cacheEnabled is true (as 1.0). */
  cacheTtl?: string;
  /** Sent as X-Guardrail-Policy, the header the gateway reads (1.0 sent x-agentcc-guardrail-policy). */
  guardrailPolicy?: string;
  properties?: Record<string, string>;
}

/** `createOpenAI(...)` settings for @ai-sdk/openai. */
export interface AiSdkProviderSettings {
  apiKey: string;
  baseURL: string;
  headers: Record<string, string>;
  /** As @agentcc/vercel 1.0 set it: no stream_options are sent (@ai-sdk/openai 1.x; later versions ignore the key). */
  compatibility: "compatible";
}

/**
 * Settings for the Vercel AI SDK's OpenAI provider, pointed at the gateway:
 *
 * ```ts
 * import { createOpenAI } from "@ai-sdk/openai";
 * import { aiSdkProviderSettings } from "@future-agi/sdk/gateway";
 * const gateway = createOpenAI(aiSdkProviderSettings({ sessionId: "s1" }));
 * ```
 *
 * There is no default URL. @agentcc/vercel 1.0 fell back to
 * https://api.agentcc.ai/v1, a host the gateway project does not name, so a
 * key set without a URL went there; here the URL must resolve or this throws.
 * The key must resolve too (createOpenAI would read OPENAI_API_KEY).
 */
export function aiSdkProviderSettings(settings: AgentCCProviderSettings = {}): AiSdkProviderSettings {
  const apiKey = requireKey(settings.apiKey, "aiSdkProviderSettings()", "@ai-sdk/openai");
  const url = settings.baseURL || fromEnv(URL_ENV);
  if (!url) {
    throw new AgentCCError(
      "aiSdkProviderSettings() needs the gateway URL: pass baseURL or set FI_GATEWAY_BASE_URL (AGENTCC_BASE_URL is still read), " +
        `for example ${DEFAULT_BASE_URL} for a local gateway. There is no default, so a key is only sent to a gateway you named.`,
    );
  }
  const headers = createHeaders({
    config: settings.config,
    traceId: settings.traceId,
    sessionId: settings.sessionId,
    metadata: settings.metadata,
    userId: settings.userId,
    guardrailPolicy: settings.guardrailPolicy,
    properties: settings.properties,
  });
  if (settings.cacheEnabled && settings.cacheTtl) headers["x-agentcc-cache-ttl"] = settings.cacheTtl;
  return {
    apiKey,
    baseURL: `${normalizeBaseUrl(url)}/v1`,
    headers: { ...headers, ...settings.headers },
    compatibility: "compatible",
  };
}
