/**
 * Every client that sends API keys through axios goes through the one `HttpClient.request`, which sets the agents of a
 * loopback request (a direct connection, `localhost` resolved as 127.0.0.1 then ::1) and the proxy rule of a keyed
 * request. A class that extends `APIKeyAuth` defines no `request` of its own and no module outside `api/auth.ts` makes an
 * axios instance or an axios call, so a keyed send cannot reach axios by another route.
 */
import { readdirSync, readFileSync, statSync } from "node:fs";
import { join, relative } from "node:path";

const SRC = join(__dirname, "../..");

function sources(dir: string): string[] {
  return readdirSync(dir).flatMap((name) => {
    const path = join(dir, name);
    if (statSync(path).isDirectory()) return /^(__tests__|__fixtures__|generated|node_modules)$/u.test(name) ? [] : sources(path);
    return /\.ts$/u.test(name) && !/\.d\.ts$/u.test(name) ? [path] : [];
  });
}

const FILES = sources(SRC).map((path) => ({ path: relative(SRC, path), text: readFileSync(path, "utf8") }));
const code = (text: string): string => text.replace(/\/\*[\s\S]*?\*\//gu, "").replace(/^\s*\/\/.*$/gmu, "");

describe("axios senders", () => {
  it("are the subclasses of the one client in api/auth.ts", () => {
    const subclasses = FILES.filter((f) => /\bextends\s+(APIKeyAuth|HttpClient)\b/u.test(code(f.text))).map((f) => f.path).sort();
    expect(subclasses).toEqual(["annotations/annotation.ts", "api/apikeys.ts", "api/auth.ts", "datasets/dataset.ts", "kb/client.ts", "prompt/client.ts", "queues/client.ts"]);
  });

  it("make no axios instance or axios call outside api/auth.ts", () => {
    const callers = FILES.filter((f) => /\baxios\s*(\.\s*(create|request|get|post|put|patch|delete|head)\b|\()/u.test(code(f.text))).map((f) => f.path);
    expect(callers).toEqual(["api/auth.ts"]);
  });

  it("define no request method of their own", () => {
    const own = FILES.filter((f) => f.path !== "api/auth.ts" && /\bextends\s+(APIKeyAuth|HttpClient)\b/u.test(code(f.text)) && /^\s*(?:public\s+|protected\s+|private\s+|override\s+)*(?:async\s+)?request\s*[<(]/mu.test(code(f.text))).map((f) => f.path);
    expect(own).toEqual([]);
  });
});
