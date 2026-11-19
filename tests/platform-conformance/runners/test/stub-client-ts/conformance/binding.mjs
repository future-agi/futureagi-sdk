// The binding contract (tests/platform-conformance/README.md "Bindings"), implemented for the stub SDK.
import { StubConfigError, StubError, StubClient } from "../index.mjs";

const CLASSES = { 401: "AuthenticationError", 403: "PermissionDeniedError", 404: "NotFoundError", 400: "BadRequestError" };

export function createClient({ baseUrl, credential, fetch }) {
  return new StubClient({ baseUrl, apiKey: credential.apiKey ?? credential.token, fetch });
}

export function call(client, { family, method }, args) {
  return client.call(`${family}.${method}`, args);
}

export function describeError(error) {
  if (error instanceof StubConfigError) return { errorClass: "HostNotAllowedError" };
  if (error instanceof StubError) return { errorClass: CLASSES[error.status] ?? "APIStatusError", status: error.status, code: error.code };
  return { errorClass: "SDKException" };
}

export function clientCase(spec, { fetch }) {
  let requests = 0;
  const counting = (...args) => ((requests += 1), fetch(...args));
  try {
    new StubClient({ baseUrl: spec.platformBaseUrl ?? spec.baseUrl, apiKey: "stub-key", fetch: counting });
    return { errorClass: null, networkRequests: requests };
  } catch (error) {
    return { ...describeError(error), networkRequests: requests };
  }
}
