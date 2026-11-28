/**
 * A host written with trailing dots (`..`, the ideographic full stop, `%2e%2e`) is the host without them: a Future AGI
 * host stays refused over http with the opt-in, and a host with an empty label is refused as ambiguous. Counted at a
 * loopback listener behind a name-resolution shim.
 */
import net from "node:net";

import { HttpClient } from "../../api/auth";
import { HttpMethod } from "../../api/types";
import { ConfigurationError } from "../errors";
import { plaintextDecision, resetHttpWarnings } from "../http-security";
import { MARKER_KEY, Sink, realConnect, shimConnect } from "../__fixtures__/plaintext-sinks";

const target = new Sink();
beforeAll(async () => { await target.listen(); net.Socket.prototype.connect = shimConnect as never; });
afterAll(() => { net.Socket.prototype.connect = realConnect; target.close(); });
beforeEach(() => { target.reset(); resetHttpWarnings(); jest.spyOn(console, "warn").mockImplementation(() => undefined); });
afterEach(() => { jest.restoreAllMocks(); });

const FUTURE_FORMS = ["api.futureagi.com..", "api.futureagi.com...", "api.futureagi.com。。", "api.futureagi.com%2e%2e", "api.futureagi.com.", "futureagi.com..", "API.FUTUREAGI.COM%2E"];
const EMPTY_LABELS = ["plain.example.test..", "a..example.test", "plain.example.test%2e%2e"];

describe("the plain-http decision", () => {
  it.each(FUTURE_FORMS)("refuses the Future AGI host written as %s even with the opt-in", (host) => {
    const decision = plaintextDecision(`http://${host}:8080/x`, { allowInsecureHttp: true, proxiesDisabled: true });
    expect(decision.allowed).toBe(false);
  });
  it.each(EMPTY_LABELS)("refuses the host %s, which has an empty label, with the opt-in", (host) => {
    const decision = plaintextDecision(`http://${host}:8080/x`, { allowInsecureHttp: true, proxiesDisabled: true });
    expect(decision).toEqual({ allowed: false, reason: "ambiguous_host" });
  });
  it("still allows a name with one trailing dot that is not a Future AGI host, with the opt-in", () => {
    expect(plaintextDecision("http://plain.example.test.:8080/x", { allowInsecureHttp: true, proxiesDisabled: true }).allowed).toBe(true);
  });
});

describe("a keyed HttpClient send with the opt-in", () => {
  const send = (host: string) => new HttpClient({ baseUrl: `http://${host}:${target.port}`, defaultHeaders: { "X-Api-Key": MARKER_KEY }, allowInsecureHttp: true, retryAttempts: 1, timeout: 3000 })
    .request({ method: HttpMethod.GET, url: "/probe" }).then(() => undefined, (error: unknown) => error);
  it.each([...FUTURE_FORMS, ...EMPTY_LABELS])("sends nothing to %s: no connection, no key byte", async (host) => {
    expect(await send(host)).toBeInstanceOf(ConfigurationError);
    expect(target.connections).toBe(0);
    expect(target.markerBytes).toBe(0);
  });
});
