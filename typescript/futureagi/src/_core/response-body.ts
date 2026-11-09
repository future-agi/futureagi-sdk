/** Bound one read by the attempt's original deadline, including native abort errors. */
export async function withResponseDeadline<T>(
  consume: () => Promise<T>,
  controller: AbortController,
  deadline: number,
  timeoutMs: number,
): Promise<T> {
  const { signal } = controller;
  const abort = () => controller.abort(new Error(`request timed out after ${timeoutMs} ms`));
  if (Date.now() >= deadline && !signal.aborted) abort();
  if (signal.aborted) throw signal.reason;
  let onAbort!: () => void;
  const aborted = new Promise<never>((_, reject) => {
    onAbort = () => reject(signal.reason);
    signal.addEventListener("abort", onAbort, { once: true });
  });
  const timer = setTimeout(abort, Math.max(0, deadline - Date.now()));
  try {
    return await Promise.race([consume(), aborted]);
  } catch (error) {
    // Native fetch can reject the body with a generic AbortError, not the supplied reason.
    throw signal.aborted ? signal.reason : error;
  } finally {
    clearTimeout(timer);
    signal.removeEventListener("abort", onAbort);
  }
}

/** Wrap buffered body reads without replacing the Response or taking ownership of its stream. */
export function mapResponseBodyReads(
  response: Response,
  read: (consume: () => Promise<unknown>) => Promise<unknown>,
): Response {
  for (const method of ["text", "arrayBuffer", "blob", "formData"] as const) {
    const consume = response[method].bind(response);
    Object.defineProperty(response, method, {
      configurable: true,
      writable: true,
      value: () => read(consume),
    });
  }
  // Parsing is deliberately outside the body-read boundary: a fully received malformed
  // document is not a connection failure, even if a stream itself throws a SyntaxError.
  Object.defineProperty(response, "json", {
    configurable: true,
    writable: true,
    value: async () => JSON.parse(await response.text()),
  });
  return response;
}
