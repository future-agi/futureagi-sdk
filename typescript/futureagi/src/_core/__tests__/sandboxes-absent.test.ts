import * as sdk from "../../index";
import { FutureAGIClient } from "../../futureagi-client";
import { PlatformNotConfiguredError } from "../errors";
import { lookup } from "../policy";
import { PLATFORM_OPERATIONS } from "../../generated/platform/policy.gen";
import * as generated from "../../generated/platform/sdk.gen";

describe("unavailable sandbox surface", () => {
  it("is absent from clients, option views and root exports", () => {
    const client = new FutureAGIClient({
      apiKey: "test-key",
      secretKey: "test-secret",
      baseUrl: "http://127.0.0.1:9",
    });
    for (const view of [client, client.withOptions({ retries: 0 })]) {
      expect("sandboxes" in view).toBe(false);
    }
    for (const name of ["Sandbox", "AsyncSandbox", "SandboxesClient"]) {
      expect(name in sdk).toBe(false);
    }
  });

  it("has no generated operation or low-level function", () => {
    expect(Object.keys(PLATFORM_OPERATIONS).filter((name) => name.startsWith("sandboxes."))).toEqual([]);
    expect(Object.keys(generated).filter((name) => /sandbox/i.test(name))).toEqual([]);
    for (const name of ["sandboxes.create", "sandboxes.commands.run", "sandboxes.files.write", "sandboxes.kill"]) {
      expect(() => lookup(PLATFORM_OPERATIONS, name)).toThrow(PlatformNotConfiguredError);
    }
  });
});
