/** Loopback listeners and the dial shim of the plain-HTTP oracle tests: key bytes are counted at the sinks. */
import net from "node:net";

export const MARKER_KEY = ["FIMARK", "ERKEY-", "7f3a91", "c2"].join("");
export const MARKER_SECRET = ["FIMARK", "ERSECR", "ET-5d0", "8be44"].join("");

export class Sink {
  readonly server: net.Server;
  port = 0;
  chunks: Buffer[] = [];
  requests = 0;
  connections = 0;
  /** "tls": count the connection and close it (a TLS client hello is not an HTTP request). */
  mode: "http" | "tls" = "http";
  constructor(private readonly status = "200 OK", private readonly location?: string) {
    this.server = net.createServer((socket) => {
      this.connections += 1;
      if (this.mode === "tls") { socket.on("error", () => undefined); socket.on("data", () => socket.destroy()); return; }
      let data = Buffer.alloc(0);
      let answered = false;
      const answer = (): void => {
        if (answered) return;
        answered = true;
        this.chunks.push(data);
        this.requests += 1;
        const extra = this.location ? `Location: ${this.location}\r\n` : "";
        socket.end(`HTTP/1.1 ${this.status}\r\n${extra}Content-Length: 2\r\nConnection: close\r\n\r\n{}`);
      };
      socket.setTimeout(300, answer);
      socket.on("error", () => undefined);
      socket.on("data", (chunk) => {
        data = Buffer.concat([data, chunk]);
        const end = data.indexOf("\r\n\r\n");
        if (end < 0) return;
        const head = data.subarray(0, end).toString("latin1");
        const length = /content-length:\s*(\d+)/iu.exec(head);
        if (data.length - end - 4 >= (length ? Number(length[1]) : 0)) answer();
      });
    });
  }
  async listen(host = "127.0.0.1", port = 0): Promise<void> {
    await new Promise<void>((resolve) => this.server.listen(port, host, resolve));
    this.port = (this.server.address() as net.AddressInfo).port;
  }
  reset(): void { this.chunks = []; this.requests = 0; this.connections = 0; }
  get markerBytes(): number {
    const blob = Buffer.concat(this.chunks).toString("latin1");
    return [MARKER_KEY, MARKER_SECRET].reduce((n, m) => n + (blob.split(m).length - 1), 0);
  }
  close(): void { this.server.close(); }
}


// A getaddrinfo shim: every name or address the SDK dials is this machine, on the port asked for.
export const realConnect = net.Socket.prototype.connect;
export function shimConnect(this: net.Socket, ...args: unknown[]): net.Socket {
  // net.connect hands connect() its normalized arguments, `[options, callback]`, as one array
  const first = args[0];
  const holder = Array.isArray(first) ? first : args;
  const options = holder[0];
  if (typeof options === "object" && options !== null && "port" in (options as object)) {
    const shimmed = { ...(options as net.TcpSocketConnectOpts), host: "127.0.0.1" };
    delete (shimmed as { lookup?: unknown }).lookup;
    if (Array.isArray(first)) first[0] = shimmed; // in place: the array carries the runtime's own marker
    else args[0] = shimmed;
    return (realConnect as (...a: unknown[]) => net.Socket).apply(this, args);
  }
  return (realConnect as (...a: unknown[]) => net.Socket).apply(this, args);
}

