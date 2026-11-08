// A historical review can cover only the exact comparison rules retained with it.
import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import { join } from "node:path";

const records = JSON.parse(readFileSync(join(__dirname, "../../../../../tests/fixtures/gateway/review-records.json"), "utf8")).entries as Record<string, { reviewer: unknown; contract_sha256: string }>;

function canonical(value: unknown): string {
  if (Array.isArray(value)) return `[${value.map(canonical).join(",")}]`;
  if (value && typeof value === "object") {
    const object = value as Record<string, unknown>;
    return `{${Object.keys(object).sort().map((key) => `${JSON.stringify(key)}:${canonical(object[key])}`).join(",")}}`;
  }
  return JSON.stringify(value);
}

export function assertRetainedReview(entry: { id: string; lang: string; status: string; applies_to: string[]; match: unknown[]; reviewer: unknown }): void {
  const retained = records[entry.id];
  if (!retained || canonical(entry.reviewer) !== canonical(retained.reviewer)) throw new Error("review differs from retained record");
  const { id, lang, status, applies_to, match } = entry;
  const digest = createHash("sha256").update(canonical({ id, lang, status, applies_to, match })).digest("hex");
  if (digest !== retained.contract_sha256) throw new Error("reviewed comparison rules changed");
}
