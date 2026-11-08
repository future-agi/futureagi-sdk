// Shared source and dual-build regressions. All responses and keys are synthetic.
const assert = require('node:assert/strict');
const ID = '01ARZ3NDEKTSV4RRFFQ69G5FAV';
const REQUEST = { method: 'POST', path: '/v1/chat/completions', body: { model: 'example/model', messages: [] } };
const GUIDANCE = 'The gateway did not confirm whether the request was applied; check whether it was applied before sending it again.';

function registerCases(api, test) {
  for (const method of ['request', 'requestWithResponse', 'requestStream']) {
    for (const status of [200, 246]) for (const dispatch of [null, 'False', 'true', 'false']) {
      test(`${method}: body failure ${status} dispatch ${dispatch}`, async () => {
        let calls = 0;
        const errors = [], retries = [];
        class Observer extends api.CallbackHandler {
          onError(_request, error) { errors.push(error); }
          onRetry(_request, error) { retries.push(error); }
        }
        const original = new Error('synthetic body closed');
        const headers = { 'x-agentcc-request-id': ID, 'x-agentcc-client-request-id': 'correlation' };
        if (dispatch !== null) headers['x-agentcc-dispatched'] = dispatch;
        const response = new Response(new ReadableStream({ start(controller) { controller.error(original); } }), { status, headers });
        const client = new api.AgentCC({
          apiKey: 'synthetic-key', baseUrl: 'https://gateway.test', maxRetries: 3,
          retryPolicy: new api.RetryPolicy({ connectionErrorRetries: 5, timeoutRetries: 5 }),
          callbacks: [new Observer()], fetch: async () => { calls++; return response; },
        });
        let error;
        try {
          if (method === 'requestStream') {
            const raw = await client.requestStream(REQUEST);
            const stream = new api.Stream(raw);
            response.headers.set('x-agentcc-dispatched', 'true');
            for await (const _chunk of stream) { /* consume the SDK-owned reader */ }
          } else await client[method](REQUEST);
        } catch (caught) { error = caught; }
        assert.ok(error instanceof (method === 'requestStream' ? api.StreamError : api.ResponseBodyError));
        assert.equal(calls, 1);
        assert.equal(retries.length, 0);
        assert.equal(error.gatewayEvidence, api.getGatewayEvidence(response));
        assert.ok(Object.isFrozen(error.gatewayEvidence));
        const unknown = dispatch === null || dispatch === 'False';
        assert.deepEqual(error.gatewayEvidence, { dispatched: unknown ? 'unknown' : dispatch === 'true', gatewayRequestId: ID, clientRequestId: 'correlation' });
        assert.equal(error.cause, undefined);
        if (method !== 'requestStream') { assert.equal(errors.length, 1); assert.equal(errors[0], error); }
        if (unknown) {
          assert.ok(error.message.includes(GUIDANCE), 'message must carry the shared check-before-retrying guidance');
          assert.equal(error.remedy, GUIDANCE);
        } else {
          assert.equal(error.message, method === 'requestStream' ? 'Failed to read stream body' : 'Failed to read response body');
          assert.equal(error.remedy ?? null, null);
        }
      });
    }
  }
  for (const method of ['requestRaw', 'requestStream']) {
    test(`${method}: caller-owned readers retain their original failure`, async () => {
      const original = new Error('synthetic reader failure');
      let calls = 0;
      const client = new api.AgentCC({ apiKey: 'synthetic-key', baseUrl: 'https://gateway.test', fetch: async () => {
        calls++;
        return new Response(new ReadableStream({ start(controller) { controller.error(original); } }), { headers: { 'x-agentcc-request-id': ID } });
      } });
      const response = await client[method](REQUEST);
      await assert.rejects(response.arrayBuffer(), error => error === original);
      assert.equal(calls, 1);
    });
  }
  test('gateway stream error wording keeps precedence', async () => {
    const response = new Response('data: {"error":{"message":"synthetic gateway error","code":"managed_billing_unavailable"}}\n\n', { headers: { 'x-agentcc-request-id': ID } });
    await assert.rejects(async () => { for await (const _chunk of new api.Stream(response)) { /* consume */ } }, error => {
      assert.ok(error instanceof api.StreamError);
      assert.equal(error.message, 'synthetic gateway error');
      assert.equal(error.code, 'managed_billing_unavailable');
      assert.equal(error.remedy ?? null, null);
      return true;
    });
  });
}
module.exports = { registerCases };
