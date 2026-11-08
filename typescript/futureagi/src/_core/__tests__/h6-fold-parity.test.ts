/** Fold-only portable parity controls. Authored, NOT_RUN; all transport is mock-only. */
import { randomUUID } from 'node:crypto';
import { AuthenticationError, ConfigurationError, PermissionDeniedError, WrongRegionError } from '../errors';
import { CoreServerError } from '../__fixtures__/platform';
import { checkHttpSecurity } from '../http-security';
import { resetWarnings } from '../origins';
import { EU, US, Wire, assertSelectedOnly, failure, invoke, isolate, success, type Mode } from '../__fixtures__/h6-k2w-transport';

let restore: () => void;
let warn: jest.SpyInstance;
beforeEach(() => {
  restore = isolate();
  resetWarnings();
  warn = jest.spyOn(console, 'warn').mockImplementation(() => undefined);
});
afterEach(() => { warn.mockRestore(); resetWarnings(); restore(); });

const scopes: { action: 'core' | 'console'; mode: Mode }[] = [
  { action: 'core', mode: 'keys' }, { action: 'console', mode: 'keys' }, { action: 'console', mode: 'bearer' },
];
test.each(scopes.flatMap(scope => [401, 503].map(status => ({ ...scope, status }))))(
  'fold: $action $mode wrong_region at $status keeps ordinary status', async ({ action, mode, status }) => {
    const wire = new Wire(), c = wire.client(mode, 0, { baseUrl: EU });
    wire.respond = () => Response.json({ error: 'wrong_region' }, { status });
    const error = await failure(() => invoke(c, action));
    expect((error as Error).constructor).toBe(status === 401 ? AuthenticationError : CoreServerError);
    expect(String(error)).not.toContain(US);
    expect(String(error)).not.toContain(EU);
    assertSelectedOnly(wire, EU, mode, 1);
    expect(wire.sleeps).toEqual([]);
  },
);

test.each([US, EU].flatMap(base => (['keys', 'bearer'] as const).flatMap(mode =>
  [false, true].map(recovers => ({ base, mode, recovers })))))(
  'fold: $base $mode 503 retries only selected origin, recovers=$recovers', async ({ base, mode, recovers }) => {
    const wire = new Wire(), c = wire.client(mode, 2, { baseUrl: base });
    wire.respond = r => recovers && wire.requests.length > 1 ? success(r) :
      Response.json({ error: 'omega_service_unavailable' }, { status: 503 });
    if (recovers) await c.environments.list();
    else await expect(c.environments.list()).rejects.toBeInstanceOf(CoreServerError);
    const count = recovers ? 2 : 3;
    assertSelectedOnly(wire, base, mode, count);
    expect(wire.sleeps).toHaveLength(count - 1);
    expect(new Set(wire.requests.map(r => r.url)).size).toBe(1);
  },
);

test.each([false, true])('fold: exact wire authority survives a hostile privacy scrubber, regional=%s', async regional => {
  const wire = new Wire(), c = wire.client('keys', 0, { baseUrl: US });
  wire.respond = () => Response.json(regional ? { error: 'wrong_region' } : { error: { code: 'wrong_region' } }, { status: 403 });
  Object.assign(c._platform.shared, { errorScrubber: () => regional ? { err: '[redacted]' } : { error: 'wrong_region' } });
  const error = await failure(() => c.environments.list());
  expect((error as Error).constructor).toBe(regional ? WrongRegionError : PermissionDeniedError);
  if (regional) {
    expect((error as WrongRegionError).payload).toEqual({ error: 'wrong_region' });
    expect(String(error)).toContain(US);
    expect(String(error)).toContain(EU);
  } else {
    expect(String(error)).not.toContain(US);
    expect(String(error)).not.toContain(EU);
  }
  assertSelectedOnly(wire, US, 'keys', 1);
});

test.each(['keys', 'bearer'] as const)('fold: canonical warning shared between credential modes, first=%s', first => {
  const host = 'fold-parity-' + randomUUID() + '.invalid';
  checkHttpSecurity(new URL(`http://${host}/private-path/a`), first, true);
  checkHttpSecurity(new URL(`http://${host.toUpperCase()}.:80/private-path/b`), first === 'keys' ? 'bearer' : 'keys', true);
  expect(warn).toHaveBeenCalledTimes(1);
  expect(String(warn.mock.calls[0])).toMatch(/cleartext.*deprecat.*future/i);
  expect(String(warn.mock.calls[0])).not.toContain('private-path');
});

test('fold: port zero is distinct from the default port', () => {
  const host = 'port-zero-' + randomUUID() + '.invalid';
  checkHttpSecurity(new URL(`http://${host}:0/`), 'keys');
  checkHttpSecurity(new URL(`http://${host}/`), 'keys');
  expect(warn).toHaveBeenCalledTimes(2);
});

test('fold: IPv4-mapped IPv6 is not the IPv6 loopback exception', async () => {
  const wire = new Wire(), c = wire.client('bearer', 0, { baseUrl: 'http://[::ffff:127.0.0.1]:19876' });
  const error = await failure(() => c.environments.list());
  expect(error).toBeInstanceOf(ConfigurationError);
  expect(error).toMatchObject({ code: 'insecure_http_origin' });
  expect(wire.requests).toEqual([]);
});
