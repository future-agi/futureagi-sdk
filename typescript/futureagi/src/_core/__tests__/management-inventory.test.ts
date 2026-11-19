import fs from "node:fs";
import path from "node:path";
import { runtime, type Case } from "../__fixtures__/contract-runtime";

const root = path.resolve(__dirname, "../../../../..");
const data = JSON.parse(fs.readFileSync(path.join(root, "tests/fixtures/contracts/operations.json"), "utf8"));
const surface: Case[] = JSON.parse(fs.readFileSync(path.join(root, "openapi/fa-mgmt/surface.json"), "utf8")).operations;

test("all nineteen management operations have public cases in every language", () => {
  const rows = data.operations.filter((row: Case) => row.adapter === "management");
  expect(rows).toHaveLength(19);
  expect(rows.map((row: Case) => row.operation_id).sort()).toEqual(surface.map(row => row.operation_id).sort());
  expect(data.modules.management).toBeUndefined();
  for (const mode of ["py_sync", "py_async", "ts"]) {
    for (const row of rows) {
      expect(data.public_cases[mode]).toContain(row.id);
      expect(data.not_offered[mode].some((item: Case) => item.id === row.id)).toBe(false);
    }
  }
});

test.each(surface)("management method $name is required before transport", async operation => {
  const row = data.operations.find((row: Case) => row.adapter === "management" && row.name === operation.name);
  expect(row).toBeDefined();
  const requests: Request[] = [];
  const subject = runtime(row, request => { requests.push(request); throw new Error("missing method must not request"); });
  const parts = row.wrapper.ts.split(".").slice(1);
  let owner: any = subject.client;
  for (const part of parts.slice(0, -1)) owner = owner[part];
  const name = parts.at(-1)!;
  const prototype = Object.getPrototypeOf(owner);
  const descriptor = Object.getOwnPropertyDescriptor(prototype, name)!;
  expect(typeof owner[name]).toBe("function");
  delete prototype[name];
  try {
    await expect(subject.call()).rejects.toThrow();
    // Compare cardinalities so a recorded native Request cannot make Jest's
    // failure renderer throw before it reports the transport assertion.
    expect(requests.length).toBe(0);
    expect(subject.setupRequests.length).toBe(0);
  } finally { Object.defineProperty(prototype, name, descriptor); }
});
