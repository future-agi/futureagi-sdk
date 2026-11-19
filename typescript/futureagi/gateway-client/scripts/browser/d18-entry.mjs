// A browser page's use of @future-agi/sdk/gateway (D-18), bundled by esbuild
// from the installed tarball and run by d18-browser.cjs in Chromium, Firefox
// and WebKit. The gateway URL comes from ?api=; the result goes to
// window.__d18.
import { AgentCC, AgentCCError } from "@future-agi/sdk/gateway";

const api = new URLSearchParams(location.search).get("api");
const PARAMS = { model: "m", messages: [{ role: "user", content: "hi" }] };
const out = {};
const failure = (e) => `${e && e.name}: ${e && e.message}`.slice(0, 200);

try {
  new AgentCC({ apiKey: "vk-browser", baseUrl: api });
  out.refused = false;
} catch (e) {
  out.refused = e instanceof AgentCCError;
  out.refusedMessage = String(e.message).slice(0, 120);
}

const client = new AgentCC({ apiKey: "vk-browser", baseUrl: api, dangerouslyAllowBrowser: true, maxRetries: 0 });
out.dryHeaderNames = Object.keys(client.chat.completions.dryRun(PARAMS).headers).map((h) => h.toLowerCase()).sort();

try {
  const r = await client.chat.completions.create({ ...PARAMS, session_id: "s-browser" });
  out.content = r.choices[0].message.content;
  out.cost = r.agentcc.cost;
  out.requestId = r.agentcc.requestId;
} catch (e) {
  out.requestError = failure(e);
}

try {
  let text = "";
  for await (const chunk of await client.chat.completions.create({ ...PARAMS, stream: true })) {
    text += (chunk.choices[0] && chunk.choices[0].delta.content) || "";
  }
  out.streamed = text;
} catch (e) {
  out.streamError = failure(e);
}

// Negative control: a header the gateway's CORS allowlist does not name is
// refused by the browser's preflight, so the check above means something.
try {
  const control = new AgentCC({ apiKey: "vk-browser", baseUrl: api, dangerouslyAllowBrowser: true, maxRetries: 0, defaultHeaders: { "x-agentcc-sdk-version": "control" } });
  await control.chat.completions.create(PARAMS);
  out.controlError = null;
} catch (e) {
  out.controlError = failure(e);
}

window.__d18 = out;
