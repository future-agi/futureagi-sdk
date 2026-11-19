// Render the React subpath's hooks on the server with the consumer's own
// React (17, 18 or 19): one component under AgentCCProvider (direct mode,
// dangerouslyAllowBrowser is not needed outside a browser) and one using
// the default server route. Proves the hooks run on that React version.
"use strict";

function renderReact(reactGw, gw, React, server) {
  const h = React.createElement;
  const client = new gw.AgentCC({ apiKey: "k", baseUrl: "http://127.0.0.1:9" });
  function Direct() {
    const c = reactGw.useAgentCCClient();
    const chat = reactGw.useAgentCCChat({ model: "m", initialMessages: [{ id: "1", role: "user", content: "hi" }] });
    return h("p", null, `${c === client}:${chat.messages.length}:${chat.isLoading}`);
  }
  function Route() {
    const chat = reactGw.useAgentCCChat({ model: "m" });
    const done = reactGw.useAgentCCCompletion({ model: "m" });
    const obj = reactGw.useAgentCCObject({ model: "m", schema: { type: "object" } });
    return h("p", null, `${chat.messages.length}:${done.completion === ""}:${obj.object === null}`);
  }
  const direct = server.renderToString(h(reactGw.AgentCCProvider, { client }, h(Direct)));
  const route = server.renderToString(h(Route));
  return { version: React.version, direct, route };
}

module.exports = { renderReact };
