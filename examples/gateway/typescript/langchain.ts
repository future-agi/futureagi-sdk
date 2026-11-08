import { ChatOpenAI } from "@langchain/openai";
import { openaiOptions } from "@future-agi/sdk/gateway";
import { isMain, settings } from "./settings.js";

/** Use stock ChatOpenAI; the helper supplies the explicit gateway URL and headers. */
export async function ask(prompt: string): Promise<string> {
  const { apiKey, baseUrl, model } = settings();
  const options = openaiOptions({ apiKey, baseUrl, sessionId: "example-langchain" });
  const chat = new ChatOpenAI({
    model,
    apiKey: options.apiKey,
    configuration: options,
    maxRetries: 0,
    timeout: 15_000,
  });
  return String((await chat.invoke(prompt)).content);
}

if (isMain(import.meta.url)) console.log(await ask("Say hello in one sentence."));
