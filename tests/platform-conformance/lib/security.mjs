/** Mandatory security vehicles and their offered-route counterparts.
 * Absence proves only absence. A counterpart must validate the same mechanism on an offered
 * operation. Keep the original vehicle binding pinned even while it is outside the scope.
 */
import { isDeepStrictEqual } from "node:util";

export const SECURITY_PAIRS = Object.freeze([
  { original: "must-exist.host-guard.fi-keypair", method: "list", path: "/workspace/sandboxes", verb: "GET" },
  { original: "must-exist.host-guard.env-switches-ignored", method: "list", path: "/workspace/sandboxes", verb: "GET" },
  { original: "must-exist.planted-secret.scan", method: "commands.run", path: "/workspace/sandboxes/{sandbox}/exec", verb: "POST" },
  { original: "gateway.credential-in-query", method: "list", path: "/workspace/sandboxes", verb: "GET" },
  { original: "gateway.mixed-credentials", method: "list", path: "/workspace/sandboxes", verb: "GET" },
  { original: "gateway.anonymous.forged-tenant-headers", method: "list", path: "/workspace/sandboxes", verb: "GET" },
].map((row) => Object.freeze({ ...row, offered: `${row.original}.offered` })));

export const SECURITY_IDS = Object.freeze(SECURITY_PAIRS.flatMap((pair) => [pair.original, pair.offered]));

export function validateSecurity(cases, perCase) {
  const byId = new Map(cases.map((c) => [c.id, c]));
  const results = new Map(perCase.map((c) => [c.id, c]));
  const errors = [];
  const reject = (id, message) => {
    errors.push({ id, message });
    results.get(id)?.errors.push(message);
  };
  for (const pair of SECURITY_PAIRS) {
    const original = byId.get(pair.original);
    const twin = byId.get(pair.offered);
    if (!original || !twin) {
      reject(pair.original, `security MUST_EXIST requires both ${pair.original} and ${pair.offered}; NOT-OFFERED absence is not security validation`);
      continue;
    }
    if (!isDeepStrictEqual(original.sdk, { family: "sandboxes", method: pair.method }) ||
        !isDeepStrictEqual(original.op, { method: pair.verb, path: pair.path })) {
      reject(pair.original, "security MUST_EXIST original vehicle does not match its pinned binding");
    }
    for (const field of ["client", "call", "expect", "expectByMode", "tenant", "modes", "runners", "tags"]) {
      if (!isDeepStrictEqual(original[field], twin[field])) reject(pair.offered, `security counterpart changes ${field}`);
    }
    if (!isDeepStrictEqual(twin.sdk, { family: "platform", method: "capabilities.get" }) ||
        !isDeepStrictEqual(twin.op, { method: "GET", path: "/workspace/capabilities" })) {
      reject(pair.offered, "security MUST_EXIST offered vehicle does not match its pinned binding");
    }
    const verdict = results.get(pair.offered);
    if (!verdict?.documented || verdict.errors.length) {
      reject(pair.offered, "security MUST_EXIST counterpart must validate on an offered route; NOT-OFFERED absence cannot clear it");
    }
  }
  for (const item of cases.filter((c) => c.tags?.includes("must-exist"))) {
    if (!results.get(item.id)?.documented && !SECURITY_PAIRS.some((pair) => pair.original === item.id &&
        results.get(pair.offered)?.documented && results.get(pair.offered).errors.length === 0)) {
      reject(item.id, "security MUST_EXIST has no validated offered counterpart; absence is not validation");
    }
  }
  return {
    securityErrors: errors,
    securityMustExist: SECURITY_IDS.filter((id) => {
      const result = results.get(id);
      return result?.documented && result.errors.length === 0;
    }),
  };
}
