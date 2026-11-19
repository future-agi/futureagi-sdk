import { describe, it, expect } from "@jest/globals";
import { RetryPolicy } from "../src/retry-policy.js";

describe("RetryPolicy", () => {
  it("returns defaults for each error type", () => {
    const rp = new RetryPolicy();
    expect(rp.getRetriesForStatus(429)).toBe(3);
    expect(rp.getRetriesForStatus(500)).toBe(2);
    expect(rp.getRetriesForStatus(502)).toBe(1);
    expect(rp.getRetriesForStatus(503)).toBe(1);
    expect(rp.getRetriesForStatus(504)).toBe(1);
    expect(rp.getRetriesForTimeout()).toBe(2);
    expect(rp.getRetriesForConnectionError()).toBe(2);
  });

  it("allows custom retry counts", () => {
    const rp = new RetryPolicy({
      rateLimitRetries: 5,
      timeoutRetries: 0,
      connectionErrorRetries: 1,
    });
    expect(rp.getRetriesForStatus(429)).toBe(5);
    expect(rp.getRetriesForTimeout()).toBe(0);
    expect(rp.getRetriesForConnectionError()).toBe(1);
  });

  it("returns 0 for unknown status codes", () => {
    const rp = new RetryPolicy();
    expect(rp.getRetriesForStatus(400)).toBe(0);
    expect(rp.getRetriesForStatus(401)).toBe(0);
    expect(rp.getRetriesForStatus(404)).toBe(0);
    expect(rp.getRetriesForStatus(418)).toBe(0);
  });

  it("partially overrides defaults", () => {
    const rp = new RetryPolicy({ rateLimitRetries: 10 });
    expect(rp.getRetriesForStatus(429)).toBe(10);
    // Other defaults still apply
    expect(rp.getRetriesForStatus(500)).toBe(2);
    expect(rp.getRetriesForTimeout()).toBe(2);
  });
});
