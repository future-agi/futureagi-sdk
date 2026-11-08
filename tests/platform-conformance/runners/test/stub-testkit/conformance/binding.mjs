// A stub test kit's binding: answers from memory, never touches the network (the fake runner
// denies it outright, so a stray request would trip the egress guard and fail the shell test).
const STATE = { sandboxes: [] };

export function createClient() {
  return { state: STATE };
}

export async function call(client, { family, method }) {
  if (family === "platform" && method === "capabilities.get") return { schemaVersion: "stub", available: true, features: {}, generatedAt: new Date(0).toISOString() };
  if (family === "sandboxes" && method === "list") return { schemaVersion: "stub", sandboxes: client.state.sandboxes, caps: {}, provider: {} };
  throw Object.assign(new Error("not found"), { status: 404, code: "not_found" });
}

export function describeError(error) {
  return { errorClass: error.status === 404 ? "NotFoundError" : "SDKException", status: error.status ?? null, code: error.code ?? null };
}
