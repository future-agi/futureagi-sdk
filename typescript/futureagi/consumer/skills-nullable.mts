// Compile against the packed declarations, not the source tree.
import { Client } from "@future-agi/sdk";
import type { LatestLoadResult, SkillsContextDetail, SkillsContextOwnDraft } from "@future-agi/sdk/platform/models";

const empty: LatestLoadResult = { load: null, fetch: null };
const context: Pick<SkillsContextDetail, "own_draft" | "latest"> = { own_draft: null, latest: null };
declare const populated: LatestLoadResult;
const version: number | null | undefined = populated.load?.version;
const draft: SkillsContextOwnDraft | null = context.own_draft;
// @ts-expect-error A null result is not the same as omitting the key.
const missingLoad: LatestLoadResult = { fetch: null };
// @ts-expect-error An unrelated scalar is not a nested fetch result.
const wrongFetch: LatestLoadResult = { load: null, fetch: "unknown" };
// @ts-expect-error Both detail properties must be present.
const missingLatest: typeof context = { own_draft: null };
declare const sdk: Client;
const latest = sdk.skills.latestLoad({resource_id: "id", kind: "skill", since: "2026-01-01T00:00:00Z"});
latest.then(value => {
  const tolerant: unknown = value;
  // @ts-expect-error Tolerant decoding may return any wire shape.
  value.fetch;
  return tolerant;
});
const strictLatest = sdk.skills.latestLoad(
  {resource_id: "id", kind: "skill", since: "2026-01-01T00:00:00Z"},
  {strictResponse: true},
);
strictLatest.then(value => {
  const fetch: LatestLoadResult["fetch"] = value.fetch;
  return fetch;
});
const detail = sdk.contexts.get("context-id");
detail.then(value => {
  const tolerant: unknown = value;
  // @ts-expect-error Tolerant decoding may return any wire shape.
  value.context;
  return tolerant;
});
const strictDetail = sdk.contexts.get("context-id", {strictResponse: true});
strictDetail.then(value => {
  const typed: SkillsContextDetail["context"] = value.context;
  return typed;
});
void [empty, version, draft, missingLoad, wrongFetch, missingLatest];
