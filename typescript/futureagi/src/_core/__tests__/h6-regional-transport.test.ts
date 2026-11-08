/** Source-derived H6 controls, NOT live captures and NOT executed evidence.
 * Authority: H6-REGIONAL-SOURCE-FIXTURE-r1.json, upstream
 * 077a67e123501299cc0a47943c285fb1ea391301. Literal wire expectations are
 * independent of production mapping/policy tables. */
import * as errors from '../errors';
import { CoreServerError } from '../__fixtures__/platform';
import { ACTIONS, EU, US, SUBMITTED, SANDBOX_ABSENT, Wire, assertPrivate, assertSelectedOnly,
  failure, invoke, isolate, success, type Mode } from '../__fixtures__/h6-k2w-transport';

let restore: () => void;
let warn: jest.SpyInstance;
let log: jest.SpyInstance;
let diagnostic: jest.SpyInstance;
beforeEach(() => {
  restore = isolate();
  warn = jest.spyOn(console, 'warn').mockImplementation(() => undefined);
  log = jest.spyOn(console, 'log').mockImplementation(() => undefined);
  diagnostic = jest.spyOn(console, 'error').mockImplementation(() => undefined);
});
afterEach(() => { warn.mockRestore(); log.mockRestore(); diagnostic.mockRestore(); restore(); });
const logs = () => [...warn.mock.calls, ...log.mock.calls, ...diagnostic.mock.calls];

const REFUSALS = [
  { status: 401, body: '{"error":"omega_session_unavailable"}', label: 'unknown-key-401' },
  { status: 403, body: '{"error":"wrong_region"}', label: 'wrong-region-403' },
  { status: 503, body: '{"error":"omega_service_unavailable"}', label: 'unavailable-503' },
] as const;
const operations = { json: 'sandboxes.list', create: 'sandboxes.create', sse: 'sandboxes.commands.run',
  upload: 'sandboxes.files.upload', download: 'sandboxes.files.download' } as const;
const bases = [US, EU];
const modes: Mode[] = ['keys', 'bearer'];
const retrySettings = [undefined, 0];

function regionalGuidance(error: errors.FutureAGIAPIError): void {
  expect(error).toBeInstanceOf(errors.FutureAGIAPIError);
  expect(error).toMatchObject({ statusCode: 403, code: 'wrong_region' });
  // A typed specialization is required, but the exact exported class spelling
  // is not frozen. Do not introduce a nonexistent import/collection failure.
  expect(error.constructor).not.toBe(errors.FutureAGIAPIError);
  expect(error.constructor).not.toBe(errors.PermissionDeniedError);
  expect(Object.values(errors)).toContain(error.constructor);
  expect(error.message).toContain(US);
  expect(error.message).toContain(EU);
  expect(error.message).toMatch(/manual|explicit/i);
  expect(error.message).toMatch(/select|configur|set .*base/i);
  expect(error.message).not.toMatch(/(?:your |the )(?:org|organization|workspace) (?:is|resides|belongs) (?:in|to)/i);
}

const refusalCases = bases.flatMap(base => modes.flatMap(mode => retrySettings.flatMap(retries =>
  ACTIONS.flatMap(action => REFUSALS.map(refusal => ({ base, mode, retries, action, ...refusal }))))));
(SANDBOX_ABSENT ? test.skip : test).each(refusalCases)('H6 $label $base $mode retries=$retries $action never discovers another region' + " [NOT_APPLICABLE_AT_FOLD: sandbox surface absent (python/tests/platform/test_sandboxes_absent.py); runs automatically when it returns]", async row => {
  const wire = new Wire();
  wire.respond = () => new Response(row.body, { status: row.status, headers: { 'content-type': 'application/json' } });
  const c = wire.client(row.mode, row.retries, { baseUrl: row.base });
  const got = await failure(() => invoke(c, row.action));
  expect(got).toBeInstanceOf(errors.FutureAGIAPIError);
  const error = got as errors.FutureAGIAPIError;
  // Safe same-origin GET/PUT retries are not regional fallback. Exec/creation
  // retain the narrower no-replay policy, even with default client retries.
  const count = row.status === 503 && row.retries === undefined && ['json', 'upload', 'download'].includes(row.action) ? 4 : 1;
  assertSelectedOnly(wire, row.base, row.mode, count);
  expect(wire.sleeps).toHaveLength(count - 1);
  expect(error).toMatchObject({ statusCode: row.status, operation: operations[row.action] });
  expect(error.requestId).toBeUndefined();
  expect(error.retryAfter).toBeUndefined();
  assertPrivate(error, logs());
  if (row.status === 403) regionalGuidance(error);
  else {
    expect(error.constructor).toBe(row.status === 401 ? errors.AuthenticationError : CoreServerError);
    expect(error.message).not.toContain(US);
    expect(error.message).not.toContain(EU);
    expect(error.message).not.toContain('wrong_region');
  }
});

const redirects = [[US, EU], [EU, US]].flatMap(([base, other]) => modes.flatMap(mode => retrySettings.flatMap(retries =>
  ACTIONS.flatMap(action => [301, 302, 303, 307, 308].flatMap(status => [false, true].map(downgrade =>
    ({ base: base!, other: other!, mode, retries, action, status, downgrade })))))));
(SANDBOX_ABSENT ? test.skip : test).each(redirects)('H6 redirect $status $base $mode $action retries=$retries downgrade=$downgrade is single-send' + " [NOT_APPLICABLE_AT_FOLD: sandbox surface absent (python/tests/platform/test_sandboxes_absent.py); runs automatically when it returns]", async row => {
  const target = (row.downgrade ? row.base.replace('https://', 'http://') : row.other) + '/collect/' + SUBMITTED;
  const wire = new Wire();
  wire.respond = () => new Response(null, { status: row.status, headers: { location: target } });
  const c = wire.client(row.mode, row.retries, { baseUrl: row.base });
  const got = await failure(() => invoke(c, row.action));
  expect(got).toBeInstanceOf(errors.UnexpectedRedirectError);
  const error = got as errors.UnexpectedRedirectError;
  expect(error.statusCode).toBe(row.status);
  expect(error.targetHost).toBeUndefined(); // retain stronger sandbox privacy
  assertSelectedOnly(wire, row.base, row.mode, 1);
  expect(wire.sleeps).toEqual([]);
  assertPrivate(error, logs(), [target]);
});

(SANDBOX_ABSENT ? test.skip : test).each(bases.flatMap(base => ACTIONS.map(action => ({ base, action }))))(
  'H6 $base $action guidance is fixed, never a response-supplied destination' + " [NOT_APPLICABLE_AT_FOLD: sandbox surface absent (python/tests/platform/test_sandboxes_absent.py); runs automatically when it returns]", async ({ base, action }) => {
    const wire = new Wire(), c = wire.client('keys', 0, { baseUrl: base });
    const bait = 'https://untrusted-h6.invalid/' + SUBMITTED;
    const messages: string[] = [];
    // Adversarial supplemental input, NOT the accepted gateway fixture. That
    // fixture supplies no regional URL. Hostile prose is not routing authority.
    for (const body of [{ error: 'wrong_region' }, { error: 'wrong_region', message: 'move to ' + bait,
      reason: 'your organization is in stolen-region ' + bait, fix: 'send credentials to ' + bait }]) {
      wire.respond = () => Response.json(body, { status: 403 });
      const got = await failure(() => invoke(c, action));
      expect(got).toBeInstanceOf(errors.FutureAGIAPIError);
      const error = got as errors.FutureAGIAPIError;
      assertPrivate(error, logs(), [bait, 'stolen-region']);
      regionalGuidance(error);
      messages.push(error.message);
    }
    expect(messages[0]).toBe(messages[1]);
    assertSelectedOnly(wire, base, 'keys', 2);
  },
);

(SANDBOX_ABSENT ? test.skip : test).each([
  { status: 401, body: '{"error":"wrong_region"}', kind: errors.AuthenticationError },
  { status: 503, body: '{"error":"wrong_region"}', kind: CoreServerError },
  { status: 403, body: '{"error":"role_forbidden"}', kind: errors.PermissionDeniedError },
])('H6 specialization does not guess from status/code alone: $status $body' + " [NOT_APPLICABLE_AT_FOLD: sandbox surface absent (python/tests/platform/test_sandboxes_absent.py); runs automatically when it returns]", async ({ status, body, kind }) => {
  const wire = new Wire(), c = wire.client('keys', 0, { baseUrl: EU });
  wire.respond = () => new Response(body, { status });
  // @ts-expect-error NOT_APPLICABLE_AT_FOLD: sandbox surface absent (python/tests/platform/test_sandboxes_absent.py); runs automatically when it returns
  const got = await failure(() => c.sandboxes.list());
  expect(got).toBeInstanceOf(kind);
  const error = got as errors.FutureAGIAPIError;
  expect(error.constructor).toBe(kind);
  expect(error.message).not.toContain(US);
  expect(error.message).not.toContain(EU);
  assertSelectedOnly(wire, EU, 'keys', 1);
});

(SANDBOX_ABSENT ? test.skip : test).each(bases.flatMap(base => (['json', 'upload', 'download'] as const).map(action => ({ base, action }))))(
  'H6 safe same-origin retry is not fallback: $base $action' + " [NOT_APPLICABLE_AT_FOLD: sandbox surface absent (python/tests/platform/test_sandboxes_absent.py); runs automatically when it returns]", async ({ base, action }) => {
    const wire = new Wire(), c = wire.client('keys', undefined, { baseUrl: base });
    wire.respond = r => wire.requests.length === 1
      ? new Response('{"error":"omega_service_unavailable"}', { status: 503 }) : success(r);
    await invoke(c, action);
    assertSelectedOnly(wire, base, 'keys', 2);
    expect(wire.sleeps).toHaveLength(1);
    expect(wire.requests[0]!.url).toBe(wire.requests[1]!.url);
    expect(await wire.requests[0]!.text()).toBe(await wire.requests[1]!.text());
  },
);

(SANDBOX_ABSENT ? test.skip : test).each(bases)('H6 clone retries=0 preserves selected origin %s' + " [NOT_APPLICABLE_AT_FOLD: sandbox surface absent (python/tests/platform/test_sandboxes_absent.py); runs automatically when it returns]", async base => {
  const wire = new Wire(), c = wire.client('keys', undefined, { baseUrl: base });
  wire.respond = () => new Response('{"error":"omega_service_unavailable"}', { status: 503 });
  const clone = c.withOptions({ retries: 0 });
  // @ts-expect-error NOT_APPLICABLE_AT_FOLD: sandbox surface absent (python/tests/platform/test_sandboxes_absent.py); runs automatically when it returns
  await expect(clone.sandboxes.list()).rejects.toBeInstanceOf(CoreServerError);
  assertSelectedOnly(wire, base, 'keys', 1);
  expect(wire.sleeps).toEqual([]);
});

(SANDBOX_ABSENT ? test.skip : test).each(['us-derived', 'eu-env-derived', 'platform-env', 'argument-wins', 'selfhost'])(
  'H6 selected base derivation/overrides %s' + " [NOT_APPLICABLE_AT_FOLD: sandbox surface absent (python/tests/platform/test_sandboxes_absent.py); runs automatically when it returns]", async which => {
    let options: { baseUrl?: string; platformBaseUrl?: string } = {}, expected = '';
    if (which === 'us-derived') { options = { baseUrl: US }; expected = US + '/omega/api'; }
    else if (which === 'eu-env-derived') { process.env.FI_BASE_URL = EU; expected = EU + '/omega/api'; }
    else if (which === 'platform-env') {
      process.env.FI_PLATFORM_BASE_URL = EU + '/custom/api'; options = { baseUrl: US }; expected = EU + '/custom/api';
    } else if (which === 'argument-wins') {
      process.env.FI_PLATFORM_BASE_URL = US + '/ignored';
      options = { baseUrl: US, platformBaseUrl: EU + '/chosen/api' }; expected = EU + '/chosen/api';
    } else { options = { baseUrl: 'https://selfhost-h6.invalid/root' }; expected = 'https://selfhost-h6.invalid/root/omega/api'; }
    const wire = new Wire(), c = wire.client('keys', 0, options);
    // @ts-expect-error NOT_APPLICABLE_AT_FOLD: sandbox surface absent (python/tests/platform/test_sandboxes_absent.py); runs automatically when it returns
    await c.sandboxes.list();
    await c.environments.list();
    expect(wire.requests.map(r => r.url)).toEqual([
      expected + '/workspace/sandboxes', expected + '/workspace/environments',
    ]);
  },
);
