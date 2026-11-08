import { describe, it, expect, jest } from "@jest/globals";
import { AgentCC } from "../src/client.js";

describe("audio resource", () => {
  it("transcriptions.create() sends FormData POST to /v1/audio/transcriptions", async () => {
    const mockFetch = jest.fn<any>().mockResolvedValue(
      new Response(
        JSON.stringify({ text: "Hello world", task: "transcribe", language: "en" }),
        { status: 200, headers: { "content-type": "application/json" } },
      ),
    );
    const client = new AgentCC({ apiKey: "sk-test", fetch: mockFetch });

    const blob = new Blob(["fake audio"], { type: "audio/mp3" });
    const result = await client.audio.transcriptions.create({
      file: blob,
      model: "whisper-1",
      language: "en",
    });

    expect(result.text).toBe("Hello world");
    expect(result.agentcc).toBeDefined();
    const [url, init] = mockFetch.mock.calls[0];
    expect(url).toContain("/v1/audio/transcriptions");
    expect(init.body).toBeInstanceOf(FormData);
  });

  it("translations.create() sends FormData POST to /v1/audio/translations", async () => {
    const mockFetch = jest.fn<any>().mockResolvedValue(
      new Response(
        JSON.stringify({ text: "Translated text", task: "translate" }),
        { status: 200, headers: { "content-type": "application/json" } },
      ),
    );
    const client = new AgentCC({ apiKey: "sk-test", fetch: mockFetch });

    const blob = new Blob(["fake audio"], { type: "audio/mp3" });
    const result = await client.audio.translations.create({
      file: blob,
      model: "whisper-1",
    });

    expect(result.text).toBe("Translated text");
    expect(result.agentcc).toBeDefined();
    expect(mockFetch.mock.calls[0][0]).toContain("/v1/audio/translations");
  });

  it("speech.create() sends POST and returns raw Response", async () => {
    const mockFetch = jest.fn<any>().mockResolvedValue(
      new Response("audio bytes...", {
        status: 200,
        headers: { "content-type": "audio/mpeg" },
      }),
    );
    const client = new AgentCC({ apiKey: "sk-test", fetch: mockFetch });

    const result = await client.audio.speech.create({
      model: "tts-1",
      voice: "alloy",
      input: "Hello world",
    });

    expect(result).toBeInstanceOf(Response);
    const [url, init] = mockFetch.mock.calls[0];
    expect(url).toContain("/v1/audio/speech");
    expect(init.method).toBe("POST");
    const body = JSON.parse(init.body);
    expect(body.voice).toBe("alloy");
    expect(body.input).toBe("Hello world");
  });
});
