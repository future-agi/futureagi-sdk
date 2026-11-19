/**
 * verifyWebhook passes the language-neutral signing vectors byte for byte.
 * The vectors are vendored unchanged from the platform webhooks core (future-agi the recorded revision, conformance 1.4.0); a drift test pins
 * each file to the vendored manifest.json, and the manifest to its sha256 at that commit.
 */
import { createHash } from "crypto";
import { readFileSync } from "fs";
import { join } from "path";

import {
  WebhookSecretError,
  WebhookVerificationError,
  signWebhook,
  verifyWebhook,
  verifyWebhookResult,
  webhookSecretKey,
  webhookSignatureHeader,
} from "../index";
import * as root from "../../index";

const DIR = join(__dirname, "conformance");
const MANIFEST_SHA256 = "3e01168cb0dbf6b91af26d9e2f915f56f93731d045061c5efeb962e42cd5c875";
const raw = (name: string) => readFileSync(join(DIR, name));
const SIGNING = JSON.parse(raw("signing.json").toString("utf8"));
const V1 = JSON.parse(raw("signing-v1.json").toString("utf8"));
const b64 = (s: string) => Buffer.from(s, "base64");
const sha = (b: Buffer) => createHash("sha256").update(b).digest("hex");

describe("conformance files", () => {
  it("match the manifest byte for byte", () => {
    const manifestBytes = raw("manifest.json");
    expect(sha(manifestBytes)).toBe(MANIFEST_SHA256);
    const manifest = JSON.parse(manifestBytes.toString("utf8"));
    expect(manifest.conformance_version).toBe("1.4.0");
    for (const name of ["signing.json", "signing-v1.json"]) {
      const bytes = raw(name);
      expect(bytes.length).toBe(manifest.files[name].bytes);
      expect(sha(bytes)).toBe(manifest.files[name].sha256);
    }
  });

  it("are byte-identical to the Python SDK's copies", () => {
    const py = join(__dirname, "..", "..", "..", "..", "..", "python", "tests", "webhooks", "conformance");
    for (const name of ["signing.json", "signing-v1.json", "manifest.json"]) {
      expect(sha(readFileSync(join(py, name)))).toBe(sha(raw(name)));
    }
  });
});

describe("signing.json", () => {
  for (const c of SIGNING.secret_format as any[]) it(`secret format ${c.id}`, () => {
    if (c.valid) {
      const key = webhookSecretKey(c.secret);
      expect(key.length).toBe(c.key_bytes);
      expect(key.toString("hex")).toBe(c.key_hex);
    } else {
      expect(() => webhookSecretKey(c.secret)).toThrow(WebhookSecretError);
      try {
        webhookSecretKey(c.secret);
      } catch (err) {
        expect((err as WebhookSecretError).reason).toBe(c.reason);
      }
    }
  });

  for (const c of SIGNING.sign as any[]) it(`sign ${c.id}`, () => {
    const body = b64(c.body_bytes_b64);
    const sigs = c.secrets.map((s: string) => signWebhook(s, c.msg_id, c.timestamp, body));
    expect(sigs).toEqual(c.expected.signatures);
    expect(webhookSignatureHeader(c.secrets, c.msg_id, c.timestamp, body)).toBe(c.expected.webhook_signature);
    for (const s of c.secrets) {
      expect(verifyWebhookResult({ secret: s, headers: c.expected.headers, body, now: c.timestamp })).toBe("ok");
    }
  });

  for (const c of SIGNING.verify as any[]) it(`verify ${c.id}`, () => {
    const body = b64(c.body_bytes_b64);
    expect(verifyWebhookResult({ secret: c.secret, headers: c.headers, body, now: c.now })).toBe(c.expected);
    if (c.expected === "ok") {
      expect(verifyWebhook({ secret: c.secret, headers: c.headers, body, now: c.now })).toEqual(
        JSON.parse(body.toString("utf8")),
      );
    } else {
      let reason: string | undefined;
      try {
        verifyWebhook({ secret: c.secret, headers: c.headers, body, now: c.now });
      } catch (err) {
        expect(err).toBeInstanceOf(WebhookVerificationError);
        reason = (err as WebhookVerificationError).reason;
      }
      expect(reason).toBe(c.expected);
    }
  });
});

describe("signing-v1.json (the published reference vectors)", () => {
  const body = b64(V1.body_bytes_b64);
  const secret = (letter: string) => V1[`secret_${letter.toLowerCase()}`];
  const headers = (sig: string) => ({
    "webhook-id": V1.msg_id,
    "webhook-timestamp": String(V1.timestamp),
    "webhook-signature": sig,
  });

  it("reproduces the body, both signatures and the overlap header", () => {
    expect(body.toString("utf8")).toBe(V1.body_text);
    expect(body.length).toBe(354);
    expect(sha(body)).toBe(V1.sha256);
    expect(signWebhook(V1.secret_a, V1.msg_id, V1.timestamp, body)).toBe(V1.signature_a);
    expect(signWebhook(V1.secret_b, V1.msg_id, V1.timestamp, body)).toBe(V1.signature_b);
    expect(webhookSignatureHeader([V1.secret_a, V1.secret_b], V1.msg_id, V1.timestamp, body)).toBe(V1.overlap_header);
  });

  for (const [i, c] of (V1.must_pass as any[]).entries()) it(`must pass ${i}`, () => {
    const sig = c.header === "overlap" ? V1.overlap_header : `v1,${V1["signature_" + c.secret.toLowerCase()]}`;
    expect(verifyWebhookResult({ secret: secret(c.secret), headers: headers(sig), body, now: c.now })).toBe("ok");
  });

  for (const [i, c] of (V1.must_fail as any[]).entries()) it(`must fail ${i}`, () => {
    const b = c.body_bytes_b64 ? b64(c.body_bytes_b64) : body;
    const result = verifyWebhookResult({
      secret: secret(c.secret),
      headers: headers(`v1,${V1.signature_a}`),
      body: b,
      now: c.now ?? V1.timestamp,
    });
    expect(result).not.toBe("ok");
  });

  it("signs the B8 delivered event like the verify vector", () => {
    const c = SIGNING.verify.find((x: any) => x.id === "b8-delivered-ok");
    const b = b64(c.body_bytes_b64);
    expect(sha(b)).toBe(V1.b8_delivered.sha256);
    expect(signWebhook(V1.secret_a, V1.b8_delivered.msg_id, V1.b8_delivered.timestamp, b)).toBe(
      V1.b8_delivered.signature_a,
    );
  });
});

describe("verifyWebhook for receivers", () => {
  const SECRET = V1.secret_a;
  const body = JSON.stringify({ id: "evt_x", type: "prompt.label.changed", test: true });
  const signed = (t = Math.floor(Date.now() / 1000), b: string = body) => ({
    "webhook-id": "evt_x",
    "webhook-timestamp": String(t),
    "webhook-signature": webhookSignatureHeader([SECRET], "evt_x", t, b),
  });

  it("verifies now, from a string, a Buffer, an ArrayBuffer and fetch Headers", () => {
    const h = signed();
    const buf = Buffer.from(body);
    const ab = buf.buffer.slice(buf.byteOffset, buf.byteOffset + buf.byteLength);
    expect(verifyWebhook({ body, headers: h, secret: SECRET }).test).toBe(true);
    expect(verifyWebhook({ body: buf, headers: h, secret: SECRET }).type).toBe("prompt.label.changed");
    expect(verifyWebhook({ body: ab, headers: h, secret: SECRET }).id).toBe("evt_x");
    expect(verifyWebhook({ body, headers: new Headers(h), secret: SECRET }).id).toBe("evt_x");
    expect(verifyWebhook({ body, headers: Object.entries(h) as [string, string][], secret: SECRET }).id).toBe("evt_x");
    expect(verifyWebhook({ body, headers: { ...h, "webhook-id": ["evt_x"] }, secret: SECRET }).id).toBe("evt_x");
  });

  it("refuses stale and tampered requests with the reason", () => {
    const old = Math.floor(Date.now() / 1000) - 301;
    expect(() => verifyWebhook({ body, headers: signed(old), secret: SECRET })).toThrow(/too far in the past/);
    expect(() => verifyWebhook({ body: body + " ", headers: signed(), secret: SECRET })).toThrow(
      WebhookVerificationError,
    );
  });

  it("treats a malformed secret as configuration, and a non-object body as invalid", () => {
    expect(() => verifyWebhook({ body, headers: signed(), secret: "AAEC" })).toThrow(WebhookSecretError);
    const arr = "[1,2]";
    try {
      verifyWebhook({ body: arr, headers: signed(undefined, arr), secret: SECRET });
      throw new Error("expected a throw");
    } catch (err) {
      expect((err as WebhookVerificationError).reason).toBe("invalid_body");
    }
  });

  it("treats a body that starts with a UTF-8 BOM as invalid_body, as Python does", () => {
    const bom = Buffer.concat([Buffer.from([0xef, 0xbb, 0xbf]), Buffer.from(body)]);
    const t = Math.floor(Date.now() / 1000);
    const h = { ...signed(t), "webhook-signature": webhookSignatureHeader([SECRET], "evt_x", t, bom) };
    expect(verifyWebhookResult({ body: bom, headers: h, secret: SECRET })).toBe("ok"); // the signature matches
    for (const b of [bom, "\uFEFF" + body, bom.buffer.slice(bom.byteOffset, bom.byteOffset + bom.byteLength)]) {
      try {
        verifyWebhook({ body: b as any, headers: h, secret: SECRET });
        throw new Error("expected a throw");
      } catch (err) {
        expect(err).toBeInstanceOf(WebhookVerificationError);
        expect((err as WebhookVerificationError).reason).toBe("invalid_body");
      }
    }
  });

  it("is exported from the package root", () => {
    expect(root.verifyWebhook).toBe(verifyWebhook);
    expect(root.WebhookVerificationError).toBe(WebhookVerificationError);
  });
});
