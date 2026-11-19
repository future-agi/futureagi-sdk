/**
 * Verify Future AGI webhook requests (Standard Webhooks v1) in Node.
 *
 * Every request carries `webhook-id` (the event id), `webhook-timestamp` (Unix seconds of this attempt) and
 * `webhook-signature` (`v1,<base64>`, or two space-separated entries during a secret rotation). The signature is
 * `base64(HMAC-SHA256(key, "<webhook-id>.<webhook-timestamp>.<raw body>"))`, where `key` is the base64-decoded part
 * of the endpoint's `whsec_...` secret. A request is genuine when any `v1` entry matches and the timestamp is within
 * 300 s of now, in either direction.
 *
 * ```ts
 * import express from "express";
 * import { verifyWebhook, WebhookVerificationError } from "@future-agi/sdk";
 *
 * app.post("/hook", express.raw({ type: "application/json" }), (req, res) => {
 *   try {
 *     const event = verifyWebhook({ body: req.body, headers: req.headers, secret: process.env.FI_WEBHOOK_SECRET! });
 *     if (event.test) return res.sendStatus(200);
 *     // ... handle event.type; dedupe on event.id (delivery is at least once)
 *     res.sendStatus(200);
 *   } catch (err) {
 *     if (err instanceof WebhookVerificationError) return res.sendStatus(400);
 *     throw err;
 *   }
 * });
 * ```
 *
 * Verify the raw body bytes (`express.raw`, `await request.text()` in a fetch handler): a body that was parsed and
 * serialized again does not verify. Any Standard Webhooks library verifies the same requests.
 *
 * The results and reason ids are the language-neutral conformance vectors' (`signing.json`), which this module
 * passes byte for byte, as `fi.webhooks.verify` does in Python.
 */
import { createHmac, timingSafeEqual } from "crypto";
import { TextDecoder } from "util";

export const WEBHOOK_SECRET_PREFIX = "whsec_";
export const WEBHOOK_TOLERANCE_S = 300;
const KEY_BYTES_MIN = 24;
const KEY_BYTES_MAX = 64;
const TIMESTAMP = /^[0-9]{1,12}$/;
const ASCII = /^[\x00-\x7f]*$/;
const REQUIRED = ["webhook-id", "webhook-timestamp", "webhook-signature"] as const;

export type WebhookVerifyResult =
  | "ok"
  | "missing_headers"
  | "invalid_timestamp"
  | "timestamp_too_old"
  | "timestamp_too_new"
  | "no_matching_signature";

export type WebhookVerificationReason = Exclude<WebhookVerifyResult, "ok"> | "invalid_body";
export type WebhookSecretReason = "missing_prefix" | "not_base64" | "bad_length";

/** A raw request body: the exact bytes received (a string is taken as UTF-8). */
export type WebhookBody = string | Uint8Array | ArrayBuffer;

/** Node's `req.headers`, a fetch `Headers`, a plain object, or `[name, value]` pairs; names in any case. */
export type WebhookHeaders =
  | Record<string, string | string[] | undefined>
  | { forEach(callback: (value: string, name: string) => void): void }
  | Iterable<[string, string]>;

const MESSAGES: Record<WebhookVerificationReason, string> = {
  missing_headers: "the request lacks a webhook-id, webhook-timestamp or webhook-signature header",
  invalid_timestamp: "webhook-timestamp is not a Unix time in whole seconds",
  timestamp_too_old: "webhook-timestamp is too far in the past (a replayed request, or this server's clock is wrong)",
  timestamp_too_new: "webhook-timestamp is too far in the future (this server's clock is wrong)",
  no_matching_signature:
    "no v1 signature matches this secret and body. Verify the raw request body, not re-serialized JSON, with the " +
    "endpoint's current secret",
  invalid_body: "the signed body is not a JSON object",
};

/** The request is not a genuine, current Future AGI webhook request: answer it with a 4xx. */
export class WebhookVerificationError extends Error {
  readonly reason: WebhookVerificationReason;

  constructor(reason: WebhookVerificationReason, message?: string) {
    super(message ?? MESSAGES[reason]);
    this.name = "WebhookVerificationError";
    this.reason = reason;
    Object.setPrototypeOf(this, WebhookVerificationError.prototype);
  }
}

/**
 * The secret is not `whsec_` followed by padded standard base64 of 24 to 64 bytes. A configuration error on the
 * receiver, not a bad request: let it surface as a 5xx, so Future AGI keeps retrying until the secret is fixed.
 */
export class WebhookSecretError extends Error {
  readonly reason: WebhookSecretReason;

  constructor(reason: WebhookSecretReason) {
    super(
      {
        missing_prefix: "the webhook secret must start with 'whsec_' (copy it whole from Future AGI)",
        not_base64: "the webhook secret is not 'whsec_' followed by padded standard base64",
        bad_length: "the webhook secret must decode to 24-64 bytes",
      }[reason],
    );
    this.name = "WebhookSecretError";
    this.reason = reason;
    Object.setPrototypeOf(this, WebhookSecretError.prototype);
  }
}

/** The HMAC key of a `whsec_` secret: the decoded bytes after the prefix. */
export function webhookSecretKey(secret: string): Buffer {
  if (typeof secret !== "string" || !secret.startsWith(WEBHOOK_SECRET_PREFIX)) {
    throw new WebhookSecretError("missing_prefix");
  }
  const raw = secret.slice(WEBHOOK_SECRET_PREFIX.length);
  const key = Buffer.from(raw, "base64");
  if (key.toString("base64") !== raw) throw new WebhookSecretError("not_base64");
  if (key.length < KEY_BYTES_MIN || key.length > KEY_BYTES_MAX) throw new WebhookSecretError("bad_length");
  return key;
}

function toBytes(body: WebhookBody): Buffer {
  if (typeof body === "string") return Buffer.from(body, "utf8");
  if (body instanceof ArrayBuffer) return Buffer.from(new Uint8Array(body));
  if (body instanceof Uint8Array) return Buffer.from(body.buffer, body.byteOffset, body.byteLength);
  throw new TypeError("body must be the raw request body (a string, Buffer, Uint8Array or ArrayBuffer)");
}

function signedContent(msgId: string, timestamp: number, body: Buffer): Buffer {
  if (msgId.includes(".") || !ASCII.test(msgId)) throw new RangeError("webhook-id must be ASCII without '.'");
  return Buffer.concat([Buffer.from(`${msgId}.${Math.trunc(timestamp)}.`, "ascii"), body]);
}

/** `base64(HMAC-SHA256(key, "<msgId>.<timestamp>.<body>"))`: the value after `v1,`. For a receiver's own tests. */
export function signWebhook(secret: string, msgId: string, timestamp: number, body: WebhookBody): string {
  return createHmac("sha256", webhookSecretKey(secret))
    .update(signedContent(msgId, timestamp, toBytes(body)))
    .digest("base64");
}

/** The `webhook-signature` value: `v1,<sig>` per secret, newest first, space-separated. */
export function webhookSignatureHeader(
  secretsNewestFirst: string[],
  msgId: string,
  timestamp: number,
  body: WebhookBody,
): string {
  if (secretsNewestFirst.length === 0) throw new RangeError("no signing secret");
  return secretsNewestFirst.map((s) => `v1,${signWebhook(s, msgId, timestamp, body)}`).join(" ");
}

function lowerHeaders(headers: WebhookHeaders): Map<string, string> {
  const out = new Map<string, string>();
  const put = (name: string, value: unknown) => {
    const key = String(name).toLowerCase();
    if (out.has(key) || value === undefined || value === null) return;
    out.set(key, Array.isArray(value) ? String(value[0]) : String(value));
  };
  const h = headers as any;
  if (h && typeof h.forEach === "function" && typeof h.get === "function") {
    h.forEach((value: string, name: string) => put(name, value));
  } else if (h && typeof h[Symbol.iterator] === "function") {
    for (const [name, value] of h as Iterable<[string, string]>) put(name, value);
  } else if (h && typeof h === "object") {
    for (const name of Object.keys(h)) put(name, h[name]);
  }
  return out;
}

export interface VerifyWebhookOptions {
  /** The raw request body, byte for byte. */
  body: WebhookBody;
  headers: WebhookHeaders;
  /** The endpoint's `whsec_...` signing secret. */
  secret: string;
  /** Accepted clock difference in seconds, both directions (300). */
  toleranceS?: number;
  /** Unix seconds to judge the timestamp against (default: now). For recorded requests and tests. */
  now?: number;
}

/**
 * `"ok"` or the reason id, the shape of the conformance vectors. A secret that is not a valid `whsec_` secret matches
 * nothing. Every `v1` entry is compared in constant time; entries with another version are ignored.
 */
export function verifyWebhookResult(options: VerifyWebhookOptions): WebhookVerifyResult {
  const h = lowerHeaders(options.headers);
  if (!REQUIRED.every((name) => h.has(name))) return "missing_headers";
  const ts = h.get("webhook-timestamp") as string;
  if (!TIMESTAMP.test(ts)) return "invalid_timestamp";
  const t = Number(ts);
  const now = options.now === undefined ? Math.floor(Date.now() / 1000) : Math.trunc(options.now);
  const tolerance = options.toleranceS ?? WEBHOOK_TOLERANCE_S;
  if (now - t > tolerance) return "timestamp_too_old";
  if (t - now > tolerance) return "timestamp_too_new";
  let expected: Buffer;
  try {
    expected = Buffer.from(signWebhook(options.secret, h.get("webhook-id") as string, t, options.body), "ascii");
  } catch (err) {
    if (err instanceof WebhookSecretError || err instanceof RangeError) return "no_matching_signature";
    throw err;
  }
  let matched = false;
  for (const item of (h.get("webhook-signature") as string).split(" ")) {
    const comma = item.indexOf(",");
    if (comma < 0 || item.slice(0, comma) !== "v1") continue;
    const value = Buffer.from(item.slice(comma + 1), "utf8");
    if (value.length === expected.length && timingSafeEqual(value, expected)) matched = true;
  }
  return matched ? "ok" : "no_matching_signature";
}

/**
 * Check a request and return its event (the parsed JSON body, `test` included). Throws
 * {@link WebhookVerificationError} (answer 4xx) for a request that is not genuine or not current, and
 * {@link WebhookSecretError} (let it be a 5xx) when the secret itself is malformed. A signed body that is not a JSON
 * object (one that starts with a UTF-8 BOM included) is `invalid_body`, as in Python.
 */
export function verifyWebhook<T extends Record<string, unknown> = Record<string, any>>(
  options: VerifyWebhookOptions,
): T {
  webhookSecretKey(options.secret);
  const raw = toBytes(options.body);
  const result = verifyWebhookResult({ ...options, body: raw });
  if (result !== "ok") throw new WebhookVerificationError(result);
  let event: unknown;
  try {
    // ignoreBOM keeps a leading U+FEFF, which JSON.parse refuses: a BOM body is invalid_body, as in Python's json.loads
    // (Future AGI never sends one; signatures are over the raw bytes either way)
    event = JSON.parse(new TextDecoder("utf-8", { fatal: true, ignoreBOM: true }).decode(raw));
  } catch {
    throw new WebhookVerificationError("invalid_body");
  }
  if (event === null || typeof event !== "object" || Array.isArray(event)) {
    throw new WebhookVerificationError("invalid_body");
  }
  return event as T;
}
