// What a user's project sees: compiled against the *packed* package (scripts/check-consumer.sh),
// not against this repository's sources. An internal build can pass while a public call does not
// type-check; this file holds the calls that must. Nothing here runs: `declare const c`.
//
// Each block names the review finding it guards (nik13, PR #35, 2026-11-03).

import { Client } from "@future-agi/sdk";
import type { JsonValue, WaitOptions } from "@future-agi/sdk/platform";
import { WaitTimeoutError, openQuestion } from "@future-agi/sdk/platform";
import type { DashboardDetail, KnowledgeBaseItem, PromptsRunResult } from "@future-agi/sdk/platform/models";

declare const c: Client;

// JSON-value inputs take a string, a boolean or a number as much as an object.
await c.prompts.run("p1", { version: "v1", is_run: "prompt" });
await c.prompts.run("p1", { version: "v1", is_run: false });
await c.scores.create({ source_type: "dataset_row", source_id: "r1", label_id: "l1", value: 0.7 });
const anyJson: JsonValue = { nested: [1, "two", null, { three: true }] };
await c.prompts.run("p1", { version: "v1", placeholders: anyJson });

// A PATCH is a partial update: a description-only dashboard update compiles.
await c.dashboards.update("d1", { description: "description only" });

// A create answers with the detail, so the returned identifier feeds the next call.
const receipt: PromptsRunResult = await c.prompts.run("p1", { version: "v1" });
const templateId: string | null | undefined = receipt.template_id;
const dashboard: DashboardDetail = await c.dashboards.create({ name: "review" });
await c.dashboards.get(dashboard.id!);
const kb: KnowledgeBaseItem = await c.knowledgeBases.create({ name: "k", chunk_size: 256 });
await c.knowledgeBases.get(kb.id!);
await c.knowledgeBases.delete(kb.id!);

// The simulation wait helpers and their exported types.
const waitFast: WaitOptions = { pollIntervalMs: 10, timeoutMs: 1000 };
const built = await c.simulation.waitForJob("j1", waitFast);
const question: Record<string, unknown> | null = openQuestion(built);
const run: { job: Record<string, unknown>; executionStatus: string | null } = await c.simulation.waitForRun("j1", { testExecutionId: "te1" });
const timedOut: Error = new WaitTimeoutError("job j1", 1000);
await c.simulation.jobs.uploadSources({ files: [{ name: "a.py", data: "a" }], paths: ["a.py"] });
export { question, run, timedOut };

// The escape hatches keep their types.
await c.request("GET", "/x/", { unwrap: null });
for await (const prompt of c.prompts.list({}, { extraQuery: { team: "x" } })) {
  prompt.name;
}

export { templateId };
