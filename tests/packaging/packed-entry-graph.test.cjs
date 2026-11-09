// Run after the TypeScript build: node --test tests/packaging/packed-entry-graph.test.cjs
// Inspect archive bytes, never the staging tree (which contains excluded files).
const assert = require('node:assert/strict');
const { execFileSync } = require('node:child_process');
const { mkdtempSync, readdirSync, rmSync } = require('node:fs');
const { createRequire } = require('node:module');
const { tmpdir } = require('node:os');
const { join, resolve, posix } = require('node:path');
const { test } = require('node:test');

const repo = resolve(__dirname, '../..');
const pkgDir = join(repo, 'typescript/futureagi');
const ts = createRequire(join(pkgDir, 'package.json'))('typescript');

function targets(value) {
  if (typeof value === 'string') return [value];
  if (value && typeof value === 'object') return Object.values(value).flatMap(targets);
  return [];
}

function entryFiles(manifest) {
  const entries = targets(manifest.exports);
  for (const key of ['main', 'module', 'types', 'typings']) {
    if (manifest[key]) entries.push(manifest[key]);
  }
  entries.push(...targets(manifest.typesVersions));
  // esnext is shipped for bundlers but has no separate exports condition.
  for (const entry of [...entries]) {
    if (entry.startsWith('./dist/esm/')) entries.push(entry.replace('./dist/esm/', './dist/esnext/'));
  }
  return [...new Set(entries.map((entry) => {
    assert.ok(entry.startsWith('./') && !entry.includes('*'), `Unsupported entry: ${entry}`);
    return posix.join('package', entry);
  }))];
}

function relativeSpecifiers(name, source) {
  const file = ts.createSourceFile(name, source, ts.ScriptTarget.Latest, true);
  assert.equal(file.parseDiagnostics.length, 0, `Cannot parse packed module: ${name}`);
  const result = [];
  function add(node) {
    if (node && ts.isStringLiteralLike(node) && /^\.{1,2}(?:\/|$)/.test(node.text)) {
      result.push(node.text);
    } else if (node && ts.isTemplateExpression(node) && node.head.text.startsWith('.')) {
      assert.fail(`Computed relative dependency cannot be checked: ${name}`);
    }
  }
  function visit(node) {
    if (ts.isImportDeclaration(node) || ts.isExportDeclaration(node)) add(node.moduleSpecifier);
    if (ts.isImportEqualsDeclaration(node) && ts.isExternalModuleReference(node.moduleReference)) {
      add(node.moduleReference.expression);
    }
    if (ts.isImportTypeNode(node) && ts.isLiteralTypeNode(node.argument)) add(node.argument.literal);
    if (ts.isCallExpression(node)) {
      const callee = node.expression;
      if (callee.kind === ts.SyntaxKind.ImportKeyword ||
          (ts.isIdentifier(callee) && callee.text === 'require') ||
          (ts.isPropertyAccessExpression(callee) && ts.isIdentifier(callee.expression) &&
           callee.expression.text === 'require' && callee.name.text === 'resolve')) {
        add(node.arguments[0]);
      }
    }
    ts.forEachChild(node, visit);
  }
  visit(file);
  return result;
}

function resolveTarget(files, importer, specifier) {
  const target = posix.normalize(posix.join(posix.dirname(importer), specifier));
  assert.ok(target.startsWith('package/'), `Dependency escapes tarball: ${importer} -> ${specifier}`);
  let candidates;
  if (/\.d\.[cm]?ts$/.test(importer)) {
    // Declaration imports often spell the corresponding runtime .js filename.
    const stem = target.replace(/\.(?:[cm]?js)$/, '');
    candidates = [stem + '.d.ts', stem + '.d.mts', stem + '.d.cts', target,
      posix.join(target, 'index.d.ts')];
  } else if (importer.startsWith('package/dist/esm/') || importer.startsWith('package/dist/gateway/esm/')) {
    candidates = [target]; // Node ESM does not add extensions or directory indexes.
  } else {
    // CommonJS and the extensionless esnext bundler output.
    candidates = [target, target + '.js', target + '.cjs', target + '.json', target + '.node',
      posix.join(target, 'index.js'), posix.join(target, 'index.cjs'), posix.join(target, 'index.json')];
  }
  const found = candidates.find((name) => files.has(name));
  assert.ok(found, `Missing packed dependency: ${importer} -> ${specifier} (${target})`);
  return found;
}

function checkGraph(files, manifest) {
  const pending = entryFiles(manifest);
  assert.ok(pending.length > 0, 'No package entry files');
  const visited = new Set();
  let edges = 0;
  while (pending.length) {
    const name = pending.pop();
    assert.ok(files.has(name), `Missing packed entry: ${name}`);
    if (visited.has(name)) continue;
    visited.add(name);
    if (!/\.(?:[cm]?js|[cm]?ts)$/.test(name)) continue;
    for (const specifier of relativeSpecifiers(name, files.get(name))) {
      pending.push(resolveTarget(files, name, specifier));
      edges += 1;
    }
  }
  return { entries: entryFiles(manifest).length, modules: visited.size, edges };
}

function readArchive(tarball) {
  // The standard-library reader rejects links/traversal and never extracts or executes members.
  const source = `import json, pathlib, sys, tarfile
with tarfile.open(sys.argv[1]) as archive:
    files = {}
    for member in archive:
        path = pathlib.PurePosixPath(member.name)
        assert not path.is_absolute() and '..' not in path.parts and path.parts[0] == 'package'
        assert not member.issym() and not member.islnk()
        if member.isfile():
            assert member.name not in files
            files[member.name] = archive.extractfile(member).read().decode('utf-8')
    print(json.dumps(files))
`;
  return new Map(Object.entries(JSON.parse(execFileSync('python3', ['-I', '-B', '-c', source, tarball], {
    cwd: repo, encoding: 'utf8', maxBuffer: 32 * 1024 * 1024,
  }))));
}

const manifest = { exports: { '.': { import: './dist/esm/index.js', require: './dist/src/index.js' },
  './gateway': { import: './dist/gateway/esm/index.js', require: './dist/gateway/cjs/index.js' } } };
function fixture() {
  return new Map([
    ['package/dist/esm/index.js', 'export * from "./resource.js";'],
    ['package/dist/esm/resource.js', 'export * from "./index.js"; import "external-package";'],
    ['package/dist/src/index.js', 'module.exports = require("./resource");'],
    ['package/dist/src/resource/index.js', 'module.exports = {};'],
    ['package/dist/esnext/index.js', 'export * from "./resource";'],
    ['package/dist/esnext/resource.js', 'export const value = 1;'],
    ['package/dist/gateway/esm/index.js', 'export const load = () => import("./resource.js");'],
    ['package/dist/gateway/esm/resource.js', 'export const value = 1;'],
    ['package/dist/gateway/cjs/index.js', 'module.exports = require("./resource.js");'],
    ['package/dist/gateway/cjs/resource.js', 'module.exports = {};'],
  ]);
}

test('walker covers exports, esnext, gateway, cycles and external dependencies', () => {
  assert.deepEqual(checkGraph(fixture(), manifest), { entries: 5, modules: 10, edges: 6 });
});
for (const family of ['esm', 'src', 'esnext', 'gateway/esm', 'gateway/cjs']) {
  test(`walker rejects missing transitive ${family} dependencies`, () => {
    const files = fixture();
    files.delete(`package/dist/${family}/${family === 'src' ? 'resource/index' : 'resource'}.js`);
    assert.throws(() => checkGraph(files, manifest), /Missing packed dependency/);
  });
}
test('walker does not confuse comments or strings with imports', () => {
  assert.deepEqual(relativeSpecifiers('module.js', `// require('./absent.js')
    const text = "import('./absent.js')"; export {x} from './actual.js';`), ['./actual.js']);
});
test('walker checks declarations, require.resolve and literal dynamic imports', () => {
  assert.deepEqual(relativeSpecifiers('module.d.ts', `export * from './other.js';
    import alias = require('./alias'); type T = import('./types.js').T;`), ['./other.js', './alias', './types.js']);
  assert.deepEqual(relativeSpecifiers('module.js', `require.resolve('./other'); import('./lazy.js');`), ['./other', './lazy.js']);
  assert.equal(resolveTarget(new Map([['package/dist/esm/types.d.ts', '']]),
    'package/dist/esm/index.d.ts', './types.js'), 'package/dist/esm/types.d.ts');
});
test('walker rejects missing entries, escaping dependencies and extensionless Node ESM', () => {
  const files = fixture();
  files.delete('package/dist/esnext/index.js');
  assert.throws(() => checkGraph(files, manifest), /Missing packed entry/);
  assert.throws(() => resolveTarget(fixture(), 'package/dist/esm/index.js', './resource'), /Missing packed dependency/);
  assert.throws(() => resolveTarget(fixture(), 'package/dist/esm/index.js', '../../../../outside.js'), /escapes tarball/);
});

test('candidate entry graphs resolve entirely inside the packed tarball', () => {
  const directory = mkdtempSync(join(tmpdir(), 'sdk-pack-graph-'));
  try {
    const out = join(directory, 'candidate');
    execFileSync(process.execPath, [join(pkgDir, 'gateway-client/scripts/stage-package.cjs'), out], {
      cwd: repo, encoding: 'utf8', env: { ...process.env, npm_config_offline: 'true', npm_config_ignore_scripts: 'true' },
    });
    const tarballs = readdirSync(out).filter((name) => name.endsWith('.tgz'));
    assert.equal(tarballs.length, 1);
    const files = readArchive(join(out, tarballs[0]));
    const packed = JSON.parse(files.get('package/package.json'));
    assert.ok(!('scripts' in packed) && !('devDependencies' in packed));
    assert.deepEqual([...files.keys()].filter((name) =>
      /(?:^|\/)(?:__fixtures__|__tests__)(?:\/|$)/.test(name) ||
      /\.(?:test|spec)\.[^/]*$|\.tsbuildinfo$/.test(name)), [],
    'The packed archive must not contain compiled fixtures or other test-only outputs');
    assert.ok(![...files.keys()].some((name) => /^package\/dist\/(esm|src|esnext)\/evals(?:[/.]|$)/.test(name)),
      'The deferred evaluation runner must stay absent');
    const graph = checkGraph(files, packed);
    console.log(JSON.stringify({ packedFiles: files.size, ...graph }));
  } finally {
    rmSync(directory, { recursive: true, force: true });
  }
});
