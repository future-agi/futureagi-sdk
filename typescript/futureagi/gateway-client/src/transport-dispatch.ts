// A fetch rejection alone cannot establish whether request bytes were sent.
// Only explicit connection-establishment / acquisition failures permit replay.
const PRE_SEND_CODES = new Set([
  "ENOTFOUND", "EAI_AGAIN", "ECONNREFUSED", "UND_ERR_CONNECT_TIMEOUT",
  "UND_ERR_POOL_TIMEOUT", "UND_ERR_QUEUE_TIMEOUT",
]);

/** Inspect bounded cause chains, including Node's multi-address connect failures.
 * Mixed or empty aggregates and cycles are unknown, not proof of a safe retry.
 * Neither error prose nor arbitrary timeout/abort names establish a pre-send phase.
 */
export function failedBeforeSend(error: unknown): boolean {
  function visit(value: unknown, seen: Set<object>, depth: number): boolean {
    if (!value || typeof value !== "object" || seen.has(value) || depth > 16) return false;
    const next = new Set(seen).add(value);
    const item = value as { code?: unknown; syscall?: unknown; cause?: unknown; errors?: unknown };
    const coded = typeof item.code === "string";
    const safeCode = coded && (PRE_SEND_CODES.has(item.code as string)
      || (item.code === "ETIMEDOUT" && item.syscall === "connect"));
    if (coded && !safeCode) return false;
    if ("errors" in item) {
      return Array.isArray(item.errors) && item.errors.length > 0 && item.errors.length <= 32
        && item.errors.every((nested) => visit(nested, next, depth + 1));
    }
    return safeCode || visit(item.cause, next, depth + 1);
  }
  // Custom fetch implementations may throw arbitrary objects, including getters.
  try { return visit(error, new Set(), 0); } catch { return false; }
}
