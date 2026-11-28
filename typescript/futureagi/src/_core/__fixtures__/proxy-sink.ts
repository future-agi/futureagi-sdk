/**
 * Loopback listeners that count what reaches them: connections, and the occurrences of a planted marker key in every
 * byte received. A proxy sink also answers `CONNECT` (it accepts the tunnel and then reads the request sent through
 * it), so a key carried by a tunnelling proxy agent is counted as well as one carried in an absolute-form request.
 */
import net from "node:net";

export class CountingSink {
  readonly server: net.Server;
  port = 0;
  connections = 0;
  tunnels = 0;
  private received: Buffer[] = [];
  constructor(private readonly markers: readonly string[]) {
    this.server = net.createServer((socket) => {
      this.connections += 1;
      let data = Buffer.alloc(0);
      let tunnelled = false;
      socket.on("error", () => undefined);
      socket.setTimeout(1500, () => socket.destroy());
      socket.on("data", (chunk) => {
        this.received.push(chunk);
        data = Buffer.concat([data, chunk]);
        const end = data.indexOf("\r\n\r\n");
        if (end < 0) return;
        if (!tunnelled && /^CONNECT /u.test(data.toString("latin1"))) {
          tunnelled = true;
          this.tunnels += 1;
          data = data.subarray(end + 4);
          socket.write("HTTP/1.1 200 Connection Established\r\n\r\n");
          if (data.indexOf("\r\n\r\n") < 0) return;
        }
        socket.end("HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: 2\r\nConnection: close\r\n\r\n{}");
      });
    });
  }
  async listen(): Promise<void> {
    await new Promise<void>((resolve) => this.server.listen(0, "127.0.0.1", resolve));
    this.port = (this.server.address() as net.AddressInfo).port;
  }
  reset(): void { this.received = []; this.connections = 0; this.tunnels = 0; }
  /** How many times a planted marker appears in the bytes this sink received. */
  get markerCount(): number {
    const blob = Buffer.concat(this.received).toString("latin1");
    return this.markers.reduce((n, marker) => n + blob.split(marker).length - 1, 0);
  }
  close(): Promise<void> { return new Promise((resolve) => { this.server.close(() => resolve()); }); }
}

const PROXY_VARIABLES = ["HTTP_PROXY", "http_proxy", "HTTPS_PROXY", "https_proxy", "ALL_PROXY", "all_proxy", "NO_PROXY", "no_proxy", "NODE_USE_ENV_PROXY"];

/** Clears the proxy variables the test process inherited, sets `values`, and returns the restore step. */
export function proxyEnvironment(values: Readonly<Record<string, string>> = {}): () => void {
  const saved = new Map(PROXY_VARIABLES.map((name) => [name, process.env[name]] as const));
  for (const name of PROXY_VARIABLES) delete process.env[name];
  Object.assign(process.env, values);
  return () => {
    for (const name of PROXY_VARIABLES) delete process.env[name];
    for (const [name, value] of saved) if (value !== undefined) process.env[name] = value;
  };
}
