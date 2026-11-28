/**
 * Run as a child process with `NODE_USE_ENV_PROXY=1` and `HTTP_PROXY` set. The runtime's own fetch installs its
 * environment-proxy agent first, so the agent is the runtime's copy of undici's `EnvHttpProxyAgent`. Prints what the
 * runtime installed and how the SDK judges it.
 */
async function main(): Promise<void> {
  await fetch("http://127.0.0.1:1/").catch(() => undefined);
  const { isUndiciEnvProxyAgent } = await import("../dispatcher-provenance");
  const { plainHttpRouting } = await import("../http-security");
  const { directDispatcher } = await import("../loopback");
  const own = (globalThis as Record<symbol, unknown>)[Symbol.for("undici.globalDispatcher.1")] as object | undefined;
  const kind = own === undefined ? "none" : (Object.getPrototypeOf(own) as { constructor?: { name?: string } }).constructor?.name ?? "unknown";
  const routing = plainHttpRouting("http://plain.example.test:8080/x", { fetchSupplied: false });
  const direct = directDispatcher(false, false) as object | undefined;
  process.stdout.write(`${JSON.stringify({ kind, recognised: isUndiciEnvProxyAgent(own), routing, direct: direct === undefined ? "none" : (Object.getPrototypeOf(direct) as { constructor?: { name?: string } }).constructor?.name })}\n`);
}
void main();

export {};
