import {
  getModelInfo,
  getValidModels,
  registerModel,
  modelAliasMap,
  supportsVision,
  supportsFunctionCalling,
  supportsJsonMode,
  supportsResponseSchema,
  validateEnvironment,
} from "../models-info";
import type { ModelInfo } from "../models-info";

describe("getModelInfo", () => {
  it("returns info for exact model names", () => {
    const info = getModelInfo("gpt-4o");
    expect(info).not.toBeNull();
    expect(info!.maxTokens).toBe(128000);
    expect(info!.maxOutputTokens).toBe(16384);
    expect(info!.inputCostPerToken).toBe(2.5e-6);
    expect(info!.supportsVision).toBe(true);
  });

  it("returns null for unknown models", () => {
    expect(getModelInfo("unknown-model-xyz")).toBeNull();
  });

  it("resolves aliases", () => {
    modelAliasMap["gpt4"] = "gpt-4o";
    const info = getModelInfo("gpt4");
    expect(info).not.toBeNull();
    expect(info!.maxTokens).toBe(128000);
    delete modelAliasMap["gpt4"];
  });

  it("resolves prefix matches", () => {
    const info = getModelInfo("gpt-4o-2024-08-06");
    expect(info).not.toBeNull();
    expect(info!.maxTokens).toBe(128000);
  });

  it("exact match takes precedence over prefix", () => {
    const info = getModelInfo("gpt-4");
    expect(info).not.toBeNull();
    expect(info!.maxTokens).toBe(8192); // gpt-4, not gpt-4o
  });
});

describe("getValidModels", () => {
  it("returns non-empty list", () => {
    const models = getValidModels();
    expect(models.length).toBeGreaterThan(0);
  });

  it("contains known models", () => {
    const models = getValidModels();
    expect(models).toContain("gpt-4o");
    expect(models).toContain("claude-sonnet-4-20250514");
    expect(models).toContain("gemini-2.0-flash");
  });

  it("all entries are strings", () => {
    for (const m of getValidModels()) {
      expect(typeof m).toBe("string");
    }
  });
});

describe("registerModel", () => {
  it("registers a new model", () => {
    const info: ModelInfo = {
      maxTokens: 32000,
      maxOutputTokens: 8000,
      inputCostPerToken: 1e-6,
      outputCostPerToken: 2e-6,
      supportsVision: false,
      supportsFunctionCalling: true,
      supportsJsonMode: false,
    };
    registerModel("my-custom-model", info);
    expect(getModelInfo("my-custom-model")).toEqual(info);
    expect(getValidModels()).toContain("my-custom-model");
  });
});

describe("capability checks", () => {
  it("supportsVision for gpt-4o", () => {
    expect(supportsVision("gpt-4o")).toBe(true);
  });

  it("supportsVision returns false for unknown", () => {
    expect(supportsVision("nonexistent")).toBe(false);
  });

  it("supportsFunctionCalling for claude-sonnet-4", () => {
    expect(supportsFunctionCalling("claude-sonnet-4-20250514")).toBe(true);
  });

  it("supportsJsonMode for gpt-4o-mini", () => {
    expect(supportsJsonMode("gpt-4o-mini")).toBe(true);
  });

  it("supportsResponseSchema is alias for supportsJsonMode", () => {
    expect(supportsResponseSchema("gpt-4o")).toBe(supportsJsonMode("gpt-4o"));
  });

  it("llama-3.1-8b does not support function calling", () => {
    expect(supportsFunctionCalling("llama-3.1-8b")).toBe(false);
  });
});

describe("validateEnvironment", () => {
  const origKey = process.env.AGENTCC_API_KEY;
  const origUrl = process.env.AGENTCC_BASE_URL;

  beforeEach(() => {
    delete process.env.AGENTCC_API_KEY;
    delete process.env.AGENTCC_BASE_URL;
  });

  it("reports missing vars", () => {
    const result = validateEnvironment();
    expect(result.ready).toBe(false);
    expect(result.keysMissing).toContain("AGENTCC_API_KEY");
    expect(result.keysMissing).toContain("AGENTCC_BASE_URL");
  });

  it("reports set vars", () => {
    process.env.AGENTCC_API_KEY = "sk-test";
    process.env.AGENTCC_BASE_URL = "http://localhost:8090";
    const result = validateEnvironment();
    expect(result.ready).toBe(true);
    expect(result.keysSet).toContain("AGENTCC_API_KEY");
    expect(result.keysSet).toContain("AGENTCC_BASE_URL");
  });

  // Restore
  afterAll(() => {
    if (origKey) process.env.AGENTCC_API_KEY = origKey;
    else delete process.env.AGENTCC_API_KEY;
    if (origUrl) process.env.AGENTCC_BASE_URL = origUrl;
    else delete process.env.AGENTCC_BASE_URL;
  });
});
