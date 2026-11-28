const PROXY_AUTHORIZATION = "proxy-authorization";

export function isProxyAuthorization(name: string): boolean {
  return name.toLowerCase() === PROXY_AUTHORIZATION;
}

export function configuredProxyAuthorization(headers: Readonly<Record<string, string>>): string | undefined {
  return Object.entries(headers).find(([name]) => isProxyAuthorization(name))?.[1];
}

/** Fetch dispatchers authenticate to the proxy separately. Only the configured reverse-proxy value belongs on the request. */
export function applyProxyAuthorization(headers: Headers, configured: string | undefined): void {
  if (configured === undefined) headers.delete(PROXY_AUTHORIZATION);
  else headers.set(PROXY_AUTHORIZATION, configured);
}
