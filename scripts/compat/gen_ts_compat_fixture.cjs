// Called by gen_compat_fixture.py; published declarations arrive as JSON on stdin.
// Parse only: never load JavaScript, package scripts, or configuration from the tarball.
const fs = require('node:fs');
const path = require('node:path');
const ts = require(require.resolve('typescript', {
  paths: [path.resolve(__dirname, '../../typescript/futureagi')],
}));
const input = JSON.parse(fs.readFileSync(0, 'utf8'));
const pkg = JSON.parse(input.files['package/package.json']);
if (pkg.version !== '0.1.2' || Object.keys(pkg.exports).join() !== '.') {
  throw new Error('Expected @future-agi/sdk 0.1.2 with only a root export');
}
for (const name of Object.keys(input.files)) {
  if (!name.startsWith('package/') || name.includes('\\') || name.split('/').some(part => part === '..' || part === '.')) {
    throw new Error(`Unsafe archive declaration path: ${name}`);
  }
}
if (path.posix.isAbsolute(pkg.types) || pkg.types.replace(/^\.\//, '').split('/').includes('..')) {
  throw new Error('Unsafe published types entry point');
}
const files = new Map(Object.entries(input.files).map(([name, text]) => [`/published/${name}`, text]));
const root = `/published/package/${pkg.types.replace(/^\.\//, '')}`;
const options = { target: ts.ScriptTarget.ES2020, skipLibCheck: true, types: [], moduleResolution: ts.ModuleResolutionKind.Node10 };
const host = ts.createCompilerHost(options);
// Standard-library declarations are needed to classify Record/readonly-array
// constants. All package declarations still come exclusively from the tarball.
const libDir = path.dirname(ts.getDefaultLibFilePath(options));
const isLib = name => path.dirname(name) === libDir && /^lib\..*\.d\.ts$/.test(path.basename(name));
const readFile = host.readFile;
const fileExists = host.fileExists;
host.fileExists = name => files.has(name) || (isLib(name) && fileExists(name));
host.readFile = name => files.get(name) ?? (isLib(name) ? readFile(name) : undefined);
host.directoryExists = name => name === libDir || [...files.keys()].some(file => file.startsWith(`${name}/`));
host.getSourceFile = (name, version) => {
  const text = host.readFile(name);
  return text === undefined ? undefined : ts.createSourceFile(name, text, version, true);
};
host.writeFile = () => { throw new Error('Declaration analysis must not emit'); };
const program = ts.createProgram([root], options, host);
const checker = program.getTypeChecker();
const source = program.getSourceFile(root);
const exported = checker.getExportsOfModule(checker.getSymbolAtLocation(source)).map(symbol => {
  const target = symbol.flags & ts.SymbolFlags.Alias ? checker.getAliasedSymbol(symbol) : symbol;
  if (!target.declarations?.length) throw new Error(`Unresolved published export: ${symbol.name}`);
  let runtime = null;
  if (target.flags & ts.SymbolFlags.Value) {
    if (target.flags & (ts.SymbolFlags.Class | ts.SymbolFlags.Function)) runtime = 'function';
    else if (target.flags & (ts.SymbolFlags.Enum | ts.SymbolFlags.ValueModule)) runtime = 'object';
    else {
      const type = checker.getTypeOfSymbolAtLocation(target, target.declarations[0]);
      if (type.getCallSignatures().length) runtime = 'function';
      else if (type.flags & ts.TypeFlags.StringLike) runtime = 'string';
      else if (type.flags & ts.TypeFlags.NumberLike) runtime = 'number';
      else if (type.flags & ts.TypeFlags.BooleanLike) runtime = 'boolean';
      else if (type.flags & ts.TypeFlags.ESSymbolLike) runtime = 'symbol';
      else if (type.flags & ts.TypeFlags.Object) runtime = 'object';
      else throw new Error(`Unknown runtime kind: ${symbol.name}`);
    }
  }
  return { name: symbol.name, type: Boolean(target.flags & ts.SymbolFlags.Type), runtime };
}).sort((a, b) => a.name < b.name ? -1 : a.name > b.name ? 1 : 0);
if (!exported.length) throw new Error('No published exports resolved');
// Keep the declarations, not today's implementation, as the compatibility oracle.
// The test compiler mounts these as virtual files; archive code is never executed.
const declarations = Object.fromEntries([...files].filter(([name]) =>
  name.endsWith('.d.ts') && !name.includes('/__tests__/'))
  .map(([name, text]) => [name.replace('/published/', ''), text])
  .sort(([a], [b]) => a < b ? -1 : a > b ? 1 : 0));
const publicMembers = type => checker.getPropertiesOfType(type).filter(member =>
  member.declarations?.some(d => d.getSourceFile().fileName.startsWith('/published/')) &&
  !member.declarations.some(d => ts.getCombinedModifierFlags(d) &
    (ts.ModifierFlags.Private | ts.ModifierFlags.Protected)));
const signaturePins = new Map();
function pinSignatures(signatures) {
  return signatures.flatMap(signature => {
    const declaration = signature.getDeclaration();
    const sourceFile = declaration?.getSourceFile();
    if (!sourceFile?.fileName.startsWith('/published/')) return [];
    const name = `PublishedCall${declaration.pos}`;
    const filename = sourceFile.fileName;
    if (!signaturePins.has(filename)) signaturePins.set(filename, new Map());
    signaturePins.get(filename).set(name, ts.factory.createTypeAliasDeclaration(
      [ts.factory.createModifier(ts.SyntaxKind.ExportKeyword)], name, undefined,
      ts.factory.createFunctionTypeNode(declaration.typeParameters, declaration.parameters, declaration.type),
    ));
    return [{ file: filename.replace('/published/', ''), name }];
  });
}
const describeType = type => ({
  properties: publicMembers(type).map(member => {
    const t = checker.getTypeOfSymbolAtLocation(member, member.valueDeclaration || member.declarations[0]);
    const readonly = member.declarations?.some(d => ts.getCombinedModifierFlags(d) & ts.ModifierFlags.Readonly)
      || (member.declarations?.some(ts.isGetAccessorDeclaration) && !member.declarations?.some(ts.isSetAccessorDeclaration));
    return { name: member.name, optional: Boolean(member.flags & ts.SymbolFlags.Optional), readonly: Boolean(readonly),
      type: checker.typeToString(t, undefined, ts.TypeFormatFlags.NoTruncation),
      calls: t.getCallSignatures().map(s => checker.signatureToString(s, undefined, ts.TypeFormatFlags.NoTruncation)),
      call_pins: pinSignatures(t.getCallSignatures()) };
  }).sort((a, b) => a.name < b.name ? -1 : a.name > b.name ? 1 : 0),
  calls: type.getCallSignatures().map(s => checker.signatureToString(s, undefined, ts.TypeFormatFlags.NoTruncation)),
  call_pins: pinSignatures(type.getCallSignatures()),
  // Private/protected constructors are not callable by published consumers.
  constructors: type.getConstructSignatures().filter(s => {
    const declaration = s.getDeclaration();
    return !declaration || !(ts.getCombinedModifierFlags(declaration) &
      (ts.ModifierFlags.Private | ts.ModifierFlags.Protected));
  }).map(s => checker.signatureToString(s, undefined, ts.TypeFormatFlags.NoTruncation)),
});
const symbols = checker.getExportsOfModule(checker.getSymbolAtLocation(source));
const surface = {};
for (const item of exported) {
  const symbol = symbols.find(s => s.name === item.name);
  const target = symbol.flags & ts.SymbolFlags.Alias ? checker.getAliasedSymbol(symbol) : symbol;
  surface[item.name] = { class: Boolean(target.flags & ts.SymbolFlags.Class),
    ...(item.type ? { instance: describeType(checker.getDeclaredTypeOfSymbol(target)) } : {}),
    ...(item.runtime !== null ? { value: describeType(checker.getTypeOfSymbolAtLocation(target, target.declarations[0])) } : {}) };
}
const fixture = { distribution: pkg.name, version: pkg.version, archive_sha256: input.archive_sha256,
  exports: exported, root: root.replace('/published/', ''), declarations, surface };
const checks = [
  `import type * as Previous from './published-0.1.2/${fixture.root.replace(/\.d\.ts$/, '')}';`,
  '// Convert methods to function properties so strictFunctionTypes checks inputs, not bivariance.',
  'type StrictCall<T> = T extends (...args: infer A) => infer R ? (...args: A) => R : never;',
  'type StrictConstruct<T> = T extends abstract new (...args: infer A) => infer R ? abstract new (...args: A) => R : never;',
];
for (const item of exported) {
  const spec = surface[item.name];
  const n = item.name;
  for (const [side, shape] of Object.entries(spec).filter(([key]) => key !== 'class')) {
    const type = side === 'instance' ? n : `typeof ${n}`;
    const ref = ns => type.startsWith('typeof ') ? `typeof ${ns}.${n}` : `${ns}.${n}`;
    const id = `${n}_${side}`;
    checks.push(`declare const old_${id}: ${ref('Previous')};`, `declare const now_${id}: ${ref('Root')};`);
    // Interfaces, unions and enums must accept old inputs without new required fields.
    // Classes gain members additively; their constructors are checked separately.
    if (side === 'instance' && !spec.class) checks.push(`const input_${id}: ${ref('Root')} = old_${id};`);
    if (!spec.class) checks.push(`const output_${id}: ${ref('Previous')} = now_${id};`);
    for (const member of shape.properties) {
      if (member.name === 'prototype') continue; // constructor prototype is checked as the instance type
      const key = JSON.stringify(member.name);
      const label = `${id}_${member.name.replace(/[^a-zA-Z0-9_]/g, '_')}`;
      checks.push(`const read_${label}: (${ref('Previous')})[${key}] = now_${id}[${key}];`);
      if (member.calls.length) {
        checks.push(`const call_${label}: StrictCall<(${ref('Previous')})[${key}]> = now_${id}[${key}];`);
        member.call_pins.forEach((pin, index) => checks.push(
          `const overload_${label}_${index}: import('./published-0.1.2/${pin.file.replace(/\.d\.ts$/, '')}').${pin.name} = now_${id}[${key}];`,
        ));
      } else {
        if (side === 'instance' && !spec.class) checks.push(`const write_${label}: Pick<${ref('Root')}, ${key}> = old_${id};`);
        if (spec.class && !member.readonly) checks.push(`now_${id}[${key}] = old_${id}[${key}];`);
      }
    }
    if (shape.calls.length) {
      checks.push(`const callable_${id}: ${ref('Previous')} = now_${id};`,
        `const strict_${id}: StrictCall<${ref('Previous')}> = now_${id};`);
      shape.call_pins.forEach((pin, index) => checks.push(
        `const overload_${id}_${index}: import('./published-0.1.2/${pin.file.replace(/\.d\.ts$/, '')}').${pin.name} = now_${id};`,
      ));
    }
    // Every public 0.1.2 constructor has one signature. Fail closed if this
    // inventory ever changes instead of silently checking only its last overload.
    if (shape.constructors.length > 1) throw new Error(`Constructor overload pins required: ${n}`);
    if (shape.constructors.length) checks.push(
      `const construct_${id}: ${ref('Previous')} = now_${id};`,
      `const strict_construct_${id}: StrictConstruct<${ref('Previous')}> = now_${id};`,
    );
  }
}
// Only public declarations participate: private/protected class members are not
// API contracts and would make otherwise identical classes nominally incompatible.
const publicOnly = context => {
  const visit = node => ts.getCombinedModifierFlags(node) & (ts.ModifierFlags.Private | ts.ModifierFlags.Protected)
    ? undefined : ts.visitEachChild(node, visit, context);
  return node => ts.visitNode(node, visit);
};
const printer = ts.createPrinter({ newLine: ts.NewLineKind.LineFeed });
for (const sourceFile of program.getSourceFiles().filter(s => s.fileName.startsWith('/published/'))) {
  const transformed = ts.transform(sourceFile, [publicOnly]);
  const filename = path.join(path.dirname(process.argv[3]), 'published-0.1.2', sourceFile.fileName.replace('/published/', ''));
  fs.mkdirSync(path.dirname(filename), { recursive: true });
  const augmented = ts.factory.updateSourceFile(transformed.transformed[0], [
    ...transformed.transformed[0].statements, ...(signaturePins.get(sourceFile.fileName)?.values() || []),
  ]);
  let text = printer.printFile(augmented);
  // A unique-symbol sentinel cannot be compared as two independent declarations.
  // Refer to today's exported sentinel TYPE, while the runtime export pin still
  // requires a symbol. This changes no callable/field contract in the baseline.
  const currentRoot = path.posix.relative(path.posix.dirname(`test/published-0.1.2/${sourceFile.fileName.replace('/published/', '')}`), 'src/index');
  for (const item of exported.filter(item => item.runtime === 'symbol')) {
    text = text.replace(new RegExp(`(declare const ${item.name}: )unique symbol;`, 'g'),
      `$1typeof import(${JSON.stringify(currentRoot)}).${item.name};`);
  }
  fs.writeFileSync(filename, '// Generated public declarations from @future-agi/sdk 0.1.2; do not edit.\n' + text);
  transformed.dispose();
}
const typeTest = [
  '// Generated from the published 0.1.2 declarations; do not trim to match current source.',
  "import type * as Root from '../src/index';",
  '',
  'export type PublishedTypes = [',
  ...exported.filter(item => item.type).map(item => `  Root.${item.name},`),
  '];',
  '',
  'export type PublishedValues = [',
  ...exported.filter(item => item.runtime !== null).map(item => `  typeof Root.${item.name},`),
  '];',
  '',
  ...checks,
  '',
].join('\n');
for (const [filename, content] of [[process.argv[2], `${JSON.stringify(fixture, null, 2)}\n`], [process.argv[3], typeTest]]) {
  fs.mkdirSync(path.dirname(filename), { recursive: true });
  fs.writeFileSync(filename, content);
}
console.log(`Pinned ${exported.length} TypeScript root exports (${exported.filter(item => item.runtime).length} runtime values)`);
