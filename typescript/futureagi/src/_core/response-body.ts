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
