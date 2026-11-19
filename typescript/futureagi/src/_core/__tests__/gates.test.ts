/**
 * Keyless gates for the TypeScript platform core: module size, imports (no node:*
 * module, so an edge-safe ./platform subpath stays possible), the shared hygiene scan, and the root exports.
 */
import { spawnSync } from "node:child_process";
import { readdirSync, readFileSync, statSync } from "node:fs";
import { join, relative } from "node:path";

import * as root from "../../index";
import { SDKException } from "../../utils/errors";

const CORE = join(__dirname, "..");
const REPO = join(CORE, "..", "..", "..", "..");
const files = (dir: string): string[] =>
  readdirSync(dir).flatMap((name) => {
    const path = join(dir, name);
    return statSync(path).isDirectory() ? files(path) : path.endsWith(".ts") ? [path] : [];
  });
const SOURCES = files(CORE).filter((p) => !p.includes("__tests__") && !p.includes("__fixtures__"));
const ALL = files(CORE);

describe("platform core gates", () => {
  it("every module is 400 lines or fewer", () => {
    const long = ALL.map((p) => [relative(CORE, p), readFileSync(p, "utf8").split("\n").length] as const).filter(([, n]) => n > 400);
    expect(long).toEqual([]);
  });

  it("platform modules import no node:* module and nothing from datasets or kb", () => {
    for (const path of SOURCES) {
      const text = readFileSync(path, "utf8");
      const imports = [...text.matchAll(/from\s+"([^"]+)"/gu)].map((m) => m[1]!);
      for (const spec of imports) {
        expect([relative(CORE, path), spec.startsWith("node:") || /datasets|\/kb\b|axios|form-data/u.test(spec)]).toEqual([
          relative(CORE, path),
          false,
        ]);
      }
    }
  });

  it("the shared hygiene scan has no hits in the platform core, this file included", () => {
    // The scanner matches internal names by hash (scripts/platform/hygiene-rules.json), so no gate spells one.
    const scan = spawnSync(process.execPath, [join(REPO, "scripts", "platform", "hygiene-scan.mjs"), relative(REPO, CORE)], {
      cwd: REPO,
      encoding: "utf8",
      timeout: 60_000,
    });
    expect([scan.status, scan.status === 0 ? "" : `${scan.error?.message ?? ""}${scan.stderr}`]).toEqual([0, ""]);
    expect(scan.stdout).toMatch(/hygiene: [1-9][0-9]* files scanned, 0 hit\(s\)/u);
  });

  it("platform core uses generated paths, not handwritten route literals", () => {
    const lint = spawnSync(process.execPath, [join(REPO, "scripts", "platform", "lint", "no-url-paths.mjs"), relative(REPO, CORE)], {
      cwd: REPO,
      encoding: "utf8",
      timeout: 60_000,
    });
    expect([lint.status, lint.status === 0 ? "" : `${lint.error?.message ?? ""}${lint.stderr}`]).toEqual([0, ""]);
    expect(lint.stdout).toMatch(/0 path literal\(s\)/u);
  });

  it("the root exports the error tree, every class an SDKException", () => {
    const names = [
      "FutureAGIAPIError",
      "BadRequestError",
      "AuthenticationError",
      "PermissionDeniedError",
      "NotFoundError",
      "ProductNotAvailableError",
      "ConflictError",
      "IdempotencyKeyInProgressError",
      "SandboxStateError",
      "PayloadTooLargeError",
      "UnprocessableEntityError",
      "IdempotencyKeyReusedError",
      "RateLimitError",
      "ServerError",
      "CoreRateLimitError",
      "CoreServerError",
      "AuthError",
      "CredentialsMissingError",
      "TransportError",
      "APIConnectionError",
      "APITimeoutError",
      "ConfigurationError",
      "HostNotAllowedError",
      "MixedCredentialsError",
      "PlatformNotConfiguredError",
      "UnexpectedRedirectError",
      "StreamInterruptedError",
    ];
    const exported = root as unknown as Record<string, unknown>;
    for (const name of names) {
      const value = exported[name] as { prototype: unknown } | undefined;
      expect([name, typeof value]).toEqual([name, "function"]);
      expect([name, value!.prototype instanceof SDKException]).toEqual([name, true]);
    }
    expect((exported.CoreRateLimitError as { prototype: unknown }).prototype instanceof (exported.FutureAGIAPIError as new () => unknown)).toBe(
      true,
    );
  });
});
