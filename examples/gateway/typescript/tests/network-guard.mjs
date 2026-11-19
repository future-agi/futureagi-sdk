import net from "node:net";
import { syncBuiltinESMExports } from "node:module";

// Loaded before any framework: an unexpected provider call fails before DNS/connect.
const connect = net.Socket.prototype.connect;
net.Socket.prototype.connect = function (...args) {
  const first = args[0];
  const options = Array.isArray(first) ? first[0] : first;
  const host = typeof options === "object" ? options.host : (typeof args[1] === "string" ? args[1] : "localhost");
  const unix = typeof options === "object" && options.path;
  if (!unix && ![undefined, "localhost", "127.0.0.1", "::1"].includes(host)) {
    throw new Error("Test network guard: non-loopback connection refused");
  }
  return connect.apply(this, args);
};
syncBuiltinESMExports();
process.env.LANGCHAIN_TRACING_V2 = "false";
process.env.LANGSMITH_TRACING = "false";
process.env.NEXT_TELEMETRY_DISABLED = "1";
