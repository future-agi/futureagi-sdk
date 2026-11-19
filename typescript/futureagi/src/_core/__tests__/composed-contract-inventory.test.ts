import fs from "node:fs";
import path from "node:path";
import { checkWire, runtime, success, type Case } from "../__fixtures__/contract-runtime";
import { publicValueAt } from "../__fixtures__/contract-absence";
import { assertConsoleAbsent } from "../__fixtures__/console-absence";

const data = JSON.parse(fs.readFileSync(path.resolve(__dirname, "../../../../../tests/fixtures/contracts/operations.json"), "utf8"));
const inputs = JSON.parse(fs.readFileSync(path.resolve(__dirname, "../../../../../openapi/contract-inputs.json"), "utf8"));
const approvals = (): Case => structuredClone(data.operations.find((row: Case) => row.id === "platform:runs.approvals"));

test.each<Case>(inputs.namespace_absences)("hidden namespace $id requires real absence", declaration => {
  const subject = runtime(approvals(), () => { throw new Error("absence must not request"); });
  expect(declaration.status).toBe("NOT-OFFERED");
  expect(declaration.owner).toBeTruthy();
  expect(declaration.reason).toBeTruthy();
  for (const path of declaration.ts) expect(publicValueAt(subject.client, path)).toBeUndefined();
});

test("hidden connector features require real absence", () => {
  const subject = runtime(approvals(), () => { throw new Error("absence must not request"); });
  for (const declaration of data.feature_absences) {
    expect(declaration.status).toBe("NOT-OFFERED");
    expect(declaration.owner).toBeTruthy();
    expect(declaration.reason).toBeTruthy();
    expect(publicValueAt(subject.client, declaration.ts)).toBeUndefined();
  }
});

test("public Run factory is independent of approval attempts", async () => {
  const row = approvals();
  const requests: Request[] = [];
  const subject = runtime(row, request => { requests.push(request); return success(row); });
  if (row.public_absence) {
    assertConsoleAbsent(row, subject);
    expect(requests).toEqual([]);
    return;
  }
  await subject.prepare();
  expect(subject.setupRequests).toHaveLength(1);
  expect(requests).toHaveLength(0);
  await subject.call();
  await subject.call();
  expect(subject.setupRequests).toHaveLength(1);
  expect(requests).toHaveLength(2);
  requests.forEach(request => checkWire(row, request));
  expect(subject.handles.Run.decide).toBeUndefined();
});

test.each(["missing_fixture", "missing_method", "misroute", "factory_misroute"])("rejects broken Run dispatch: %s", async mutation => {
  const row = approvals();
  const requests: Request[] = [];
  const subject = runtime(row, request => { requests.push(request); return success(row); });
  if (row.public_absence) {
    assertConsoleAbsent(row, subject);
    expect(requests).toEqual([]);
    return;
  }
  if (mutation === "missing_fixture") {
    row.handle_fixtures = {};
    await expect(subject.call()).rejects.toThrow("public handle fixture required");
    expect(requests).toHaveLength(0);
    expect(subject.setupRequests).toHaveLength(0);
    return;
  }
  if (mutation === "factory_misroute") {
    row.handle_fixtures.Run.ts.path = "client.agents.runs.delete";
    await expect(subject.prepare()).rejects.toThrow();
    expect(requests).toHaveLength(0);
    return;
  }
  await subject.prepare();
  subject.handles.Run.approvals = mutation === "missing_method" ? null : subject.handles.Run.cancel;
  if (mutation === "missing_method") {
    await expect(subject.call()).rejects.toThrow("callable");
    expect(requests).toHaveLength(0);
  } else {
    await subject.call();
    expect(requests).toHaveLength(1);
    expect(() => checkWire(row, requests[0])).toThrow();
  }
});

test("every composed namespace is scheduled and hidden roots are explicit", () => {
  for (const id of ["platform:runs.approvals", "platform:runs.events", "platform:platform.agents.roster",
    "catalog:models.list", "core:tracing.traces"]) {
    const row = data.operations.find((row: Case) => row.id === id);
    expect(data.public_cases.ts.includes(id)).toBe(!row.public_absence);
    expect(data.not_offered.ts.some((entry: Case) => entry.id === id)).toBe(Boolean(row.public_absence));
  }
  const features = JSON.parse(fs.readFileSync(path.resolve(__dirname, "../../../../../openapi/connectors/features.json"), "utf8"));
  expect(data.public_cases.ts.includes("platform:platform.credentials.list")).toBe(features.credential_reads);
  expect(data.public_cases.ts.some((id: string) => id.startsWith("connectors:connectors."))).toBe(features.mcp_core);
  expect(data.public_cases.ts.some((id: string) => id.startsWith("connectors:integrations_"))).toBe(features.data_integrations);
  expect(data.public_cases.ts.some((id: string) => id.startsWith("tracing:"))).toBe(true);
  expect(data.namespace_absences).toEqual(inputs.namespace_absences);
  expect(data.module_absences).toEqual(inputs.module_absences);
  const manifest = JSON.parse(fs.readFileSync(path.resolve(__dirname, "../../../package.json"), "utf8"));
  for (const entry of data.module_absences) {
    expect(entry.status).toBe("NOT-OFFERED");
    expect(manifest.exports[entry.ts_subpath]).toBeUndefined();
  }
});
