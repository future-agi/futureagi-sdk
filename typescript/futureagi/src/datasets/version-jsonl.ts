import type {
  DatasetVersionCreate,
  DatasetVersionRead,
  DatasetVersionItemRead,
} from "../generated/openapi/types.gen";

export const VERSION_JSONL_MAX_BYTES = 10 * 1024 * 1024;
export const VERSION_JSONL_MAX_ITEMS = 10_000;
export type LegacyRowsPolicy = "reject" | "preserve" | "drop";

const caseFields = [
  "example_id",
  "external_id",
  "input",
  "expected",
  "metadata",
  "source_trace_id",
  "source_span_id",
  "content_hash",
  "legacy_row",
] as const;
const headerFields = [
  "format",
  "format_version",
  "dataset_id",
  "version_id",
  "parent_version",
  "description",
  "metadata",
  "source_revision",
  "content_hash",
  "item_count",
  "records_sha256",
] as const;
type Json = null | boolean | number | string | Json[] | { [key: string]: Json };
type ObjectRecord = Record<string, unknown>;

function fail(line: number, message: string): never {
  throw new Error(`JSONL line ${line}: ${message}`);
}

function validateJson(
  value: unknown,
  line: number,
  depth = 0,
): asserts value is Json {
  if (depth > 100) fail(line, "JSON nesting exceeds 100 levels");
  if (value === null || typeof value === "boolean") return;
  if (typeof value === "number") {
    if (
      !Number.isFinite(value) ||
      (Number.isInteger(value) && !Number.isSafeInteger(value))
    )
      fail(line, "number is not finite or safely representable");
    return;
  }
  if (typeof value === "string") {
    if (
      value.includes("\0") ||
      /[\uD800-\uDBFF](?![\uDC00-\uDFFF])|(?<![\uD800-\uDBFF])[\uDC00-\uDFFF]/u.test(
        value,
      )
    )
      fail(line, "invalid Unicode or null character");
    return;
  }
  if (Array.isArray(value)) {
    for (const child of value) validateJson(child, line, depth + 1);
    return;
  }
  if (
    typeof value === "object" &&
    (Object.getPrototypeOf(value) === Object.prototype ||
      Object.getPrototypeOf(value) === null)
  ) {
    for (const [key, child] of Object.entries(value)) {
      validateJson(key, line, depth + 1);
      validateJson(child, line, depth + 1);
    }
    return;
  }
  fail(line, "unsupported JSON value");
}

function object(value: unknown, line: number): asserts value is ObjectRecord {
  if (!value || typeof value !== "object" || Array.isArray(value))
    fail(line, "record must be an object");
}

function exact(
  value: ObjectRecord,
  fields: readonly string[],
  line: number,
): void {
  if (
    Object.keys(value).length !== fields.length ||
    fields.some((field) => !Object.prototype.hasOwnProperty.call(value, field))
  )
    fail(line, "missing or unknown fields");
}

function uuid(value: unknown, line: number): string {
  if (
    typeof value !== "string" ||
    !/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(
      value,
    )
  )
    fail(line, "identity must be a UUID string");
  return value.toLowerCase();
}

function text(value: unknown, line: number, maximum?: number): void {
  if (
    typeof value !== "string" ||
    (maximum !== undefined && [...value].length > maximum)
  )
    fail(line, "invalid or oversized text field");
}

function hash(value: unknown, line: number, allowBlank = true): void {
  if (allowBlank && value === "") return;
  if (typeof value !== "string" || !/^[0-9a-f]{64}$/.test(value))
    fail(line, "invalid SHA-256 fingerprint");
}

function validate(header: ObjectRecord, cases: ObjectRecord[]): void {
  exact(header, headerFields, 1);
  validateJson(header, 1);
  if (
    header.format !== "futureagi.dataset-version" ||
    header.format_version !== 1
  )
    fail(1, "unsupported format/version");
  if (
    header.item_count !== cases.length ||
    cases.length > VERSION_JSONL_MAX_ITEMS
  )
    fail(
      1,
      `item_count must match 0–${VERSION_JSONL_MAX_ITEMS} complete records`,
    );
  uuid(header.dataset_id, 1);
  uuid(header.version_id, 1);
  if (header.parent_version !== null) uuid(header.parent_version, 1);
  text(header.description, 1);
  text(header.source_revision, 1, 255);
  object(header.metadata, 1);
  hash(header.content_hash, 1);
  hash(header.records_sha256, 1, false);
  const examples = new Set<string>();
  const external = new Set<string>();
  for (const [index, item] of cases.entries()) {
    const line = index + 2;
    exact(item, caseFields, line);
    validateJson(item, line);
    const exampleId = uuid(item.example_id, line);
    if (examples.has(exampleId)) fail(line, "duplicate example_id");
    examples.add(exampleId);
    if (item.input === null) fail(line, "input must not be null");
    object(item.metadata, line);
    if (item.external_id !== null) text(item.external_id, line, 500);
    if (item.external_id) {
      const externalId = item.external_id as string;
      if (external.has(externalId)) fail(line, "duplicate external_id");
      external.add(externalId);
    }
    text(item.source_trace_id, line, 255);
    text(item.source_span_id, line, 255);
    if (item.legacy_row !== null) uuid(item.legacy_row, line);
    hash(item.content_hash, line);
  }
}

function stable(value: unknown): string {
  if (Array.isArray(value)) return `[${value.map(stable).join(",")}]`;
  if (value && typeof value === "object")
    return `{${Object.keys(value)
      .sort()
      .map(
        (key) =>
          `${JSON.stringify(key)}:${stable((value as ObjectRecord)[key])}`,
      )
      .join(",")}}`;
  return JSON.stringify(value);
}

async function sha256(value: Uint8Array): Promise<string> {
  const digest = await globalThis.crypto.subtle.digest(
    "SHA-256",
    value as BufferSource,
  );
  return [...new Uint8Array(digest)]
    .map((byte) => byte.toString(16).padStart(2, "0"))
    .join("");
}

export function caseRecordsSize(items: DatasetVersionItemRead[]): number {
  let total = 0;
  for (const [index, item] of items.entries()) {
    const record = Object.fromEntries(
      caseFields.map((field) => [field, item[field]]),
    );
    validateJson(record, index + 2);
    total += new TextEncoder().encode(`${stable(record)}\n`).byteLength;
    if (total > VERSION_JSONL_MAX_BYTES)
      fail(index + 2, `archive exceeds ${VERSION_JSONL_MAX_BYTES} bytes`);
  }
  return total;
}

export async function encodeVersionJsonl(
  version: DatasetVersionRead,
  items: DatasetVersionItemRead[],
): Promise<string> {
  if (!items.length) fail(1, "empty exports are not accepted");
  if (items.length > VERSION_JSONL_MAX_ITEMS)
    fail(1, `at most ${VERSION_JSONL_MAX_ITEMS} cases are supported`);
  const cases = items.map((item) =>
    Object.fromEntries(caseFields.map((field) => [field, item[field]])),
  );
  const header: ObjectRecord = {
    format: "futureagi.dataset-version",
    format_version: 1,
    dataset_id: version.dataset,
    version_id: version.id,
    parent_version: version.parent_version,
    description: version.description,
    metadata: version.metadata,
    source_revision: version.source_revision,
    content_hash: version.content_hash,
    item_count: version.item_count,
    records_sha256: "0".repeat(64),
  };
  validate(header, cases);
  cases.sort((left, right) =>
    uuid(left.example_id, 1) < uuid(right.example_id, 1) ? -1 : 1,
  );
  const records = cases.map((item) => `${stable(item)}\n`).join("");
  header.records_sha256 = await sha256(new TextEncoder().encode(records));
  const result = `${stable(header)}\n${records}`;
  if (new TextEncoder().encode(result).byteLength > VERSION_JSONL_MAX_BYTES)
    fail(1, `archive exceeds ${VERSION_JSONL_MAX_BYTES} bytes`);
  return result;
}

export async function decodeVersionJsonl(
  source: string | Uint8Array,
  datasetId: string,
  options: { parentVersionId?: string; legacyRows?: LegacyRowsPolicy } = {},
): Promise<DatasetVersionCreate> {
  const policy = options.legacyRows ?? "reject";
  if (!["reject", "preserve", "drop"].includes(policy))
    fail(1, "invalid legacyRows policy");
  if (typeof source === "string") validateJson(source, 1);
  const bytes =
    typeof source === "string" ? new TextEncoder().encode(source) : source;
  if (
    !(bytes instanceof Uint8Array) ||
    bytes.byteLength > VERSION_JSONL_MAX_BYTES
  )
    fail(
      1,
      `archive must be UTF-8 text/bytes at most ${VERSION_JSONL_MAX_BYTES} bytes`,
    );
  let decoded: string;
  try {
    decoded = new TextDecoder("utf-8", { fatal: true }).decode(bytes);
  } catch {
    fail(1, "invalid UTF-8");
  }
  if (!decoded.endsWith("\n")) fail(1, "archive must end with a newline");
  const lines = decoded.slice(0, -1).split("\n");
  if (lines.length < 2 || lines.length > VERSION_JSONL_MAX_ITEMS + 1)
    fail(1, `archive must contain 1–${VERSION_JSONL_MAX_ITEMS} cases`);
  const objects = lines.map((raw, index) => {
    let value: unknown;
    try {
      value = JSON.parse(raw);
    } catch {
      fail(index + 1, "invalid JSON");
    }
    object(value, index + 1);
    return value;
  });
  const [header, ...cases] = objects;
  validate(header, cases);
  if (!cases.length) fail(1, "empty imports are not accepted");
  const recordBytes = bytes.slice(bytes.indexOf(10) + 1);
  if ((await sha256(recordBytes)) !== header.records_sha256)
    fail(1, "case-record checksum mismatch");
  const target = uuid(datasetId, 1);
  if (options.parentVersionId !== undefined) uuid(options.parentVersionId, 1);
  const items = cases.map((item, index) => {
    const result = Object.fromEntries(
      caseFields
        .filter((field) => field !== "content_hash" && field !== "legacy_row")
        .map((field) => [field, item[field]]),
    );
    if (item.legacy_row !== null) {
      if (
        policy === "reject" ||
        (policy === "preserve" && uuid(header.dataset_id, 1) !== target)
      )
        fail(
          index + 2,
          "legacy_row requires explicit same-dataset preserve or drop",
        );
      if (policy === "preserve") result.legacy_row_id = item.legacy_row;
    }
    return result;
  });
  const payload = {
    items,
    description: header.description,
    metadata: header.metadata,
    source_revision: header.source_revision,
    ...(options.parentVersionId
      ? { parent_version_id: options.parentVersionId }
      : {}),
  };
  if (
    new TextEncoder().encode(stable(payload)).byteLength >
    VERSION_JSONL_MAX_BYTES
  )
    fail(1, "snapshot request exceeds byte limit");
  return payload as DatasetVersionCreate;
}
