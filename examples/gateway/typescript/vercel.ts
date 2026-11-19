import { createOpenAI } from "@ai-sdk/openai";
import { generateText } from "ai";
import { aiSdkProviderSettings } from "@future-agi/sdk/gateway";
import { isMain, settings } from "./settings.js";

/** Select the chat API explicitly so this example does not rely on provider defaults. */
export async function ask(prompt: string): Promise<string> {
  const { apiKey, baseUrl, model } = settings();
  const gateway = createOpenAI(aiSdkProviderSettings({
    apiKey,
    baseURL: baseUrl,
    sessionId: "example-vercel",
  }));
  const answer = await generateText({
    model: gateway.chat(model),
    prompt,
    maxRetries: 0,
    abortSignal: AbortSignal.timeout(15_000),
  });
  return answer.text;
}

if (isMain(import.meta.url)) console.log(await ask("Say hello in one sentence."));
