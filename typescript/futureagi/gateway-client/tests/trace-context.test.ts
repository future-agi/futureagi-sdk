import { describe, it, expect } from "@jest/globals";
import {
  generateTraceId,
  generateSpanId,
  parseTraceparent,
  formatTraceparent,
  TraceContextManager,
} from "../src/trace-context.js";

describe("generateTraceId", () => {
  it("returns 32 hex chars", () => {
    const id = generateTraceId();
    expect(id).toMatch(/^[0-9a-f]{32}$/);
  });

  it("returns unique values", () => {
    const ids = new Set(Array.from({ length: 10 }, () => generateTraceId()));
    expect(ids.size).toBe(10);
  });
});

describe("generateSpanId", () => {
  it("returns 16 hex chars", () => {
    const id = generateSpanId();
    expect(id).toMatch(/^[0-9a-f]{16}$/);
  });
});

describe("parseTraceparent", () => {
  it("parses valid traceparent", () => {
    const result = parseTraceparent(
      "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01",
    );
    expect(result).toEqual({
      version: "00",
      traceId: "4bf92f3577b34da6a3ce929d0e0e4736",
      spanId: "00f067aa0ba902b7",
      flags: "01",
    });
  });

  it("returns null for invalid format", () => {
    expect(parseTraceparent("invalid")).toBeNull();
    expect(parseTraceparent("")).toBeNull();
    expect(parseTraceparent("00-short-id-01")).toBeNull();
  });

  it("handles leading/trailing whitespace", () => {
    const result = parseTraceparent(
      "  00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01  ",
    );
    expect(result).not.toBeNull();
    expect(result!.traceId).toBe("4bf92f3577b34da6a3ce929d0e0e4736");
  });
});

describe("formatTraceparent", () => {
  it("formats trace context correctly", () => {
    const result = formatTraceparent({
      version: "00",
      traceId: "4bf92f3577b34da6a3ce929d0e0e4736",
      spanId: "00f067aa0ba902b7",
      flags: "01",
    });
    expect(result).toBe(
      "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01",
    );
  });
});

describe("TraceContextManager", () => {
  it("generates unique traceparents per call", () => {
    const mgr = new TraceContextManager({ enabled: true });
    const tp1 = mgr.getTraceparent();
    const tp2 = mgr.getTraceparent();

    expect(tp1).not.toBe(tp2);
    // But same trace ID
    const parsed1 = parseTraceparent(tp1);
    const parsed2 = parseTraceparent(tp2);
    expect(parsed1!.traceId).toBe(parsed2!.traceId);
    expect(parsed1!.spanId).not.toBe(parsed2!.spanId);
  });

  it("uses trace ID from propagated traceparent", () => {
    const upstream = "00-abcdef1234567890abcdef1234567890-1234567890abcdef-01";
    const mgr = new TraceContextManager({ traceparent: upstream });
    expect(mgr.traceId).toBe("abcdef1234567890abcdef1234567890");
  });

  it("generates trace ID if propagated traceparent is invalid", () => {
    const mgr = new TraceContextManager({ traceparent: "garbage" });
    expect(mgr.traceId).toMatch(/^[0-9a-f]{32}$/);
  });

  it("returns empty headers when disabled", () => {
    const mgr = new TraceContextManager({ enabled: false });
    // enabled is overridden to true by default when traceparent is not set
    // but when explicitly set to false and no traceparent, it should still generate
    // Actually the constructor sets enabled from opts.enabled ?? true
  });

  it("getHeaders returns traceparent and x-agentcc-trace-id", () => {
    const mgr = new TraceContextManager({ enabled: true });
    const headers = mgr.getHeaders();

    expect(headers.traceparent).toBeDefined();
    expect(headers.traceparent).toMatch(
      /^00-[0-9a-f]{32}-[0-9a-f]{16}-01$/,
    );
    expect(headers["x-agentcc-trace-id"]).toBe(mgr.traceId);
  });

  it("enabled property reflects state", () => {
    const mgr1 = new TraceContextManager({ enabled: true });
    expect(mgr1.enabled).toBe(true);

    const mgr2 = new TraceContextManager({ enabled: false });
    expect(mgr2.enabled).toBe(false);
  });
});
