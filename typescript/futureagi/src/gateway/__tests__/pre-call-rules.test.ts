import {
  evaluatePreCallRules,
  allowModels,
  blockModels,
  requireSessionId,
} from "../pre-call-rules";
import type { PreCallRule, PreCallRuleInput } from "../pre-call-rules";

function makeInput(overrides: Partial<PreCallRuleInput> = {}): PreCallRuleInput {
  return {
    model: "gpt-4o",
    path: "/v1/chat/completions",
    body: { model: "gpt-4o", messages: [] },
    ...overrides,
  };
}

describe("evaluatePreCallRules", () => {
  it("passes when no rules", () => {
    expect(() => evaluatePreCallRules([], makeInput())).not.toThrow();
  });

  it("passes when all rules allow", () => {
    const rules: PreCallRule[] = [
      () => ({ allow: true }),
      () => ({ allow: true }),
    ];
    expect(() => evaluatePreCallRules(rules, makeInput())).not.toThrow();
  });

  it("throws on first blocking rule", () => {
    const rules: PreCallRule[] = [
      () => ({ allow: true }),
      () => ({ allow: false, reason: "blocked by test" }),
      () => ({ allow: true }),
    ];
    expect(() => evaluatePreCallRules(rules, makeInput())).toThrow(
      "blocked by test",
    );
  });

  it("includes default reason when none given", () => {
    const rules: PreCallRule[] = [() => ({ allow: false })];
    expect(() => evaluatePreCallRules(rules, makeInput())).toThrow(
      "no reason given",
    );
  });

  it("passes input to rule functions", () => {
    const captured: PreCallRuleInput[] = [];
    const rules: PreCallRule[] = [
      (input) => {
        captured.push(input);
        return { allow: true };
      },
    ];
    const input = makeInput({ model: "special-model" });
    evaluatePreCallRules(rules, input);
    expect(captured).toHaveLength(1);
    expect(captured[0].model).toBe("special-model");
  });
});

describe("allowModels", () => {
  it("allows listed models", () => {
    const rule = allowModels(["gpt-4o", "gpt-4o-mini"]);
    expect(rule(makeInput({ model: "gpt-4o" })).allow).toBe(true);
    expect(rule(makeInput({ model: "gpt-4o-mini" })).allow).toBe(true);
  });

  it("blocks unlisted models", () => {
    const rule = allowModels(["gpt-4o"]);
    const result = rule(makeInput({ model: "o1-preview" }));
    expect(result.allow).toBe(false);
    expect(result.reason).toContain("o1-preview");
    expect(result.reason).toContain("not in the allowed list");
  });

  it("allows requests without a model", () => {
    const rule = allowModels(["gpt-4o"]);
    expect(rule(makeInput({ model: undefined })).allow).toBe(true);
  });
});

describe("blockModels", () => {
  it("blocks listed models", () => {
    const rule = blockModels(["o1-preview"]);
    const result = rule(makeInput({ model: "o1-preview" }));
    expect(result.allow).toBe(false);
    expect(result.reason).toContain("o1-preview");
  });

  it("allows unlisted models", () => {
    const rule = blockModels(["o1-preview"]);
    expect(rule(makeInput({ model: "gpt-4o" })).allow).toBe(true);
  });
});

describe("requireSessionId", () => {
  it("blocks when no session_id", () => {
    const rule = requireSessionId();
    const result = rule(makeInput({ body: { model: "gpt-4o", messages: [] } }));
    expect(result.allow).toBe(false);
    expect(result.reason).toContain("session_id");
  });

  it("allows when session_id present", () => {
    const rule = requireSessionId();
    const result = rule(
      makeInput({
        body: { model: "gpt-4o", messages: [], session_id: "sess-123" },
      }),
    );
    expect(result.allow).toBe(true);
  });
});
