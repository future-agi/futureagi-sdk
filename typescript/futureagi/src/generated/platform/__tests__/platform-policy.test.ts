/**
 * The TypeScript side of the platform codegen gates, run by jest in the existing job: the generated
 * operation table agrees with the committed scoped contract, operation by operation, and the platform
 * core's own executor (`src/_core`) calls every operation from it, as a client does.
 */
import { createHash } from "crypto";
import { readFileSync } from "fs";
import { join } from "path";

import type { PlatformOrigin } from "../../../_core/origins";
import { PlatformCore } from "../../../_core/platform-base";
import {
  counts,
  lookup,
  type OperationSpec,
  type OperationTable,
  retryClassOf,
} from "../../../_core/policy";
import {
  PLATFORM_CONTRACT,
  PLATFORM_KNOWN_EVENTS,
  PLATFORM_OPERATION_EXTRAS,
  PLATFORM_OPERATIONS,
  type PlatformOperationExtras,
} from "../policy.gen";
import * as sdk from "../sdk.gen";

const REPO = join(__dirname, "..", "..", "..", "..", "..", "..");
const SPEC_FILE = join(
  REPO,
  "openapi",
  "platform",
  "generated",
  "futureagi-platform.openapi.json",
);
const METHODS = ["get", "post", "put", "patch", "delete"] as const;
const BASE = "http://127.0.0.1:9/omega/api";
const credentialReads: boolean = JSON.parse(readFileSync(join(REPO, "openapi/connectors/features.json"), "utf8")).credential_reads;
const operationCount = credentialReads ? 57 : 54;
const httpIdempotentCount = credentialReads ? 35 : 32;
const paginatedCount = credentialReads ? 5 : 4;
function expectCredentialScope(names: string[]) {
  expect(names.filter((name) => name.startsWith("platform.credentials.")).sort()).toEqual(
    credentialReads ? ["platform.credentials.bindings", "platform.credentials.get", "platform.credentials.list"] : [],
  );
}

type Operation = Record<string, unknown> & {
  operationId: string;
  "x-omega-sdk": { family: string; method: string };
  "x-omega-idempotent"?: boolean;
  "x-omega-idempotency"?: { durable?: boolean | null };
};

function specOperations(): Map<
  string,
  { method: string; path: string; op: Operation }
> {
  const spec = JSON.parse(readFileSync(SPEC_FILE, "utf8")) as {
    paths: Record<string, Record<string, Operation>>;
  };
  const out = new Map<
    string,
    { method: string; path: string; op: Operation }
  >();
  for (const [path, item] of Object.entries(spec.paths)) {
    for (const method of METHODS) {
      const op = item[method];
      if (op)
        out.set(`${op["x-omega-sdk"].family}.${op["x-omega-sdk"].method}`, {
          method: method.toUpperCase(),
          path,
          op,
        });
    }
  }
  return out;
}

function retryClass(method: string, op: Operation): string {
  if (op["x-omega-idempotent"] === true)
    return op["x-omega-idempotency"]?.durable === false
      ? "keyed-not-durable"
      : "keyed";
  return ["GET", "PUT", "DELETE"].includes(method)
    ? "http-idempotent"
    : "unsafe";
}

describe("platform policy table (generated)", () => {
  const ops = specOperations();
  const table: OperationTable = PLATFORM_OPERATIONS;

  it("was generated from the committed scoped contract", () => {
    const digest = createHash("sha256")
      .update(readFileSync(SPEC_FILE))
      .digest("hex");
    expect(PLATFORM_CONTRACT.scopedSha256).toBe(digest);
    expect(PLATFORM_CONTRACT.operationCount).toBe(ops.size);
  });

  it("has one entry per operation, and the core derives the contract's retry class from it", () => {
    expect(Object.keys(table).sort()).toEqual([...ops.keys()].sort());
    expectCredentialScope(Object.keys(table));
    for (const [name, { method, path, op }] of ops) {
      const entry = lookup(table, name);
      expect([
        name,
        entry.method,
        entry.path,
        entry.operationId,
        retryClassOf(entry),
        entry.idempotent,
      ]).toEqual([
        name,
        method,
        path,
        op.operationId,
        retryClass(method, op),
        op["x-omega-idempotent"] === true,
      ]);
    }
    expect(counts(table)).toEqual({
      keyed: 13,
      "keyed-not-durable": 3,
      "http-idempotent": httpIdempotentCount,
      unsafe: 6,
      stream: 2,
      paginated: paginatedCount,
    });
  });

  it("generates a callable for every operation", () => {
    const functions = sdk as unknown as Record<string, unknown>;
    for (const { op } of ops.values())
      expect([op.operationId, typeof functions[op.operationId]]).toEqual([
        op.operationId,
        "function",
      ]);
  });

  it("keeps the counts and the shapes the clients rely on", () => {
    expectCredentialScope(Object.keys(PLATFORM_OPERATIONS));
    expect(PLATFORM_CONTRACT.counts).toEqual({
      operations: operationCount,
      keyed: 13,
      "keyed-not-durable": 3,
      "http-idempotent": httpIdempotentCount,
      unsafe: 6,
      idempotent: 16,
      durableUnstated: 4,
      streams: 2,
      paginated: paginatedCount,
      notFoundMeansApplied: 0,
    });
    expect(Object.keys(PLATFORM_OPERATIONS).some((name) => name.startsWith("sandboxes."))).toBe(false);
    expect(retryClassOf(PLATFORM_OPERATIONS["platform.agents.create"])).toBe("unsafe");
    expect(Object.values(PLATFORM_OPERATIONS).some((op) => op.notFoundMeansApplied)).toBe(false);
    expect(
      PLATFORM_OPERATION_EXTRAS["deployments.rotateAccessToken"].replayOmits,
    ).toEqual(["accessToken"]);
    const extras: Record<string, PlatformOperationExtras> =
      PLATFORM_OPERATION_EXTRAS;
    const unstated = Object.keys(extras)
      .filter((name) => extras[name]?.durableUnstated === true)
      .sort();
    expect(unstated).toEqual([
      "platform.agents.draft",
      "platform.agents.rollbackDeployment",
      "platform.schedules.create",
      "platform.schedules.runNow",
    ]);
    expect(unstated).toHaveLength(PLATFORM_CONTRACT.counts.durableUnstated);
    for (const name of unstated) expect(lookup(table, name).durable).toBe(true);
    expect(Object.keys(PLATFORM_OPERATION_EXTRAS).sort()).toEqual(
      Object.keys(table).sort(),
    );
    expect(PLATFORM_OPERATIONS["runs.events"].stream?.knownEvents).toEqual(
      PLATFORM_KNOWN_EVENTS.OmegaRunEventFrame,
    );
    expect(Object.keys(PLATFORM_KNOWN_EVENTS).sort()).toEqual([
      "OmegaDeploymentLogFrame",
      "OmegaRunEventFrame",
    ]);
  });
});

describe("the platform core calls every operation from the generated table", () => {
  const origin: PlatformOrigin = {
    url: new URL(BASE),
    base: BASE,
    mode: "keys",
    source: "derived",
    custom: false,
    headers: { "X-Api-Key": "k-test-1234", "X-Secret-Key": "s-test-1234" },
    secrets: ["k-test-1234", "s-test-1234"],
  };
  const requests: Request[] = [];
  const fetchStub = (async (
    input: RequestInfo | URL,
    init?: RequestInit,
  ): Promise<Response> => {
    const request = new Request(input as RequestInfo, init);
    requests.push(request);
    if (request.headers.get("accept") === "text/event-stream")
      return new Response(": ok\n\n", {
        status: 200,
        headers: { "content-type": "text/event-stream" },
      });
    return new Response("{}", {
      status: 200,
      headers: { "content-type": "application/json" },
    });
  }) as typeof fetch;
  const core = new PlatformCore({
    resolveOrigin: () => origin,
    table: PLATFORM_OPERATIONS,
    fetch: fetchStub,
    retries: 0,
    sleep: async () => undefined,
  });

  function argsFor(spec: OperationSpec) {
    const path: Record<string, string> = {};
    for (const p of spec.pathParams ?? [])
      path[p] = (spec.multiSegment ?? []).includes(p)
        ? "dir/file.txt"
        : `v-${p}`;
    let body: unknown;
    if ((spec.body ?? "none") !== "none")
      body =
        spec.contentType === "application/octet-stream"
          ? new Uint8Array([120])
          : {};
    return { path, body };
  }

  it("with the contract's method, path and idempotency key", async () => {
    for (const [name, { method, path: route, op }] of specOperations()) {
      const spec = lookup(PLATFORM_OPERATIONS, name);
      const params = argsFor(spec);
      const before = requests.length;
      if (spec.stream === undefined) await core.call(name, params);
      else await (await core.openStream(name, params)).response.body?.cancel();
      expect([name, requests.length]).toEqual([name, before + 1]);
      const request = requests[requests.length - 1]!;
      let expected = route;
      for (const [key, value] of Object.entries(params.path))
        expected = expected.replace(`{${key}}`, value);
      expect([
        name,
        request.method,
        new URL(request.url).pathname,
        request.headers.has("idempotency-key"),
      ]).toEqual([
        name,
        method,
        `/omega/api${expected}`,
        op["x-omega-idempotent"] === true,
      ]);
    }
    expect(requests).toHaveLength(operationCount);
    expectCredentialScope([...specOperations().keys()]);
  });
});
