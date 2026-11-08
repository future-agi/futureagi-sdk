// Dependency-free regression, also called by the Jest test-name suite.
const assert = require("node:assert/strict");
const { spawn, spawnSync } = require("node:child_process");
const { mkdtempSync, openSync, closeSync, readFileSync, rmSync, writeFileSync } = require("node:fs");
const { tmpdir } = require("node:os");
const { join } = require("node:path");

const root = join(__dirname, "..", "..");
const tests = join(root, "tests");
const read = (name) => JSON.parse(readFileSync(join(tests, "port", name), "utf8")).files;

function largeRun(exitCode) {
  const baseline = { ...read("vitest-legacy-client.json") };
  for (const [file, list] of Object.entries(read("react-vitest-legacy.json"))) baseline[`react/${file}`] = list;
  const manifest = read("manifest.json");
  const assertion = (name, status = "passed") => {
    const parts = name.split(" > ");
    return { title: parts.pop(), ancestorTitles: parts, status };
  };
  const testResults = Object.entries(baseline)
    .filter(([file]) => manifest[file].to === "port")
    .map(([file, list]) => ({
      name: join(tests, file), status: "passed",
      assertionResults: [
        ...list.filter((t) => !manifest[file].shim_tests?.[t.name]).map((t) => assertion(t.name)),
        ...Object.keys(manifest[file].added || {}).map((name) => assertion(name)),
      ],
    }));
  testResults.push({
    name: join(tests, "synthetic-large-output.test.ts"), status: exitCode ? "failed" : "passed",
    assertionResults: Array.from({ length: 1024 }, (_, i) =>
      assertion(`diagnostic ${i} ${"x".repeat(1024)}`, exitCode ? "failed" : "passed")),
  });
  return { testResults };
}

function readPipe(script, input) {
  return new Promise((resolve, reject) => {
    const child = spawn(process.execPath, [script, input], { stdio: ["ignore", "pipe", "pipe"] });
    const chunks = [];
    const errors = [];
    child.stdout.on("data", (chunk) => chunks.push(chunk));
    child.stderr.on("data", (chunk) => errors.push(chunk));
    // Backpressure makes an immediate process.exit lose the queued tail even
    // on hosts where an eager reader would otherwise hide the defect.
    child.stdout.pause();
    const resume = setTimeout(() => child.stdout.resume(), 100);
    const timeout = setTimeout(() => { child.kill(); reject(new Error("Checker did not finish")); }, 10000);
    child.on("error", reject);
    child.on("close", (code, signal) => {
      clearTimeout(resume);
      clearTimeout(timeout);
      resolve({ code, signal, stdout: Buffer.concat(chunks).toString("utf8"), stderr: Buffer.concat(errors).toString("utf8") });
    });
  });
}

async function checkPipedDiagnostics(exitCode) {
  const dir = mkdtempSync(join(tmpdir(), "test-name-pipe-"));
  try {
    const input = join(dir, "run.json");
    const output = join(dir, "output.json");
    const script = join(root, "scripts/check-test-names.cjs");
    writeFileSync(input, JSON.stringify(largeRun(exitCode)));
    // A regular-file control checks byte-for-byte JSON compatibility as well
    // as exit status; file writes are not subject to pipe backpressure.
    const fd = openSync(output, "wx");
    let control;
    try {
      control = spawnSync(process.execPath, [script, input], { stdio: ["ignore", fd, "pipe"], timeout: 10000 });
    } finally {
      closeSync(fd);
    }
    assert.ifError(control.error);
    assert.equal(control.status, exitCode);
    assert.equal(control.stderr.toString(), "");
    const expected = readFileSync(output, "utf8");
    assert.ok(Buffer.byteLength(expected) > 1024 * 1024, "Exercise output larger than a pipe buffer");
    const piped = await readPipe(script, input);
    assert.equal(piped.signal, null);
    assert.equal(piped.code, exitCode);
    assert.equal(piped.stderr, "");
    const parsed = JSON.parse(piped.stdout);
    assert.deepEqual(parsed, JSON.parse(expected));
    assert.equal(Buffer.compare(Buffer.from(piped.stdout), Buffer.from(expected)), 0, "Piped JSON differs from regular-file output");
    assert.equal(parsed.problems.length, exitCode ? 1024 : 0);
    assert.equal(parsed.summary.accounted, parsed.summary.baseline_tests);
    return { exitCode, bytes: Buffer.byteLength(piped.stdout), problems: parsed.problems.length };
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
}

module.exports = { checkPipedDiagnostics };
if (require.main === module) {
  (async () => {
    for (const code of [0, 1]) console.log(JSON.stringify(await checkPipedDiagnostics(code)));
  })().catch((error) => { console.error(error); process.exitCode = 1; });
}
