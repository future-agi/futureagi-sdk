import { createMiddleware, composeMiddlewares } from "../middleware";
import type { MiddlewareContext, MiddlewareResult, NextFn } from "../middleware";
import type { AgentCCMetadata } from "../types/shared";

function makeAgentCCMeta(): AgentCCMetadata {
  return {
    requestId: "req-1",
    traceId: "trace-1",
    provider: "openai",
    latencyMs: 100,
    cost: 0.005,
    cacheStatus: null,
    modelUsed: "gpt-4o",
    guardrailTriggered: false,
    guardrailName: null,
    guardrailAction: null,
    guardrailConfidence: null,
    guardrailMessage: null,
    fallbackUsed: false,
    routingStrategy: null,
    timeoutMs: null,
    ratelimit: null,
  };
}

function makeResult(data: unknown = { ok: true }): MiddlewareResult {
  return {
    data,
    response: new Response("ok"),
    statusCode: 200,
    latencyMs: 100,
    agentcc: makeAgentCCMeta(),
  };
}

function makeContext(overrides?: Partial<MiddlewareContext>): MiddlewareContext {
  return {
    method: "POST",
    path: "/v1/chat/completions",
    body: { model: "gpt-4o", messages: [] },
    headers: {},
    model: "gpt-4o",
    ...overrides,
  };
}

describe("createMiddleware", () => {
  it("creates a middleware with name", () => {
    const mw = createMiddleware({
      name: "test",
      async onRequest(ctx, next) {
        return next(ctx);
      },
    });
    expect(mw.name).toBe("test");
    expect(typeof mw.onRequest).toBe("function");
  });
});

describe("composeMiddlewares", () => {
  it("calls handler when no middlewares", async () => {
    const handler = jest.fn(async () => makeResult());
    const composed = composeMiddlewares([], handler);

    const ctx = makeContext();
    await composed(ctx);

    expect(handler).toHaveBeenCalledWith(ctx);
  });

  it("runs middleware in correct order (first = outermost)", async () => {
    const order: string[] = [];

    const mw1 = createMiddleware({
      name: "first",
      async onRequest(ctx, next) {
        order.push("first-before");
        const result = await next(ctx);
        order.push("first-after");
        return result;
      },
    });

    const mw2 = createMiddleware({
      name: "second",
      async onRequest(ctx, next) {
        order.push("second-before");
        const result = await next(ctx);
        order.push("second-after");
        return result;
      },
    });

    const handler = jest.fn(async () => {
      order.push("handler");
      return makeResult();
    });

    const composed = composeMiddlewares([mw1, mw2], handler);
    await composed(makeContext());

    expect(order).toEqual([
      "first-before",
      "second-before",
      "handler",
      "second-after",
      "first-after",
    ]);
  });

  it("middleware can modify the context", async () => {
    const mw = createMiddleware({
      name: "header-injector",
      async onRequest(ctx, next) {
        return next({
          ...ctx,
          headers: { ...ctx.headers, "x-custom": "injected" },
        });
      },
    });

    const handler = jest.fn(async (ctx: MiddlewareContext) => {
      expect(ctx.headers["x-custom"]).toBe("injected");
      return makeResult();
    });

    const composed = composeMiddlewares([mw], handler);
    await composed(makeContext());

    expect(handler).toHaveBeenCalled();
  });

  it("middleware can modify the result", async () => {
    const mw = createMiddleware({
      name: "enricher",
      async onRequest(ctx, next) {
        const result = await next(ctx);
        return { ...result, data: { ...result.data as Record<string, unknown>, enriched: true } };
      },
    });

    const handler = jest.fn(async () => makeResult({ original: true }));
    const composed = composeMiddlewares([mw], handler);
    const result = await composed(makeContext());

    expect((result.data as Record<string, unknown>).original).toBe(true);
    expect((result.data as Record<string, unknown>).enriched).toBe(true);
  });

  it("middleware can short-circuit (skip handler)", async () => {
    const mw = createMiddleware({
      name: "cache",
      async onRequest(_ctx, _next) {
        // Don't call next — return cached result
        return makeResult({ cached: true });
      },
    });

    const handler = jest.fn(async () => makeResult());
    const composed = composeMiddlewares([mw], handler);
    const result = await composed(makeContext());

    expect(handler).not.toHaveBeenCalled();
    expect((result.data as Record<string, unknown>).cached).toBe(true);
  });

  it("errors propagate through middleware", async () => {
    const mw = createMiddleware({
      name: "error-handler",
      async onRequest(ctx, next) {
        try {
          return await next(ctx);
        } catch (err) {
          return makeResult({ error: (err as Error).message });
        }
      },
    });

    const handler = jest.fn(async () => {
      throw new Error("upstream failure");
    });

    const composed = composeMiddlewares([mw], handler);
    const result = await composed(makeContext());

    expect((result.data as Record<string, unknown>).error).toBe("upstream failure");
  });

  it("middleware that throws propagates to caller", async () => {
    const mw = createMiddleware({
      name: "broken",
      async onRequest(_ctx, _next) {
        throw new Error("middleware crash");
      },
    });

    const handler = jest.fn(async () => makeResult());
    const composed = composeMiddlewares([mw], handler);

    await expect(composed(makeContext())).rejects.toThrow("middleware crash");
    expect(handler).not.toHaveBeenCalled();
  });
});
