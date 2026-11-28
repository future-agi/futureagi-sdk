/**
 * One rule for the host of a request URL: the host as the URL text writes it (tests/fixtures/loopback/hosts.json,
 * "request_urls"). The forms the URL parser rewrites to a loopback address (127.0.0.1. and 127.1 and 0x7f.0.0.1 and
 * 2130706433) are not loopback for a Bearer token or for API keys, in the origin checks and in the platform transport.
 */
import { readFileSync } from "node:fs";
import { join } from "node:path";

import { checkHttpSecurity, isInsecureHttp, isLoopback, resetHttpWarnings } from "../http-security";

const ROWS = (JSON.parse(readFileSync(join(__dirname, "../../../../../tests/fixtures/loopback/hosts.json"), "utf8")) as {
  request_urls: { url: string; loopback: boolean }[];
}).request_urls;
const ROW_PAIRS = ROWS.map((row) => [row.url, row.loopback] as const);

const SAVED = process.env.FI_ALLOW_INSECURE_HTTP;
beforeEach(() => { delete process.env.FI_ALLOW_INSECURE_HTTP; resetHttpWarnings(); });
afterEach(() => { if (SAVED === undefined) delete process.env.FI_ALLOW_INSECURE_HTTP; else process.env.FI_ALLOW_INSECURE_HTTP = SAVED; });

describe("the written host of a request URL", () => {
  it("lists the four rewritten forms as not loopback", () => {
    const hosts = ROWS.filter((row) => !row.loopback).map((row) => row.url);
    for (const form of ["http://127.0.0.1.:9/", "http://127.1:9/", "http://0x7f.0.0.1:9/", "http://2130706433:9/"]) {
      expect(hosts).toContain(form);
    }
  });

  it.each(ROW_PAIRS)("isLoopback(%s) is %s", (url, loopback) => {
    expect(isLoopback(url)).toBe(loopback);
    expect(isInsecureHttp(url)).toBe(!loopback);
  });

  it.each(ROW_PAIRS)("a Bearer token over %s: loopback is %s", (url, loopback) => {
    if (loopback) expect(() => checkHttpSecurity(url, "bearer")).not.toThrow();
    else expect(() => checkHttpSecurity(url, "bearer")).toThrow(/Bearer token/u);
  });
});
