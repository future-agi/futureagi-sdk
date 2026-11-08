import { createHash } from "node:crypto";
import type {
  FileMetadata,
  ResolutionLease,
  Selector,
  SnapshotIdentity,
  SnapshotKind,
  SnapshotManifest,
  SnapshotSource,
} from "./types";

export const CHUNK_BYTES = 32768;
export const PAGE_SIZE = 25;
const MAX_FILES = 200;
const MAX_FILE_BYTES = 512 * 1024;
const MAX_BUNDLE_BYTES = 2 * 1024 * 1024;

export class SnapshotIntegrityError extends Error {}
export class ResolutionExpiredError extends Error {}
function invalid(message: string): never {
  throw new SnapshotIntegrityError(message);
}
function object(value: unknown): Record<string, unknown> {
  if (value === null || typeof value !== "object" || Array.isArray(value))
    return invalid("Expected a JSON object");
  return value as Record<string, unknown>;
}
function string(value: unknown, name: string): string {
  if (typeof value !== "string" || !value) return invalid(`Invalid ${name}`);
  return value;
}
function integer(
  value: unknown,
  name: string,
  min: number,
  max: number,
): number {
  if (
    typeof value !== "number" ||
    !Number.isSafeInteger(value) ||
    value < min ||
    value > max
  )
    return invalid(`Invalid ${name}`);
  return value;
}
function uuid(value: unknown): string {
  const result = string(value, "UUID");
  if (
    !/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/.test(
      result,
    )
  )
    return invalid("Invalid UUID");
  return result;
}
function hash(value: unknown, digest = false): string {
  const result = string(value, "SHA-256 identity");
  if (!(digest ? /^sha256:[0-9a-f]{64}$/ : /^[0-9a-f]{64}$/).test(result))
    return invalid("Invalid SHA-256 identity");
  return result;
}
export function validatePath(value: unknown): string {
  const path = string(value, "path");
  const parts = path.split("/");
  if (
    Array.from(path).length > 255 ||
    parts.length > 8 ||
    /[\\:\x00-\x1f\x7f]/.test(path) ||
    Array.from(path).some(
      (char) =>
        char.codePointAt(0)! >= 0xd800 && char.codePointAt(0)! <= 0xdfff,
    ) ||
    parts.some(
      (part) => !part || part === "." || part === ".." || /[ .]$/.test(part),
    )
  )
    return invalid("Unsafe snapshot path");
  return path;
}
function utf8(text: string): Buffer {
  // Buffer.from otherwise replaces unpaired surrogates, hiding wire corruption.
  for (const char of Array.from(text)) {
    const code = char.codePointAt(0)!;
    if (
      (code >= 0xd800 && code <= 0xdfff) ||
      (code < 32 && !"\t\r\n".includes(char)) ||
      code === 127
    )
      return invalid("Non-text snapshot content");
  }
  return Buffer.from(text, "utf8");
}
function sha256(text: string): string {
  return createHash("sha256").update(utf8(text)).digest("hex");
}
export function parseSelector(raw: unknown): Selector {
  const value = object(raw);
  if (Object.keys(value).length !== 1)
    return invalid("Expected exactly one selector");
  if ("version" in value)
    return Object.freeze({
      version: integer(
        value.version,
        "selector version",
        1,
        Number.MAX_SAFE_INTEGER,
      ),
    });
  if (
    "label" in value &&
    typeof value.label === "string" &&
    /^[a-z0-9][a-z0-9-]{0,39}$/.test(value.label)
  )
    return Object.freeze({ label: value.label });
  return invalid("Invalid selector");
}
function identity(
  value: Record<string, unknown>,
  kind: SnapshotKind,
): SnapshotIdentity {
  const name = string(value.name, "name");
  if (name.length > 64 || !/^[a-z0-9]+(-[a-z0-9]+)*$/.test(name))
    return invalid("Invalid snapshot name");
  if (
    kind === "agent_context" &&
    (value.entrypoint !== "AGENTS.md" ||
      value.descriptor_path !== ".futureagi/context.json")
  )
    return invalid("Invalid context entrypoint");
  return Object.freeze({
    kind,
    resourceId: uuid(
      value[kind === "agent_context" ? "context_id" : "skill_id"],
    ),
    name,
    version: integer(value.version, "version", 1, Number.MAX_SAFE_INTEGER),
    versionId: uuid(value.version_id),
    digest: hash(value.digest, true),
  });
}
function lease(value: Record<string, unknown>): ResolutionLease {
  const resolutionId = string(value.resolution_id, "resolution ID");
  const resolutionExpiresAt = string(
    value.resolution_expires_at,
    "resolution expiry",
  );
  if (resolutionId.length > 4096 || /[^\x21-\x7e]/.test(resolutionId))
    return invalid("Invalid resolution ID");
  if (
    !/^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d+)?(?:Z|[+-]\d\d:\d\d)$/.test(
      resolutionExpiresAt,
    ) ||
    !Number.isFinite(Date.parse(resolutionExpiresAt))
  )
    return invalid("Invalid resolution expiry");
  return Object.freeze({ resolutionId, resolutionExpiresAt });
}
export function requireLive(value: ResolutionLease): void {
  if (Date.now() >= Date.parse(value.resolutionExpiresAt))
    throw new ResolutionExpiredError(
      "Resolution expired; explicitly resolve and replan",
    );
}
function file(raw: unknown): FileMetadata {
  const value = object(raw);
  return Object.freeze({
    path: validatePath(value.path),
    sha256: hash(value.sha256),
    sizeBytes: integer(value.size_bytes, "file size", 0, MAX_FILE_BYTES),
  });
}
function codepointOrder(a: string, b: string): number {
  const left = Array.from(a, (char) => char.codePointAt(0)!);
  const right = Array.from(b, (char) => char.codePointAt(0)!);
  for (let i = 0; i < Math.min(left.length, right.length); i++)
    if (left[i] !== right[i]) return left[i] - right[i];
  return left.length - right.length;
}
export function manifestDigest(files: readonly FileMetadata[]): string {
  const pairs = [...files]
    .sort((a, b) => codepointOrder(a.path, b.path))
    .map((item) => [item.path, item.sha256]);
  // Match Python json.dumps(ensure_ascii=True), including UTF-16 surrogate pairs.
  const ascii = JSON.stringify(pairs).replace(
    /[\u007f-\uffff]/g,
    (char) => `\\u${char.charCodeAt(0).toString(16).padStart(4, "0")}`,
  );
  return `sha256:${createHash("sha256").update(ascii, "utf8").digest("hex")}`;
}
function sameIdentity(a: SnapshotIdentity, b: SnapshotIdentity): boolean {
  return JSON.stringify(a) === JSON.stringify(b);
}

export class ManifestCollector {
  readonly identity: SnapshotIdentity;
  readonly requested: Selector;
  readonly lease: ResolutionLease;
  readonly count: number;
  private files: FileMetadata[] = [];
  nextOffset: number | null = 0;

  constructor(raw: unknown, kind: SnapshotKind) {
    const first = object(raw);
    this.identity = identity(first, kind);
    this.requested = parseSelector(first.requested);
    this.lease = lease(first);
    this.count = integer(first.file_count, "file count", 1, MAX_FILES);
    this.add(first);
  }
  add(raw: unknown): void {
    const page = object(raw);
    if (this.nextOffset === null)
      return invalid("Unexpected manifest continuation");
    if (!sameIdentity(identity(page, this.identity.kind), this.identity))
      return invalid("Manifest identity changed during continuation");
    if (integer(page.file_count, "file count", 1, MAX_FILES) !== this.count)
      return invalid("Manifest count changed during continuation");
    if (
      integer(page.file_offset, "file offset", 0, MAX_FILES) !== this.nextOffset
    )
      return invalid("Noncontiguous manifest page");
    if ("resolution_id" in page || "resolution_expires_at" in page) {
      const nextLease = lease(page);
      if (
        nextLease.resolutionId !== this.lease.resolutionId ||
        Date.parse(nextLease.resolutionExpiresAt) !==
          Date.parse(this.lease.resolutionExpiresAt)
      )
        return invalid("Resolution lease changed during continuation");
    }
    if (
      !Array.isArray(page.files) ||
      page.files.length < 1 ||
      page.files.length > PAGE_SIZE
    )
      return invalid("Invalid manifest page length");
    this.files.push(...page.files.map(file));
    if (this.files.length > this.count)
      return invalid("Manifest exceeds declared inventory");
    const expected = this.files.length < this.count ? this.files.length : null;
    if (page.next_file_offset !== expected)
      return invalid("Incomplete or looping manifest continuation");
    this.nextOffset = expected;
  }
  finish(): SnapshotManifest {
    if (this.nextOffset !== null || this.files.length !== this.count)
      return invalid("Incomplete manifest");
    const paths = this.files.map((item) => item.path.toLowerCase());
    const pathSet = new Set(paths);
    if (pathSet.size !== paths.length)
      return invalid("Duplicate or case-colliding snapshot paths");
    for (const path of paths) {
      const parts = path.split("/");
      for (let i = 1; i < parts.length; i++)
        if (pathSet.has(parts.slice(0, i).join("/")))
          return invalid("File/directory prefix collision");
    }
    if (
      this.files.reduce((sum, item) => sum + item.sizeBytes, 0) >
      MAX_BUNDLE_BYTES
    )
      return invalid("Snapshot exceeds byte budget");
    const root =
      this.identity.kind === "agent_context" ? "AGENTS.md" : "SKILL.md";
    if (!this.files.some((item) => item.path === root && item.sizeBytes > 0))
      return invalid("Snapshot root is missing or empty");
    if (
      this.identity.kind === "agent_context" &&
      !this.files.some((item) => item.path === ".futureagi/context.json")
    )
      return invalid("Context descriptor is missing");
    if (manifestDigest(this.files) !== this.identity.digest)
      return invalid("Full manifest digest mismatch");
    requireLive(this.lease);
    return Object.freeze({
      identity: this.identity,
      requested: this.requested,
      lease: this.lease,
      files: Object.freeze([...this.files]),
    });
  }
}

export class ChunkCollector {
  readonly file: FileMetadata;
  offset = 0;
  eof = false;
  private totalChars?: number;
  private receivedBytes = 0;
  private parts: string[] = [];
  constructor(
    private readonly manifest: SnapshotManifest,
    path: string,
  ) {
    const found = manifest.files.find((item) => item.path === path);
    if (!found)
      throw new SnapshotIntegrityError(
        "Path is not in this immutable snapshot",
      );
    this.file = found;
  }
  add(raw: unknown): void {
    const value = object(raw);
    if (this.eof) return invalid("Unexpected chunk after EOF");
    if (
      value.path !== this.file.path ||
      value.sha256 !== this.file.sha256 ||
      value.size_bytes !== this.file.sizeBytes
    )
      return invalid("File identity changed during continuation");
    const id = this.manifest.identity;
    const identities = {
      [id.kind === "agent_context" ? "context_id" : "skill_id"]: id.resourceId,
      version_id: id.versionId,
      digest: id.digest,
    };
    if (
      Object.entries(identities).some(
        ([key, expected]) =>
          (id.kind === "agent_context" || key in value) &&
          value[key] !== expected,
      )
    )
      return invalid("Chunk belongs to another snapshot");
    if (
      integer(value.offset, "chunk offset", 0, MAX_FILE_BYTES) !== this.offset
    )
      return invalid("Noncontiguous chunk");
    const total = integer(
      value.total_chars,
      "character count",
      0,
      this.file.sizeBytes,
    );
    if (this.totalChars !== undefined && this.totalChars !== total)
      return invalid("File character count changed");
    this.totalChars = total;
    if (typeof value.text !== "string") return invalid("Missing chunk text");
    const encoded = utf8(value.text);
    const end = this.offset + Array.from(value.text).length;
    if (encoded.length > CHUNK_BYTES || end > total)
      return invalid("Chunk exceeds declared bounds");
    this.receivedBytes += encoded.length;
    if (this.receivedBytes > this.file.sizeBytes)
      return invalid("File exceeds declared size");
    if (typeof value.eof !== "boolean" || value.eof !== (end === total))
      return invalid("Invalid EOF marker");
    if (value.next_offset !== (value.eof ? null : end))
      return invalid("Invalid chunk continuation");
    if (!value.eof && !value.text) return invalid("Chunk made no progress");
    if (!value.eof && encoded.length < CHUNK_BYTES - 3)
      return invalid("Nonfinal chunk is not the maximal UTF-8 prefix");
    this.parts.push(value.text);
    this.offset = end;
    this.eof = value.eof;
  }
  finish(): string {
    if (!this.eof) return invalid("Incomplete file");
    const text = this.parts.join("");
    if (
      this.receivedBytes !== this.file.sizeBytes ||
      sha256(text) !== this.file.sha256
    )
      return invalid("File checksum mismatch");
    requireLive(this.manifest.lease);
    return text;
  }
}

function canonical(value: unknown): string {
  if (Array.isArray(value)) return `[${value.map(canonical).join(",")}]`;
  if (value !== null && typeof value === "object")
    return `{${Object.keys(value)
      .sort(codepointOrder)
      .map(
        (key) =>
          `${JSON.stringify(key)}:${canonical((value as Record<string, unknown>)[key])}`,
      )
      .join(",")}}`;
  return JSON.stringify(value);
}
function validateDescriptor(
  files: Readonly<Record<string, string>>,
  id: SnapshotIdentity,
): void {
  const text = files[".futureagi/context.json"];
  let parsed: unknown;
  try {
    parsed = JSON.parse(text);
  } catch {
    return invalid("Invalid context descriptor");
  }
  const descriptor = object(parsed);
  if (canonical(descriptor) !== text || descriptor.schema !== 1)
    return invalid("Noncanonical context descriptor");
  if (
    descriptor.kind !== "agent_context" ||
    descriptor.name !== id.name ||
    descriptor.entrypoint !== "AGENTS.md"
  )
    return invalid("Context descriptor identity mismatch");
  const owned = descriptor.owned_paths;
  const links = descriptor.links;
  if (!Array.isArray(owned) || !Array.isArray(links) || links.length > 20)
    return invalid("Invalid descriptor inventory");
  if (
    !owned.every((path) => typeof path === "string") ||
    JSON.stringify(owned) !==
      JSON.stringify([...new Set(owned)].sort(codepointOrder)) ||
    !owned.includes("AGENTS.md")
  )
    return invalid("Invalid owned paths");
  const covered = new Set([".futureagi/context.json"]);
  for (const rawPath of owned) {
    const path = validatePath(rawPath);
    if (
      /^(skills|\.futureagi)\//.test(path) ||
      !Object.prototype.hasOwnProperty.call(files, path)
    )
      return invalid("Invalid owned path");
    covered.add(path);
  }
  const mounts: string[] = [];
  const childIds = new Set<string>();
  for (const raw of links) {
    const link = object(raw);
    const mount = string(link.mount, "child mount");
    if (!/^skills\/[a-z0-9]+(?:-[a-z0-9]+)*\/$/.test(mount))
      return invalid("Invalid child mount");
    const childId = uuid(link.skill_id);
    uuid(link.version_id);
    integer(link.version, "child version", 1, Number.MAX_SAFE_INTEGER);
    parseSelector(link.requested);
    if (
      childIds.has(childId) ||
      mounts.includes(mount) ||
      !Object.prototype.hasOwnProperty.call(files, `${mount}SKILL.md`)
    )
      return invalid("Invalid linked skill inventory");
    childIds.add(childId);
    mounts.push(mount);
    const children = Object.entries(files)
      .filter(([path]) => path.startsWith(mount))
      .map(([path, content]) => ({
        path: path.slice(mount.length),
        sha256: sha256(content),
        sizeBytes: utf8(content).length,
      }));
    if (manifestDigest(children) !== hash(link.digest, true))
      return invalid("Linked skill digest mismatch");
    Object.keys(files)
      .filter((path) => path.startsWith(mount))
      .forEach((path) => covered.add(path));
  }
  if (
    JSON.stringify(mounts) !==
      JSON.stringify([...mounts].sort(codepointOrder)) ||
    covered.size !== Object.keys(files).length
  )
    return invalid("Descriptor does not cover the exact snapshot");
  if (!files["AGENTS.md"].trim()) return invalid("Context root is empty");
}

export class VerifiedSnapshot {
  readonly files: Readonly<Record<string, string>>;
  readonly manifest: SnapshotManifest;
  constructor(
    manifest: SnapshotManifest,
    files: Readonly<Record<string, string>>,
  ) {
    const copied: Record<string, string> = Object.assign(
      Object.create(null) as Record<string, string>,
      files,
    );
    this.manifest = manifest;
    this.files = Object.freeze(copied);
    if (manifestDigest(manifest.files) !== manifest.identity.digest)
      invalid("Full manifest digest mismatch");
    if (manifest.files.length < 1 || manifest.files.length > MAX_FILES)
      invalid("Verified snapshot inventory mismatch");
    if (
      Object.keys(copied).length !== manifest.files.length ||
      !manifest.files.every((item) =>
        Object.prototype.hasOwnProperty.call(copied, item.path),
      )
    )
      invalid("Verified snapshot inventory mismatch");
    for (const item of manifest.files)
      if (
        typeof copied[item.path] !== "string" ||
        utf8(copied[item.path]).length !== item.sizeBytes ||
        sha256(copied[item.path]) !== item.sha256
      )
        invalid("Verified snapshot checksum mismatch");
    if (manifest.identity.kind === "agent_context")
      validateDescriptor(copied, manifest.identity);
    Object.freeze(this);
  }
  get identity(): SnapshotIdentity {
    return this.manifest.identity;
  }
}

export class ContextSnapshot {
  readonly #source: SnapshotSource;
  constructor(
    readonly manifest: SnapshotManifest,
    source: SnapshotSource,
  ) {
    this.#source = source;
    Object.freeze(this);
  }
  get identity(): SnapshotIdentity {
    return this.manifest.identity;
  }
  async readFile(path: string): Promise<string> {
    const chunks = new ChunkCollector(this.manifest, path);
    while (!chunks.eof) {
      requireLive(this.manifest.lease);
      chunks.add(
        await this.#source.chunk(this.identity, path, chunks.offset, {
          resolutionId: this.manifest.lease.resolutionId,
        }),
      );
    }
    return chunks.finish();
  }
  async readAll(): Promise<VerifiedSnapshot> {
    const files: Record<string, string> = Object.create(null) as Record<
      string,
      string
    >;
    for (const item of this.manifest.files)
      files[item.path] = await this.readFile(item.path);
    requireLive(this.manifest.lease);
    return new VerifiedSnapshot(this.manifest, files);
  }
}
