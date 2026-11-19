import { createHash } from "node:crypto";
import { Client } from "../../platform/client";
import type { FetchLike } from "../../platform/transport";
import { ContextClient } from "../../context/client";
import {
  ChunkCollector,
  ManifestCollector,
  ResolutionExpiredError,
  SnapshotIntegrityError,
  VerifiedSnapshot,
  manifestDigest,
} from "../../context/snapshot";
import type { SnapshotKind, SnapshotSource } from "../../context/types";
import { SkillsClient } from "../../skills/client";

const RESOURCE = "11111111-1111-4111-8111-111111111111";
const VERSION = "22222222-2222-4222-8222-222222222222";
const PREFIX = "/model-hub/skills/contexts/";
const LEASE = "synthetic-resolution-lease";
const sum = (text: string) =>
  createHash("sha256").update(text, "utf8").digest("hex");
function canonical(value: unknown): string {
  if (Array.isArray(value)) return `[${value.map(canonical).join(",")}]`;
  if (value !== null && typeof value === "object")
    return `{${Object.keys(value)
      .sort()
      .map(
        (key) =>
          `${JSON.stringify(key)}:${canonical((value as Record<string, unknown>)[key])}`,
      )
      .join(",")}}`;
  return JSON.stringify(value);
}
function order(a: string, b: string): number {
  const left = Array.from(a, (char) => char.codePointAt(0)!);
  const right = Array.from(b, (char) => char.codePointAt(0)!);
  for (let i = 0; i < Math.min(left.length, right.length); i++)
    if (left[i] !== right[i]) return left[i] - right[i];
  return left.length - right.length;
}
function digest(files: Record<string, string>): string {
  const pairs = Object.keys(files)
    .sort(order)
    .map((path) => [path, sum(files[path])]);
  return `sha256:${sum(JSON.stringify(pairs).replace(/[\u007f-\uffff]/g, (char) => `\\u${char.charCodeAt(0).toString(16).padStart(4, "0")}`))}`;
}
class Fixture {
  files: Record<string, string> = {};
  metadata: { path: string; sha256: string; size_bytes: number }[] = [];
  digest = "";
  expiry = new Date(Date.now() + 600000).toISOString();
  requests: { url: URL; headers: Headers }[] = [];
  resolves = 0;
  denied = false;
  mutatePage?: (page: Record<string, unknown>, offset: number) => void;
  mutateChunk?: (chunk: Record<string, unknown>) => void;
  constructor(readonly kind: SnapshotKind = "agent_context") {
    for (let i = 0; i < 27; i++)
      this.files[`references/file-${String(i).padStart(2, "0")}.md`] =
        `Reference ${i}\n`;
    Object.assign(this.files, {
      "references/😀é.txt": "unicode path\n",
      "references/\ue000.txt": "private use path\n",
      "empty.txt": "",
    });
    this.files[kind === "agent_context" ? "AGENTS.md" : "SKILL.md"] =
      "Boundary é😀\n".repeat(11000);
    if (kind === "agent_context") {
      const child = {
        "SKILL.md":
          "---\nname: refund\ndescription: Use for refund requests.\n---\nRefund rules.\n",
        "references/policy.md": "Retain local rules.\n",
      };
      const descriptor = {
        schema: 1,
        kind,
        name: "fixture",
        description: "Synthetic fixture",
        entrypoint: "AGENTS.md",
        owned_paths: Object.keys(this.files).sort(order),
        links: [
          {
            mount: "skills/refund/",
            skill_id: "33333333-3333-4333-8333-333333333333",
            version: 4,
            version_id: "44444444-4444-4444-8444-444444444444",
            digest: digest(child),
            requested: { version: 4 },
          },
        ],
      };
      for (const [path, text] of Object.entries(child))
        this.files[`skills/refund/${path}`] = text;
      this.files[".futureagi/context.json"] = canonical(descriptor);
    }
    this.rehash();
  }
  rehash(): void {
    this.metadata = Object.keys(this.files)
      .sort(order)
      .map((path) => ({
        path,
        sha256: sum(this.files[path]),
        size_bytes: Buffer.byteLength(this.files[path]),
      }));
    this.digest = digest(this.files);
  }
  page(offset = 0): Record<string, unknown> {
    return {
      resource_id: RESOURCE,
      kind: this.kind,
      name: "fixture",
      version: 7,
      version_id: VERSION,
      digest: this.digest,
      requested: { label: "production" },
      entrypoint: this.kind === "agent_context" ? "AGENTS.md" : "SKILL.md",
      descriptor_path:
        this.kind === "agent_context" ? ".futureagi/context.json" : null,
      resolution_id: LEASE,
      resolution_expires_at: this.expiry,
      files: this.metadata
        .slice(offset, offset + 25)
        .map((item) => ({ ...item })),
      file_count: this.metadata.length,
      file_offset: offset,
      next_file_offset: offset + 25 < this.metadata.length ? offset + 25 : null,
    };
  }
  chunk(path: string, offset: number): Record<string, unknown> {
    const text = this.files[path];
    const chars = Array.from(text);
    let end = offset;
    let bytes = 0;
    while (end < chars.length && bytes + Buffer.byteLength(chars[end]) <= 32768)
      bytes += Buffer.byteLength(chars[end++]);
    return {
      path,
      sha256: sum(text),
      size_bytes: Buffer.byteLength(text),
      total_chars: chars.length,
      offset,
      next_offset: end < chars.length ? end : null,
      eof: end === chars.length,
      text: chars.slice(offset, end).join(""),
      resource_id: RESOURCE,
      version_id: VERSION,
      digest: this.digest,
    };
  }
  fetch: FetchLike = async (input, init) => {
    const url = new URL(input);
    const headers = new Headers(init.headers);
    this.requests.push({ url, headers });
    expect(url.host).toBe("fixture.invalid");
    expect(headers.get("authorization")).toBe("Context synthetic-credential");
    for (const key of ["x-api-key", "x-secret-key", "x-workspace-id"])
      expect(headers.has(key)).toBe(false);
    if (this.denied)
      return new Response(
        JSON.stringify({ status: false, code: "context_credential_revoked" }),
        { status: 403 },
      );
    let result: Record<string, unknown>;
    if (url.pathname === `${PREFIX}resolve/`) {
      expect(++this.resolves).toBe(1);
      result = this.page();
      this.mutatePage?.(result, 0);
    } else {
      expect(headers.get("x-context-resolution")).toBe(LEASE);
      const immutable = `${PREFIX}${RESOURCE}/versions/7/`;
      expect(url.pathname.startsWith(immutable)).toBe(true);
      expect(url.searchParams.has("label")).toBe(false);
      if (url.pathname === `${immutable}manifest/`) {
        const offset = Number(url.searchParams.get("file_offset"));
        result = this.page(offset);
        this.mutatePage?.(result, offset);
      } else {
        expect(url.pathname).toBe(`${immutable}files/`);
        result = this.chunk(
          url.searchParams.get("path")!,
          Number(url.searchParams.get("offset")),
        );
        this.mutateChunk?.(result);
      }
    }
    return new Response(JSON.stringify({ status: true, result }), {
      status: 200,
      headers: { "Content-Type": "application/json" },
    });
  };
}
function client(fixture: Fixture): ContextClient {
  return new ContextClient(
    new Client({
      auth: { type: "context", credential: "synthetic-credential" },
      baseUrl: "https://fixture.invalid",
      fetch: fixture.fetch,
      maxRetries: 0,
    }),
  );
}

test.each([false, true])(
  "complete snapshot with stale broad keys=%s",
  async (stale) => {
    const saved = { ...process.env };
    try {
      for (const key of ["FI_API_KEY", "FI_SECRET_KEY", "FI_WORKSPACE_ID"]) {
        delete process.env[key];
        if (stale) process.env[key] = "stale-broad";
      }
      const fixture = new Fixture();
      const snapshot = await client(fixture).resolve("fixture");
      const verified = await snapshot.readAll();
      expect(verified.files).toEqual(fixture.files);
      expect(snapshot.manifest.files).toHaveLength(34);
      expect(manifestDigest(snapshot.manifest.files)).toBe(fixture.digest);
      expect(fixture.digest).toBe(
        "sha256:567bb27c361daf3faf3368cc1afc6d83b7187eef6f6226fba318579efcad3bc4",
      );
      expect(snapshot.identity.version).toBe(7);
      expect(snapshot.manifest.requested).toEqual({ label: "production" });
      expect(await snapshot.readFile("empty.txt")).toBe("");
      expect(
        fixture.requests.filter(
          (item) => item.url.searchParams.get("path") === "AGENTS.md",
        ).length,
      ).toBeGreaterThan(4);
      expect(fixture.resolves).toBe(1);
      expect(() => {
        (verified.files as Record<string, string>)["AGENTS.md"] = "bad";
      }).toThrow();
      expect(Object.isFrozen(snapshot.identity)).toBe(true);
    } finally {
      process.env = saved;
    }
  },
);

test.each([
  ["next_file_offset", null],
  ["next_file_offset", 0],
  ["file_count", 201],
  ["file_offset", 1],
  ["files", []],
  ["file_count", true],
  ["version", true],
  ["resource_id", "../../escape"],
  ["resolution_id", "bad\nheader"],
  ["resolution_expires_at", "2026-01-01T00:00:00"],
  ["entrypoint", "SKILL.md"],
])("reject malformed initial manifest %s", (key, value) => {
  const fixture = new Fixture();
  const page = fixture.page();
  page[key as string] = value;
  expect(() => new ManifestCollector(page, "agent_context").finish()).toThrow(
    SnapshotIntegrityError,
  );
});

test.each([
  ["version", 8],
  ["version_id", "55555555-5555-4555-8555-555555555555"],
  ["digest", "sha256:" + "0".repeat(64)],
  ["resolution_id", "new-lease"],
  ["file_count", 35],
  ["file_offset", 0],
  ["next_file_offset", 25],
])("reject mixed continuation %s", async (key, value) => {
  const fixture = new Fixture();
  fixture.mutatePage = (page, offset) => {
    if (offset) page[key as string] = value;
  };
  await expect(client(fixture).resolve("fixture")).rejects.toThrow(
    SnapshotIntegrityError,
  );
  expect(fixture.resolves).toBe(1);
});

test.each([
  "../evil",
  "/absolute",
  "a\\b",
  "x/./y",
  "a//b",
  "a./b",
  "x\x00y",
  "C:/drive",
  "a/".repeat(8) + "b",
])("reject unsafe path %s", (path) => {
  const fixture = new Fixture();
  fixture.metadata[0].path = path;
  expect(() => new ManifestCollector(fixture.page(), "agent_context")).toThrow(
    SnapshotIntegrityError,
  );
});

test.each(["agents.md", "references", "references/FILE-00.md"])(
  "reject case/prefix collisions %s",
  async (path) => {
    const fixture = new Fixture();
    fixture.files[path] = "collision";
    fixture.rehash();
    await expect(client(fixture).resolve("fixture")).rejects.toThrow(
      SnapshotIntegrityError,
    );
  },
);

test.each([
  ["sha256", "0".repeat(64)],
  ["path", "other.md"],
  ["offset", 1],
  ["version_id", "55555555-5555-4555-8555-555555555555"],
  ["total_chars", 0],
  ["eof", true],
  ["next_offset", 1],
  ["size_bytes", 2 ** 30],
  ["text", "\ud800"],
  ["text", "\x00"],
])("reject invalid chunks %s", async (key, value) => {
  const fixture = new Fixture();
  fixture.mutateChunk = (chunk) => {
    chunk[key as string] = value;
  };
  const snapshot = await client(fixture).resolve("fixture");
  await expect(snapshot.readFile("AGENTS.md")).rejects.toThrow(
    SnapshotIntegrityError,
  );
  expect(fixture.resolves).toBe(1);
});

test("same-sized corruption fails checksum", async () => {
  const fixture = new Fixture();
  fixture.mutateChunk = (chunk) => {
    chunk.text = (chunk.text as string).replace(/Boundary/g, "Changed!");
  };
  const snapshot = await client(fixture).resolve("fixture");
  await expect(snapshot.readFile("AGENTS.md")).rejects.toThrow(/checksum/);
});

test("zero progress and missing next offset fail", () => {
  const fixture = new Fixture();
  const pages = new ManifestCollector(fixture.page(), "agent_context");
  pages.add(fixture.page(25));
  const manifest = pages.finish();
  for (const mutate of [
    (chunk: Record<string, unknown>) => {
      delete chunk.next_offset;
    },
    (chunk: Record<string, unknown>) => {
      Object.assign(chunk, { text: "", next_offset: 0, eof: false });
    },
  ]) {
    const chunk = fixture.chunk("AGENTS.md", 0);
    mutate(chunk);
    expect(() => new ChunkCollector(manifest, "AGENTS.md").add(chunk)).toThrow(
      SnapshotIntegrityError,
    );
  }
});

test("repeated reads reauthorize without a cache", async () => {
  const fixture = new Fixture();
  const snapshot = await client(fixture).resolve("fixture");
  expect(await snapshot.readFile("empty.txt")).toBe("");
  fixture.denied = true;
  await expect(snapshot.readFile("empty.txt")).rejects.toMatchObject({
    status: 403,
  });
  expect(
    fixture.requests.filter(
      (item) => item.url.searchParams.get("path") === "empty.txt",
    ),
  ).toHaveLength(2);
});

test.each([304, 302, 403, 410])(
  "status %s is never content",
  async (status) => {
    const fixture = new Fixture();
    const original = fixture.fetch;
    fixture.fetch = async (url, init) =>
      url.includes("/files/")
        ? new Response(null, {
            status,
            headers: { Location: "https://other.invalid/leak" },
          })
        : original(url, init);
    const snapshot = await client(fixture).resolve("fixture");
    await expect(snapshot.readFile("AGENTS.md")).rejects.toThrow();
    expect(fixture.resolves).toBe(1);
  },
);

test("expired lease never renews", async () => {
  const fixture = new Fixture();
  fixture.expiry = "2000-01-01T00:00:00Z";
  await expect(client(fixture).resolve("fixture")).rejects.toThrow(
    ResolutionExpiredError,
  );
  expect(fixture.requests).toHaveLength(1);
});

test("missing path makes no request", async () => {
  const fixture = new Fixture();
  const snapshot = await client(fixture).resolve("fixture");
  const count = fixture.requests.length;
  await expect(snapshot.readFile("not-there")).rejects.toThrow(
    SnapshotIntegrityError,
  );
  expect(fixture.requests).toHaveLength(count);
});

test.each(["root", "name", "canonical", "child", "coverage"])(
  "reject invalid descriptor %s",
  async (mutation) => {
    const fixture = new Fixture();
    const descriptor = JSON.parse(fixture.files[".futureagi/context.json"]);
    if (mutation === "root") fixture.files["AGENTS.md"] = " ";
    else if (mutation === "name") descriptor.name = "another";
    else if (mutation === "child")
      descriptor.links[0].digest = "sha256:" + "0".repeat(64);
    else if (mutation === "coverage")
      descriptor.owned_paths = descriptor.owned_paths.filter(
        (path: string) => path !== "empty.txt",
      );
    fixture.files[".futureagi/context.json"] =
      canonical(descriptor) + (mutation === "canonical" ? "\n" : "");
    fixture.rehash();
    const snapshot = await client(fixture).resolve("fixture");
    await expect(snapshot.readAll()).rejects.toThrow(SnapshotIntegrityError);
  },
);

test("verified bytes are defensive copies", () => {
  const fixture = new Fixture();
  const pages = new ManifestCollector(fixture.page(), "agent_context");
  pages.add(fixture.page(25));
  const manifest = pages.finish();
  const verified = new VerifiedSnapshot(manifest, fixture.files);
  fixture.files["AGENTS.md"] = "bad";
  expect(verified.files["AGENTS.md"]).not.toBe("bad");
  expect(() => new VerifiedSnapshot(manifest, fixture.files)).toThrow(
    SnapshotIntegrityError,
  );
});

test("leaf sources use the same lease and byte verification", async () => {
  const fixture = new Fixture("skill");
  const source: SnapshotSource = {
    async resolve(name, selector) {
      expect(name).toBe("fixture");
      expect(selector).toEqual({ label: "production" });
      return fixture.page();
    },
    async manifest(identity, offset, options) {
      expect(identity.kind).toBe("skill");
      expect(options.resolutionId).toBe(LEASE);
      return fixture.page(offset);
    },
    async chunk(identity, path, offset, options) {
      expect(identity.versionId).toBe(VERSION);
      expect(options.resolutionId).toBe(LEASE);
      return fixture.chunk(path, offset);
    },
  };
  const snapshot = await new SkillsClient(source).resolve("fixture");
  expect((await snapshot.readAll()).files).toEqual(fixture.files);
  expect(snapshot.identity.kind).toBe("skill");
});

test("lease expiry midchunk discards staged bytes", async () => {
  const fixture = new Fixture();
  let instant = Date.now();
  const clock = jest.spyOn(Date, "now").mockImplementation(() => instant);
  try {
    fixture.mutateChunk = () => {
      instant += 1200000;
    };
    const snapshot = await client(fixture).resolve("fixture");
    await expect(snapshot.readFile("AGENTS.md")).rejects.toThrow(
      ResolutionExpiredError,
    );
    expect(
      fixture.requests.filter((item) => item.url.pathname.endsWith("files/")),
    ).toHaveLength(1);
    expect(fixture.resolves).toBe(1);
  } finally {
    clock.mockRestore();
  }
});

test.each([
  "over_file",
  "over_bundle",
  "missing_root",
  "missing_descriptor",
  "hash",
  "duplicate",
  "missing_offset",
])("inventory boundary %s", async (scenario) => {
  const fixture = new Fixture();
  if (scenario === "over_file") fixture.metadata[0].size_bytes = 524289;
  else if (scenario === "over_bundle")
    fixture.metadata.forEach((item) => {
      item.size_bytes = 524288;
    });
  else if (scenario === "missing_root") {
    delete fixture.files["AGENTS.md"];
    fixture.rehash();
  } else if (scenario === "missing_descriptor") {
    delete fixture.files[".futureagi/context.json"];
    fixture.rehash();
  } else if (scenario === "hash") fixture.digest = "sha256:" + "0".repeat(64);
  else if (scenario === "duplicate")
    fixture.metadata[fixture.metadata.length - 1] = fixture.metadata[0];
  else
    fixture.mutatePage = (page) => {
      delete page.next_file_offset;
    };
  await expect(client(fixture).resolve("fixture")).rejects.toThrow(
    SnapshotIntegrityError,
  );
});

test("maximum inventory is complete", () => {
  const fixture = new Fixture("skill");
  fixture.files = { "SKILL.md": "root" };
  for (let i = 0; i < 199; i++) fixture.files[`references/${i}.txt`] = "";
  fixture.rehash();
  const pages = new ManifestCollector(fixture.page(), "skill");
  while (pages.nextOffset !== null) pages.add(fixture.page(pages.nextOffset));
  expect(pages.finish().files).toHaveLength(200);
});

test("surrogate paths and forged verified manifests fail", async () => {
  const fixture = new Fixture();
  fixture.metadata[0].path = "invalid\ud800.txt";
  await expect(client(fixture).resolve("fixture")).rejects.toThrow(
    SnapshotIntegrityError,
  );
  fixture.rehash();
  const pages = new ManifestCollector(fixture.page(), "agent_context");
  pages.add(fixture.page(25));
  const manifest = pages.finish();
  expect(
    () =>
      new VerifiedSnapshot(
        {
          ...manifest,
          identity: {
            ...manifest.identity,
            digest: "sha256:" + "0".repeat(64),
          },
        },
        fixture.files,
      ),
  ).toThrow(/manifest digest/);
});

test("leaf chunks reject contradictory identity", () => {
  const fixture = new Fixture("skill");
  const pages = new ManifestCollector(fixture.page(), "skill");
  pages.add(fixture.page(25));
  const chunk = fixture.chunk("SKILL.md", 0);
  chunk.version_id = "55555555-5555-4555-8555-555555555555";
  expect(() =>
    new ChunkCollector(pages.finish(), "SKILL.md").add(chunk),
  ).toThrow(SnapshotIntegrityError);
});

test("snapshot serialization never exposes the authenticated transport", async () => {
  const fixture = new Fixture();
  const snapshot = await client(fixture).resolve("fixture");
  const serialized = JSON.stringify(snapshot);
  expect(serialized).not.toContain("synthetic-credential");
  expect(Object.keys(snapshot)).toEqual(["manifest"]);
});
