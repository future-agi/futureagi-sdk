import { createHash } from "node:crypto";
import { ContextClient } from "../../context/client";
import { SnapshotIntegrityError } from "../../context/snapshot";
import type { SnapshotKind } from "../../context/types";
import { Client } from "../../platform/client";
import type { FetchLike } from "../../platform/transport";
import { SkillsClient } from "../../skills/client";

const RESOURCE = "11111111-1111-4111-8111-111111111111";
const VERSION = "22222222-2222-4222-8222-222222222222";
const LEASE = "33333333-3333-4333-8333-333333333333";
const sum = (text: string) => createHash("sha256").update(text).digest("hex");

function fixture(kind: SnapshotKind) {
  const root = kind === "skill" ? "SKILL.md" : "AGENTS.md";
  const files: Record<string, string> = { [root]: "Synthetic policy.\n" };
  for (let i = 0; i < 26; i++) files[`references/${i}.md`] = `Rule ${i}.\n`;
  files["references/escaped.md"] = '\t"\\雪😀\n'.repeat(14000);
  if (kind === "agent_context") {
    files[".futureagi/context.json"] = JSON.stringify({
      description: "Synthetic policy",
      entrypoint: "AGENTS.md",
      kind,
      links: [],
      name: "fixture",
      owned_paths: Object.keys(files).sort(),
      schema: 1,
    });
  }
  const metadata = Object.keys(files)
    .sort()
    .map((path) => ({
      path,
      sha256: sum(files[path]),
      size_bytes: Buffer.byteLength(files[path]),
      origin: {
        kind: path === ".futureagi/context.json" ? "generated" : "owned",
        skill_id: null,
        version_id: null,
        source_path: null,
      },
    }));
  const digest = `sha256:${sum(JSON.stringify(metadata.map(({ path, sha256 }) => [path, sha256])))}`;
  const prefix = `/model-hub/skills/${kind === "skill" ? "consumption" : "contexts"}/`;
  const requests: { url: URL; init: RequestInit }[] = [];
  let requested: Record<string, string | number> = { label: "production" };
  let resolves = 0;
  let denial = 0;
  let mutate: (value: Record<string, unknown>, path: string) => void = () =>
    undefined;
  const expiry = new Date(Date.now() + 600000).toISOString();
  function page(offset = 0): Record<string, unknown> {
    return {
      resource_id: RESOURCE,
      kind,
      name: "fixture",
      description: "Synthetic policy",
      version: 7,
      version_id: VERSION,
      digest,
      requested,
      entrypoint: root,
      descriptor_path: kind === "skill" ? null : ".futureagi/context.json",
      files: metadata.slice(offset, offset + 25),
      file_count: metadata.length,
      file_offset: offset,
      next_file_offset: offset + 25 < metadata.length ? offset + 25 : null,
      resolution_id: LEASE,
      resolution_expires_at: expiry,
      created_at: "2026-11-01T00:00:00Z",
    };
  }
  const fetch: FetchLike = async (input, init) => {
    const url = new URL(input);
    requests.push({ url, init });
    const headers = new Headers(init.headers);
    expect(headers.get("authorization")).toBe("Context synthetic-credential");
    expect(headers.has("x-api-key")).toBe(false);
    expect(headers.has("x-secret-key")).toBe(false);
    expect(init.credentials).toBe("omit");
    if (denial)
      return new Response(
        JSON.stringify({ status: false, code: "context_credential_revoked" }),
        { status: denial },
      );
    let result: Record<string, unknown>;
    if (url.pathname === `${prefix}resolve/`) {
      resolves++;
      requested = url.searchParams.has("version")
        ? { version: Number(url.searchParams.get("version")) }
        : { label: url.searchParams.get("label")! };
      result = page();
    } else {
      expect(url.pathname.startsWith(`${prefix}${RESOURCE}/versions/7/`)).toBe(
        true,
      );
      expect(headers.get("x-context-resolution")).toBe(LEASE);
      expect(url.searchParams.has("label")).toBe(false);
      if (url.pathname.endsWith("manifest/")) {
        result = page(Number(url.searchParams.get("file_offset")));
      } else if (url.pathname.endsWith("access-check/")) {
        expect(init.method).toBe("POST");
        expect(JSON.parse(init.body as string)).toEqual({});
        result = {
          allowed: true,
          version_id: VERSION,
          digest,
          checked_at: new Date().toISOString(),
        };
      } else {
        expect(url.pathname.endsWith("files/")).toBe(true);
        const path = url.searchParams.get("path")!;
        const offset = Number(url.searchParams.get("offset"));
        const chars = Array.from(files[path]);
        // The bounded JSON envelope may shorten chunks below max_bytes.
        const text = chars.slice(offset, offset + 1000).join("");
        const end = offset + Array.from(text).length;
        result = {
          path,
          sha256: sum(files[path]),
          size_bytes: Buffer.byteLength(files[path]),
          total_chars: chars.length,
          offset,
          next_offset: end === chars.length ? null : end,
          eof: end === chars.length,
          text,
          resource_id: RESOURCE,
          version_id: VERSION,
          digest,
        };
      }
    }
    mutate(result, url.pathname);
    return new Response(JSON.stringify({ status: true, result }), {
      status: 200,
    });
  };
  const platform = new Client({
    auth: { type: "context", credential: "synthetic-credential" },
    baseUrl: "https://fixture.invalid",
    fetch,
    maxRetries: 0,
  });
  return {
    platform,
    files,
    requests,
    page,
    get resolves() {
      return resolves;
    },
    deny(status: number) {
      denial = status;
    },
    change(callback: typeof mutate) {
      mutate = callback;
    },
  };
}

test.each(["skill", "agent_context"] as const)(
  "F12 %s reconstructs complete escaped bytes and live authorizes",
  async (kind) => {
    const saved = { ...process.env };
    try {
      process.env.FI_API_KEY = process.env.FI_SECRET_KEY = "stale-broad";
      const wire = fixture(kind);
      const client =
        kind === "skill"
          ? new SkillsClient(wire.platform)
          : new ContextClient(wire.platform);
      const snapshot = await client.resolve("fixture");
      expect((await snapshot.readAll()).files).toEqual(wire.files);
      expect(snapshot.manifest.files.length).toBeGreaterThan(25);
      expect(
        Buffer.byteLength(wire.files["references/escaped.md"]),
      ).toBeGreaterThan(100 * 1024);
      await client.checkAccess(snapshot.identity, snapshot.manifest.lease);
      wire.change((result, path) => {
        if (path.endsWith("access-check/"))
          result.digest = `sha256:${"0".repeat(64)}`;
      });
      await expect(
        client.checkAccess(snapshot.identity, snapshot.manifest.lease),
      ).rejects.toThrow(SnapshotIntegrityError);
      wire.deny(403);
      await expect(
        client.checkAccess(snapshot.identity, snapshot.manifest.lease),
      ).rejects.toMatchObject({ status: 403 });
      expect(wire.resolves).toBe(1);
      expect(
        wire.requests.some(({ url }) => url.pathname.includes("receipts")),
      ).toBe(false);
    } finally {
      process.env = saved;
    }
  },
);

test.each(["skill", "agent_context"] as const)(
  "generated %s methods preserve number, file path and lease",
  async (kind) => {
    const wire = fixture(kind);
    const resource =
      kind === "skill"
        ? wire.platform.skillConsumption
        : wire.platform.contexts;
    const resolved = await resource.resolve({ name: "fixture", version: 7 });
    expect(resolved.resource_id).toBe(RESOURCE);
    expect(resolved.requested).toEqual({ version: 7 });
    const page = await resource.manifest(RESOURCE, 7, {
      resolution_id: LEASE,
      file_offset: 25,
    });
    expect(page.file_offset).toBe(25);
    const chunk = await resource.readFile(RESOURCE, 7, {
      path: "references/escaped.md",
      resolution_id: LEASE,
    });
    expect(chunk.resource_id).toBe(RESOURCE);
    expect(chunk.text).toBe(
      Array.from(wire.files["references/escaped.md"]).slice(0, 1000).join(""),
    );
    expect(
      (await resource.checkAccess(RESOURCE, 7, { resolution_id: LEASE }))
        .allowed,
    ).toBe(true);
    const count = wire.requests.length;
    expect(() =>
      resource.manifest(
        RESOURCE,
        7,
        { resolution_id: LEASE },
        { resolutionId: "another" },
      ),
    ).toThrow(/conflicting/);
    expect(wire.requests).toHaveLength(count);
  },
);

test.each(["resource_id", "version_id", "digest"])(
  "leaf chunk requires %s",
  async (field) => {
    const wire = fixture("skill");
    const snapshot = await new SkillsClient(wire.platform).resolve("fixture");
    wire.change((result, path) => {
      if (path.endsWith("files/")) delete result[field];
    });
    await expect(snapshot.readFile("SKILL.md")).rejects.toThrow(
      SnapshotIntegrityError,
    );
  },
);

test.each(["kind", "resource_id"])(
  "reject obsolete or wrong-kind F12 manifest %s",
  async (field) => {
    const wire = fixture("skill");
    wire.change((result) => {
      if (field === "kind") result.kind = "agent_context";
      else {
        result.skill_id = result.resource_id;
        delete result.resource_id;
      }
    });
    await expect(
      new SkillsClient(wire.platform).resolve("fixture"),
    ).rejects.toThrow(SnapshotIntegrityError);
  },
);
