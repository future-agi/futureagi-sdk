// Compile against the packed declarations, not the source tree.
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
void [empty, version, draft, missingLoad, wrongFetch, missingLatest];
