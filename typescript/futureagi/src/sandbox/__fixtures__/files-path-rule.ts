/**
 * Test fixture (not shipped API): the sandbox service's rule for file paths, which the mock files routes in
 * `openapi-mock.ts` keep before any answer, scripted or default. A file path is relative to `/workspace`, so an
 * absolute one, a `.` or `..` segment, a backslash, a NUL or one over 4096 characters is answered with a 400.
 */

/** What the rule reads of a mock call (a `MockCall` of `openapi-mock.ts`). */
interface FilesCall {
  readonly operation: { readonly operationId: string; readonly pathParams: readonly string[] };
  readonly params: Readonly<Record<string, string>>;
  readonly query: URLSearchParams;
  readonly json?: unknown;
}

/** The longest file path the service takes, in characters. */
const MAX_PATH_CHARS = 4096;

/** The service's refusal of a file path it does not take: `<field> must be ...`, in its 400 envelope. */
function pathRefusal(field: string, value: string): Response | undefined {
  let message: string | undefined;
  if (value.length > MAX_PATH_CHARS || value.includes("\u0000") || value.includes("\\") || value.startsWith("/")) {
    message = `${field} must be a workspace-relative path.`;
  } else if (value.split("/").some((part) => part === "." || part === "..")) {
    message = `${field} must not contain "." or ".." path segments.`;
  }
  if (message === undefined) return undefined;
  const body = { schemaVersion: "omega-workspace-sandboxes/v1", error: { code: "validation", message } };
  return new Response(JSON.stringify(body), { status: 400, headers: { "content-type": "application/json" } });
}

/**
 * The 400 the service answers for a files call whose path it would refuse: the list route's `path` query, the move
 * body's `from` and `to`, and every `{path}` route parameter, each relative to `/workspace`. Undefined when the call
 * is not a files call or its paths are workspace-relative. (A `{path}` parameter reaches the mock already
 * normalised: the SDK drops leading slashes and refuses `.` and `..` segments before sending, and the URL folds dot
 * segments, so a misplaced absolute path shows here as `workspace/...`, which is a valid relative path.)
 */
export function refusedFilePath(call: FilesCall): Response | undefined {
  const id = call.operation.operationId;
  const fields: [string, unknown][] = [];
  if (id === "listWorkspaceSandboxFiles") fields.push(["path", call.query.get("path") ?? undefined]);
  if (id === "moveWorkspaceSandboxPath") {
    const record = call.json !== null && typeof call.json === "object" && !Array.isArray(call.json);
    const body: Record<string, unknown> = record ? (call.json as Record<string, unknown>) : {};
    fields.push(['"from"', body.from], ['"to"', body.to]);
  }
  if (call.operation.pathParams.includes("path")) fields.push(["path", call.params.path]);
  for (const [field, value] of fields) {
    const refusal = typeof value === "string" ? pathRefusal(field, value) : undefined;
    if (refusal !== undefined) return refusal;
  }
  return undefined;
}
