/** Run with FI_API_KEY, FI_SECRET_KEY, FI_BASE_URL, DATASET_ID and METRIC_ID.
 * The metric must describe output === expected. This example calls no model.
 * Each invocation creates one snapshot and two external runs.
 */
import { writeFileSync } from "node:fs";
import { randomUUID } from "node:crypto";

import { FutureAGIClient } from "../src/futureagi-client";

async function main() {
  const datasetId = process.env.DATASET_ID!;
  const metricId = process.env.METRIC_ID!.toLowerCase();
  const client = new FutureAGIClient();
  const created = await client.datasets.versions.create(datasetId, {
    description: "SDK external workflow example",
    items: [
      { external_id: "shipping", input: { topic: "shipping" }, expected: 5 },
      { external_id: "returns", input: { topic: "returns" }, expected: 30 },
    ],
  });
  const versionId = created.result.id;
  if (!versionId) throw new Error("Creation returned no version ID");
  const detail = await client.datasets.versions.get(datasetId, versionId);
  const cases = detail.result.items;
  if (cases.length !== 2) throw new Error("Expected two cases");
  await client.datasets.versions.list(datasetId, { limit: 1 });
  const runs: Record<string, string> = {};
  const configurations = [
    ["baseline", { shipping: 5, returns: 14 }],
    ["candidate", { shipping: 3, returns: 30 }],
  ] as const;
  for (const [label, policy] of configurations) {
    const identities = cases.map((item) => {
      if (!item.example_id) throw new Error("Snapshot has no example ID");
      return { example_id: item.example_id, trial_number: 1 };
    });
    const body = {
      run_id: randomUUID(),
      dataset_version_id: versionId,
      expected_items: identities,
      evaluator_metric_ids: [metricId],
      model_config: policy,
      metadata: { name: label, task_revision: "sdk-example-v1" },
    };
    const run = (await client.experimentRuns.create(body)).result;
    const replay = (await client.experimentRuns.create(body)).result;
    if (replay.id !== run.id)
      throw new Error("Run creation replay changed identity");
    const binding = run.evaluator_bindings.find(
      (item) => item.metric_id === metricId,
    );
    if (!binding) throw new Error("Missing evaluator pin");
    const results = cases.map((item, index) => {
      // Replace this caller-owned retrieval/tool task with your agent.
      const topic = item.external_id;
      if (topic !== "shipping" && topic !== "returns")
        throw new Error("Unknown topic");
      const document = { days: policy[topic] };
      const output = Number(document.days);
      return {
        ...identities[index],
        receipt_key: randomUUID(),
        status: "completed" as const,
        output,
        score_refs: [
          {
            metric_id: metricId,
            evaluator_version_id: binding.evaluator_version_id,
            status: "assessed" as const,
            value: Number(output === item.expected),
          },
        ],
      };
    });
    const first = await client.experimentRuns.ingestResults(run.id, {
      items: results,
    });
    const repeated = await client.experimentRuns.ingestResults(run.id, {
      items: results,
    });
    if (JSON.stringify(first) !== JSON.stringify(repeated))
      throw new Error("Result replay changed evidence");
    runs[label] = run.id;
  }
  const comparison = await client.experimentRuns.compare({
    baseline_run_id: runs.baseline,
    candidate_run_id: runs.candidate,
    metric_id: metricId,
    passing_score: 1,
  });
  const summary = comparison.result.comparison;
  if (
    summary.baseline.score_average !== 0.5 ||
    summary.candidate.score_average !== 0.5 ||
    summary.status_counts.regressed !== 1 ||
    summary.status_counts.improved !== 1
  ) {
    throw new Error("Unexpected comparison outcomes");
  }
  writeFileSync(
    "sdk-comparison-ts.json",
    JSON.stringify(comparison, null, 2) + "\n",
  );
  console.log(
    "TypeScript SDK: equal means 0.5; improved=1, regressed=1; replay unchanged",
  );
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
