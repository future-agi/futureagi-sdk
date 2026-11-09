// Execute from the clean tarball installation, never from source resolution.
import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { createRequire } from "node:module";
import * as esm from "@future-agi/sdk";
const require = createRequire(import.meta.url);
const sha = (text) => createHash("sha256").update(text).digest("hex");
const resource = "11111111-1111-4111-8111-111111111111";
const version = "22222222-2222-4222-8222-222222222222";
const lease = "33333333-3333-4333-8333-333333333333";

for (const sdk of [esm, require("@future-agi/sdk")]) {
  for (const kind of ["skill", "agent_context"]) {
    const root = kind === "skill" ? "SKILL.md" : "AGENTS.md";
    const files = {
      [root]: 'Synthetic instructions. 雪😀\t"\\\n'.repeat(4000),
    };
    for (let i = 0; i < 26; i++) files[`references/${i}.md`] = `Reference ${i}`;
    if (kind === "agent_context")
      files[".futureagi/context.json"] = JSON.stringify({
        description: "Synthetic",
        entrypoint: root,
        kind,
        links: [],
        name: "fixture",
        owned_paths: Object.keys(files).sort(),
        schema: 1,
      });
    const metadata = Object.keys(files)
      .sort()
      .map((path) => ({
        path,
        sha256: sha(files[path]),
        size_bytes: Buffer.byteLength(files[path]),
      }));
    const digest = `sha256:${sha(JSON.stringify(metadata.map(({ path, sha256 }) => [path, sha256])))}`;
    const prefix = `/model-hub/skills/${kind === "skill" ? "consumption" : "contexts"}/`;
    let resolves = 0;
    let denied = false;
    process.env.FI_API_KEY = process.env.FI_SECRET_KEY = "stale-broad";
    const client = new sdk.Client({
      auth: { type: "context", credential: "synthetic" },
      baseUrl: "https://fixture.invalid",
      maxRetries: 0,
      fetch: async (input, init) => {
        const url = new URL(input);
        const headers = new Headers(init.headers);
        assert.equal(headers.get("authorization"), "Context synthetic");
        assert.equal(headers.has("x-api-key"), false);
        assert.equal(headers.has("x-secret-key"), false);
        if (denied)
          return new Response(
            JSON.stringify({
              status: false,
              code: "context_credential_revoked",
            }),
            { status: 403 },
          );
        let result;
        if (
          url.pathname.endsWith("resolve/") ||
          url.pathname.endsWith("manifest/")
        ) {
          if (url.pathname.endsWith("resolve/")) {
            assert.equal(url.pathname, `${prefix}resolve/`);
            resolves++;
          } else assert.equal(headers.get("x-context-resolution"), lease);
          const offset = Number(url.searchParams.get("file_offset") ?? 0);
          result = {
            resource_id: resource,
            kind,
            name: "fixture",
            version: 7,
            version_id: version,
            digest,
            requested: { label: "production" },
            entrypoint: root,
            descriptor_path:
              kind === "skill" ? null : ".futureagi/context.json",
            resolution_id: lease,
            resolution_expires_at: new Date(Date.now() + 600000).toISOString(),
            files: metadata.slice(offset, offset + 25),
            file_count: metadata.length,
            file_offset: offset,
            next_file_offset:
              offset + 25 < metadata.length ? offset + 25 : null,
          };
          // A lease's expiry is immutable across pages.
          result.resolution_expires_at = expiry;
        } else {
          assert.equal(headers.get("x-context-resolution"), lease);
          assert.ok(
            url.pathname.startsWith(`${prefix}${resource}/versions/7/`),
          );
          if (url.pathname.endsWith("access-check/"))
            result = { allowed: true, version_id: version, digest };
          else {
            const path = url.searchParams.get("path");
            const offset = Number(url.searchParams.get("offset"));
            const chars = Array.from(files[path]);
            const text = chars.slice(offset, offset + 1000).join("");
            const end = offset + Array.from(text).length;
            result = {
              resource_id: resource,
              version_id: version,
              digest,
              path,
              sha256: sha(files[path]),
              size_bytes: Buffer.byteLength(files[path]),
              total_chars: chars.length,
              offset,
              next_offset: end === chars.length ? null : end,
              eof: end === chars.length,
              text,
            };
          }
        }
        return new Response(JSON.stringify({ status: true, result }), {
          status: 200,
        });
      },
    });
    const expiry = new Date(Date.now() + 600000).toISOString();
    const wrapper =
      kind === "skill"
        ? new sdk.SkillsClient(client)
        : new sdk.ContextClient(client);
    const snapshot = await wrapper.resolve("fixture");
    assert.deepEqual({ ...(await snapshot.readAll()).files }, files);
    await wrapper.checkAccess(snapshot.identity, snapshot.manifest.lease);
    denied = true;
    await assert.rejects(
      wrapper.checkAccess(snapshot.identity, snapshot.manifest.lease),
      (error) => error.status === 403,
    );
    assert.equal(resolves, 1);
  }
}
console.log(
  "consumer: installed ESM/CommonJS context and leaf byte/lease conformance passed",
);
