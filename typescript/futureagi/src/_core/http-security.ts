/** Plain-HTTP policy, independent of credential provenance and retry routing. */
import { ConfigurationError } from "./errors";

const LOOPBACK = new Set(["127.0.0.1", "[::1]", "::1", "localhost"]);
const warned = new Set<string>();

/** Match the origin guard's loopback spellings, including a trailing DNS dot. */
export function isLoopback(url: URL): boolean {
  return LOOPBACK.has(url.hostname.toLowerCase().replace(/\.$/u, ""));
}

/** HTTP-policy loopback: localhost, any 127.0.0.0/8 address or ::1 (URL canonicalizes the spellings).
 * The origin guard keeps its narrower isLoopback list. */
function isLoopbackHost(url: URL): boolean {
  const host = url.hostname.toLowerCase().replace(/\.$/u, "");
  return host === "localhost" || host === "[::1]" || host === "::1" || /^127\.\d{1,3}\.\d{1,3}\.\d{1,3}$/u.test(host);
}

/** Plain HTTP to anything other than loopback. */
export function isInsecureHttp(url: URL): boolean {
  return url.protocol === "http:" && !isLoopbackHost(url);
}

/** Run only after credentials and their provenance have been checked, before any transport call. */
export function checkHttpSecurity(url: URL, mode: "keys" | "bearer", allowInsecureHttp = false): void {
  if (!isInsecureHttp(url)) return;
  if (mode === "bearer" && !allowInsecureHttp) {
    throw new ConfigurationError(
      "Refusing to send a Bearer token over non-loopback HTTP. Use HTTPS or explicitly set " +
        "allowInsecureHttp: true or FI_ALLOW_INSECURE_HTTP=1; allowCustomPlatformUrl is not this opt-out.",
      "insecure_http_origin",
    );
  }
  // URL.origin removes paths and default ports and normalizes host casing. Share the warning budget
  // across core/platform calls, client copies and credential modes, never across different ports.
  // Same identity as Python: host without a trailing DNS dot, default port dropped by URL.
  const key = `${url.protocol}//${url.hostname.toLowerCase().replace(/\.$/u, "")}${url.port ? `:${url.port}` : ""}`;
  if (warned.has(key)) return;
  warned.add(key);
  console.warn(
    `futureagi: sending credentials (API keys or a Bearer token) in cleartext over HTTP to ${url.origin}. ` +
      "Plain-HTTP keys origins are deprecated and will be refused in a future minor; use HTTPS. " +
      "Bearer HTTP requires allowInsecureHttp or FI_ALLOW_INSECURE_HTTP=1.",
  );
}

/** Test seam shared with the origin guard. */
export function resetHttpWarnings(): void {
  warned.clear();
}
