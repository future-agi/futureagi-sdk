import * as http from "node:http";
import type { AddressInfo } from "node:net";

import { HttpClient } from "../api/auth";
import { HttpMethod } from "../api/types";
import {
  EXTRA_HEADERS_ENV,
  ExtraHeaders,
  ExtraHeadersError,
  isPlatformUrl,
  mergeExtraHeaders,
  parseExtraHeaders,
  validateExtraHeaders,
} from "../extra-headers";
import { FutureAGIClient } from "../futureagi-client";

// a made-up value, low entropy on purpose (never a real token)
const TOKEN = "fake-identity-token-" + "x".repeat(12);
const VALUE = `Bearer ${TOKEN}`;
const SETTING = `Proxy-Authorization=${VALUE};X-Team=team-env-value`;

type Seen = { method: string; path: string; headers: http.IncomingHttpHeaders };

class Server {
  readonly seen: Seen[] = [];
  readonly routes = new Map<string, { status: number; headers: Record<string, string> }>();
  private server!: http.Server;
  url = "";

  async start(): Promise<this> {
    this.server = http.createServer((req, res) => {
      this.seen.push({ method: req.method ?? "", path: req.url ?? "", headers: req.headers });
      req.resume();
      const route = this.routes.get((req.url ?? "").split("?")[0]) ?? { status: 200, headers: {} };
      res.writeHead(route.status, { "Content-Type": "application/json", ...route.headers });
      res.end("{}");
    });
    await new Promise<void>((resolve) => this.server.listen(0, "127.0.0.1", resolve));
    this.url = `http://127.0.0.1:${(this.server.address() as AddressInfo).port}`;
    return this;
  }

  at(path: string): Seen[] {
    return this.seen.filter((s) => s.path.split("?")[0] === path);
  }

  async stop(): Promise<void> {
    this.server.closeAllConnections?.();
    await new Promise<void>((resolve) => this.server.close(() => resolve()));
  }
}

const carries = (s: Seen) => s.headers["proxy-authorization"] === VALUE && s.headers["x-team"] === "team-env-value";
const carriesNone = (s: Seen) => !("proxy-authorization" in s.headers) && !("x-team" in s.headers);

describe("FI_EXTRA_HEADERS parsing and rules", () => {
  it("parses ';' and newlines, trims, keeps '=' in a value", () => {
    expect(parseExtraHeaders(` Proxy-Authorization = ${VALUE} ;\n\nX-Team=india\r\nX-Sig=a=b== ;`)).toEqual({
      "Proxy-Authorization": VALUE,
      "X-Team": "india",
      "X-Sig": "a=b==",
    });
    expect(parseExtraHeaders(" ;\n ")).toEqual({});
  });

  it.each<[string, string]>([
    [`Proxy-Authorization ${VALUE}`, "no '='"],
    [`Proxy-Authorization: ${VALUE}=x`, "not a valid HTTP header name"],
    ["X-Empty=", "empty"],
    ["Proxy-Authorization=Bearer", "only an auth scheme"],
    ["X-Uni=café", "not visible ASCII"],
    [`X-Dup=1;x-dup=${TOKEN}`, "given twice"],
    [`X-Api-Key=${TOKEN}`, "X-Api-Key cannot be set"],
    [`x-secret-key=${TOKEN}`, "x-secret-key cannot be set"],
    [`Authorization=${VALUE}`, "Authorization cannot be set"],
  ])("refuses %j, naming the setting and never the value", (text, words) => {
    let error: unknown;
    try {
      parseExtraHeaders(text);
    } catch (e) {
      error = e;
    }
    expect(error).toBeInstanceOf(ExtraHeadersError);
    const message = String((error as Error).message);
    expect(message.startsWith(EXTRA_HEADERS_ENV)).toBe(true);
    expect(message).toContain(words);
    expect(message).not.toContain(TOKEN);
    expect((error as ExtraHeadersError).code).toBe("EXTRA_HEADERS_INVALID");
  });

  it("the argument wins over the setting per name, without case", () => {
    const env = parseExtraHeaders(SETTING);
    expect(mergeExtraHeaders(env, validateExtraHeaders({ "x-team": "arg" }))).toEqual({
      "Proxy-Authorization": VALUE,
      "x-team": "arg",
    });
    expect(() => validateExtraHeaders({ Authorization: "x" })).toThrow(/extraHeaders entry 1: Authorization/);
  });

  it.each<[string, string, boolean]>([
    ["https://team.example/x", "https://team.example", true],
    ["https://team.example/api/v1", "https://team.example/api", true],
    ["https://team.example/apix", "https://team.example/api", false],
    ["http://team.example/x", "https://team.example", false],
    ["https://team.example:8443/x", "https://team.example", false],
    ["https://team.example.evil.example/x", "https://team.example", false],
    ["/relative", "https://team.example", false],
  ])("isPlatformUrl(%s, %s) is %s", (url, base, ok) => {
    expect(isPlatformUrl(url, base)).toBe(ok);
  });

  it("reads the setting per request and never shows values", () => {
    const saved = process.env[EXTRA_HEADERS_ENV];
    try {
      const extra = new ExtraHeaders("http://127.0.0.1:1", { "X-Arg": "argument-value-1" });
      process.env[EXTRA_HEADERS_ENV] = SETTING;
      expect(extra.forUrl("http://127.0.0.1:1/x")).toEqual({
        "Proxy-Authorization": VALUE,
        "X-Team": "team-env-value",
        "X-Arg": "argument-value-1",
      });
      expect(extra.forUrl("http://127.0.0.2:1/x")).toEqual({});
      expect(JSON.stringify(extra)).not.toContain("argument-value-1");
      expect(JSON.stringify(extra)).toContain("X-Arg");
      process.env[EXTRA_HEADERS_ENV] = "broken";
      expect(() => extra.forUrl("http://127.0.0.1:1/x")).toThrow(ExtraHeadersError);
    } finally {
      if (saved === undefined) delete process.env[EXTRA_HEADERS_ENV];
      else process.env[EXTRA_HEADERS_ENV] = saved;
    }
  });
});

describe("FI_EXTRA_HEADERS on the wire (127.0.0.1 servers only)", () => {
  const saved = { ...process.env };
  let platform: Server;
  let other: Server;

  beforeEach(async () => {
    platform = await new Server().start();
    other = await new Server().start();
    process.env[EXTRA_HEADERS_ENV] = SETTING;
    process.env.FI_API_KEY = "ak-test";
    process.env.FI_SECRET_KEY = "sk-test";
  });

  afterEach(async () => {
    process.env = { ...saved };
    await platform.stop();
    await other.stop();
  });

  it("HttpClient (axios): platform requests carry them; other hosts and redirects off the base URL do not", async () => {
    platform.routes.set("/redir-same", { status: 302, headers: { Location: `${platform.url}/landed` } });
    platform.routes.set("/redir-off", { status: 302, headers: { Location: `${other.url}/landing` } });
    const client = new HttpClient({ baseUrl: platform.url });
    for (const url of ["/model-hub/x", `${other.url}/elsewhere`, "/redir-same", "/redir-off"]) {
      await client.request({ method: HttpMethod.GET, url, retry_attempts: 1 } as any);
    }
    await client.close();
    expect(carries(platform.at("/model-hub/x")[0])).toBe(true);
    expect(carriesNone(other.at("/elsewhere")[0])).toBe(true);
    expect(carries(platform.at("/landed")[0])).toBe(true);
    expect(carries(platform.at("/redir-off")[0])).toBe(true);
    expect(carriesNone(other.at("/landing")[0])).toBe(true);
  });

  it("FutureAGIClient (fetch): platform requests carry them, extraHeaders wins, a redirect is not followed", async () => {
    const client = new FutureAGIClient({ baseUrl: platform.url, extraHeaders: { "X-Team": "argument-wins" } });
    await client.users.current();
    const got = platform.seen[0].headers;
    expect(got["proxy-authorization"]).toBe(VALUE);
    expect(got["x-team"]).toBe("argument-wins");
    expect(got["x-api-key"]).toBe("ak-test");

    platform.routes.set("/accounts/user-info/", { status: 302, headers: { Location: `${other.url}/landing` } });
    await expect(client.users.current()).rejects.toBeDefined();
    expect(other.seen).toEqual([]);
  });

  it("a malformed setting sends nothing and its error names no value", async () => {
    process.env[EXTRA_HEADERS_ENV] = `Proxy-Authorization ${VALUE}`;
    const client = new FutureAGIClient({ baseUrl: platform.url, retries: 0 });
    let error: unknown;
    try {
      await client.users.current();
    } catch (e) {
      error = e;
    }
    expect(error).toBeInstanceOf(ExtraHeadersError);
    expect(String((error as Error).message)).not.toContain(TOKEN);
    expect(platform.seen).toEqual([]);
    expect(() => new FutureAGIClient({ baseUrl: platform.url, extraHeaders: { "X-Api-Key": "k" } })).toThrow(
      /X-Api-Key cannot be set/,
    );
  });

  it("without the setting, requests are unchanged", async () => {
    delete process.env[EXTRA_HEADERS_ENV];
    const client = new FutureAGIClient({ baseUrl: platform.url });
    await client.users.current();
    expect(carriesNone(platform.seen[0])).toBe(true);
  });
});
