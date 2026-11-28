import { writeSync } from "node:fs";
import { pathToFileURL } from "node:url";

const [probe, controlPort, controlKey] = process.argv.slice(2);
const slot = Symbol.for("undici.globalDispatcher.1");
const record = Symbol.for("@future-agi/sdk.runtime-undici");

new Request("http://127.0.0.1/");
const saved = Object.getOwnPropertyDescriptor(globalThis, slot);
if (saved.configurable) delete globalThis[slot];
else globalThis[slot] = undefined;
new Request("http://127.0.0.1/");
const captureEmpty = globalThis[slot] === undefined;
Object.defineProperty(globalThis, slot, saved);

const runtime = saved.value;
const RuntimeAgent = runtime.constructor;
const factory = Object.getOwnPropertySymbols(runtime).find((key) => key.description === "factory");
const pool = runtime[factory]("http://127.0.0.1", {});
const client = runtime[factory]("http://127.0.0.1", { connections: 1 });
const counts = { captureEmpty, constructed: 0, dispatched: 0 };

// The application records calls while keeping the runtime Agent's prototype levels and direct routing.
function Agent(...args) {
  counts.constructed += 1;
  return Reflect.construct(RuntimeAgent, args, new.target);
}
const methods = Object.getOwnPropertyDescriptors(RuntimeAgent.prototype);
const dispatch = Object.getOwnPropertySymbols(methods).find((key) => key.description === "dispatch");
const runtimeDispatch = methods[dispatch].value;
methods.constructor.value = Agent;
methods[dispatch].value = function (...args) {
  counts.dispatched += 1;
  return Reflect.apply(runtimeDispatch, this, args);
};
Agent.prototype = Object.create(Object.getPrototypeOf(RuntimeAgent.prototype), methods);
const agent = new Agent();
Object.defineProperty(globalThis, record, {
  value: Object.freeze({ Agent, Pool: pool.constructor, Client: client.constructor, EnvHttpProxyAgent: undefined }),
  writable: false,
  enumerable: false,
  configurable: false,
});
await Promise.all([pool.close(), client.close()]);
for (const key of [slot, Symbol.for("undici.globalDispatcher.2")]) {
  const held = Object.getOwnPropertyDescriptor(globalThis, key);
  if (held !== undefined) Object.defineProperty(globalThis, key, { ...held, value: agent });
}

if (probe === "control") {
  const response = await fetch(`http://127.0.0.1:${controlPort}/probe`, {
    headers: { "X-Api-Key": controlKey }, signal: AbortSignal.timeout(3000),
  });
  await response.text();
  await agent.close();
  writeSync(1, `${JSON.stringify({ outcome: `http:${response.status}` })}\n`);
  writeSync(1, `${JSON.stringify(counts)}\n`);
} else {
  counts.constructed = 0;
  process.once("exit", () => { writeSync(1, `${JSON.stringify(counts)}\n`); });
  await import(pathToFileURL(probe).href);
}
