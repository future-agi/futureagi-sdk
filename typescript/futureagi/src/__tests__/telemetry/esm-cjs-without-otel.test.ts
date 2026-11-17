/** Cloud-only qualification. Build the package before this suite. It installs
 * the packed output into an isolated fixture without development/optional peers. */
import { execFileSync } from "node:child_process";
import { mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";

it("imports the packed root and telemetry subpath from ESM and CJS without OTel", () => {
  const directory = mkdtempSync(join(tmpdir(), "sdk-no-otel-"));
  const packageRoot = resolve(__dirname, "../../..");
  try {
    const packed = JSON.parse(execFileSync("npm", ["pack", "--ignore-scripts", "--json", "--pack-destination", directory], { cwd: packageRoot, encoding: "utf8" })) as Array<{ filename: string }>;
    writeFileSync(join(directory, "package.json"), JSON.stringify({ private: true, name: "sdk-optional-peer-fixture" }));
    execFileSync("npm", ["install", "--ignore-scripts", "--omit=dev", "--omit=optional", "--omit=peer", "--no-audit", "--no-fund", join(directory, packed[0].filename)], { cwd: directory, stdio: "pipe" });
    const body = `
      const assert = require('node:assert/strict');
      const { createHash } = require('node:crypto');
      assert.throws(() => require.resolve('@opentelemetry/api'));
      assert.equal(telemetry.status().otel_found, false);
      const { ContextSnapshot } = contextModule;
      const manifestDigest = files => 'sha256:' + createHash('sha256').update(JSON.stringify(files.map(file=>[file.path,file.sha256]))).digest('hex');
      const text = 'verified policy';
      const sha256 = createHash('sha256').update(text).digest('hex');
      const files = [{path:'SKILL.md', sha256, sizeBytes:Buffer.byteLength(text)}];
      const identity = {kind:'skill', resourceId:'11111111-1111-4111-8111-111111111111', versionId:'22222222-2222-4222-8222-222222222222', version:1, name:'refund', digest:manifestDigest(files)};
      const manifest = {identity, requested:{label:'production'}, lease:{resolutionId:'opaque',resolutionExpiresAt:'2099-01-01T00:00:00Z'}, files};
      const snapshot = new ContextSnapshot(manifest, {chunk:async()=>({path:'SKILL.md',sha256,size_bytes:Buffer.byteLength(text),text,total_chars:text.length,offset:0,next_offset:null,eof:true,resource_id:identity.resourceId,version_id:identity.versionId,digest:identity.digest})});
      assert.equal((await snapshot.readAll()).files['SKILL.md'], text);
      assert.equal(globalThis[Symbol.for('futureagi.runtime.skills.v1')], undefined);
      assert.equal(globalThis[Symbol.for('opentelemetry.js.api.1')], undefined);
      assert.equal(Object.keys(require.cache).some(path=>path.includes('@opentelemetry')),false);
    `;
    writeFileSync(join(directory, "probe.cjs"), `const root = require('@future-agi/sdk'); const telemetry = require('@future-agi/sdk/telemetry'); const contextModule = require('@future-agi/sdk/context'); (async()=>{${body}})().catch(error=>{console.error(error);process.exitCode=1;});`);
    writeFileSync(join(directory, "probe.mjs"), `import * as root from '@future-agi/sdk'; import * as telemetry from '@future-agi/sdk/telemetry'; import * as contextModule from '@future-agi/sdk/context'; import { createRequire } from 'node:module'; const require=createRequire(import.meta.url); ${body}`);
    for (const file of ["probe.cjs", "probe.mjs"]) execFileSync(process.execPath, [join(directory, file)], { cwd: directory, stdio: "pipe" });
    const pkg = JSON.parse(readFileSync(join(directory, "node_modules/@future-agi/sdk/package.json"), "utf8")) as { bin: Record<string, string> };
    const doctor = execFileSync(process.execPath, [join(directory, "node_modules/@future-agi/sdk", pkg.bin["futureagi-telemetry"]), "doctor"], { cwd: directory, encoding: "utf8" });
    expect(doctor).toContain("Provider: none");
    expect(doctor).toContain("first read of any file");
  } finally { rmSync(directory, { recursive: true, force: true }); }
}, 180000);
