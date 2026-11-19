/**
 * Execute one case with the raw HTTP transport, in one mode, against one target.
 *
 * Steps: resolve the caller's credential (skip when the fixtures hold none), run `setup` steps,
 * make the call `repeat` times (each attempt is checked against the expectation and, for a 2xx
 * on a documented operation, against the contract's response or event schema), capture values,
 * run `cleanup` steps, and return a verdict: pass, fail, xfail (an expected failure with its
 * owner), xpass (an expected failure that passed: the known gap may be closed) or skip.
 * Nothing secret and no response body is put in the result: only statuses, codes, ids and shapes.
 */
import { randomUUID } from "node:crypto";
import { expectFor } from "../../lib/cases.mjs";
import { checkResponse, eventSchema, opKey } from "../../lib/contract.mjs";
import { errorClassFor, normalizeError } from "../../lib/errors.mjs";
import { checkOutcome, get } from "../../lib/expect.mjs";
import { checkSchema, resolvePointer } from "../../lib/schema-check.mjs";
import { fill, fillPath } from "../../lib/template.mjs";
import { credentialFor } from "./auth.mjs";
import { rawCall } from "./client.mjs";

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

function declaresIdempotencyKey(contract, operation) {
  const params = operation?.op?.parameters ?? [];
  return params.some((p) => {
    const param = p && typeof p.$ref === "string" ? resolvePointer(contract.openapi, p.$ref) : p;
    return param && param.in === "header" && /^idempotency-key$/i.test(param.name);
  });
}

/** Observe one raw response as an outcome (the shape expect.mjs and compare.mjs read). */
export function toOutcome(response) {
  if (response.status === null) {
    return { status: null, code: "transport_error", errorClass: "APIConnectionError", body: null, events: [], headers: {}, transportError: response.transportError, durationMs: response.durationMs };
  }
  const header = (name) => response.headers[name];
  const ok = response.status >= 200 && response.status < 300;
  const error = ok ? null : normalizeError(response.status, response.body, header);
  return {
    status: response.status,
    code: error?.code ?? null,
    errorClass: ok ? null : errorClassFor(response.status, error.code),
    errorShape: error?.shape,
    retryAfterSeconds: error?.retryAfterSeconds,
    requestId: header("x-request-id") ?? error?.requestId,
    upstreamRequestId: error?.upstreamRequestId ?? (typeof response.body?.request_id === "string" ? response.body.request_id : undefined),
    receiptId: header("x-omega-receipt-id") ?? response.body?.receipt?.auditEntryId,
    body: response.body,
    events: response.events ?? [],
    headers: response.headers,
    location: header("location"),
    nonJson: response.nonJson,
    streamEnded: response.streamEnded,
    durationMs: response.durationMs,
  };
}

function contractFailures(contract, operation, outcome, known) {
  if (!operation?.documented || outcome.status === null || outcome.status < 200 || outcome.status >= 300) return { checked: false, failures: [], drift: [] };
  if (outcome.events.length) {
    const union = eventSchema(contract, operation);
    if (!union) return { checked: false, failures: [], drift: [] };
    const failures = [];
    for (const event of outcome.events) {
      // The union describes whole frames: the SSE `event:` name, its `id:` (when sent) and the JSON `data:`.
      const frame = { event: event.event, ...(event.id !== undefined && event.id !== null ? { id: event.id } : {}), data: event.data };
      const errors = checkSchema(union, frame, { root: contract.openapi, at: `event(${event.type})` });
      failures.push(...errors.map((e) => `contract: ${e}`));
    }
    return splitDrift(checked(true), failures, known);
  }
  const { checked: wasChecked, errors } = checkResponse(contract, operation, outcome.status, outcome.body);
  return splitDrift(checked(wasChecked), errors.map((e) => `contract: ${e}`), known);
}

const checked = (value) => ({ checked: value });

/**
 * An answer field the contract does not declare is DRIFT, not a failure: responses are
 * forward-compatible, but the contract is stale, so each one is recorded for the contract's owner.
 * A missing required field, a wrong type or an enum miss is a failure, unless the case declares that
 * exact message in `expect.knownDrift` with its owner (from an expectations file): then it is
 * recorded as owned drift, so a case whose answer depends on earlier state stays deterministic.
 */
export function splitDrift(base, messages, known) {
  const unique = [...new Set(messages)];
  const norm = (m) => m.replace(/^contract: /, "").replace(/\[\d+\]/g, "[]");
  const declared = new Set(known?.messages ?? []);
  const isDrift = (m) => /: unknown property /.test(m) || declared.has(norm(m));
  const drift = unique.filter(isDrift).map((m) => (declared.has(norm(m)) ? `${norm(m)} (known, owner ${known.owner})` : norm(m)));
  return { ...base, failures: unique.filter((m) => !isDrift(m)).slice(0, 10), drift: [...new Set(drift)].slice(0, 20) };
}

export function createExecutor({ target, base, contract, fixtures, world, runId, fetchImpl, log = () => {} }) {
  async function send(step, ctx, mode, org, role, { idempotencyKey, omitScopeHeaders, noIdempotencyKey, allowRateLimit = false, scopeOrg } = {}) {
    const operation = contract.operations.get(opKey(step.op.method, step.op.path));
    const credential = credentialFor(fixtures, mode, org, role, { omitScopeHeaders, scopeOrg });
    if (credential.skip) return { skip: credential.skip };
    const params = fill(step.params ?? {}, ctx);
    const headers = { ...credential.headers, ...fill(step.headers ?? {}, ctx) };
    const key = noIdempotencyKey ? undefined : idempotencyKey ?? (step.idempotencyKey ? fill(step.idempotencyKey, ctx) : declaresIdempotencyKey(contract, operation) ? `sdkconf-${randomUUID()}` : undefined);
    if (key && !Object.keys(headers).some((h) => h.toLowerCase() === "idempotency-key")) headers["idempotency-key"] = key;
    const request = {
      base,
      method: step.op.method,
      path: fillPath(step.op.path, params),
      query: fill(step.query ?? {}, ctx),
      headers,
      body: step.body === undefined ? undefined : fill(step.body, ctx),
      rawBody: step.rawBody,
      contentType: step.contentType,
      stream: step.stream,
      timeoutMs: step.timeoutMs,
      fetchImpl,
    };
    // A 429 is refused, not applied, so the call is sent again after Retry-After
    // (at most 3 times, 60 s each) unless the case expects the 429 itself; the receipt counts them.
    let response = await rawCall(request);
    let rateLimited = 0;
    while (response.status === 429 && !allowRateLimit && rateLimited < 3) {
      rateLimited += 1;
      const wait = Math.min(Number(response.headers["retry-after"]) || 2, 60);
      log(`429 on ${step.op.method} ${step.op.path}; waiting ${wait} s (${rateLimited}/3)`);
      await sleep(wait * 1000);
      response = await rawCall(request);
    }
    return { operation, outcome: { ...toOutcome(response), idempotencyKey: key, rateLimited } };
  }

  async function runStep(step, ctx, mode, caller) {
    const owner = step.as === "caller" ? caller : { org: caller.resourceOrg ?? caller.org, role: "owner" };
    const sent = await send(step, ctx, mode, owner.org, owner.role);
    if (sent.skip) throw new Error(`setup skipped: ${sent.skip}`);
    const { outcome } = sent;
    if (step.expect) {
      const checked = checkOutcome(fill(step.expect, ctx), outcome);
      if (!checked.pass) throw new Error(`${step.op.method} ${step.op.path}: ${checked.failures.join("; ")}`);
    }
    const want = step.expectStatus ?? (step.expect ? [outcome.status] : [200, 201, 202]);
    if (!(Array.isArray(want) ? want : [want]).includes(outcome.status)) {
      throw new Error(`${step.op.method} ${step.op.path} answered ${outcome.status}${outcome.code ? ` ${outcome.code}` : ""}`);
    }
    for (const [name, dotted] of Object.entries(step.capture ?? {})) {
      const found = get(outcome.body, dotted);
      if (!found.found) throw new Error(`${step.op.path}: no ${dotted} to capture as ${name}`);
      ctx.cap[name] = found.value;
    }
    if (step.waitFor) await waitFor(step.waitFor, ctx, mode, owner);
    return outcome;
  }

  async function waitFor(rule, ctx, mode, owner) {
    const deadline = Date.now() + (rule.timeoutMs ?? 120_000);
    let last;
    while (Date.now() < deadline) {
      const sent = await send({ op: rule.op, params: rule.params }, ctx, mode, owner.org, owner.role);
      last = get(sent.outcome?.body, rule.field);
      if (last.found && rule.in.includes(last.value)) return;
      await sleep(rule.intervalMs ?? 1000);
    }
    throw new Error(`waitFor ${rule.field} in ${rule.in.join("|")}: last ${JSON.stringify(last?.value)}`);
  }

  // One case's bug (a missing parameter, a bad template) is that case's failure, never the run's.
  return async function execute(testCase, mode) {
    try {
      return await executeCase(testCase, mode);
    } catch (error) {
      return { id: testCase.id, mode, target, tenant: testCase.tenant, tags: testCase.tags, sdk: testCase.sdk, attempts: [], verdict: "fail", failures: [`runner: ${error.message}`.slice(0, 300)] };
    }
  };

  async function executeCase(testCase, mode) {
    const { org, role, resourceOrg } = testCase.tenant;
    const caller = { org, role, resourceOrg };
    const ctx = {
      run: { id: runId, short: runId.slice(-8) },
      own: world?.[org] ?? {},
      res: world?.[resourceOrg ?? org] ?? {},
      ids: fixtures?.ids ?? {},
      cap: {},
    };
    const result = { id: testCase.id, mode, target, tenant: testCase.tenant, tags: testCase.tags, sdk: testCase.sdk, attempts: [], failures: [] };
    for (const need of testCase.needs ?? []) {
      if (!(need in ctx.res) && !(need in ctx.own)) return { ...result, verdict: "skip", reason: `world has no ${need}` };
    }
    const xf = testCase.expectedFailure && (!testCase.expectedFailure.modes || testCase.expectedFailure.modes.includes(mode));
    try {
      for (const step of testCase.setup ?? []) await runStep(step, ctx, mode, caller);
    } catch (error) {
      // A declared, owned gap that breaks the setup is still that gap (xfail); never a pass.
      return { ...result, verdict: xf ? "xfail" : "fail", failures: [`setup: ${error.message}`], ...(xf ? { expectedFailure: testCase.expectedFailure } : {}) };
    }
    let expect;
    try {
      expect = fill(expectFor(testCase, mode), ctx);
    } catch (error) {
      return { ...result, verdict: "fail", failures: [`expect: ${error.message}`] };
    }
    const call = { op: testCase.op, ...(testCase.call ?? {}) };
    const fixedKey = call.idempotencyKey ? fill(call.idempotencyKey, ctx) : undefined;
    let first;
    for (let attempt = 0; attempt < (testCase.repeat ?? 1); attempt += 1) {
      const sent = await send(call, ctx, mode, org, role, { idempotencyKey: fixedKey, omitScopeHeaders: call.omitScopeHeaders, noIdempotencyKey: call.noIdempotencyKey, allowRateLimit: [expect.status].flat().includes(429), scopeOrg: testCase.tenant.scopeOrg });
      if (sent.skip) return { ...result, verdict: "skip", reason: sent.skip };
      const { outcome, operation } = sent;
      first ??= outcome;
      const checked = checkOutcome(expect, outcome);
      const contractCheck = expect.contract === false ? { checked: false, failures: [], drift: [] } : contractFailures(contract, operation, outcome, expect.knownDrift);
      if (contractCheck.drift.length) result.contractDrift = [...new Set([...(result.contractDrift ?? []), ...contractCheck.drift])];
      const failures = [...checked.failures, ...contractCheck.failures];
      result.attempts.push({
        status: outcome.status, code: outcome.code, errorClass: outcome.errorClass, requestId: outcome.requestId,
        upstreamRequestId: outcome.upstreamRequestId, retryAfterSeconds: outcome.retryAfterSeconds, durationMs: outcome.durationMs,
        contractChecked: contractCheck.checked, events: outcome.events.length || undefined, streamEnded: outcome.streamEnded,
        transportError: outcome.transportError, rateLimited: outcome.rateLimited || undefined, ok: failures.length === 0,
      });
      if (failures.length) result.failures.push(...failures.map((f) => (testCase.repeat > 1 ? `#${attempt + 1} ${f}` : f)));
      if (attempt === 0) {
        for (const [name, dotted] of Object.entries(testCase.capture ?? {})) {
          const found = get(outcome.body, dotted);
          if (found.found) ctx.cap[name] = found.value;
        }
        if (outcome.events.length) result.eventTypes = [...new Set(outcome.events.map((e) => e.type))];
      }
    }
    for (const step of testCase.verify ?? []) {
      try {
        await runStep(step, ctx, mode, caller);
      } catch (error) {
        result.failures.push(`verify: ${error.message}`.slice(0, 300));
      }
    }
    for (const step of testCase.cleanup ?? []) {
      try {
        await runStep({ ...step, expectStatus: step.expectStatus ?? [200, 201, 202, 204, 404] }, ctx, mode, caller);
      } catch (error) {
        result.cleanupError = error.message.slice(0, 200);
        log(`cleanup ${testCase.id}: ${error.message}`);
      }
    }
    result.first = first;
    result.failures = [...new Set(result.failures)].slice(0, 30);
    const passed = result.failures.length === 0;
    result.verdict = xf ? (passed ? "xpass" : "xfail") : passed ? "pass" : "fail";
    if (xf) result.expectedFailure = testCase.expectedFailure;
    return result;
  }
}
