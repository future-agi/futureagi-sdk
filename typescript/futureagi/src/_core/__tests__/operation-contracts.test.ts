import fs from "node:fs";
import path from "node:path";
import { checkWire, pathArgs, runtime, success, streamEvents, type Case } from "../__fixtures__/contract-runtime";
import { listPage } from "../pagination";
import { assertConsoleAbsent } from "../__fixtures__/console-absence";
import { envelopeAdapter, payloads } from "../__fixtures__/contract-payloads";

const data = JSON.parse(fs.readFileSync(path.resolve(__dirname, "../../../../../tests/fixtures/contracts/operations.json"), "utf8"));
const eeResourceError = JSON.parse(fs.readFileSync(path.resolve(__dirname, "../../../../../tests/fixtures/server-contracts/console-404.json"), "utf8")).ee[0].body;
const rows: Case[] = data.operations.filter((row: Case) => data.public_cases.ts.includes(row.id) || row.public_absence);

describe.each(rows)("operation contract $id", (row) => {
  test("method, path, idempotency, retry policy, response and stream shape", async () => {
    const requests: Request[] = [];
    const subject = runtime(row, request => { requests.push(request); return success(row); });
    if (row.public_absence) {
      assertConsoleAbsent(row, subject);
      expect(requests).toEqual([]);
      return;
    }
    const result = await subject.call();
    expect(requests).toHaveLength(1);
    checkWire(row, requests[0]);
    if (row.stream) {
      expect(result.map((event: any) => event.type)).toEqual(streamEvents(row));
      expect(result.every((event: any) => event.marker === "kept")).toBe(true);
    }
    if (row.adapter !== "platform") {
      // Assert the actual public value; manually unwrapping here hides adapter defects.
      const raw = (row.adapter === "catalog" && row.catalog.pagination) || row.public_page ? result.raw : result;
      expect(raw).toEqual(payloads(row).publicValue);
    }
  });

  test("retry class controls real transport attempts and preserves the key", async () => {
    const requests: Request[] = [];
    const subject = runtime(row, request => {
      requests.push(request);
      return requests.length === 1 ? Response.json({ code: "service_unavailable" }, { status: 503, headers: { "Retry-After": "0" } }) : success(row);
    }, 1);
    if (row.public_absence) {
      assertConsoleAbsent(row, subject);
      expect(requests).toEqual([]);
      return;
    }
    const retried = ["http-idempotent", "keyed"].includes(row.retry) && !row.stream;
    if (retried) await subject.call();
    else if (row.stream) await expect(subject.call()).rejects.toMatchObject({ name: "StreamInterruptedError", cause: { statusCode: 503 } });
    else await expect(subject.call()).rejects.toHaveProperty("statusCode", 503);
    expect(requests).toHaveLength(retried ? 2 : 1);
    requests.forEach(request => checkWire(row, request));
    if (row.idempotent) expect(new Set(requests.map(r => r.headers.get("Idempotency-Key"))).size).toBe(1);
  });

  test("each status and management error code has the declared class", async () => {
    const answers: Array<[number, string | undefined, string]> = Object.entries(data.status_classes).map(([s, cls]) => [Number(s), undefined, cls as string]);
    for (const [code, status] of Object.entries(data.fa_codes)) answers.push([Number(status), code, data.status_classes[String(status)]]);
    answers.push([404, "product_not_admitted", "ProductNotAvailableError"], [422, "idempotency_key_reused", "IdempotencyKeyReusedError"], [409, "idempotency_key_in_progress", "IdempotencyKeyInProgressError"]);
    for (const [status, code, expected] of answers) {
      const cls = status === 409 && (code === undefined || code === "conflict") && row.adapter === "platform" && row.namespace === "sandboxes" ? "SandboxStateError" : expected;
      const subject = runtime(row, (request) => {
        // This oracle covers resource 404s, not the separately tested unserved Console origin.
        const body = status === 404 && code === undefined && new URL(request.url).pathname.startsWith("/omega/api/workspace/")
          ? eeResourceError : { status: false, code, message: "fixture refusal", result: "fixture refusal" };
        return Response.json(body, { status, headers: { "Retry-After": "999", "X-Request-Id": "contract-request" } });
      });
      if (row.public_absence) {
        assertConsoleAbsent(row, subject);
        continue;
      }
      let caught: any;
      try { await subject.call(); } catch (error) { caught = error; }
      if (row.stream && ![401, 403, 404].includes(status)) {
        expect(caught?.constructor.name).toBe("StreamInterruptedError");
        expect(caught.lastSequence).toBeUndefined();
        caught = caught.cause;
      }
      // The shared fixture keeps Python names; only these two core TS names differ.
      const tsClass = ({ RateLimitError: "CoreRateLimitError", ServerError: "CoreServerError" } as Record<string, string>)[cls] ?? cls;
      expect(caught?.constructor.name).toBe(tsClass);
      expect(caught?.statusCode).toBe(status);
      expect(caught?.requestId).toBe("contract-request");
      if (code) expect(caught?.code).toBe(code);
    }
  });
});

for (const row of rows.filter(envelopeAdapter)) {
  test(`public logical failure ${row.id}`, async () => {
    const subject = runtime(row, () => Response.json({ status: false, code: "invalid", result: "fixture refusal" },
      { headers: { "X-Request-Id": "logical-refusal" } }));
    await expect(subject.call()).rejects.toMatchObject({ statusCode: 400, code: "invalid", requestId: "logical-refusal" });
  });
}

for (const row of rows.filter(r => r.adapter === "platform" && r.pagination)) {
  test(`pagination ${row.id}`, async () => {
    const requests: Request[] = [];
    const p = row.pagination;
    const subject = runtime(row, request => {
      requests.push(request);
      const body: Record<string, unknown> = { [p.itemsField]: [{ n: requests.length }] };
      if (p.nextCursorField) body[p.nextCursorField] = requests.length === 1 ? "opaque/+==" : null;
      if (p.truncatedField) body[p.truncatedField] = true;
      return Response.json(body);
    });
    const first = await listPage(subject.core, row.name, { path: pathArgs(row) });
    expect(first.items).toEqual([{ n: 1 }]);
    if (p.style === "cursor") {
      expect(first.nextCursor).toBe("opaque/+==");
      const next = await first.nextPage();
      expect(next?.items).toEqual([{ n: 2 }]);
      expect(next?.hasMore).toBe(false);
      expect(new URL(requests[1].url).searchParams.get(p.cursorParam)).toBe("opaque/+==");
    } else expect(first.hasMore).toBe(false);
    if (p.style === "window") expect(first.truncated).toBe(true);
  });
}

test.each(["method", "idempotency"])("seeded %s defect fails the wire gate", async mutation => {
  const row: Case = data.operations.find((r: Case) => r.adapter === "platform" && r.idempotent && !r.stream)!;
  const requests: Request[] = [];
  const subject = runtime(row, request => { requests.push(request); return success(row); });
  const op = subject.core.operation(row.name);
  subject.core.shared.table = { [row.name]: { ...op, ...(mutation === "method" ? { method: "PUT" } : { idempotent: false }) } };
  // Isolate policy mutation; every operation still has a mandatory public call above.
  const body = row.content_type ? (row.content_type === "application/json" ? {} : new Uint8Array([1])) : undefined;
  await subject.core.call(row.name, { path: pathArgs(row), body });
  expect(() => checkWire(row, requests[0])).toThrow();
});
