/**
 * Test helpers (not shipped API) for keyed https:// requests to a loopback host: a scratch certificate authority built
 * in the test with node:crypto alone (an ECDSA P-256 CA and a server certificate for 127.0.0.1 and localhost signed by
 * it), an https target, and a proxy sink that answers `CONNECT`, terminates the TLS inside the tunnel with a certificate
 * from the same CA and counts the planted markers in the bytes it decrypts. A client process that trusts the CA
 * (`NODE_EXTRA_CA_CERTS`) hands such a proxy everything it sends through the tunnel.
 */
import { createHash, generateKeyPairSync, randomBytes, sign, type KeyObject } from "node:crypto";
import net from "node:net";
import tls from "node:tls";

function length(size: number): Buffer {
  if (size < 0x80) return Buffer.from([size]);
  const bytes: number[] = [];
  for (let rest = size; rest > 0; rest = Math.floor(rest / 256)) bytes.unshift(rest % 256);
  return Buffer.from([0x80 | bytes.length, ...bytes]);
}
const tlv = (tag: number, ...parts: Buffer[]): Buffer => {
  const body = Buffer.concat(parts);
  return Buffer.concat([Buffer.from([tag]), length(body.length), body]);
};
const sequence = (...parts: Buffer[]): Buffer => tlv(0x30, ...parts);
function oid(dotted: string): Buffer {
  const [first, second, ...rest] = dotted.split(".").map(Number) as [number, number, ...number[]];
  const bytes: number[] = [first * 40 + second];
  for (const arc of rest) {
    const chunk: number[] = [arc & 0x7f];
    for (let value = Math.floor(arc / 128); value > 0; value = Math.floor(value / 128)) chunk.unshift((value & 0x7f) | 0x80);
    bytes.push(...chunk);
  }
  return tlv(0x06, Buffer.from(bytes));
}
const integer = (bytes: Buffer): Buffer => tlv(0x02, bytes[0]! & 0x80 ? Buffer.concat([Buffer.from([0]), bytes]) : bytes);
const bitString = (bytes: Buffer): Buffer => tlv(0x03, Buffer.from([0]), bytes);
const name = (common: string): Buffer => sequence(tlv(0x31, sequence(oid("2.5.4.3"), tlv(0x0c, Buffer.from(common, "utf8")))));
function utcTime(date: Date): Buffer {
  const text = date.toISOString().replace(/[-:T]/gu, "").slice(2, 14);
  return tlv(0x17, Buffer.from(`${text}Z`, "latin1"));
}
const ECDSA_SHA256 = sequence(oid("1.2.840.10045.4.3.2"));
const extension = (id: string, critical: boolean, value: Buffer): Buffer =>
  sequence(oid(id), ...(critical ? [tlv(0x01, Buffer.from([0xff]))] : []), tlv(0x04, value));

function keyId(key: KeyObject): Buffer {
  return createHash("sha1").update(key.export({ type: "spki", format: "der" })).digest();
}

function certificate(subject: string, key: KeyObject, issuer: string, issuerKey: KeyObject, issuerPublic: KeyObject, extensions: Buffer[]): string {
  const issued = Date.now();
  const tbs = sequence(
    tlv(0xa0, integer(Buffer.from([2]))),
    integer(Buffer.concat([Buffer.from([0x01]), randomBytes(8)])),
    ECDSA_SHA256,
    name(issuer),
    sequence(utcTime(new Date(issued - 86_400_000)), utcTime(new Date(issued + 86_400_000))),
    name(subject),
    key.export({ type: "spki", format: "der" }),
    tlv(0xa3, sequence(...extensions, extension("2.5.29.35", false, sequence(tlv(0x80, keyId(issuerPublic)))))),
  );
  const der = sequence(tbs, ECDSA_SHA256, bitString(sign("sha256", tbs, issuerKey)));
  return `-----BEGIN CERTIFICATE-----\n${der.toString("base64").replace(/(.{64})/gu, "$1\n").trim()}\n-----END CERTIFICATE-----\n`;
}

export interface ScratchCa { caPem: string; serverCert: string; serverKey: string }

/** A CA made for this test run alone, and a server certificate it signed for 127.0.0.1, localhost and `dnsNames`. */
export function scratchCa(dnsNames: readonly string[] = []): ScratchCa {
  const ca = generateKeyPairSync("ec", { namedCurve: "P-256" });
  const server = generateKeyPairSync("ec", { namedCurve: "P-256" });
  const caName = "scratch loopback test CA";
  const caPem = certificate(caName, ca.publicKey, caName, ca.privateKey, ca.publicKey, [
    extension("2.5.29.19", true, sequence(tlv(0x01, Buffer.from([0xff])))),
    extension("2.5.29.15", true, tlv(0x03, Buffer.from([0x01, 0x06]))),
    extension("2.5.29.14", false, tlv(0x04, keyId(ca.publicKey))),
  ]);
  const serverCert = certificate("localhost", server.publicKey, caName, ca.privateKey, ca.publicKey, [
    extension("2.5.29.19", true, sequence()),
    extension("2.5.29.37", false, sequence(oid("1.3.6.1.5.5.7.3.1"))),
    extension("2.5.29.17", false, sequence(
      tlv(0x82, Buffer.from("localhost", "latin1")),
      ...dnsNames.map((dnsName) => tlv(0x82, Buffer.from(dnsName, "latin1"))),
      tlv(0x87, Buffer.from([127, 0, 0, 1])),
    )),
  ]);
  return { caPem, serverCert, serverKey: server.privateKey.export({ type: "pkcs8", format: "pem" }).toString() };
}

const ANSWER = "HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: 2\r\nConnection: close\r\n\r\n{}";

function countIn(chunks: readonly Buffer[], markers: readonly string[]): number {
  const blob = Buffer.concat(chunks).toString("latin1");
  return markers.reduce((n, marker) => n + blob.split(marker).length - 1, 0);
}

/** Reads one request from `stream`, keeping every byte in `into`, and answers 200 `{}` once its head is complete. */
function answerRequest(stream: net.Socket | tls.TLSSocket, into: Buffer[]): void {
  let head = Buffer.alloc(0);
  stream.on("data", (chunk: Buffer) => {
    into.push(chunk);
    head = Buffer.concat([head, chunk]);
    if (head.indexOf("\r\n\r\n") >= 0 && stream.writable) stream.end(ANSWER);
  });
}

/** An https server on 127.0.0.1 with the scratch server certificate, counting connections and the markers it reads. */
export class HttpsCountingTarget {
  readonly server: tls.Server;
  port = 0;
  connections = 0;
  private received: Buffer[] = [];
  constructor(ca: ScratchCa, private readonly markers: readonly string[]) {
    this.server = tls.createServer({ cert: ca.serverCert, key: ca.serverKey }, (socket) => {
      socket.on("error", () => undefined);
      socket.setTimeout(3000, () => socket.destroy());
      answerRequest(socket, this.received);
    });
    this.server.on("connection", () => { this.connections += 1; });
    this.server.on("tlsClientError", () => undefined);
  }
  async listen(): Promise<void> {
    await new Promise<void>((resolve) => this.server.listen(0, "127.0.0.1", resolve));
    this.port = (this.server.address() as net.AddressInfo).port;
  }
  get markerCount(): number { return countIn(this.received, this.markers); }
  close(): Promise<void> { return new Promise((resolve) => { this.server.close(() => resolve()); }); }
}

/**
 * A proxy on 127.0.0.1 that answers `CONNECT` with 200 and then serves TLS inside the tunnel with the scratch server
 * certificate, so a client that trusts the CA completes its handshake with the proxy. Counts connections, tunnels,
 * finished handshakes and the markers in every byte it reads, decrypted tunnel bytes and absolute-form requests alike.
 */
export class TlsTerminatingProxySink {
  readonly server: net.Server;
  port = 0;
  connections = 0;
  tunnels = 0;
  handshakes = 0;
  private received: Buffer[] = [];
  constructor(ca: ScratchCa, private readonly markers: readonly string[]) {
    const context = tls.createSecureContext({ cert: ca.serverCert, key: ca.serverKey });
    this.server = net.createServer((socket) => {
      this.connections += 1;
      socket.on("error", () => undefined);
      socket.setTimeout(3000, () => socket.destroy());
      let head = Buffer.alloc(0);
      const onData = (chunk: Buffer): void => {
        this.received.push(chunk);
        head = Buffer.concat([head, chunk]);
        const end = head.indexOf("\r\n\r\n");
        if (end < 0) return;
        if (!/^CONNECT /u.test(head.toString("latin1"))) { socket.end(ANSWER); return; }
        this.tunnels += 1;
        socket.off("data", onData);
        socket.pause();
        const rest = head.subarray(end + 4);
        if (rest.length > 0) socket.unshift(rest);
        socket.write("HTTP/1.1 200 Connection Established\r\n\r\n");
        const inner = new tls.TLSSocket(socket, { isServer: true, secureContext: context });
        inner.on("error", () => undefined);
        inner.on("secure", () => { this.handshakes += 1; });
        answerRequest(inner, this.received);
        socket.resume();
      };
      socket.on("data", onData);
    });
  }
  async listen(): Promise<void> {
    await new Promise<void>((resolve) => this.server.listen(0, "127.0.0.1", resolve));
    this.port = (this.server.address() as net.AddressInfo).port;
  }
  /** How many times a planted marker appears in the bytes this sink read, after TLS inside a tunnel is removed. */
  get markerCount(): number { return countIn(this.received, this.markers); }
  close(): Promise<void> { return new Promise((resolve) => { this.server.close(() => resolve()); }); }
}
