import fs from 'node:fs';
import path from 'node:path';
import ts from 'typescript';
import { FutureAGIClient } from '../../futureagi-client';
import { BadRequestError } from '../errors';

test('wrong paging dialect reaches the server unchanged', async () => {
  const seen: string[] = [];
  const client = new FutureAGIClient({apiKey: 'fixture-api', secretKey: 'fixture-secret', baseUrl: 'http://localhost:9012', retries: 0,
    fetch: (async (input: RequestInfo | URL, init?: RequestInit) => {
      const request = input instanceof Request ? input : new Request(input, init);
      seen.push(new URL(request.url).search);
      return Response.json({page: ['Unknown field.']}, {status: 400});
    }) as typeof fetch});
  await expect(client.tracing.spans({page: 1})).rejects.toBeInstanceOf(BadRequestError);
  expect(seen).toEqual(['?page=1']);
});

test('generated facade preserves an undeclared paging key at runtime', async () => {
  const seen: string[] = [];
  const client = new FutureAGIClient({apiKey: 'fixture-api', secretKey: 'fixture-secret', baseUrl: 'http://localhost:9012', retries: 0,
    fetch: (async (input: RequestInfo | URL, init?: RequestInit) => {
      const request = input instanceof Request ? input : new Request(input, init);
      seen.push(new URL(request.url).search);
      return Response.json({page_size: ['Unknown field.']}, {status: 400});
    }) as typeof fetch});
  await expect(client.annotationQueues.items.list('queue', {page_size: 4} as any)).rejects.toBeInstanceOf(BadRequestError);
  expect(seen).toEqual(['?page_size=4']);
});

test('alert details preserves zero-based nested log paging', async () => {
  const seen: Record<string, string>[] = [];
  const client = new FutureAGIClient({apiKey: 'fixture-api', secretKey: 'fixture-secret', baseUrl: 'http://localhost:9012', retries: 0,
    fetch: (async (input: RequestInfo | URL, init?: RequestInit) => {
      const request = input instanceof Request ? input : new Request(input, init);
      seen.push(Object.fromEntries(new URL(request.url).searchParams));
      return Response.json({status: true, result: {logs: {results: []}}});
    }) as typeof fetch});
  await client.alerts.details('alert', {page_number: 0, page_size: 2});
  expect(seen).toEqual([{page_number: '0', page_size: '2'}]);
});

const root = path.resolve(__dirname, '../../../../..');
const paging = new Set(['page', 'limit', 'page_size', 'page_number', 'offset', 'cursor', 'cursor_mode', 'page_token', 'current_page', 'current_page_index']);
const specs = ['openapi/sdk/generated/futureagi-sdk.openapi.json', 'openapi/catalog/source.json',
  'openapi/catalog/models-source.json', 'openapi/tracing/source.json', 'openapi/connectors/fa.json', 'openapi/fa-mgmt/swagger.json'];
const read = (file: string) => JSON.parse(fs.readFileSync(path.join(root, file), 'utf8'));
type Ref = {file: string; symbol: string};
type Row = {method: string; path: string; accepted: string[]; bases: Record<string, number>;
  evidence: string[]; documentation: string; methods: {python: Ref[]; typescript: Ref[]}; not_offered?: Record<string, string>;
  upstream_missing_query_parameters: string[]};
function table(): {fa_head: string; operations: Row[]} {
  const file = 'openapi/sdk/pagination-dialects.json';
  expect({paginationTableExists: fs.existsSync(path.join(root, file))}).toEqual({paginationTableExists: true});
  return read(file);
}
function operations(): {spec: string; method: string; route: string; declared: string[]}[] {
  return specs.flatMap(spec => Object.entries(read(spec).paths ?? {}).flatMap(([route, value]) => {
    const item = value as any;
    return ['get', 'post'].filter(method => item[method]).map(method => ({spec, method, route,
      declared: [...(item.parameters ?? []), ...(item[method].parameters ?? [])]
        .filter(p => p.in === 'query' && paging.has(p.name)).map(p => p.name)}));
  }));
}

test('typed operations do not mix pagination dialects', () => {
  for (const op of operations()) {
    // AnnotationQueuePagination explicitly supports page_size as a size alias.
    if (['/model-hub/annotation-queues/', '/simulate/agent-definitions/{agent_id}/versions/{version_id}/call-executions/'].includes(op.route)) continue;
    expect({operation: `${op.method} ${op.route}`, mixed: op.declared.includes('limit') && op.declared.includes('page_size')})
      .toEqual({operation: `${op.method} ${op.route}`, mixed: false});
  }
});

test('table is complete for declared paging and carries FA evidence', () => {
  const data = table();
  expect(data.fa_head).toMatch(/^[a-f0-9]{40}$/);
  const rows = new Map(data.operations.map(row => [`${row.method.toLowerCase()} ${row.path}`, row]));
  expect(rows.size).toBe(data.operations.length);
  for (const row of data.operations) {
    expect(row.evidence.length).toBeGreaterThan(0);
    for (const evidence of row.evidence) expect(evidence).toMatch(/^[^:]+\.py:\d+(?:-\d+)?$/);
    expect(row.documentation).toMatch(/^Pagination:/);
    for (const language of ['python', 'typescript'] as const) {
      expect(row.methods[language].length > 0 || !!row.not_offered?.[language]).toBe(true);
    }
    for (const name of row.accepted) expect(row.documentation).toContain(name);
    for (const [name, base] of Object.entries(row.bases)) {
      expect(row.accepted).toContain(name);
      expect([0, 1]).toContain(base);
      expect(row.documentation).toContain(`${base}-based`);
    }
  }
  for (const op of operations().filter(op => op.declared.length)) {
    const row = rows.get(`${op.method} ${op.route}`);
    expect({operation: `${op.method} ${op.route}`, inventoried: !!row}).toEqual({operation: `${op.method} ${op.route}`, inventoried: true});
    for (const param of op.declared) expect(row!.accepted).toContain(param);
  }
});

test.each([
  ['/model-hub/eval-templates/{template_id}/feedback-list/', ['page', 'page_size'], {page: 0}],
  ['/tracer/trace-session/{id}/eval_logs/', ['page', 'page_size'], {page: 0}],
  ['/tracer/user-alerts/{id}/details/', ['page_number', 'page_size'], {page_number: 0}],
] as const)('inventories source-paginated endpoint omitted by Swagger: %s', (route, accepted, bases) => {
  const row = table().operations.find(row => row.method === 'GET' && row.path === route);
  expect({route, inventoried: !!row}).toEqual({route, inventoried: true});
  expect([...row!.accepted].sort()).toEqual([...accepted].sort());
  expect(row!.bases).toEqual(bases);
  expect([...row!.upstream_missing_query_parameters].sort()).toEqual([...accepted].sort());
});

test('generated TypeScript query types declare only accepted paging keys', () => {
  const file = path.join(root, 'typescript/futureagi/src/generated/openapi/types.gen.ts');
  const ast = ts.createSourceFile(file, fs.readFileSync(file, 'utf8'), ts.ScriptTarget.Latest, true);
  const aliases = new Map(ast.statements.filter(ts.isTypeAliasDeclaration).map(node => [node.name.text, node]));
  for (const row of table().operations) for (const ref of row.methods.typescript) {
    if (!ref.file.endsWith('/generated/openapi/sdk.gen.ts')) continue;
    const name = ref.symbol[0].toUpperCase() + ref.symbol.slice(1) + 'Data';
    const alias = aliases.get(name);
    expect({operation: ref.symbol, typeFound: !!alias}).toEqual({operation: ref.symbol, typeFound: true});
    expect(ts.isTypeLiteralNode(alias!.type)).toBe(true);
    const query = (alias!.type as ts.TypeLiteralNode).members.find(member =>
      ts.isPropertySignature(member) && member.name.getText(ast) === 'query') as ts.PropertySignature | undefined;
    if (!query?.type || !ts.isTypeLiteralNode(query.type)) continue;
    for (const member of query.type.members) {
      if (!ts.isPropertySignature(member)) continue;
      const key = member.name.getText(ast).replace(/['"]/g, '');
      if (paging.has(key)) expect({operation: ref.symbol, key, accepted: row.accepted.includes(key)})
        .toEqual({operation: ref.symbol, key, accepted: true});
    }
  }
});

test('every enumerated TypeScript method documents the accepted dialect', () => {
  const cache = new Map<string, Map<string, {doc: string; query: string[]}>>();
  for (const row of table().operations) for (const ref of row.methods.typescript) {
    if (!cache.has(ref.file)) {
      const source = fs.readFileSync(path.join(root, ref.file), 'utf8');
      const ast = ts.createSourceFile(ref.file, source, ts.ScriptTarget.Latest, true);
      const symbols = new Map<string, {doc: string; query: string[]}>();
      const walk = (node: ts.Node, prefix = '') => {
        let name: string | undefined;
        if (ts.isMethodDeclaration(node) || ts.isFunctionDeclaration(node) || ts.isVariableStatement(node) || ts.isTypeAliasDeclaration(node)) {
          name = ts.isVariableStatement(node) ? node.declarationList.declarations[0]?.name.getText(ast) : node.name?.getText(ast);
          if (name) {
            const query: string[] = [];
            const members = (n: ts.Node) => {
              if (ts.isPropertySignature(n) && n.name) {
                const key = n.name.getText(ast).replace(/['"]/g, '').replace(/[A-Z]/g, c => '_' + c.toLowerCase());
                if (paging.has(key)) query.push(key);
              }
              ts.forEachChild(n, members);
            };
            // Query type aliases contain response/body fields too; only inspect query/options members.
            const queries = (n: ts.Node) => {
              if ((ts.isPropertySignature(n) || ts.isParameter(n)) && ['query', 'options'].includes(n.name.getText(ast))) members(n);
              else ts.forEachChild(n, queries);
            };
            queries(node);
            symbols.set(prefix + name, {doc: source.slice(node.getFullStart(), node.getStart(ast)), query});
          }
        }
        const next = ts.isClassDeclaration(node) && node.name ? prefix + node.name.text + '.' : prefix;
        ts.forEachChild(node, child => walk(child, next));
      };
      walk(ast);
      cache.set(ref.file, symbols);
    }
    const symbol = cache.get(ref.file)!.get(ref.symbol);
    expect({ref, found: !!symbol}).toEqual({ref, found: true});
    expect(symbol!.doc.replace(/\n\s*\* ?/g, ' ').replace(/\s+/g, ' ')).toContain(row.documentation);
    for (const param of symbol!.query) expect(row.accepted).toContain(param);
  }
});
