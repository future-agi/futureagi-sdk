import assert from "node:assert/strict";
import { test } from "node:test";
import { setTimeout } from "node:timers/promises";
import React from "react";
import { act, create, type ReactTestRenderer } from "react-test-renderer";
import Chat from "../app/chat.js";
import { POST } from "../app/api/chat/route.js";
import { resetAgentCCClient } from "@future-agi/sdk/gateway/nextjs";
import { answer, key, mockGateway, configure } from "./mock-gateway.js";

test("React can send again after gateway failures without losing completed replies", async () => {
  const gateway = await mockGateway();
  const restore = configure(gateway.url);
  const originalFetch = globalThis.fetch;
  const statuses: number[] = [];
  const browserRequests: Request[] = [];
  let view: ReactTestRenderer | undefined;
  resetAgentCCClient();
  globalThis.fetch = async (input, init) => {
    if (input !== "/api/chat") return originalFetch(input, init);
    const request = new Request("http://localhost:3000/api/chat", init);
    browserRequests.push(request.clone());
    const response = await POST(request);
    statuses.push(response.status);
    return response;
  };
  async function send(text: string) {
    const expectedResponses = statuses.length + 1;
    await act(async () => { view!.root.findByType("input").props.onChange({ target: { value: text } }); });
    await act(async () => { view!.root.findByType("form").props.onSubmit({ preventDefault() {} }); });
    for (let attempt = 0; attempt < 100; attempt++) {
      const loading = view!.root.findAllByType("button").some((button) => button.props.children === "Stop");
      if (statuses.length === expectedResponses && !loading) return;
      await act(async () => { await setTimeout(20); });
    }
    assert.fail("Chat request did not finish");
  }
  try {
    await act(async () => { view = create(<Chat />); });
    gateway.refuse(503);
    await send("First attempt");
    assert.deepEqual(statuses, [502]);
    assert.equal(view!.root.findAllByProps({ role: "alert" }).length, 1);

    gateway.refuse(200);
    await send("Try again");
    assert.deepEqual(statuses, [502, 200], "A failed placeholder must not poison the next request");
    assert.equal(view!.root.findAllByProps({ role: "alert" }).length, 0);
    assert.ok(JSON.stringify(view!.toJSON()).includes(answer));
    const history = [
      { role: "user", content: "First attempt" },
      { role: "user", content: "Try again" },
    ];
    assert.deepEqual((await browserRequests[1].json()).messages, history);
    assert.deepEqual(gateway.calls.at(-1)!.body.messages, history);

    gateway.refuse(503);
    await send("Another attempt");
    assert.deepEqual(statuses, [502, 200, 502]);
    assert.ok(JSON.stringify(view!.toJSON()).includes(answer), "Keep the earlier completed reply");
    gateway.refuse(200);
    await send("Recovered again");
    assert.deepEqual(statuses, [502, 200, 502, 200]);
    assert.deepEqual((await browserRequests[3].json()).messages, [
      ...history,
      { role: "assistant", content: answer },
      { role: "user", content: "Another attempt" },
      { role: "user", content: "Recovered again" },
    ]);
    assert.equal(view!.root.findAllByProps({ role: "alert" }).length, 0);
    assert.equal(gateway.mock.chat.completions.calls.length, 2);
    assert.equal(view!.root.findAllByType("li").length, 6, "Only users and completed replies remain");
    for (const request of browserRequests) assert.equal(request.headers.get("authorization"), null);
  } finally {
    await act(async () => view?.unmount());
    globalThis.fetch = originalFetch;
    resetAgentCCClient(); restore(); await gateway.close();
  }
});

test("React form uses the Next route, renders streamed text, and never sends the gateway key", async () => {
  const gateway = await mockGateway();
  const restore = configure(gateway.url);
  const originalFetch = globalThis.fetch;
  const browserRequests: Request[] = [];
  let view: ReactTestRenderer | undefined;
  resetAgentCCClient();
  globalThis.fetch = async (input, init) => {
    if (input !== "/api/chat") return originalFetch(input, init);
    const request = new Request("http://localhost:3000/api/chat", init);
    browserRequests.push(request.clone());
    return POST(request);
  };
  try {
    await act(async () => { view = create(<Chat />); });
    await act(async () => { view!.root.findByType("input").props.onChange({ target: { value: "Hello" } }); });
    await act(async () => { view!.root.findByType("form").props.onSubmit({ preventDefault() {} }); });
    for (let attempt = 0; attempt < 100 && !JSON.stringify(view!.toJSON()).includes(answer); attempt++) {
      await act(async () => { await setTimeout(20); });
    }
    assert.ok(JSON.stringify(view!.toJSON()).includes(answer));
    assert.equal(gateway.mock.chat.completions.calls.length, 1);
    assert.equal(gateway.calls[0].body.stream, true);
    assert.equal(browserRequests.length, 1);
    assert.equal(browserRequests[0].headers.get("authorization"), null);
    assert.ok(!(await browserRequests[0].text()).includes(key));
    assert.equal(view!.root.findAllByType("button")[0].props.disabled, true, "Input cleared after send");
  } finally {
    await act(async () => view?.unmount());
    globalThis.fetch = originalFetch;
    resetAgentCCClient(); restore(); await gateway.close();
  }
});
