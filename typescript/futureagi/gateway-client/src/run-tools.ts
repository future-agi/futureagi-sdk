// ---------------------------------------------------------------------------
// Tool Call Execution Loop — Autonomous tool-calling agent loop
// ---------------------------------------------------------------------------

import type { ChatCompletion, ToolCall } from "./types/chat/chat-completion.js";
import type {
  ChatCompletionMessageParam,
  ChatCompletionCreateParams,
  ToolDefinition,
} from "./types/chat/completion-create-params.js";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface ToolWithExecute {
  type: "function";
  function: {
    name: string;
    description?: string;
    parameters?: Record<string, unknown>;
    execute: (args: Record<string, unknown>) => Promise<unknown>;
  };
}

export interface ToolStep {
  completion: ChatCompletion;
  toolCalls: ToolCall[];
  toolResults: Array<{ toolCallId: string; result: unknown }>;
}

export interface RunToolsResult {
  completion: ChatCompletion;
  steps: ToolStep[];
  totalSteps: number;
}

export interface RunToolsParams {
  model: string;
  messages: ChatCompletionMessageParam[];
  tools: ToolWithExecute[];
  maxSteps?: number;
  onStep?: (step: ToolStep) => void;
  temperature?: number;
  max_tokens?: number;
  [key: string]: unknown;
}

// Client shape (duck-typed to avoid circular imports)
interface ToolRunnerClient {
  chat: {
    completions: {
      create(params: ChatCompletionCreateParams): Promise<ChatCompletion>;
    };
  };
}

// ---------------------------------------------------------------------------
// RunToolsRunner
// ---------------------------------------------------------------------------

export class RunToolsRunner {
  private _client: ToolRunnerClient;
  private _params: RunToolsParams;

  constructor(client: ToolRunnerClient, params: RunToolsParams) {
    this._client = client;
    this._params = params;
  }

  async run(): Promise<RunToolsResult> {
    const messages: ChatCompletionMessageParam[] = [
      ...this._params.messages,
    ];
    const maxSteps = this._params.maxSteps ?? 10;

    // Build tool definitions without `execute` (just the schema)
    const toolDefs: ToolDefinition[] = this._params.tools.map((t) => ({
      type: "function" as const,
      function: {
        name: t.function.name,
        description: t.function.description,
        parameters: t.function.parameters,
      },
    }));

    // Map tool name → execute function
    const toolMap = new Map<
      string,
      (args: Record<string, unknown>) => Promise<unknown>
    >();
    for (const t of this._params.tools) {
      toolMap.set(t.function.name, t.function.execute);
    }

    // Extract pass-through params
    const passThrough: Record<string, unknown> = {};
    if (this._params.temperature !== undefined)
      passThrough.temperature = this._params.temperature;
    if (this._params.max_tokens !== undefined)
      passThrough.max_tokens = this._params.max_tokens;

    const steps: ToolStep[] = [];

    for (let stepNum = 0; stepNum < maxSteps; stepNum++) {
      const completion = await this._client.chat.completions.create({
        model: this._params.model,
        messages,
        tools: toolDefs,
        ...passThrough,
      });

      const choice = completion.choices[0];
      if (!choice) {
        steps.push({ completion, toolCalls: [], toolResults: [] });
        this._params.onStep?.(steps[steps.length - 1]);
        return { completion, steps, totalSteps: stepNum + 1 };
      }

      const toolCalls = choice.message.tool_calls ?? [];

      // No tool calls → final answer
      if (
        choice.finish_reason !== "tool_calls" ||
        toolCalls.length === 0
      ) {
        steps.push({ completion, toolCalls: [], toolResults: [] });
        this._params.onStep?.(steps[steps.length - 1]);
        return { completion, steps, totalSteps: stepNum + 1 };
      }

      // Append assistant message with tool calls
      messages.push({
        role: "assistant",
        content: choice.message.content,
        tool_calls: toolCalls,
      } as unknown as ChatCompletionMessageParam);

      // Execute each tool call
      const toolResults: Array<{ toolCallId: string; result: unknown }> =
        [];
      for (const tc of toolCalls) {
        const execute = toolMap.get(tc.function.name);
        let result: unknown;

        try {
          const args = JSON.parse(tc.function.arguments);
          if (execute) {
            result = await execute(args);
          } else {
            result = `Error: unknown tool "${tc.function.name}"`;
          }
        } catch (err) {
          result = `Error: ${(err as Error).message}`;
        }

        toolResults.push({ toolCallId: tc.id, result });

        messages.push({
          role: "tool",
          tool_call_id: tc.id,
          content:
            typeof result === "string" ? result : JSON.stringify(result),
        } as ChatCompletionMessageParam);
      }

      const currentStep: ToolStep = { completion, toolCalls, toolResults };
      steps.push(currentStep);
      this._params.onStep?.(currentStep);
    }

    // Max steps reached — return last completion
    return {
      completion: steps[steps.length - 1].completion,
      steps,
      totalSteps: maxSteps,
    };
  }
}
