import { pathToFileURL } from "node:url";

/** Server-only options. Never put a gateway key in a NEXT_PUBLIC_ variable. */
export function settings() {
  const apiKey = process.env.FI_GATEWAY_API_KEY;
  const baseUrl = process.env.FI_GATEWAY_BASE_URL;
  const model = process.env.FI_GATEWAY_MODEL;
  if (!apiKey || !baseUrl || !model) {
    throw new Error("Set FI_GATEWAY_API_KEY, FI_GATEWAY_BASE_URL and FI_GATEWAY_MODEL on the server.");
  }
  return { apiKey, baseUrl, model };
}

/** Keep importing an example free of network calls and listening sockets. */
export function isMain(url: string): boolean {
  return !!process.argv[1] && url === pathToFileURL(process.argv[1]).href;
}
