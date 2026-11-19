import type { RequestOptions } from "./client-options.js";
import { scrubCredentialHeaders } from "./redact.js";

/** Construct the attempt before entering the transport-error boundary. */
export function requestInit(options: RequestOptions, headers: Record<string, string>, timeout: number): RequestInit {
  const isFormData = options.body instanceof FormData;
  const init: RequestInit = {
    method: options.method,
    headers,
    signal: AbortSignal.timeout(options.timeout ?? timeout),
  };

  if (options.body && options.method !== "GET") {
    if (isFormData) {
      init.body = options.body as FormData;
    } else {
      init.body = JSON.stringify(options.body);
    }
  }
  return init;
}

/** Scrub before parsing bodies, delivering callbacks or exposing errors.
 * The headers belong to this attempt, never to the caller's options.
 * A thunk preserves the custom transport's receiver and synchronous throws.
 */
export async function fetchWithScrub(send: () => Promise<Response>, headers: Record<string, string>): Promise<Response> {
  try {
    return await send();
  } finally {
    scrubCredentialHeaders(headers);
  }
}
