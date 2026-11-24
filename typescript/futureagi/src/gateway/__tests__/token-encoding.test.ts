import { getEncodingForModel, _resetTokenizerCache, encode, decode } from "../token-encoding";

describe("getEncodingForModel", () => {
  it("maps gpt-4o to o200k_base", () => {
    expect(getEncodingForModel("gpt-4o")).toBe("o200k_base");
  });

  it("maps gpt-4o-mini to o200k_base", () => {
    expect(getEncodingForModel("gpt-4o-mini")).toBe("o200k_base");
  });

  it("maps gpt-4 to cl100k_base", () => {
    expect(getEncodingForModel("gpt-4")).toBe("cl100k_base");
  });

  it("maps gpt-3.5-turbo to cl100k_base", () => {
    expect(getEncodingForModel("gpt-3.5-turbo")).toBe("cl100k_base");
  });

  it("maps gpt-4-turbo to cl100k_base", () => {
    expect(getEncodingForModel("gpt-4-turbo")).toBe("cl100k_base");
  });

  it("maps o1 to o200k_base", () => {
    expect(getEncodingForModel("o1")).toBe("o200k_base");
  });

  it("maps o3-mini to o200k_base", () => {
    expect(getEncodingForModel("o3-mini")).toBe("o200k_base");
  });

  it("falls back to cl100k_base for unknown models", () => {
    expect(getEncodingForModel("claude-3-opus")).toBe("cl100k_base");
    expect(getEncodingForModel("unknown-model")).toBe("cl100k_base");
  });

  it("handles versioned model names via prefix matching", () => {
    expect(getEncodingForModel("gpt-4o-2024-05-13")).toBe("o200k_base");
    expect(getEncodingForModel("gpt-4-0613")).toBe("cl100k_base");
  });

  it("maps embedding models", () => {
    expect(getEncodingForModel("text-embedding-3-small")).toBe("cl100k_base");
    expect(getEncodingForModel("text-embedding-3-large")).toBe("cl100k_base");
  });
});

describe("encode/decode", () => {
  it("throws when gpt-tokenizer is not installed", async () => {
    _resetTokenizerCache();
    // gpt-tokenizer is not installed in this test environment
    await expect(encode("gpt-4o", "Hello")).rejects.toThrow(
      "gpt-tokenizer",
    );
  });

  it("decode throws when gpt-tokenizer is not installed", async () => {
    _resetTokenizerCache();
    await expect(decode("gpt-4o", [1, 2, 3])).rejects.toThrow(
      "gpt-tokenizer",
    );
  });
});
