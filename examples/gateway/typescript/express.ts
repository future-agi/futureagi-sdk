import express, { type Request } from "express";
import type { AgentCC } from "@future-agi/sdk/gateway";
import { agentccMiddleware } from "@future-agi/sdk/gateway/express";
import { messagesFrom } from "./messages.js";
import { isMain, settings } from "./settings.js";

/** Local-only demo. Add application authentication and rate limits before deploying. */
export function createApp() {
  const { apiKey, baseUrl, model } = settings();
  const app = express();
  app.use(express.json({ limit: "96kb" }));
  app.use(agentccMiddleware({ apiKey, baseUrl, clientOptions: { maxRetries: 0, timeout: 15_000 } }));
  app.post("/api/chat", async (request: Request & { agentcc?: AgentCC }, response) => {
    let messages;
    try {
      messages = messagesFrom(request.body);
    } catch {
      response.status(400).json({ error: "Invalid messages" });
      return;
    }
    try {
      const answer = await request.agentcc!.chat.completions.create({ model, messages });
      response.json({ text: answer.choices[0].message.content });
    } catch {
      // Do not leak upstream bodies, configuration or credentials to the browser.
      response.status(502).json({ error: "Gateway request failed" });
    }
  });
  return app;
}

if (isMain(import.meta.url)) {
  createApp().listen(3001, "127.0.0.1", () => console.log("Chat demo listening on http://127.0.0.1:3001"));
}
