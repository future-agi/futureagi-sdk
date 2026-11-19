import { describe, it, expect, jest } from "@jest/globals";
import { RunToolsRunner } from "../src/run-tools.js";
import type { ChatCompletion } from "../src/types/chat/chat-completion.js";

function makeCompletion(
  content: string | null,
  finishReason: string,
  toolCalls?: Array<{
    id: string;
    type: "function";
    function: { name: string; arguments: string };
  }>,
): ChatCompletion {
  return {
    id: "chatcmpl-test",
    object: "chat.completion",
    created: Date.now(),
    model: "gpt-4o",
    choices: [
      {
        index: 0,
        message: {
          role: "assistant",
          content,
          tool_calls: toolCalls,
        },
        finish_reason: finishReason,
      },
    ],
    usage: { prompt_tokens: 10, completion_tokens: 5, total_tokens: 15 },
  };
}

describe("RunToolsRunner", () => {
  it("completes in single step when no tool calls", async () => {
    const client = {
      chat: {
        completions: {
          create: jest.fn<any>(async () => makeCompletion("Hello!", "stop")),
        },
      },
    };

    const runner = new RunToolsRunner(client, {
      model: "gpt-4o",
      messages: [{ role: "user", content: "hi" }],
      tools: [],
    });

    const result = await runner.run();

    expect(result.totalSteps).toBe(1);
    expect(result.completion.choices[0].message.content).toBe("Hello!");
    expect(result.steps).toHaveLength(1);
    expect(result.steps[0].toolCalls).toHaveLength(0);
  });

  it("executes tool calls and feeds results back", async () => {
    let callNum = 0;
    const client = {
      chat: {
        completions: {
          create: jest.fn<any>(async () => {
            callNum++;
            if (callNum === 1) {
              return makeCompletion(null, "tool_calls", [
                {
                  id: "call_1",
                  type: "function",
                  function: {
                    name: "get_weather",
                    arguments: '{"city":"NYC"}',
                  },
                },
              ]);
            }
            return makeCompletion("The weather in NYC is sunny, 72F.", "stop");
          }),
        },
      },
    };

    const executeFn = jest.fn<any>(async (args: Record<string, unknown>) => ({
      temp: 72,
      condition: "sunny",
      city: args.city,
    }));

    const runner = new RunToolsRunner(client, {
      model: "gpt-4o",
      messages: [{ role: "user", content: "What's the weather in NYC?" }],
      tools: [
        {
          type: "function",
          function: {
            name: "get_weather",
            parameters: {
              type: "object",
              properties: { city: { type: "string" } },
            },
            execute: executeFn,
          },
        },
      ],
    });

    const result = await runner.run();

    expect(result.totalSteps).toBe(2);
    expect(executeFn).toHaveBeenCalledWith({ city: "NYC" });
    expect(result.steps[0].toolCalls).toHaveLength(1);
    expect(result.steps[0].toolResults[0].result).toEqual({
      temp: 72,
      condition: "sunny",
      city: "NYC",
    });
    expect(result.completion.choices[0].message.content).toContain("sunny");
  });

  it("handles errors in tool execute gracefully", async () => {
    let callNum = 0;
    const client = {
      chat: {
        completions: {
          create: jest.fn<any>(async () => {
            callNum++;
            if (callNum === 1) {
              return makeCompletion(null, "tool_calls", [
                {
                  id: "call_1",
                  type: "function",
                  function: { name: "bad_tool", arguments: "{}" },
                },
              ]);
            }
            return makeCompletion("I couldn't get the data.", "stop");
          }),
        },
      },
    };

    const runner = new RunToolsRunner(client, {
      model: "gpt-4o",
      messages: [{ role: "user", content: "test" }],
      tools: [
        {
          type: "function",
          function: {
            name: "bad_tool",
            execute: async () => {
              throw new Error("connection timeout");
            },
          },
        },
      ],
    });

    const result = await runner.run();

    // Should not throw — error is sent back to model
    expect(result.totalSteps).toBe(2);
    expect(result.steps[0].toolResults[0].result).toBe(
      "Error: connection timeout",
    );
  });

  it("handles unknown tool name", async () => {
    let callNum = 0;
    const client = {
      chat: {
        completions: {
          create: jest.fn<any>(async () => {
            callNum++;
            if (callNum === 1) {
              return makeCompletion(null, "tool_calls", [
                {
                  id: "call_1",
                  type: "function",
                  function: { name: "nonexistent", arguments: "{}" },
                },
              ]);
            }
            return makeCompletion("Done.", "stop");
          }),
        },
      },
    };

    const runner = new RunToolsRunner(client, {
      model: "gpt-4o",
      messages: [{ role: "user", content: "test" }],
      tools: [], // no tools registered
    });

    const result = await runner.run();

    expect(result.steps[0].toolResults[0].result).toBe(
      'Error: unknown tool "nonexistent"',
    );
  });

  it("respects maxSteps limit", async () => {
    // Model always requests tool calls — should stop at maxSteps
    const client = {
      chat: {
        completions: {
          create: jest.fn<any>(async () =>
            makeCompletion(null, "tool_calls", [
              {
                id: "call_1",
                type: "function",
                function: { name: "loop_tool", arguments: "{}" },
              },
            ]),
          ),
        },
      },
    };

    const runner = new RunToolsRunner(client, {
      model: "gpt-4o",
      messages: [{ role: "user", content: "test" }],
      tools: [
        {
          type: "function",
          function: {
            name: "loop_tool",
            execute: async () => "ok",
          },
        },
      ],
      maxSteps: 3,
    });

    const result = await runner.run();

    expect(result.totalSteps).toBe(3);
    expect(result.steps).toHaveLength(3);
    expect(client.chat.completions.create).toHaveBeenCalledTimes(3);
  });

  it("calls onStep callback for each step", async () => {
    let callNum = 0;
    const client = {
      chat: {
        completions: {
          create: jest.fn<any>(async () => {
            callNum++;
            if (callNum === 1) {
              return makeCompletion(null, "tool_calls", [
                {
                  id: "call_1",
                  type: "function",
                  function: { name: "tool", arguments: "{}" },
                },
              ]);
            }
            return makeCompletion("done", "stop");
          }),
        },
      },
    };

    const onStep = jest.fn<any>();
    const runner = new RunToolsRunner(client, {
      model: "gpt-4o",
      messages: [{ role: "user", content: "test" }],
      tools: [
        {
          type: "function",
          function: { name: "tool", execute: async () => "result" },
        },
      ],
      onStep,
    });

    await runner.run();

    expect(onStep).toHaveBeenCalledTimes(2);
  });

  it("handles multiple parallel tool calls", async () => {
    let callNum = 0;
    const client = {
      chat: {
        completions: {
          create: jest.fn<any>(async () => {
            callNum++;
            if (callNum === 1) {
              return makeCompletion(null, "tool_calls", [
                {
                  id: "call_1",
                  type: "function",
                  function: {
                    name: "get_weather",
                    arguments: '{"city":"NYC"}',
                  },
                },
                {
                  id: "call_2",
                  type: "function",
                  function: {
                    name: "get_weather",
                    arguments: '{"city":"LA"}',
                  },
                },
              ]);
            }
            return makeCompletion("NYC is sunny, LA is cloudy", "stop");
          }),
        },
      },
    };

    const runner = new RunToolsRunner(client, {
      model: "gpt-4o",
      messages: [{ role: "user", content: "weather in NYC and LA?" }],
      tools: [
        {
          type: "function",
          function: {
            name: "get_weather",
            execute: async (args: Record<string, unknown>) => ({
              city: args.city,
              temp: args.city === "NYC" ? 72 : 85,
            }),
          },
        },
      ],
    });

    const result = await runner.run();

    expect(result.totalSteps).toBe(2);
    expect(result.steps[0].toolCalls).toHaveLength(2);
    expect(result.steps[0].toolResults).toHaveLength(2);
  });
});
