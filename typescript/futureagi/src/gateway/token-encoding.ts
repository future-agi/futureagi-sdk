// ---------------------------------------------------------------------------
// Token Encoding — encode()/decode() with optional gpt-tokenizer peer dep
// ---------------------------------------------------------------------------

import { AgentCCError } from "./errors";

// ---------------------------------------------------------------------------
// Model → encoding mapping
// ---------------------------------------------------------------------------

const MODEL_TO_ENCODING: Record<string, string> = {
  "gpt-4o": "o200k_base",
  "gpt-4o-mini": "o200k_base",
  "o1": "o200k_base",
  "o1-mini": "o200k_base",
  "o1-preview": "o200k_base",
  "o3": "o200k_base",
  "o3-mini": "o200k_base",
  "gpt-4": "cl100k_base",
  "gpt-4-turbo": "cl100k_base",
  "gpt-4-turbo-preview": "cl100k_base",
  "gpt-3.5-turbo": "cl100k_base",
  "gpt-3.5-turbo-16k": "cl100k_base",
  "text-embedding-3-small": "cl100k_base",
  "text-embedding-3-large": "cl100k_base",
  "text-embedding-ada-002": "cl100k_base",
};

const DEFAULT_ENCODING = "cl100k_base";

/**
 * Resolve the encoding name for a given model.
 * Falls back to cl100k_base for unknown models.
 */
export function getEncodingForModel(model: string): string {
  // Check exact match first
  if (MODEL_TO_ENCODING[model]) return MODEL_TO_ENCODING[model];

  // Check prefix matches (e.g. "gpt-4o-2024-05-13" → "gpt-4o")
  for (const [prefix, encoding] of Object.entries(MODEL_TO_ENCODING)) {
    if (model.startsWith(prefix)) return encoding;
  }

  return DEFAULT_ENCODING;
}

// ---------------------------------------------------------------------------
// Dynamic import helper
// ---------------------------------------------------------------------------

let _tokenizerModule: Record<string, unknown> | null = null;

async function loadTokenizer(): Promise<Record<string, unknown>> {
  if (_tokenizerModule) return _tokenizerModule;

  try {
    // Dynamic import of optional peer dependency
    // eslint-disable-next-line @typescript-eslint/no-require-imports
    _tokenizerModule = await (Function('return import("gpt-tokenizer")')() as Promise<Record<string, unknown>>);
    return _tokenizerModule;
  } catch {
    throw new AgentCCError(
      "Token encoding requires the 'gpt-tokenizer' package. " +
        "Install it with: npm install gpt-tokenizer",
    );
  }
}

// ---------------------------------------------------------------------------
// Public API
// ---------------------------------------------------------------------------

/**
 * Encode text into token IDs for a given model.
 *
 * Requires `gpt-tokenizer` as an optional peer dependency.
 * Falls back to cl100k_base encoding for unknown models.
 *
 * @example
 * ```typescript
 * import { encode } from "@future-agi/sdk/gateway";
 * const tokens = await encode("gpt-4o", "Hello, world!");
 * console.log(tokens); // [9906, 11, 1917, 0]
 * ```
 */
export async function encode(model: string, text: string): Promise<number[]> {
  const mod = await loadTokenizer();
  const encoding = getEncodingForModel(model);

  // gpt-tokenizer exports encoding-specific encode functions
  const encodeFn = mod[`encode`] as ((text: string) => number[]) | undefined;
  if (typeof encodeFn !== "function") {
    throw new AgentCCError(
      `gpt-tokenizer does not export an encode function. ` +
        `Ensure you have a compatible version installed.`,
    );
  }

  // If the module exports encodingForModel or similar, use it
  const encodingForModelFn = mod["encodingForModel"] as
    | ((model: string) => { encode: (text: string) => number[] })
    | undefined;

  if (typeof encodingForModelFn === "function") {
    try {
      const enc = encodingForModelFn(model);
      return Array.from(enc.encode(text));
    } catch {
      // Fall through to default encode
    }
  }

  return Array.from(encodeFn(text));
}

/**
 * Decode token IDs back to text for a given model.
 *
 * Requires `gpt-tokenizer` as an optional peer dependency.
 *
 * @example
 * ```typescript
 * import { decode } from "@future-agi/sdk/gateway";
 * const text = await decode("gpt-4o", [9906, 11, 1917, 0]);
 * console.log(text); // "Hello, world!"
 * ```
 */
export async function decode(model: string, tokens: number[]): Promise<string> {
  const mod = await loadTokenizer();

  const decodeFn = mod[`decode`] as ((tokens: number[]) => string) | undefined;
  if (typeof decodeFn !== "function") {
    throw new AgentCCError(
      `gpt-tokenizer does not export a decode function. ` +
        `Ensure you have a compatible version installed.`,
    );
  }

  // Try model-specific decoding
  const encodingForModelFn = mod["encodingForModel"] as
    | ((model: string) => { decode: (tokens: number[]) => string })
    | undefined;

  if (typeof encodingForModelFn === "function") {
    try {
      const enc = encodingForModelFn(model);
      return enc.decode(tokens);
    } catch {
      // Fall through to default decode
    }
  }

  return decodeFn(tokens);
}

// ---------------------------------------------------------------------------
// Reset (for testing)
// ---------------------------------------------------------------------------

/** @internal Reset cached tokenizer module (testing only). */
export function _resetTokenizerCache(): void {
  _tokenizerModule = null;
}
