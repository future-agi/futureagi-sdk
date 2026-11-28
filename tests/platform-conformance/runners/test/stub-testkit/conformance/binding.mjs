// The test kit's stub binding answers from memory without network access. The fake runner
// blocks network requests, so an attempted request trips the egress guard and fails the shell test.
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
