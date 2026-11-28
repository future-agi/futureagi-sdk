/** The decision from the final request headers: which headers make a request a keyed one. */
import { headerRecord, headersCarryKey, normalizeHeaders, queryCarriesKey } from "../key-headers";

const KEY = "sk-KEYHDRUNIT-12345";
const ENV = { FI_API_KEY: ["envkey", "-01234", "56789"].join(""), FI_SECRET_KEY: ["envsec", "ret-98", "765432", "10"].join("") };

describe("headersCarryKey", () => {
  it.each([
    ["a record, any letter case", [{ "x-API-key": "v" }]],
    ["a Headers", [new Headers({ "X-Secret-Key": "v" })]],
    ["pairs", [[["authorization", "Bearer v"]]]],
    ["a later layer", [{}, undefined, { Authorization: "v" }]],
    ["a value that is not a string", [{ "X-Api-Key": ["v"] }]],
  ] as const)("finds a credential header in %s", (_name, sources) => {
    expect(headersCarryKey(sources as never, { env: {} })).toBe(true);
  });

  it.each([
    [{}], [undefined], [null], [{ "X-Team": "blue" }], [{ "X-Api-Key": "" }], [{ Authorization: "  " }], [{ "X-Api-Key": undefined }],
  ])("does not find a key in %j", (source) => {
    expect(headersCarryKey([source as never], { env: {} })).toBe(false);
  });

  it("counts an empty credential header when asked to", () => {
    expect(headersCarryKey([{ Authorization: "" }], { emptyCounts: true, env: {} })).toBe(true);
    expect(headersCarryKey([{ "X-Api-Key": undefined }], { emptyCounts: true, env: {} })).toBe(true);
  });

  it("leaves the Authorization header of a Bearer origin alone", () => {
    expect(headersCarryKey([{ Authorization: "Bearer token" }], { skipAuthorization: true, env: {} })).toBe(false);
    expect(headersCarryKey([{ "X-Api-Key": "v" }], { skipAuthorization: true, env: {} })).toBe(true);
  });

  it("finds a configured key and the environment keys inside any header value", () => {
    expect(headersCarryKey([{ "X-Trace": `a-${KEY}-b` }], { configured: [KEY], env: {} })).toBe(true);
    expect(headersCarryKey([{ "X-Trace": `a-${ENV.FI_API_KEY}` }], { env: ENV })).toBe(true);
    expect(headersCarryKey([{ "X-Trace": ENV.FI_SECRET_KEY }], { env: ENV })).toBe(true);
    expect(headersCarryKey([{ "X-Trace": "unrelated" }], { configured: [KEY], env: ENV })).toBe(false);
  });

  it("looks for a key of eight characters or more, not a shorter one", () => {
    expect(headersCarryKey([{ "X-Team": "abcdefgh-team" }], { env: { FI_API_KEY: "abcdefgh" } })).toBe(true);
    expect(headersCarryKey([{ "X-Team": "abcdefg-team" }], { env: { FI_API_KEY: "abcdefg" } })).toBe(false);
    expect(headersCarryKey([{ "X-Team": "abcdefg-team" }], { configured: ["abcdefg"], env: {} })).toBe(false);
  });
});

describe("header records", () => {
  it("uses the last pair across letter cases", () => {
    expect(headerRecord([["X-Trace", "first"], ["x-trace", "second"], ["X-Trace", "third"]])).toEqual({ "X-Trace": "third" });
  });

  it("reads the entries reported by forEach without emitting methods", () => {
    const source = {
      forEach(visit: (value: string, name: string) => void) { visit("marker", "X-Api-Key"); },
      get() { return "marker"; },
    };
    expect(normalizeHeaders(source)).toEqual({ "X-Api-Key": "marker" });
    expect(headerRecord(source)).toEqual({ "X-Api-Key": "marker" });
    expect(headersCarryKey([source], { env: {} })).toBe(true);
  });

  it("accepts a numeric header name outside an indexed record", () => {
    expect(normalizeHeaders({ 123: "field" })).toEqual({ 123: "field" });
    expect(headerRecord({ 123: "field" })).toEqual({ 123: "field" });
    expect(headersCarryKey([{ 123: "field" }], { env: {} })).toBe(false);
    expect(headersCarryKey([{ 123: KEY }], { configured: [KEY], env: {} })).toBe(true);
    expect(headersCarryKey([{ 123: [KEY, "field"] }], { configured: [KEY], env: {} })).toBe(true);
  });

  it("keeps and checks each Set-Cookie value from native Headers", () => {
    const source = new Headers([["Set-Cookie", `first=${KEY}`], ["Set-Cookie", "second=2"]]);
    const record = normalizeHeaders(source);
    expect(record).toEqual({ "set-cookie": [`first=${KEY}`, "second=2"] });
    expect(headersCarryKey([record], { configured: [KEY], env: {} })).toBe(true);
  });

  it("reads params as fields, not as a header container", () => {
    const forEach = jest.fn();
    expect(queryCarriesKey("/", { api_key: "marker", forEach, get() { return "marker"; } }, { env: {} })).toBe(true);
    expect(forEach).not.toHaveBeenCalled();
  });
});
