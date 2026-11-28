/**
 * Run as a child process with `NODE_USE_ENV_PROXY=1`, `HTTP_PROXY`/`HTTPS_PROXY` naming the parent's proxy sink and
 * `NO_PROXY` as the parent sets it, so the runtime's own `EnvHttpProxyAgent` is the global dispatcher from start-up.
 * The SDK is loaded through its root entry. PROBE_SENDER picks one request to PROBE_URL:
 * - `runtimeFetch`: the runtime's fetch called bare, with no SDK in the path (the comparison row);
 * - `platformClient`: a keyed send carrying PROBE_KEY.
 * Prints the outcome as one JSON line: "sent" when an answer came back, otherwise the error's name, code and message.
 */
async function main(): Promise<void> {
  const url = process.env.PROBE_URL ?? "http://127.0.0.1:1/";
  const key = process.env.PROBE_KEY ?? "";
  const sender = process.env.PROBE_SENDER ?? "";
  let outcome = "sent";
  let code = "";
  let message = "";
  try {
    const root = await import("../../index");
    const origin = new URL(url).origin;
    const path = new URL(url).pathname;
    if (sender === "runtimeFetch") {
      const response = await fetch(url, { signal: AbortSignal.timeout(3000) });
      await response.text();
    } else if (sender === "platformClient") {
      await new root.Client({ apiKey: key, secretKey: key, baseUrl: origin, maxRetries: 0, timeout: 3000 }).request("GET", path);
    } else {
      throw new Error(`unknown sender ${sender}`);
    }
  } catch (error) {
    outcome = (error as Error).name;
    code = String((error as { code?: unknown }).code ?? "");
    message = String((error as Error).message);
  }
  process.stdout.write(`${JSON.stringify({ outcome, code, message })}\n`);
  process.exit(0);
}
void main();

export {};
