/** Mock-only H6/K2W public-client harness, authored against 219fa74698afa6173e8f48192783643d54e5c873.
 * Regional hostnames are configuration strings, not live readiness evidence.
 * The public fetch seam and backoff sleep are the ONLY replacements. */
import { Socket } from 'node:net';
import { inspect } from 'node:util';
import { FutureAGIClient, type FutureAGIClientOptions } from '../../futureagi-client';
import { PLATFORM_OPERATIONS } from '../../generated/platform/policy.gen';

export const US = 'https://api.futureagi.com';
export const EU = 'https://api-eu.futureagi.com';
export const API_KEY = 'h6-synthetic-api-key-not-valid';
export const SECRET_KEY = 'h6-synthetic-secret-key-not-valid';
export const TOKEN = 'h6-synthetic-bearer-token-not-valid';
export const SUBMITTED = 'h6-synthetic-private-input';
export const SID = 'sbx_' + 'a'.repeat(24);
export const ACTIONS = ['json', 'create', 'sse', 'upload', 'download'] as const;
export type Action = typeof ACTIONS[number] | 'core' | 'console';
export type Mode = 'keys' | 'bearer';
export const SANDBOX_ABSENT = !Object.keys(PLATFORM_OPERATIONS).some((name) => name.startsWith("sandboxes."));
export const NOT_APPLICABLE_AT_FOLD = "NOT_APPLICABLE_AT_FOLD: sandbox surface absent (python/tests/platform/test_sandboxes_absent.py); runs automatically when it returns";

export function success(_r: Request): Response {
  return Response.json({ environments: [], count: 0, next: null, previous: null, results: [] });
}

export class Wire {
  readonly requests: Request[] = [];
  readonly sleeps: number[] = [];
  respond: (request: Request) => Response = success;
  readonly fetch: typeof fetch = async (input, init) => {
    const request = new Request(input, init);
    this.requests.push(request.clone());
    // A real fetch would follow by default. Assert this at the actual fetch seam,
    // not just against a mock which is incapable of following a redirect.
    expect(request.redirect).toBe('manual');
    return this.respond(request);
  };
  client(mode: Mode = 'keys', retries?: number,
         options: FutureAGIClientOptions & { allowInsecureHttp?: boolean } = {}): FutureAGIClient {
    const c = new FutureAGIClient({
      ...(mode === 'keys' ? { apiKey: API_KEY, secretKey: SECRET_KEY } : { platformToken: TOKEN }),
      ...(retries !== undefined ? { retries } : {}), ...options, fetch: this.fetch,
    });
    // Retain the real public client, resolver, tables and executor. No policy mock.
    Object.assign(c._platform.shared, { sleep: async (ms: number) => { this.sleeps.push(ms); } });
    return c;
  }
}

export function isolate(): () => void {
  const keys = ['FI_BASE_URL', 'FI_PLATFORM_BASE_URL', 'FI_API_KEY', 'FI_SECRET_KEY', 'FI_PLATFORM_TOKEN',
    'FI_WORKSPACE_ID', 'FI_ORGANIZATION_ID', 'FI_ALLOW_CUSTOM_PLATFORM_URL', 'FI_ALLOW_INSECURE_HTTP',
    'FI_EXTRA_HEADERS', 'NODE_TLS_REJECT_UNAUTHORIZED'];
  const before = keys.map(key => [key, process.env[key]] as const);
  for (const key of keys) delete process.env[key];
  const attempted: string[] = [];
  const socket = jest.spyOn(Socket.prototype, 'connect').mockImplementation(function (): never {
    attempted.push('socket'); throw new Error('H6/K2W tests must not open sockets');
  });
  const nativeFetch = jest.spyOn(globalThis, 'fetch').mockImplementation(async () => {
    attempted.push('native fetch'); throw new Error('H6/K2W fake fetch was bypassed');
  });
  return () => {
    socket.mockRestore(); nativeFetch.mockRestore();
    for (const [key, value] of before) {
      if (value === undefined) delete process.env[key]; else process.env[key] = value;
    }
    expect(attempted).toEqual([]);
  };
}

export async function invoke(c: FutureAGIClient, action: Action): Promise<unknown> {
  if (action === 'console') return c.environments.list();
  if (action === 'core') return c.prompts.list();
  throw new Error(NOT_APPLICABLE_AT_FOLD);
}

/** Never throw a test sentinel into the SDK catch branch. Success is asserted by the caller. */
export async function failure(call: () => PromiseLike<unknown>): Promise<unknown> {
  try { await call(); } catch (error) { return error; }
  return undefined;
}

export function assertPrivate(error: unknown, logs: unknown[] = [], extra: string[] = []): void {
  const dump = String(error) + inspect(error, { depth: 20, showHidden: true, customInspect: false }) +
    JSON.stringify(error) + inspect(logs, { depth: 20 });
  for (const value of [API_KEY, SECRET_KEY, TOKEN, SUBMITTED, ...extra]) expect(dump).not.toContain(value);
  expect((error as Error).cause).toBeUndefined();
}

export function assertSelectedOnly(wire: Wire, base: string, mode: Mode, count: number): void {
  expect(wire.requests).toHaveLength(count);
  const foreign = wire.requests.filter(r => new URL(r.url).origin !== new URL(base).origin);
  expect(foreign).toEqual([]); // even a credential-free automatic probe is forbidden
  expect(foreign.flatMap(r => ['authorization', 'x-api-key', 'x-secret-key'].filter(h => r.headers.has(h)))).toEqual([]);
  for (const r of wire.requests) {
    expect(r.redirect).toBe('manual');
    if (mode === 'keys') {
      expect(r.headers.get('x-api-key')).toBe(API_KEY);
      expect(r.headers.get('x-secret-key')).toBe(SECRET_KEY);
      expect(r.headers.has('authorization')).toBe(false);
    } else {
      expect(r.headers.get('authorization')).toBe('Bearer ' + TOKEN);
      expect(r.headers.has('x-api-key')).toBe(false);
      expect(r.headers.has('x-secret-key')).toBe(false);
    }
  }
}

/** Register every supplemental row; only the scout's withdrawn-surface rows are skipped. */
export function foldEach<T>(rows: readonly T[], sandbox: (row: T) => boolean) {
  return (name: string, body: (row: T) => void | Promise<unknown>): void => {
    for (const row of rows) {
      const skipped = sandbox(row);
      const title = `${name} ${JSON.stringify(row)}${skipped ? ` [${NOT_APPLICABLE_AT_FOLD}]` : ''}`;
      (skipped && SANDBOX_ABSENT ? test.skip : test)(title, () => body(row));
    }
  };
}
