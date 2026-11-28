/**
 * A name-resolution shim for the loopback dial tests: `dns.lookup` answers the names it is given from a table and
 * everything else from the real resolver, and every connection the process makes is recorded as the address and port
 * it reached. Two loopback listeners stand for "the address the SDK was told" and "the address the shim answers".
 */
import dns from "node:dns";
import net from "node:net";

export interface NameShim {
  /** Names the process asked the resolver about. */
  readonly asked: string[];
  /** `address:port` of every connection that was made. */
  readonly connected: string[];
  restore(): void;
}

export function installNameShim(answers: Readonly<Record<string, string>>): NameShim {
  const asked: string[] = [];
  const connected: string[] = [];
  const realLookup = dns.lookup;
  const realConnect = net.Socket.prototype.connect;
  (dns as { lookup: unknown }).lookup = ((hostname: string, ...rest: unknown[]) => {
    const options = (typeof rest[0] === "object" && rest[0] !== null ? rest[0] : {}) as dns.LookupOptions;
    const done = rest[rest.length - 1] as (...a: unknown[]) => void;
    const address = answers[hostname.toLowerCase()];
    if (address === undefined) return (realLookup as (...a: unknown[]) => unknown)(hostname, ...rest);
    asked.push(hostname);
    const entry = { address, family: net.isIPv6(address) ? 6 : 4 };
    process.nextTick(() => { if (options.all === true) done(null, [entry]); else done(null, address, entry.family); });
    return {};
  }) as never;
  net.Socket.prototype.connect = function connect(this: net.Socket, ...args: unknown[]): net.Socket {
    this.once("connect", () => { connected.push(`${this.remoteAddress ?? "?"}:${this.remotePort ?? 0}`); });
    return (realConnect as (...a: unknown[]) => net.Socket).apply(this, args);
  } as never;
  return {
    asked, connected,
    restore: () => { (dns as { lookup: unknown }).lookup = realLookup; net.Socket.prototype.connect = realConnect; },
  };
}
