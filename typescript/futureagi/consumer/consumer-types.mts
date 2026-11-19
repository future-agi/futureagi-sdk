// What a user's project sees: compiled against the *packed* package (scripts/check-consumer.sh),
// not against this repository's sources. An internal build can pass while a public call does not
// type-check; this file holds the calls that must. Nothing here runs: `declare const c`.
//
// Each block names the review finding it guards (nik13, PR #35, 2026-11-03).

import { Client } from "@future-agi/sdk";
import type { Auth, JsonValue, RequestOptions } from "@future-agi/sdk/platform";
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

// The escape hatches keep their types.
await c.request("GET", "/x/", { unwrap: null });
for await (const prompt of c.prompts.list({}, { extraQuery: { team: "x" } })) {
  prompt.name;
}

// Exclusive auth and continuation options survive package export/declaration generation.
const contextAuth: Auth = { type: "context", credential: "synthetic-context" };
const context = new Client({ auth: contextAuth, workspaceId: "workspace-1" });
const options: RequestOptions = { resolutionId: "lease", idempotencyKey: "operation" };
await context.request("GET", "/fixture/download/", { decode: "bytes" }, options);
new Client({ auth: { type: "api_key", apiKey: "key", secretKey: "secret" } });
// @ts-expect-error Mixed authentication must be rejected for package consumers.
new Client({ auth: contextAuth, apiKey: "broad", secretKey: "broad" });
// @ts-expect-error A Context credential cannot include paired keys.
const mixed: Auth = { type: "context", credential: "synthetic", apiKey: "broad", secretKey: "broad" };

// Public snapshot subpaths must carry usable declarations in the packed package.
import { ContextClient, type VerifiedSnapshot, type SnapshotSource } from "@future-agi/sdk/context";
import { SkillsClient } from "@future-agi/sdk/skills";
import { ContextClient as RootContextClient, SkillsClient as RootSkillsClient } from "@future-agi/sdk";
const snapshots = new ContextClient(context);
const snapshot = await snapshots.resolve("team-policy", { label: "production" });
const verified: VerifiedSnapshot = await snapshot.readAll();
const text: string = await snapshot.readFile("AGENTS.md");
const sourceText: string | undefined = verified.files["AGENTS.md"];
declare const leafSource: SnapshotSource;
const leaf = await new SkillsClient(leafSource).resolve("refund", { version: 2 });
await leaf.readFile("SKILL.md");
new RootContextClient(context);
new RootSkillsClient(leafSource);
const onlineSkills = new SkillsClient(context);
const onlineLeaf = await onlineSkills.resolve("refund", { version: 2 });
await onlineSkills.checkAccess(onlineLeaf.identity, onlineLeaf.manifest.lease);
await snapshots.checkAccess(snapshot.identity, snapshot.manifest.lease);
await context.contexts.readFile("resource-id", 7, {path: "AGENTS.md", resolution_id: "lease"});
await context.skillConsumption.manifest("resource-id", 7, {resolution_id: "lease", file_offset: 25});
await c.contextCredentials.issue({purpose: "consume", grants: [{kind: "skill", resource_id: "resource-id", labels: ["production"], version_ids: []}], binding_ids: [], expires_at: "2026-12-01T00:00:00Z", idempotency_key: "operation-id"});
// @ts-expect-error A selector is exclusive, not both label and version.
await snapshots.resolve("team-policy", { label: "production", version: 2 });

export { templateId, mixed, text, sourceText };
