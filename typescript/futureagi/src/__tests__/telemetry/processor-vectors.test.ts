import { readFileSync } from "node:fs";
import { join } from "node:path";
import { ROOT_CONTEXT } from "@opentelemetry/api";
import type { Span } from "@opentelemetry/api";
import { FutureAGISkillsSpanProcessor } from "../../telemetry/processor";
import { CARRIER_KEY, configure, REGISTRY_KEY } from "../../telemetry/otel";
import { ScopeState, TraceRegistry } from "../../telemetry/registry";

type Vector = { name: string; carrier: unknown; registry: Record<string, unknown>; explicit: Record<string, unknown>; expected: Record<string, unknown> };
const vectors = JSON.parse(readFileSync(join(__dirname, "vectors/processor_v1.json"), "utf8")) as { vectors: Vector[] };
const globals = globalThis as unknown as Record<symbol, unknown>;
afterEach(() => { delete globals[REGISTRY_KEY]; configure(); });

it.each(vectors.vectors)("$name", vector => {
  configure({ skillsTracing: "on" });
  globals[REGISTRY_KEY] = { v: 1, get: () => vector.registry };
  const attributes = { ...vector.explicit };
  const span = { attributes, spanContext: () => ({ traceId: "trace" }), setAttribute: (key: string, value: unknown) => { attributes[key] = value; } } as unknown as Span & { attributes: Record<string, unknown> };
  new FutureAGISkillsSpanProcessor().onStart(span, vector.carrier === null ? ROOT_CONTEXT : ROOT_CONTEXT.setValue(CARRIER_KEY, vector.carrier));
  expect(attributes).toEqual(vector.expected);
});

it("is bounded by LRU capacity and absolute TTL without timers", () => {
  let now = 0;
  const registry = new TraceRegistry(2, 10, () => now);
  registry.state("a", true);
  registry.state("b", true);
  registry.get("a");
  registry.state("c", true);
  expect(registry.get("b")).toBeUndefined();
  expect(registry.size).toBe(2);
  now = 9;
  expect(registry.get("a")).toBeDefined();
  now = 10;
  expect(registry.get("a")).toBeUndefined();
});

it("caps aligned skill lists at 32, preserves order and stronger evidence", () => {
  const state = new ScopeState();
  for (let n = 0; n < 40; n++) state.addSkill({ "fi.skill.version_id": `v${n}`, "fi.skill.id": `s${n}`, "fi.skill.name": `name${n}`, "fi.skill.version": 1 });
  state.addSkill({ "fi.skill.version_id": "v0" });
  expect(state.attrs["fi.skills.count"]).toBe(32);
  expect(state.attrs["fi.skills.version_ids"]).toHaveLength(32);
  expect(state.attrs["fi.skills.ids"]).toHaveLength(32);
  expect(state.attrs["fi.skills.refs"]).toHaveLength(32);
  expect(state.attrs["fi.skills.truncated"]).toBe(true);
  expect(Object.isFrozen(state.attrs)).toBe(true);
});

it.each(["off", "load_only"] as const)("does no processor work in %s mode", mode => {
  configure({ skillsTracing: mode });
  const setAttribute = jest.fn();
  new FutureAGISkillsSpanProcessor().onStart({ setAttribute } as unknown as Span, ROOT_CONTEXT);
  expect(setAttribute).not.toHaveBeenCalled();
});
