import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import * as root from "../index";
import * as facade from "../futureagi-client";
import * as generated from "../generated/openapi/sdk.gen";

const classes = [
  "SimulationsClient", "SimulationAgentDefinitionsClient", "SimulationRunTestsClient",
  "SimulationTestExecutionsClient", "SimulationPersonasClient", "SimulationScenariosClient",
];
const namespaces = ["agentDefinitions", "runTests", "testExecutions", "personas", "scenarios"];
const makeClient = () => new root.FutureAGIClient({
  apiKey: "fixture-api", secretKey: "fixture-secret", baseUrl: "http://localhost:9031",
});

describe("simulation withdrawal", () => {
  it("does not expose the namespace or any of its five children, including on clones", () => {
    const original = makeClient();
    for (const client of [original, original.withOptions({ timeoutMs: 2 })]) {
      expect("simulations" in client).toBe(false);
      for (const name of namespaces) {
        expect(name in client).toBe(false);
        expect((client as unknown as Record<string, unknown>)["simulations"]).toBeUndefined();
      }
    }
  });

  it("preserves the other namespace names", () => {
    const original = makeClient();
    for (const client of [original, original.withOptions({ timeoutMs: 2 })]) {
      const properties = Object.entries(Object.getOwnPropertyDescriptors(Object.getPrototypeOf(client)))
        .filter(([, descriptor]) => descriptor.get).map(([name]) => name);
      const internal = new Set(["generated", "generatedClient", "platformShared", "platformCore", "managementShared", "managementCore"]);
      const names = [...new Set([...Object.keys(client), ...properties])]
        .filter(name => !name.startsWith("_") && !internal.has(name)).sort();
      expect(names).toEqual([
        "agents", "alerts", "annotationLabels", "annotationQueues", "connectors", "credentials",
        "datasets", "environments", "evals", "experimentRuns", "experiments", "experimentsV2",
        "gateway", "integrations", "knowledgeBases", "models", "optimizations", "prompts",
        "scores", "tracing", "users", "workspaces",
      ].sort());
    }
  });

  it.each(classes)("does not export %s from the root or facade", name => {
    expect(root).not.toHaveProperty(name);
    expect(facade).not.toHaveProperty(name);
  });

  it("does not expose simulation operations through the generated escape hatch", () => {
    const withdrawn = /simulat|runTest|testExecution|persona|scenario|agentDefinition/i;
    expect(Object.keys(generated).filter(name => withdrawn.test(name))).toEqual([]);
    expect(Object.keys(makeClient().generated).filter(name => withdrawn.test(name))).toEqual([]);
    const source = readFileSync(resolve(__dirname, "../generated/openapi/sdk.gen.ts"), "utf8");
    expect(source).not.toContain("/simulate/");
    expect(source).not.toContain("/sdk/api/v1/simulation/");
  });

  it("has no simulation package subpath or type-resolution entry", () => {
    const pkg = JSON.parse(readFileSync(resolve(__dirname, "../../package.json"), "utf8"));
    const entries = [...Object.keys(pkg.exports), ...Object.keys(pkg.typesVersions["*"])];
    expect(entries.some(name => /simulat|scenario|persona|run.tests|agent.definitions/i.test(name))).toBe(false);
    expect(entries.some(name => name.includes("*"))).toBe(false);
  });
});
