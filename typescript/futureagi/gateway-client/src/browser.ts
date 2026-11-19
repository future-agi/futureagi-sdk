// ---------------------------------------------------------------------------
// Browsers: a gateway key in a page is a key everyone who loads the
// page can read, so the client refuses to run there unless the caller opts
// in with dangerouslyAllowBrowser. Nothing here touches the DOM types: the
// build has no "dom" lib, so the checks go through globalThis.
// ---------------------------------------------------------------------------

/**
 * True in a browser page: `window`, `window.document` and `navigator` all
 * exist (the check openai-node makes). Node, Deno, Bun, edge runtimes and
 * web workers are not browser pages.
 */
export function isBrowser(): boolean {
  const g = globalThis as { window?: { document?: unknown } | null; navigator?: unknown };
  return (
    typeof g.window === "object" &&
    g.window !== null &&
    typeof g.window.document !== "undefined" &&
    typeof g.navigator !== "undefined"
  );
}

/**
 * The error a browser construction raises without dangerouslyAllowBrowser.
 * With it, the client still leaves out x-agentcc-sdk-version and User-Agent
 * in a browser: the gateway's CORS allowlist (middleware/cors.go at
 * the recorded revision) names neither, so a preflight asking for them fails, and the
 * gateway reads neither.
 */
export const BROWSER_REFUSED =
  "The AgentCC client is running in a browser, where every visitor can read its gateway key. " +
  "Call the gateway from your server instead: @future-agi/sdk/gateway/nextjs streamResponse or " +
  "@future-agi/sdk/gateway/express behind your own route, which @future-agi/sdk/gateway/react's hooks " +
  "use by default (api: \"/api/chat\"). If the key is meant to be public (for example a short-lived, " +
  "budget-capped virtual key), pass dangerouslyAllowBrowser: true.";
