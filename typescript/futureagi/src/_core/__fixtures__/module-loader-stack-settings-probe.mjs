/**
 * Run as a child process (tsx) with the path of a module-loader source file. PROBE_STACK names how the application
 * sets the stack settings before the loader is imported: "default", "locked-formatter" (a non-writable
 * Error.prepareStackTrace that formats call sites as text) or "zero-limit" (a non-writable Error.stackTraceLimit of 0).
 * Prints whether the loader found the undici package and the settings afterwards, as one JSON line.
 */
const mode = process.env.PROBE_STACK ?? "default";
const format = (error, sites) => `${String(error)}\n${sites.map((site) => `    at ${String(site)}`).join("\n")}`;
if (mode === "locked-formatter") Object.defineProperty(Error, "prepareStackTrace", { value: format, writable: false, configurable: false });
if (mode === "zero-limit") Object.defineProperty(Error, "stackTraceLimit", { value: 0, writable: false, configurable: false });
const before = { prepare: Error.prepareStackTrace, limit: Error.stackTraceLimit };
const { loadModule } = await import(process.argv[2]);
const undici = loadModule("undici");
process.stdout.write(`${JSON.stringify({
  mode, undiciAgent: typeof undici?.Agent, prepareKept: Error.prepareStackTrace === before.prepare, limitKept: Error.stackTraceLimit === before.limit,
})}\n`);
