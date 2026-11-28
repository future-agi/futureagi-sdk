/**
 * A CONNECT-aware proxy sink on a loopback port: a CONNECT is answered 200 and the request that follows in the tunnel
 * is read and answered 200; a request sent to it in absolute form is answered 200 too. Every byte is recorded, so the
 * marker key bytes that reach the proxy are counted whichever way the client hands the request over.
 */
import net from "node:net";

import { MARKER_KEY, MARKER_SECRET } from "../../_core/__fixtures__/plaintext-sinks";

export class TunnelSink {
  readonly server: net.Server;
  port = 0;
  connections = 0;
  tunnels = 0;
  received = Buffer.alloc(0);
  constructor() {
    this.server = net.createServer((socket) => {
      this.connections += 1;
      socket.on("error", () => undefined);
      socket.setTimeout(1_000, () => socket.destroy());
      let tunnel = false;
      let head = "";
      socket.on("data", (chunk) => {
        this.received = Buffer.concat([this.received, chunk]);
        head += chunk.toString("latin1");
        if (!head.includes("\r\n\r\n")) return;
        if (!tunnel && head.startsWith("CONNECT ")) {
          tunnel = true;
          this.tunnels += 1;
          head = "";
          socket.write("HTTP/1.1 200 Connection established\r\n\r\n");
          return;
        }
        socket.end("HTTP/1.1 200 OK\r\nContent-Length: 2\r\nConnection: close\r\n\r\n{}");
      });
    });
  }
  async listen(): Promise<void> {
    await new Promise<void>((resolve) => this.server.listen(0, "127.0.0.1", resolve));
    this.port = (this.server.address() as net.AddressInfo).port;
  }
  reset(): void { this.received = Buffer.alloc(0); this.connections = 0; this.tunnels = 0; }
  get markerBytes(): number {
    const blob = this.received.toString("latin1");
    return [MARKER_KEY, MARKER_SECRET].reduce((n, m) => n + (blob.split(m).length - 1), 0);
  }
  close(): void { this.server.close(); }
}
