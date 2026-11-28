import { EnvHttpProxyAgent, ProxyAgent, setGlobalDispatcher } from "undici";
import { ConfigurationError } from "../errors";
import { callerProxyDispatcher, checkHttpSecurity } from "../http-security";
import { proxyEnvironment } from "./proxy-sink";

export type ProxyKind = "ProxyAgent" | "EnvHttpProxyAgent";
export interface RefusalResult {
  callerProxied: boolean;
  code: string | undefined;
  message: string;
}

async function main(): Promise<void> {
  const [kind, targetUrl, proxyUrl] = process.argv.slice(2);
  const restoreProxy = proxyEnvironment();
  const agent = kind === "EnvHttpProxyAgent"
    ? new EnvHttpProxyAgent({ httpProxy: proxyUrl, noProxy: "" })
    : new ProxyAgent(proxyUrl);
  try {
    setGlobalDispatcher(agent);
    // This policy check judges the route that retains the global dispatcher.
    const callerProxied = callerProxyDispatcher(targetUrl);
    try {
      checkHttpSecurity(targetUrl, "keys", true, callerProxied);
      process.stdout.write(`${JSON.stringify({ callerProxied, message: "allowed" })}\n`);
    } catch (error) {
      if (!(error instanceof ConfigurationError)) throw error;
      const result: RefusalResult = { callerProxied, code: error.code, message: error.message };
      process.stdout.write(`${JSON.stringify(result)}\n`);
    }
  } finally {
    await agent.close();
    restoreProxy();
  }
}

void main();
