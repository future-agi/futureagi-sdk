// ---------------------------------------------------------------------------
// functionToTool — Convert Zod schema or JSON Schema → OpenAI ToolDefinition
// ---------------------------------------------------------------------------

import type { ToolDefinition } from "./types/chat/completion-create-params.js";
import { isZodSchema, zodToJsonSchema } from "./structured-output.js";
import { AgentCCError } from "./errors.js";

export interface FunctionToToolOptions {
  name: string;
  description?: string;
  strict?: boolean;
}

/**
 * Generate an OpenAI-compatible tool definition from a Zod schema or JSON Schema.
 *
 * @example
 * ```typescript
 * // From Zod schema
 * const tool = functionToTool(z.object({ city: z.string() }), {
 *   name: "get_weather",
 *   description: "Get weather",
 * });
 *
 * // From JSON Schema
 * const tool2 = functionToTool(
 *   { type: "object", properties: { q: { type: "string" } } },
 *   { name: "search" },
 * );
 * ```
 */
export function functionToTool(
  schema: unknown,
  opts: FunctionToToolOptions,
): ToolDefinition {
  let parameters: Record<string, unknown>;

  if (isZodSchema(schema)) {
    parameters = zodToJsonSchema(schema);
  } else if (
    schema !== null &&
    typeof schema === "object" &&
    "type" in (schema as Record<string, unknown>)
  ) {
    // Already a JSON Schema
    parameters = schema as Record<string, unknown>;
  } else {
    throw new AgentCCError(
      "functionToTool: schema must be a Zod schema or a JSON Schema object with a 'type' property",
    );
  }

  const funcDef: Record<string, unknown> = {
    name: opts.name,
    parameters,
  };

  if (opts.description !== undefined) {
    funcDef.description = opts.description;
  }
  if (opts.strict) {
    funcDef.strict = true;
  }

  return {
    type: "function",
    function: funcDef as unknown as ToolDefinition["function"],
  };
}
