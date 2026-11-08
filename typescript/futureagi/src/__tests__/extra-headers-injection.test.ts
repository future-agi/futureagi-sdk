/**
 * Header injection through FI_EXTRA_HEADERS and extraHeaders is refused (src/extra-headers.ts), with
 * the same vectors as python/tests/test_extra_headers_injection.py and _wire.py:
 * - a value with CR, LF, CRLF, NUL or any other control character, and a name with ':' or
 *   whitespace, is refused with EXTRA_HEADERS_INVALID, through the setting and the argument (record
 *   and text); in the text forms ';', CR and LF separate entries by design, each one checked;
 * - on the wire, against a raw 127.0.0.1 socket server that records the exact request bytes: for
 *   each attempt, through FutureAGIClient (fetch) and HttpClient / APIKeyAuth (axios), either nothing
 *   is sent (no connection) or exactly the intended header lines arrive, never an injected one;
 * - a malformed setting fails HttpClient.request at once (ExtraHeadersError is never retried);
 * - an HttpClient-based client built with extraHeaders never shows a value through util.inspect,
 *   console.log or JSON.stringify.
 */
import * as net from "node:net";
import { Writable } from "node:stream";
import * as util from "node:util";
import { Console } from "node:console";
import type { AddressInfo } from "node:net";

import { APIKeyAuth, HttpClient } from "../api/auth";
import { HttpMethod } from "../api/types";
import {
  EXTRA_HEADERS_ENV,
  ExtraHeaders,
  ExtraHeadersError,
  parseExtraHeaders,
  validateExtraHeaders,
} from "../extra-headers";
import { FutureAGIClient } from "../futureagi-client";

const BASE = "http://127.0.0.1:9";
const FORBIDDEN = ["x-evil", "other", "smuggled", "evil-token"];
const CONTROLS = [...Array.from({ length: 0x20 }, (_, c) => String.fromCharCode(c)), "\x7f"];
const TEXT_CONTROLS = CONTROLS.filter((c) => c !== "\r" && c !== "\n");
const POSITIONS: Record<string, (c: string) => string> = {
  inside: (c) => `a${c}b`,
  leading: (c) => `${c}ab`,
  trailing: (c) => `ab${c}`,
};
const hex = (c: string) => `0x${c.charCodeAt(0).toString(16).padStart(2, "0")}`;

const BAD_VALUES: Record<string, string> = {
  "cr-header": "1\rX-Evil: 1",
  "lf-header": "1\nX-Evil: 1",
  "crlf-api-key": "1\r\nX-Api-Key: other",
  "crlf-trailing": "1\r\n",
  "lf-leading": "\n1",
  "crlf-smuggle": "1\r\n\r\nGET /smuggled HTTP/1.1",
  "nul-header": "1\x00X-Evil: 1",
  "nul-trailing": "1\x00",
  "tab-header": "1\tX-Evil: 1",
  "vt-trailing": "1\x0b",
  "ff-leading": "\x0c1",
  esc: "1\x1b[2J",
  "us-0x1f-trailing": "1\x1f",
  "fs-0x1c-leading": "\x1c1",
  del: "1\x7f",
  "nel-0x85": "1\x85",
  "ls-u2028-header": "1 X-Evil: 1",
};

const BAD_NAMES: Record<string, string> = {
  colon: "X:A",
  "colon-trailing": "X-A:",
  "colon-leading": ":X-A",
  "header-line": "X-A: 1\r\nX-Evil",
  "space-inside": "X A",
  "tab-inside": "X\tA",
  "crlf-inside": "X-A\r\nX-Evil",
  "lf-trailing": "X-A\n",
  "cr-trailing": "X-A\r",
  "nul-trailing": "X-A\x00",
  "vt-trailing": "X-A\x0b",
  "space-leading": " X-A",
  "space-trailing": "X-A ",
  "nbsp-trailing": "X-A\xa0",
};
const TEXT_BAD_NAMES = Object.fromEntries(
  Object.entries(BAD_NAMES).filter(([, v]) => v.replace(/^ +| +$/g, "") !== "X-A" && !/[\r\n]/.test(v)),
);

const SETTING_INJECTIONS: Record<string, [string, string]> = {
  "crlf-colon-api-key": ["X-A=1\r\nX-Api-Key: other", "entry 2 has no '='"],
  "crlf-equals-api-key": ["X-A=1\r\nX-Api-Key=other", "entry 2: X-Api-Key cannot be set"],
  "lf-colon-authorization": ["X-A=1\nAuthorization: Bearer evil-token-1", "entry 2 has no '='"],
  "lf-equals-authorization": ["X-A=1\nAuthorization=Bearer evil-token-1", "entry 2: Authorization cannot be set"],
  "cr-colon-secret-key": ["X-A=1\rX-Secret-Key: other", "entry 2 has no '='"],
  "semicolon-api-key": ["X-A=1;x-api-key=other", "entry 2: x-api-key cannot be set"],
  "crlf-smuggled-request": ["X-A=1\r\n\r\nGET /smuggled HTTP/1.1", "entry 2 has no '='"],
  "nul-api-key": ["X-A=1\x00X-Api-Key: other", "(X-A): the value has a control character"],
  "tab-api-key": ["X-A=1\tX-Api-Key: other", "(X-A): the value has a control character"],
  "vt-entry": ["X-A=1\n\x0b\n", "entry 2 has no '='"],
  "colon-name": ["X-A: 1=2", "entry 1: the name is not a valid HTTP header name"],
};

function refused(call: () => unknown, source: string, ...fragments: string[]): ExtraHeadersError {
  let error: unknown;
  try {
    call();
  } catch (e) {
    error = e;
  }
  expect(error).toBeInstanceOf(ExtraHeadersError);
  const err = error as ExtraHeadersError;
  expect(err.code).toBe("EXTRA_HEADERS_INVALID");
  expect(err.message.startsWith(source)).toBe(true);
  for (const bad of ["=other", ": other", "X-Evil", "evil-token-1", "smuggled", "\r", "\n", "\x00"]) {
    expect(err.message).not.toContain(bad);
  }
  for (const fragment of fragments) expect(err.message).toContain(fragment);
  return err;
}

describe("header injection: refused by the rules", () => {
  const saved = process.env[EXTRA_HEADERS_ENV];
  beforeEach(() => {
    delete process.env[EXTRA_HEADERS_ENV];
  });
  afterAll(() => {
    if (saved === undefined) delete process.env[EXTRA_HEADERS_ENV];
    else process.env[EXTRA_HEADERS_ENV] = saved;
  });

  it.each(Object.entries(BAD_VALUES))("value %s is refused in the extraHeaders record", (_id, value) => {
    refused(() => validateExtraHeaders({ "X-A": value }), "extraHeaders entry 1 (X-A)");
    refused(() => new ExtraHeaders(BASE, { "X-A": value }), "extraHeaders entry 1 (X-A)");
  });

  const everyControl = CONTROLS.flatMap((c) => Object.keys(POSITIONS).map((where) => [hex(c), where, c] as const));
  it.each(everyControl)("control %s (%s) is refused in the extraHeaders record", (_id, where, c) => {
    refused(() => validateExtraHeaders({ "X-A": POSITIONS[where](c) }), "extraHeaders entry 1 (X-A)", "control character");
  });

  const everyTextControl = TEXT_CONTROLS.flatMap((c) =>
    Object.keys(POSITIONS).map((where) => [hex(c), where, c] as const),
  );
  it.each(everyTextControl)("control %s (%s) is refused in the setting and the extraHeaders text", (_id, where, c) => {
    const text = `X-A=${POSITIONS[where](c)}`;
    refused(() => parseExtraHeaders(text), `${EXTRA_HEADERS_ENV} entry 1 (X-A)`, "control character");
    process.env[EXTRA_HEADERS_ENV] = text;
    if (process.env[EXTRA_HEADERS_ENV] === text) {
      refused(() => new ExtraHeaders(BASE).forUrl(`${BASE}/x`), `${EXTRA_HEADERS_ENV} entry 1 (X-A)`, "control character");
    } else {
      // Node keeps an environment value only up to a NUL: the rest never reaches the SDK
      expect(c).toBe("\x00");
      expect(process.env[EXTRA_HEADERS_ENV]).toBe(text.slice(0, text.indexOf("\x00")));
    }
    delete process.env[EXTRA_HEADERS_ENV];
    refused(() => validateExtraHeaders(text), "extraHeaders entry 1 (X-A)", "control character");
  });

  it.each(Object.entries(BAD_NAMES))("name %s is refused in the extraHeaders record", (_id, name) => {
    refused(() => validateExtraHeaders({ [name]: "1" }), "extraHeaders entry 1: the name is not a valid HTTP header name");
    refused(() => new ExtraHeaders(BASE, { [name]: "1" }), "extraHeaders entry 1: the name is not a valid");
  });

  it.each(Object.entries(TEXT_BAD_NAMES))("name %s is refused in the setting and the extraHeaders text", (_id, name) => {
    refused(() => parseExtraHeaders(`${name}=1`), `${EXTRA_HEADERS_ENV} entry 1: the name is not a valid HTTP header name`);
    refused(() => validateExtraHeaders(`${name}=1`), "extraHeaders entry 1: the name is not a valid HTTP header name");
  });

  it.each(Object.entries(SETTING_INJECTIONS))("payload %s is refused in the setting and the extraHeaders text", (_id, [payload, words]) => {
    refused(() => parseExtraHeaders(payload), EXTRA_HEADERS_ENV, words);
    refused(() => validateExtraHeaders(payload), "extraHeaders", words);
    refused(() => new ExtraHeaders(BASE, payload), "extraHeaders", words);
  });

  it.each<[string, string, Record<string, string>]>([
    ["lf-two-headers", "X-A=1\nX-B=2", { "X-A": "1", "X-B": "2" }],
    ["crlf-two-headers", "X-A=1\r\nX-B=2", { "X-A": "1", "X-B": "2" }],
    ["cr-two-headers", "X-A=1\rX-B=2", { "X-A": "1", "X-B": "2" }],
    ["crlf-trailing-one-header", "X-A=1\r\n", { "X-A": "1" }],
    ["empty-entries", "\r\nX-A=1;;\n", { "X-A": "1" }],
    ["padding", " X-A = 1 ", { "X-A": "1" }],
  ])("separators by design (%s) give separate, checked headers", (_id, text, expected) => {
    expect(parseExtraHeaders(text)).toEqual(expected);
    expect(validateExtraHeaders(text)).toEqual(expected);
  });
});

// ---- the wire: a raw socket server, no HTTP library ----------------------------------------------

class RawServer {
  connections = 0;
  readonly heads: string[] = [];
  private server!: net.Server;
  private readonly sockets = new Set<net.Socket>();
  url = "";

  async start(): Promise<this> {
    this.server = net.createServer((socket) => {
      this.connections += 1;
      this.sockets.add(socket);
      let data = Buffer.alloc(0);
      let answered = false;
      socket.on("data", (chunk: Buffer) => {
        data = Buffer.concat([data, chunk]);
        const end = data.indexOf("\r\n\r\n");
        if (end < 0 || answered) return;
        const head = data.subarray(0, end).toString("latin1");
        const length = Number(/\r\ncontent-length:\s*(\d+)/i.exec(head)?.[1] ?? 0);
        if (data.length < end + 4 + length) return;
        answered = true;
        this.heads.push(head);
        socket.end("HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: 2\r\nConnection: close\r\n\r\n{}");
      });
      socket.on("error", () => undefined);
      socket.on("close", () => this.sockets.delete(socket));
    });
    await new Promise<void>((resolve) => this.server.listen(0, "127.0.0.1", resolve));
    this.url = `http://127.0.0.1:${(this.server.address() as AddressInfo).port}`;
    return this;
  }

  async stop(): Promise<void> {
    for (const s of this.sockets) s.destroy();
    await new Promise<void>((resolve) => this.server.close(() => resolve()));
  }
}

function assertExact(server: RawServer, expected: Record<string, string>): void {
  expect(server.connections).toBe(1);
  expect(server.heads).toHaveLength(1);
  const lines = server.heads[0].split("\r\n").slice(1);
  const names = lines.map((l) => l.slice(0, l.indexOf(":")).toLowerCase());
  for (const line of lines) {
    expect(line.indexOf(":")).toBeGreaterThan(0);
    expect(/^[\x20-\x7e\t]+$/.test(line) && !/^[ \t]/.test(line)).toBe(true);
    for (const word of FORBIDDEN) expect(line.toLowerCase()).not.toContain(word);
  }
  for (const [name, value] of Object.entries(expected)) {
    expect(names.filter((n) => n === name.toLowerCase())).toHaveLength(1);
    const line = lines[names.indexOf(name.toLowerCase())];
    expect(line.slice(line.indexOf(":") + 1).trim()).toBe(value);
  }
  expect(names.filter((n) => n === "x-api-key").length).toBeLessThanOrEqual(1);
  const key = lines.find((l) => l.toLowerCase().startsWith("x-api-key:"));
  if (key) expect(key.slice(key.indexOf(":") + 1).trim()).toBe("ak-test");
}

type Arg = Record<string, string> | string | undefined;
const CLIENTS: Record<string, (base: string, arg: Arg) => Promise<unknown>> = {
  fetch_client: async (base, arg) => new FutureAGIClient({ baseUrl: base, extraHeaders: arg }).users.current(),
  http_client: async (base, arg) => {
    const client = new HttpClient({ baseUrl: base, extraHeaders: arg });
    try {
      return await client.request({ method: HttpMethod.GET, url: "/model-hub/x" } as any);
    } finally {
      await client.close();
    }
  },
  api_key_auth: async (base, arg) => {
    const client = new APIKeyAuth({ fiApiKey: "ak-test", fiSecretKey: "sk-test", fiBaseUrl: base, extraHeaders: arg });
    try {
      return await client.request({ method: HttpMethod.GET, url: "/model-hub/x" } as any);
    } finally {
      await client.close();
    }
  },
};

const SETTING_ATTEMPTS: Record<string, string> = {
  "crlf-colon-api-key": "X-A=1\r\nX-Api-Key: other",
  "crlf-equals-api-key": "X-A=1\r\nX-Api-Key=other",
  "lf-colon-authorization": "X-A=1\nAuthorization: Bearer evil-token-1",
  "cr-colon-header": "X-A=1\rX-Evil: 1",
  "crlf-smuggled-request": "X-A=1\r\n\r\nGET /smuggled HTTP/1.1",
  "nul-header": "X-A=1\x00X-Evil: 1",
  "tab-header": "X-A=1\tX-Evil: 1",
  "vt-header": "X-A=1\x0bX-Evil: 1",
  "del-header": "X-A=1\x7fX-Evil: 1",
  "colon-name": "X-A: 1=2",
  "space-name": "X A=1",
  "tab-name": "X-A\t=1",
};
const RECORD_ATTEMPTS: Record<string, Record<string, string>> = {
  "value-crlf-api-key": { "X-A": "1\r\nX-Api-Key: other" },
  "value-lf-header": { "X-A": "1\nX-Evil: 1" },
  "value-cr-header": { "X-A": "1\rX-Evil: 1" },
  "value-crlf-trailing": { "X-A": "1\r\n" },
  "value-crlf-smuggle": { "X-A": "1\r\n\r\nGET /smuggled HTTP/1.1" },
  "value-nul-header": { "X-A": "1\x00X-Evil: 1" },
  "value-tab-header": { "X-A": "1\tX-Evil: 1" },
  "value-esc": { "X-A": "1\x1b[2J" },
  "value-del": { "X-A": "1\x7f" },
  "name-crlf-header": { "X-A\r\nX-Evil": "1" },
  "name-lf-trailing": { "X-A\n": "1" },
  "name-colon": { "X-A:": "1" },
  "name-header-line": { "X-A: 1\r\nX-Evil": "1" },
  "name-space-inside": { "X A": "1" },
  "name-space-trailing": { "X-A ": "1" },
  "name-tab": { "X\tA": "1" },
};
const TEXT_ATTEMPTS: Record<string, string> = {
  "text-crlf-colon-api-key": "X-A=1\r\nX-Api-Key: other",
  "text-crlf-equals-api-key": "X-A=1\r\nX-Api-Key=other",
  "text-nul-header": "X-A=1\x00X-Evil: 1",
  "text-colon-name": "X-A:=1",
};
const BY_DESIGN: Record<string, [string, Record<string, string>]> = {
  "crlf-two-headers": ["X-A=1\r\nX-B=2", { "X-A": "1", "X-B": "2" }],
  "lf-two-headers": ["X-A=1\nX-B=2", { "X-A": "1", "X-B": "2" }],
  "crlf-trailing-one-header": ["X-A=1\r\n", { "X-A": "1" }],
};

const cross = <T>(cases: Record<string, T>) =>
  Object.keys(CLIENTS).flatMap((client) => Object.entries(cases).map(([id, c]) => [client, id, c] as [string, string, T]));

describe("header injection on the wire (raw 127.0.0.1 socket server)", () => {
  const saved = { ...process.env };
  let server: RawServer;

  beforeEach(async () => {
    server = await new RawServer().start();
    delete process.env[EXTRA_HEADERS_ENV];
    process.env.FI_API_KEY = "ak-test";
    process.env.FI_SECRET_KEY = "sk-test";
  });

  afterEach(async () => {
    process.env = { ...saved };
    await server.stop();
  });

  async function refusedNothingSent(call: () => Promise<unknown>, source: string): Promise<void> {
    let error: unknown;
    try {
      await call();
    } catch (e) {
      error = e;
    }
    expect(error).toBeInstanceOf(ExtraHeadersError);
    expect((error as ExtraHeadersError).code).toBe("EXTRA_HEADERS_INVALID");
    expect((error as Error).message.startsWith(source)).toBe(true);
    for (const word of FORBIDDEN) expect((error as Error).message.toLowerCase()).not.toContain(word);
    expect(server.connections).toBe(0);
    expect(server.heads).toEqual([]);
  }

  it.each(cross(SETTING_ATTEMPTS))("%s: setting %s sends nothing", async (client, _id, payload) => {
    process.env[EXTRA_HEADERS_ENV] = payload;
    const stored = process.env[EXTRA_HEADERS_ENV];
    if (stored !== payload) {
      // Node keeps an environment value only up to a NUL ("X-A=1"): exactly that one line arrives
      expect(payload).toContain("\x00");
      expect(stored).toBe(payload.slice(0, payload.indexOf("\x00")));
      await CLIENTS[client](server.url, undefined);
      assertExact(server, { "X-A": "1" });
      return;
    }
    await refusedNothingSent(() => CLIENTS[client](server.url, undefined), EXTRA_HEADERS_ENV);
  });

  it.each(cross(RECORD_ATTEMPTS))("%s: extraHeaders record %s sends nothing", async (client, _id, arg) => {
    await refusedNothingSent(() => CLIENTS[client](server.url, arg), "extraHeaders");
  });

  it.each(cross(TEXT_ATTEMPTS))("%s: extraHeaders text %s sends nothing", async (client, _id, arg) => {
    await refusedNothingSent(() => CLIENTS[client](server.url, arg), "extraHeaders");
  });

  it.each(cross(BY_DESIGN))("%s: setting separators %s send exactly the checked lines", async (client, _id, [text, expected]) => {
    process.env[EXTRA_HEADERS_ENV] = text;
    await CLIENTS[client](server.url, undefined);
    assertExact(server, expected);
  });

  it.each(Object.keys(CLIENTS))("%s: a valid argument arrives as exactly one line per header", async (client) => {
    process.env[EXTRA_HEADERS_ENV] = "X-A=from-setting;X-B=2";
    await CLIENTS[client](server.url, { "X-A": "from-argument", "X-C": "Bearer abc.def-ghi" });
    assertExact(server, { "X-A": "from-argument", "X-B": "2", "X-C": "Bearer abc.def-ghi" });
  });

  it("HttpClient: a malformed setting fails at once with ExtraHeadersError (never retried) and sends nothing", async () => {
    process.env[EXTRA_HEADERS_ENV] = "Proxy-Authorization Bearer fake-identity-token-xxxxxxxxxxxx";
    for (const make of [
      () => new HttpClient({ baseUrl: server.url }),
      () => new APIKeyAuth({ fiApiKey: "ak-test", fiSecretKey: "sk-test", fiBaseUrl: server.url }),
    ]) {
      const client = make(); // the defaults: 3 attempts, 1 s then 2 s backoff (about 3 s if it were retried)
      const started = Date.now();
      let error: unknown;
      try {
        await client.request({ method: HttpMethod.GET, url: "/model-hub/x" } as any);
      } catch (e) {
        error = e;
      }
      const elapsed = Date.now() - started;
      await client.close();
      expect(error).toBeInstanceOf(ExtraHeadersError);
      expect((error as Error).message).toContain(`${EXTRA_HEADERS_ENV} entry 1 has no '='`);
      expect((error as Error).message).not.toContain("fake-identity-token");
      expect(elapsed).toBeLessThan(500);
    }
    expect(server.connections).toBe(0);
  });
});

// ---- privacy: argument values never shown --------------------------------------------------------

describe("extraHeaders values never shown by util.inspect, console.log or JSON.stringify", () => {
  const SECRET = "argument-secret-" + "y".repeat(12);
  const saved = { ...process.env };
  afterEach(() => {
    process.env = { ...saved };
  });

  function shown(obj: unknown): string[] {
    const out: string[] = [];
    out.push(util.inspect(obj));
    out.push(util.inspect(obj, { showHidden: true, depth: Infinity, getters: true }));
    out.push(util.inspect(obj, { customInspect: false, showHidden: true, depth: Infinity }));
    out.push(util.format("%o", obj), util.format("%O", obj), util.format("%j", obj));
    const chunks: string[] = [];
    const sink = new Writable({
      write(chunk, _enc, done) {
        chunks.push(String(chunk));
        done();
      },
    });
    new Console({ stdout: sink, stderr: sink }).log(obj); // a real Node console, not jest's
    new Console({ stdout: sink, stderr: sink }).dir(obj, { depth: Infinity, showHidden: true });
    out.push(chunks.join(""));
    const seen = new WeakSet<object>();
    out.push(
      JSON.stringify(obj, (_k, v) => {
        if (typeof v === "object" && v !== null) {
          if (seen.has(v)) return "[circular]";
          seen.add(v);
        }
        return v;
      }) ?? "",
    );
    return out;
  }

  it.each<[string, () => unknown]>([
    ["ExtraHeaders", () => new ExtraHeaders(BASE, { "X-Arg": SECRET })],
    ["HttpClient record", () => new HttpClient({ baseUrl: BASE, extraHeaders: { "X-Arg": SECRET } })],
    ["HttpClient text", () => new HttpClient({ baseUrl: BASE, extraHeaders: `X-Arg=${SECRET}` })],
    ["APIKeyAuth", () => new APIKeyAuth({ fiApiKey: "ak-test", fiSecretKey: "sk-test", fiBaseUrl: BASE, extraHeaders: { "X-Arg": SECRET } })],
    ["FutureAGIClient", () => new FutureAGIClient({ baseUrl: BASE, extraHeaders: { "X-Arg": SECRET } })],
  ])("%s", async (_id, make) => {
    const obj = make();
    for (const text of shown(obj)) {
      expect(text).not.toContain(SECRET);
    }
    if (obj instanceof ExtraHeaders) {
      expect(JSON.stringify(obj)).toBe(JSON.stringify({ baseUrl: BASE, argumentNames: ["X-Arg"] }));
      expect(util.inspect(obj)).toContain("X-Arg");
      // the value is still sent: kept off the instance, not lost
      expect(obj.forUrl(`${BASE}/x`)).toEqual({ "X-Arg": SECRET });
    }
    if (obj instanceof HttpClient) await obj.close();
  });
});
