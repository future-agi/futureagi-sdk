/**
 * Which hosts a conformance run may reach. Pure and decided on the host NAME,
 * before any DNS lookup, so a lookup of a production name is never made either.
 *
 *  - Any host in the Future AGI production zone (`futureagi.com` or `*.futureagi.com`, after
 *    lower-casing and dropping a trailing dot) is ALWAYS refused, even when listed. That covers
 *    api.futureagi.com, app.futureagi.com, gateway.futureagi.com and every other one.
 *  - Loopback (127.0.0.0/8, ::1, localhost) is allowed.
 *  - Anything else is allowed only when it is on the run's explicit allowlist.
 */

export const PRODUCTION_ZONE = "futureagi.com";
export const NAMED_PRODUCTION_HOSTS = Object.freeze(["api.futureagi.com", "app.futureagi.com", "gateway.futureagi.com"]);

/** Lower-case, strip IPv6 brackets and one trailing dot. */
export function normalizeHost(host) {
  let value = String(host ?? "").trim().toLowerCase();
  if (value.startsWith("[") && value.endsWith("]")) value = value.slice(1, -1);
  if (value.endsWith(".")) value = value.slice(0, -1);
  return value;
}

export function isProductionHost(host) {
  const value = normalizeHost(host);
  return value === PRODUCTION_ZONE || value.endsWith(`.${PRODUCTION_ZONE}`);
}

export function isLoopbackHost(host) {
  const value = normalizeHost(host);
  if (value === "localhost" || value.endsWith(".localhost") || value === "::1" || value === "0:0:0:0:0:0:0:1") return true;
  return /^127(\.\d{1,3}){3}$/.test(value) || /^::ffff:127(\.\d{1,3}){3}$/.test(value);
}

/** The host of a URL string or URL object, or null if it cannot be parsed. */
export function hostOf(url) {
  try {
    return normalizeHost(new URL(String(url)).hostname);
  } catch {
    return null;
  }
}

/** { allowed, reason } for one host name against an allowlist of host names. */
export function classifyHost(host, allowlist = []) {
  const value = normalizeHost(host);
  if (!value) return { allowed: false, reason: "no host" };
  if (isProductionHost(value)) return { allowed: false, reason: "production Future AGI host" };
  if (isLoopbackHost(value)) return { allowed: true, reason: "loopback" };
  if (allowlist.map(normalizeHost).includes(value)) return { allowed: true, reason: "allowlisted" };
  return { allowed: false, reason: "not on the run's allowlist" };
}
