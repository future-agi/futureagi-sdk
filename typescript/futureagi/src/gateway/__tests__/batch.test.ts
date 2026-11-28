import { batchCompletion, batchCompletionModels } from "../batch";
import type { ChatCompletion } from "../types/chat/chat-completion";

function makeCompletion(content: string, model = "gpt-4o"): ChatCompletion {
  return {
    id: `chatcmpl-${Math.random().toString(36).slice(2)}`,
    object: "chat.completion",
    created: Date.now(),
    model,
    choices: [
      {
        index: 0,
        message: { role: "assistant", content },
        finish_reason: "stop",
      },
    ],
    usage: { prompt_tokens: 10, completion_tokens: 5, total_tokens: 15 },
  };
}

function makeMockClient(responses?: ChatCompletion[]) {
  let callIndex = 0;
  const createFn = jest.fn(async (params: { model: string }) => {
    if (responses && callIndex < responses.length) {
      return responses[callIndex++];
    }
    return makeCompletion("response", params.model);
  });

  return {
    chat: { completions: { create: createFn } },
    _createFn: createFn,
  };
}

describe("batchCompletion", () => {
  it("runs multiple completions and preserves order", async () => {
    const responses = [
      makeCompletion("first"),
      makeCompletion("second"),
      makeCompletion("third"),
    ];
    const client = makeMockClient(responses);

    const results = await batchCompletion(client, {
      model: "gpt-4o",
      messages: [
        [{ role: "user", content: "1" }],
        [{ role: "user", content: "2" }],
        [{ role: "user", content: "3" }],
      ],
    });

    expect(results).toHaveLength(3);
    expect((results[0] as ChatCompletion).choices[0].message.content).toBe("first");
    expect((results[1] as ChatCompletion).choices[0].message.content).toBe("second");
    expect((results[2] as ChatCompletion).choices[0].message.content).toBe("third");
    expect(client._createFn).toHaveBeenCalledTimes(3);
  });

  it("respects maxConcurrency", async () => {
    let concurrentCount = 0;
    let maxConcurrent = 0;

    const client = {
      chat: {
        completions: {
          create: jest.fn(async () => {
            concurrentCount++;
            maxConcurrent = Math.max(maxConcurrent, concurrentCount);
            await new Promise((r) => setTimeout(r, 10));
            concurrentCount--;
            return makeCompletion("ok");
          }),
        },
      },
    };

    await batchCompletion(client, {
      model: "gpt-4o",
      messages: Array(10).fill([{ role: "user" as const, content: "hi" }]),
      maxConcurrency: 2,
    });

    expect(maxConcurrent).toBeLessThanOrEqual(2);
  });

  it("returnExceptions captures errors instead of throwing", async () => {
    let callNum = 0;
    const client = {
      chat: {
        completions: {
          create: jest.fn(async () => {
            callNum++;
            if (callNum === 2) throw new Error("API error");
            return makeCompletion("ok");
          }),
        },
      },
    };

    const results = await batchCompletion(client, {
      model: "gpt-4o",
      messages: [
        [{ role: "user", content: "1" }],
        [{ role: "user", content: "2" }],
        [{ role: "user", content: "3" }],
      ],
      returnExceptions: true,
    });

    expect(results).toHaveLength(3);
    expect(results[0]).toHaveProperty("choices");
    expect(results[1]).toBeInstanceOf(Error);
    expect(results[2]).toHaveProperty("choices");
  });

  it("throws on first error when returnExceptions is false", async () => {
    let callNum = 0;
    const client = {
      chat: {
        completions: {
          create: jest.fn(async () => {
            callNum++;
            if (callNum === 1) throw new Error("fail");
            return makeCompletion("ok");
          }),
        },
      },
    };

    await expect(
      batchCompletion(client, {
        model: "gpt-4o",
        messages: [
          [{ role: "user", content: "1" }],
          [{ role: "user", content: "2" }],
        ],
        returnExceptions: false,
      }),
    ).rejects.toThrow("fail");
  });
});

describe("batchCompletionModels", () => {
  it("runs same prompt across different models", async () => {
    const client = makeMockClient();

    const results = await batchCompletionModels(client, {
      models: ["gpt-4o", "claude-3.5-sonnet", "gemini-1.5-pro"],
      messages: [{ role: "user", content: "hello" }],
    });

    expect(results).toHaveLength(3);
    expect(results[0].model).toBe("gpt-4o");
    expect(results[1].model).toBe("claude-3.5-sonnet");
    expect(results[2].model).toBe("gemini-1.5-pro");
    expect(results[0].completion).not.toBeNull();
    expect(results[0].error).toBeNull();
  });

  it("captures per-model errors without throwing", async () => {
    let callNum = 0;
    const client = {
      chat: {
        completions: {
          create: jest.fn(async (params: { model: string }) => {
            callNum++;
            if (params.model === "bad-model") throw new Error("not found");
            return makeCompletion("ok", params.model);
          }),
        },
      },
    };

    const results = await batchCompletionModels(client, {
      models: ["gpt-4o", "bad-model", "claude-3.5-sonnet"],
      messages: [{ role: "user", content: "hi" }],
    });

    expect(results[0].completion).not.toBeNull();
    expect(results[0].error).toBeNull();
    expect(results[1].completion).toBeNull();
    expect(results[1].error).toBeInstanceOf(Error);
    expect(results[2].completion).not.toBeNull();
  });
});
