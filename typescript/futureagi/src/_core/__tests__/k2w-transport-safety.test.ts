/** K2W launch scope: bearer HTTP guard, compatible keys warnings, no redirect
 * credential forwarding. Authored tests only; no claimed execution or readiness. */
import { randomUUID } from 'node:crypto';
import { inspect } from 'node:util';
import * as errors from '../errors';
import { API_KEY, SECRET_KEY, TOKEN, EU, US, SANDBOX_ABSENT, Wire, assertPrivate, assertSelectedOnly,
  failure, invoke, isolate, type Mode } from '../__fixtures__/h6-k2w-transport';

let restore: () => void;
let warn: jest.SpyInstance;
beforeEach(() => { restore = isolate(); warn = jest.spyOn(console, 'warn').mockImplementation(() => undefined); });
afterEach(() => { warn.mockRestore(); restore(); });

function assertWarnings(expected: number, keys = false): void {
  expect(warn).toHaveBeenCalledTimes(expected);
  for (const call of warn.mock.calls) {
    const text = inspect(call);
    expect(text).toMatch(/http|cleartext|unencrypted/i);
    if (keys) { expect(text).toMatch(/key/i); expect(text).toMatch(/future|deprecat|will refus/i); }
    for (const secret of [API_KEY, SECRET_KEY, TOKEN, 'private-path']) expect(text).not.toContain(secret);
  }
}

test.each(['argument', 'environment', 'derived'].flatMap(source => ['argument', 'environment'].map(tokenSource => ({ source, tokenSource }))))(
  'K2W bearer HTTP nonloopback refused before transport: $source token=$tokenSource', async ({ source, tokenSource }) => {
  const wire = new Wire();
  const options: { baseUrl: string; platformBaseUrl?: string; platformToken?: string } = { baseUrl: 'https://base-k2w.invalid' };
  if (tokenSource === 'environment') { process.env.FI_PLATFORM_TOKEN = TOKEN; options.platformToken = undefined; }
  if (source === 'argument') options.platformBaseUrl = 'http://bearer-k2w.invalid/omega/api';
  else if (source === 'environment') process.env.FI_PLATFORM_BASE_URL = 'http://bearer-k2w.invalid/omega/api';
  else options.baseUrl = 'http://bearer-k2w.invalid';
  const c = wire.client('bearer', undefined, options);
  const got = await failure(() => c.environments.list());
  expect(got).toBeInstanceOf(errors.ConfigurationError);
  expect(wire.requests).toEqual([]);
  expect(String(got)).toMatch(/http/i);
  expect(String(got)).toMatch(/allowInsecureHttp|FI_ALLOW_INSECURE_HTTP/);
  assertPrivate(got);
});

test.each((['keys', 'bearer'] as const).flatMap(mode => [
  'http://localhost:19876', 'http://127.0.0.1:19876', 'http://[::1]:19876', 'https://secure-k2w.invalid',
].map(base => ({ mode, base }))))('K2W loopback/HTTPS unchanged: $mode $base', async ({ mode, base }) => {
  const wire = new Wire(), c = wire.client(mode, 0, { baseUrl: base });
  await c.environments.list();
  assertSelectedOnly(wire, base, mode, 1);
  expect(warn).not.toHaveBeenCalled();
});

test.each(['argument', 'environment'])('K2W named bearer optout warns once/origin and survives clone: %s', async flag => {
  const wire = new Wire(), host = 'k2w-' + randomUUID() + '.invalid';
  if (flag === 'environment') process.env.FI_ALLOW_INSECURE_HTTP = '1';
  const options = flag === 'argument' ? { allowInsecureHttp: true } : {};
  // Same host/scheme/port despite different paths and explicit default port.
  // A different port is another origin; neither warning echoes path or secrets.
  for (const platformBaseUrl of [`http://${host}/private-path/a`, `http://${host}:80/private-path/b`, `http://${host}:8080/private-path/c`]) {
    const c = wire.client('bearer', undefined, { platformBaseUrl, ...options });
    const clone = c.withOptions({ retries: 0 }); // only existing clone settings
    await c.environments.list();
    await clone.environments.list();
  }
  expect(wire.requests).toHaveLength(6);
  for (const request of wire.requests) expect(request.headers.get('authorization')).toBe('Bearer ' + TOKEN);
  assertWarnings(2);
});

test.each(['core', 'console'] as const)('K2W keys HTTP existing %s namespace warns, never globally refuses', async scope => {
  const wire = new Wire(), host = 'keys-k2w-' + randomUUID() + '.invalid';
  for (const baseUrl of [`http://${host}/private-path/a`, `http://${host}:80/private-path/b`, `http://${host}:8080/private-path/c`]) {
    const c = wire.client('keys', 0, { baseUrl });
    await invoke(c, scope);
    await invoke(c, scope);
  }
  expect(wire.requests).toHaveLength(6);
  for (const request of wire.requests) {
    expect(request.headers.get('x-api-key')).toBe(API_KEY);
    expect(request.headers.get('x-secret-key')).toBe(SECRET_KEY);
  }
  assertWarnings(2, true);
});

test('K2W explicit HTTP platform warns with an HTTPS core base', async () => {
  const wire = new Wire(), base = 'http://explicit-k2w-' + randomUUID() + '.invalid';
  const c = wire.client('keys', 0, { baseUrl: 'https://core-k2w.invalid', platformBaseUrl: base + '/omega/api' });
  await c.environments.list(); await c.environments.list();
  assertSelectedOnly(wire, base, 'keys', 2);
  assertWarnings(1, true);
});

test('K2W custom host optout is not the insecure HTTP optout', async () => {
  const wire = new Wire(), c = wire.client('bearer', undefined, {
    baseUrl: 'http://custom-k2w.invalid', allowCustomPlatformUrl: true,
  });
  const got = await failure(() => c.environments.list());
  expect(got).toBeInstanceOf(errors.ConfigurationError);
  expect(wire.requests).toEqual([]);
});

(SANDBOX_ABSENT ? test.skip : test).each((['keys', 'bearer'] as const).flatMap(mode => ['argument', 'environment'].map(flag => ({ mode, flag }))))(
  'K2W global optout cannot weaken sandbox HTTPS: $mode $flag' + " [NOT_APPLICABLE_AT_FOLD: sandbox surface absent (python/tests/platform/test_sandboxes_absent.py); runs automatically when it returns]", async ({ mode, flag }) => {
    if (flag === 'environment') process.env.FI_ALLOW_INSECURE_HTTP = '1';
    const options = flag === 'argument' ? { allowInsecureHttp: true } : {};
    const wire = new Wire(), c = wire.client(mode, undefined, { baseUrl: 'http://sandbox-k2w.invalid', ...options });
    // @ts-expect-error NOT_APPLICABLE_AT_FOLD: sandbox surface absent (python/tests/platform/test_sandboxes_absent.py); runs automatically when it returns
    const got = await failure(() => c.sandboxes.list());
    expect(got).toBeInstanceOf(errors.ConfigurationError);
    expect(got).toMatchObject({ code: 'insecure_sandbox_origin' });
    expect(wire.requests).toEqual([]);
    assertPrivate(got);
  },
);

test.each(['arguments', 'environment'])('K2W MixedCredentialsError precedes new refusal for valid origin: %s', async source => {
  const wire = new Wire();
  const options = source === 'arguments' ? { apiKey: API_KEY, secretKey: SECRET_KEY } : {};
  if (source === 'environment') { process.env.FI_API_KEY = API_KEY; process.env.FI_SECRET_KEY = SECRET_KEY; }
  const c = wire.client('bearer', undefined, { baseUrl: 'http://mixed-k2w.invalid', ...options });
  const got = await failure(() => c.environments.list());
  expect(got).toBeInstanceOf(errors.MixedCredentialsError);
  expect(got).toMatchObject({ code: 'mixed_credentials' });
  expect(wire.requests).toEqual([]);
  assertPrivate(got);
});

test('K2W makes no universal mixed precedence claim for malformed origins', async () => {
  const wire = new Wire(), c = wire.client('bearer', undefined, {
    apiKey: API_KEY, secretKey: SECRET_KEY, platformBaseUrl: 'https://invalid-k2w.invalid/?query=not-an-origin',
  });
  await expect(c.environments.list()).rejects.toBeInstanceOf(errors.PlatformNotConfiguredError);
  expect(wire.requests).toEqual([]);
});

const scopes: { scope: 'core' | 'console'; mode: Mode }[] = [
  { scope: 'core', mode: 'keys' }, { scope: 'console', mode: 'keys' }, { scope: 'console', mode: 'bearer' },
];
const redirects = scopes.flatMap(pair => [[US, EU], [EU, US]].flatMap(([base, other]) =>
  [undefined, 0].flatMap(retries => [301, 302, 303, 307, 308].flatMap(status => [false, true].map(downgrade =>
    ({ ...pair, base: base!, other: other!, retries, status, downgrade }))))));
test.each(redirects)('K2W $scope $mode $base $status retries=$retries downgrade=$downgrade never forwards credentials', async row => {
  const target = (row.downgrade ? row.base.replace('https://', 'http://') : row.other) + '/untrusted-path?not-a-key=synthetic-marker';
  const wire = new Wire();
  wire.respond = () => new Response(null, { status: row.status, headers: { location: target } });
  const c = wire.client(row.mode, row.retries, { baseUrl: row.base });
  const got = await failure(() => invoke(c, row.scope));
  expect(got).toBeInstanceOf(errors.UnexpectedRedirectError);
  assertSelectedOnly(wire, row.base, row.mode, 1);
  expect(wire.sleeps).toEqual([]);
  // Non-sandbox diagnostics may retain the target host, never path/query/URL.
  expect(String(got)).not.toContain(target);
  for (const value of [API_KEY, SECRET_KEY, TOKEN, 'synthetic-marker']) expect(String(got)).not.toContain(value);
});
