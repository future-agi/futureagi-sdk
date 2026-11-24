/**
 * Model information database — pricing, context windows, capabilities.
 *
 * @module
 */

export interface ModelInfo {
  maxTokens: number;
  maxOutputTokens: number | null;
  inputCostPerToken: number;
  outputCostPerToken: number;
  supportsVision: boolean;
  supportsFunctionCalling: boolean;
  supportsJsonMode: boolean;
}

function m(
  maxTokens: number,
  opts: Partial<Omit<ModelInfo, "maxTokens">> = {},
): ModelInfo {
  return {
    maxTokens,
    maxOutputTokens: opts.maxOutputTokens ?? null,
    inputCostPerToken: opts.inputCostPerToken ?? 0,
    outputCostPerToken: opts.outputCostPerToken ?? 0,
    supportsVision: opts.supportsVision ?? false,
    supportsFunctionCalling: opts.supportsFunctionCalling ?? false,
    supportsJsonMode: opts.supportsJsonMode ?? false,
  };
}

// Pricing as of Feb 2026 — update periodically.
const MODEL_INFO: Record<string, ModelInfo> = {
  // OpenAI
  "gpt-4o": m(128000, {
    maxOutputTokens: 16384,
    inputCostPerToken: 2.5e-6,
    outputCostPerToken: 10e-6,
    supportsVision: true,
    supportsFunctionCalling: true,
    supportsJsonMode: true,
  }),
  "gpt-4o-mini": m(128000, {
    maxOutputTokens: 16384,
    inputCostPerToken: 0.15e-6,
    outputCostPerToken: 0.6e-6,
    supportsVision: true,
    supportsFunctionCalling: true,
    supportsJsonMode: true,
  }),
  "gpt-4-turbo": m(128000, {
    maxOutputTokens: 4096,
    inputCostPerToken: 10e-6,
    outputCostPerToken: 30e-6,
    supportsVision: true,
    supportsFunctionCalling: true,
    supportsJsonMode: true,
  }),
  "gpt-4": m(8192, {
    maxOutputTokens: 8192,
    inputCostPerToken: 30e-6,
    outputCostPerToken: 60e-6,
    supportsFunctionCalling: true,
  }),
  "gpt-3.5-turbo": m(16385, {
    maxOutputTokens: 4096,
    inputCostPerToken: 0.5e-6,
    outputCostPerToken: 1.5e-6,
    supportsFunctionCalling: true,
    supportsJsonMode: true,
  }),
  o1: m(200000, {
    maxOutputTokens: 100000,
    inputCostPerToken: 15e-6,
    outputCostPerToken: 60e-6,
    supportsVision: true,
    supportsFunctionCalling: true,
  }),
  "o1-mini": m(128000, {
    maxOutputTokens: 65536,
    inputCostPerToken: 3e-6,
    outputCostPerToken: 12e-6,
    supportsFunctionCalling: true,
  }),
  "o3-mini": m(200000, {
    maxOutputTokens: 100000,
    inputCostPerToken: 1.1e-6,
    outputCostPerToken: 4.4e-6,
    supportsFunctionCalling: true,
  }),

  // OpenAI Embeddings
  "text-embedding-3-small": m(8191, { inputCostPerToken: 0.02e-6 }),
  "text-embedding-3-large": m(8191, { inputCostPerToken: 0.13e-6 }),
  "text-embedding-ada-002": m(8191, { inputCostPerToken: 0.1e-6 }),

  // Anthropic
  "claude-sonnet-4-20250514": m(200000, {
    maxOutputTokens: 64000,
    inputCostPerToken: 3e-6,
    outputCostPerToken: 15e-6,
    supportsVision: true,
    supportsFunctionCalling: true,
    supportsJsonMode: true,
  }),
  "claude-3-5-sonnet-20241022": m(200000, {
    maxOutputTokens: 8192,
    inputCostPerToken: 3e-6,
    outputCostPerToken: 15e-6,
    supportsVision: true,
    supportsFunctionCalling: true,
    supportsJsonMode: true,
  }),
  "claude-3-5-haiku-20241022": m(200000, {
    maxOutputTokens: 8192,
    inputCostPerToken: 0.8e-6,
    outputCostPerToken: 4e-6,
    supportsFunctionCalling: true,
    supportsJsonMode: true,
  }),
  "claude-3-opus-20240229": m(200000, {
    maxOutputTokens: 4096,
    inputCostPerToken: 15e-6,
    outputCostPerToken: 75e-6,
    supportsVision: true,
    supportsFunctionCalling: true,
  }),
  "claude-3-haiku-20240307": m(200000, {
    maxOutputTokens: 4096,
    inputCostPerToken: 0.25e-6,
    outputCostPerToken: 1.25e-6,
    supportsVision: true,
    supportsFunctionCalling: true,
  }),

  // Google
  "gemini-2.0-flash": m(1048576, {
    maxOutputTokens: 8192,
    inputCostPerToken: 0.1e-6,
    outputCostPerToken: 0.4e-6,
    supportsVision: true,
    supportsFunctionCalling: true,
    supportsJsonMode: true,
  }),
  "gemini-1.5-pro": m(2097152, {
    maxOutputTokens: 8192,
    inputCostPerToken: 1.25e-6,
    outputCostPerToken: 5e-6,
    supportsVision: true,
    supportsFunctionCalling: true,
    supportsJsonMode: true,
  }),
  "gemini-1.5-flash": m(1048576, {
    maxOutputTokens: 8192,
    inputCostPerToken: 0.075e-6,
    outputCostPerToken: 0.3e-6,
    supportsVision: true,
    supportsFunctionCalling: true,
    supportsJsonMode: true,
  }),

  // Meta
  "llama-3.1-70b": m(128000, {
    maxOutputTokens: 4096,
    inputCostPerToken: 0.88e-6,
    outputCostPerToken: 0.88e-6,
    supportsFunctionCalling: true,
  }),
  "llama-3.1-8b": m(128000, {
    maxOutputTokens: 4096,
    inputCostPerToken: 0.18e-6,
    outputCostPerToken: 0.18e-6,
  }),

  // Mistral
  "mistral-large-latest": m(128000, {
    maxOutputTokens: 4096,
    inputCostPerToken: 2e-6,
    outputCostPerToken: 6e-6,
    supportsFunctionCalling: true,
    supportsJsonMode: true,
  }),
  "mistral-small-latest": m(128000, {
    maxOutputTokens: 4096,
    inputCostPerToken: 0.2e-6,
    outputCostPerToken: 0.6e-6,
    supportsFunctionCalling: true,
    supportsJsonMode: true,
  }),
};

/**
 * Map short names to full model names.
 * E.g. `modelAliasMap["gpt4"] = "gpt-4o"`.
 */
export const modelAliasMap: Record<string, string> = {};

// ---------------------------------------------------------------------------
// Lookups
// ---------------------------------------------------------------------------

/**
 * Look up model info by name.
 *
 * Resolution order:
 * 1. Exact match.
 * 2. Alias lookup via `modelAliasMap`.
 * 3. Prefix match (e.g. `"gpt-4o-2024-08-06"` → `"gpt-4o"`).
 */
export function getModelInfo(model: string): ModelInfo | null {
  // 1. Exact match
  if (model in MODEL_INFO) return MODEL_INFO[model];

  // 2. Alias resolution
  const resolved = modelAliasMap[model];
  if (resolved && resolved in MODEL_INFO) return MODEL_INFO[resolved];

  // 3. Prefix match (longest match first)
  const sortedKeys = Object.keys(MODEL_INFO).sort(
    (a, b) => b.length - a.length,
  );
  for (const known of sortedKeys) {
    if (model.startsWith(known)) return MODEL_INFO[known];
  }

  return null;
}

/** Return all known model names. */
export function getValidModels(): string[] {
  return Object.keys(MODEL_INFO);
}

/** Register or update a model in the info database. */
export function registerModel(modelName: string, info: ModelInfo): void {
  MODEL_INFO[modelName] = info;
}

// ---------------------------------------------------------------------------
// Capability checks
// ---------------------------------------------------------------------------

export function supportsVision(model: string): boolean {
  return getModelInfo(model)?.supportsVision ?? false;
}

export function supportsFunctionCalling(model: string): boolean {
  return getModelInfo(model)?.supportsFunctionCalling ?? false;
}

export function supportsJsonMode(model: string): boolean {
  return getModelInfo(model)?.supportsJsonMode ?? false;
}

export function supportsResponseSchema(model: string): boolean {
  return supportsJsonMode(model);
}

// ---------------------------------------------------------------------------
// Environment validation
// ---------------------------------------------------------------------------

const REQUIRED_ENV_VARS = ["AGENTCC_API_KEY", "AGENTCC_BASE_URL"];

export function validateEnvironment(): {
  keysSet: string[];
  keysMissing: string[];
  ready: boolean;
} {
  const keysSet: string[] = [];
  const keysMissing: string[] = [];

  for (const v of REQUIRED_ENV_VARS) {
    const val =
      typeof process !== "undefined" ? process.env?.[v] : undefined;
    if (val) {
      keysSet.push(v);
    } else {
      keysMissing.push(v);
    }
  }
  return { keysSet, keysMissing, ready: keysMissing.length === 0 };
}
