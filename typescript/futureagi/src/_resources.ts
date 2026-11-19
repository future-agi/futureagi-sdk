/**
 * The adapter the core resource namespaces share (prompts, knowledge bases, scores): each calls a
 * generated core operation through the root client's generated client, so credentials, retries,
 * timeouts and error mapping are the root client's. It sits outside `_core`, which never imports
 * the generated core client.
 */
import type { Client } from "./generated/openapi/client";
import { apiError } from "./_core/error-map";

/** Use the root client's transport rather than resolving credentials again. */
export const coreOptions = <T extends object>(client: Client, options: T) => ({
  ...options,
  client,
  responseStyle: "fields" as const,
  throwOnError: true as const,
});

type Unwrapped<T> = T extends { status?: unknown; result: infer R } ? R : T;

/** Response metadata stays available until logical API errors have been mapped. */
export type CoreResponse<T> = { data: T; response: Response };

/** Keep bare resources and DRF pages; operations with sibling fields opt out of unwrapping. */
export function coreResult<T>(request: Promise<CoreResponse<T>>, unwrap?: true): Promise<Unwrapped<T>>;
export function coreResult<T>(request: Promise<CoreResponse<T>>, unwrap: false): Promise<T>;
export async function coreResult<T>(
  request: Promise<CoreResponse<T>>, unwrap = true,
): Promise<T | Unwrapped<T>> {
  const { data: payload, response } = await request;
  if (payload !== null && typeof payload === "object" && "status" in payload) {
    if (payload.status === false) throw apiError(400, payload, response.headers);
    if (unwrap && "result" in payload) return payload.result as Unwrapped<T>;
  }
  return payload;
}
