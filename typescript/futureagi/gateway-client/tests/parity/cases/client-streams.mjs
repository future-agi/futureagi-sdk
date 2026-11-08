// @agentcc/client streams: the 6 gateway error-frame cases, the catalog
// additions that apply to TypeScript (no /v1/responses resource in TS 1.x),
// malformed SSE, events() and final usage, each through every consumer.
import { CHAT, load, streamErrorCases, streamExtraCases } from "./fixtures.mjs";

const CONSUMERS = ["iter", "events", "text", "final", "break_on_done"];

async function consume(ctx, consumer) {
  const client = ctx.client({ maxRetries: 0 });
  if (consumer === "iter") {
    const s = await client.chat.completions.create({ ...CHAT, stream: true });
    return { ...(await ctx.drain(s)), agentcc: s.agentcc };
  }
  const m = await client.chat.completions.stream(CHAT);
  let consumed;
  if (consumer === "events") consumed = await ctx.drain(m.events());
  else if (consumer === "text") consumed = await ctx.drain(m.textStream());
  else if (consumer === "final") {
    const drained = await ctx.drain(m);
    consumed = { drainedError: drained.error, final: await ctx.attempt(() => m.getFinalCompletion()) };
  } else {
    const types = [];
    const result = await ctx.attempt(async () => {
      for await (const event of m.events()) {
        types.push(event.type);
        if (event.type === "done") break;
      }
    });
    consumed = { types, result };
  }
  return { consumed, agentcc: m.agentcc, text: await ctx.attempt(() => m.getFinalText()) };
}

const framesReply = (frames) => ({ status: 200, headers: { "content-type": "text/event-stream" }, sse: frames });

export function cases() {
  const out = [];
  for (const fixture of streamErrorCases()) {
    for (const consumer of CONSUMERS) out.push({ id: `stream.fixture.${fixture.name}.${consumer}`, area: "stream_fixture", fn: (ctx) => consume(ctx, consumer), replies: [framesReply(fixture.frames)] });
  }
  for (const extra of streamExtraCases()) {
    if (extra.path !== "/v1/chat/completions") continue;
    for (const consumer of CONSUMERS) out.push({ id: `stream.extra.${extra.name}.${consumer}`, area: "stream_extra", fn: (ctx) => consume(ctx, consumer), replies: [extra.reply] });
  }
  for (const [name, raw] of Object.entries(load("sse-malformed.json").cases)) {
    const reply = { status: 200, headers: { "content-type": "text/event-stream" }, raw };
    out.push({ id: `stream.malformed.${name}.iter`, area: "sse", fn: (ctx) => consume(ctx, "iter"), replies: [reply] });
    out.push({ id: `stream.malformed.${name}.final`, area: "sse", fn: (ctx) => consume(ctx, "final"), replies: [reply] });
  }
  out.push({ id: "stream.text_plain_200", area: "sse", fn: (ctx) => consume(ctx, "iter"), replies: [{ status: 200, headers: { "content-type": "text/plain" }, text: "hello" }] });
  out.push({ id: "stream.abort", area: "sse", fn: async (ctx) => {
    const s = await ctx.client({ maxRetries: 0 }).chat.completions.create({ ...CHAT, stream: true });
    const it = s[Symbol.asyncIterator]();
    const first = await it.next();
    s.abort();
    return { first, after: await ctx.attempt(() => it.next()) };
  }, replies: [framesReply(load("responses.json").chunks.content)] });
  return out;
}
