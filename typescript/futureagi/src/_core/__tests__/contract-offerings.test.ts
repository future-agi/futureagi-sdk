import fs from "node:fs";
import path from "node:path";
import { methodAt, publicPath } from "../__fixtures__/contract-public";
import { absenceCandidates, publicValueAt, unavailableTypeScriptPaths } from "../__fixtures__/contract-absence";
import { runtime, type Case } from "../__fixtures__/contract-runtime";
import { assertConsoleAbsent } from "../__fixtures__/console-absence";

const data = JSON.parse(fs.readFileSync(path.resolve(__dirname, "../../../../../tests/fixtures/contracts/operations.json"), "utf8"));

test("offered and unavailable TypeScript cases partition the full inventory", () => {
  const offered = new Set(data.public_cases.ts);
  const absent = new Set(data.not_offered.ts.map((row: Case) => row.id));
  expect([...offered].filter(id => absent.has(id))).toEqual([]);
  expect([...offered, ...absent].sort()).toEqual(data.operations.map((row: Case) => row.id).sort());
  expect(data.not_offered.ts.every((row: Case) => row.status === "NOT-OFFERED" && row.owner && row.reason)).toBe(true);
});

function assertUnavailable(row: Case): void {
  const subject = runtime(row, () => { throw new Error("resolution must not request"); });
  for (const path of absenceCandidates(row, data.operations, subject.handles)) {
    expect(publicValueAt(subject.client, path, subject.handles)).toBeUndefined();
  }
}

test("unavailable declarations cannot conceal registered TypeScript methods", () => {
  const absent = new Set(data.not_offered.ts.map((row: Case) => row.id));
  for (const row of data.operations.filter((r: Case) => absent.has(r.id))) assertUnavailable(row);
});

const missingTypeScript = { status: "NOT-OFFERED", owner: "namespace", reason: "Facade is not implemented" };
function deploymentCase(): Case {
  return structuredClone(data.operations.find((row: Case) => row.id === "platform:deployments.create"));
}

function withDeployment(descriptor: PropertyDescriptor, run: () => void): void {
  const subject = runtime(deploymentCase(), () => { throw new Error("resolution must not request"); });
  const prototype = Object.getPrototypeOf(subject.client);
  const previous = Object.getOwnPropertyDescriptor(prototype, "deployments");
  Object.defineProperty(prototype, "deployments", { configurable: true, ...descriptor });
  try { run(); } finally {
    if (previous) Object.defineProperty(prototype, "deployments", previous);
    else delete prototype.deployments;
  }
}

for (const missing of [false, true]) {
  test(`unavailable registration is rejected with ${missing ? "missing" : "declared"} TypeScript path`, () => {
    const row = deploymentCase();
    if (missing) {
      delete row.wrappers[0].ts;
      row.wrappers[0].not_offered = { ts: missingTypeScript };
    }
    withDeployment({ value: { create: () => undefined } }, () => {
      const subject = runtime(row, () => { throw new Error("resolution must not request"); });
      expect(typeof methodAt(subject.client, "client.deployments.create").method).toBe("function");
      expect(() => assertUnavailable(row)).toThrow();
    });
  });
}

test("every unavailable wrapper is checked after TypeScript case conversion", () => {
  const row = deploymentCase();
  row.wrappers.push({ py: "client.deployments.wait_for_approval", not_offered: { ts: missingTypeScript } });
  withDeployment({ value: { waitForApproval: () => undefined } }, () => {
    expect(() => assertUnavailable(row)).toThrow();
  });
});

test("namespace accessor errors are not absence evidence", () => {
  withDeployment({ get: () => { throw new Error("broken namespace getter"); } }, () => {
    expect(() => assertUnavailable(deploymentCase())).toThrow("broken namespace getter");
  });
});

for (const value of [null, false, 0, "registered", {}]) {
  test(`non-callable registration ${JSON.stringify(value)} is not absence`, () => {
    withDeployment({ value: { create: value } }, () => {
      expect(() => assertUnavailable(deploymentCase())).toThrow();
    });
  });
}

test("missing both language paths fails closed", () => {
  const row = deploymentCase();
  delete row.wrappers[0].ts;
  delete row.wrappers[0].py;
  row.wrappers[0].not_offered = { ts: missingTypeScript };
  expect(() => assertUnavailable(row)).toThrow();
});

test("missing TypeScript spelling is derived for every wrapper without changing the inventory", () => {
  const row = deploymentCase();
  row.wrappers = [
    { py: "client.deployments.rotate_access_token", not_offered: { ts: missingTypeScript } },
    { py: "Deployment.wait_for_approval", not_offered: { ts: missingTypeScript } },
  ];
  const before = structuredClone(row);
  expect(unavailableTypeScriptPaths(row)).toEqual(["client.deployments.rotateAccessToken", "Deployment.waitForApproval"]);
  expect(row).toEqual(before);
});

for (const path of [undefined, null, "", "client", "client..create", "client.deployments.create()", "client.deployments.bad-name"]) {
  test(`invalid Python comparison path ${String(path)} fails closed`, () => {
    const row = deploymentCase();
    row.wrappers = [{ py: path, not_offered: { ts: missingTypeScript } }];
    expect(() => assertUnavailable(row)).toThrow();
  });
}

for (const path of [null, "", "client", "client..create", "client.deployments.create()"] ) {
  test(`invalid declared TypeScript path ${String(path)} fails closed`, () => {
    const row = deploymentCase();
    row.wrappers[0].ts = path;
    expect(() => assertUnavailable(row)).toThrow();
  });
}

test("a removed TypeScript twin requires an explicit declaration", () => {
  const row = deploymentCase();
  delete row.wrappers[0].ts;
  expect(() => assertUnavailable(row)).toThrow("valid language declaration");
});

test("an empty wrapper list is not absence evidence", () => {
  const row = deploymentCase();
  row.wrappers = [];
  expect(() => assertUnavailable(row)).toThrow("missing wrappers");
});

test("an absent derived TypeScript method resolves to undefined on a real client", () => {
  const row = deploymentCase();
  delete row.wrappers[0].ts;
  row.wrappers[0].not_offered = { ts: missingTypeScript };
  withDeployment({ value: {} }, () => expect(() => assertUnavailable(row)).not.toThrow());
});

test("missing handle fixtures cannot conceal a registered root factory", () => {
  const row = deploymentCase();
  row.wrappers = [{ py: "Deployment.wait_for_approval", not_offered: { ts: missingTypeScript } }];
  withDeployment({ value: { create: () => undefined } }, () => {
    expect(() => assertUnavailable(row)).toThrow();
  });
});

test("unknown handle roots fail closed rather than resolving against an empty fixture", () => {
  const row = deploymentCase();
  row.wrappers = [{ py: "Unknown.refresh", ts: "Unknown.refresh" }];
  expect(() => assertUnavailable(row)).toThrow("cannot resolve public handle absence");
});

test("explicit handle fixtures resolve the method value, not the root factory", () => {
  const row = deploymentCase();
  row.wrappers = [{ py: "Deployment.refresh", ts: "Deployment.refresh" }];
  const handles = { Deployment: { refresh: () => undefined } };
  expect(absenceCandidates(row, [], handles)).toEqual(["Deployment.refresh"]);
  expect(publicValueAt({}, "Deployment.refresh", handles)).toBe(handles.Deployment.refresh);
  expect(() => publicValueAt({}, "Deployment.refresh")).toThrow("public handle fixture required");
});

for (const row of data.operations.filter((r: Case) => data.public_cases.ts.includes(r.id) || r.public_absence)) {
  test(`real root resolves ${row.id}`, async () => {
    const subject = runtime(row, () => { throw new Error("resolution must not request"); });
    if (row.public_absence) {
      assertConsoleAbsent(row, subject);
      return;
    }
    await subject.prepare();
    expect(typeof methodAt(subject.client, publicPath(row), subject.handles).method).toBe("function");
  });
}
