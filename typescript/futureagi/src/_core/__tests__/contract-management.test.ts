import { runtime, checkWire, type Case } from "../__fixtures__/contract-runtime";
import { coreOptions, coreResult } from "../../_resources";

const management: Case = {
  id: "management:fixture.get", name: "fixture.get", adapter: "management",
  method: "GET", path: "/agentcc/config/", path_params: [], idempotent: false,
  retry: "http-idempotent", stream: null,
  wrapper: { py: "client.contract_fixture.get_active", ts: "client.contractFixture.getActive" },
  invocation: { py: { args: [], kwargs: {} }, ts: { args: [] } },
};

test("management adapter calls the public method and real envelope adapter", async () => {
  const requests: Request[] = [];
  let payload: unknown = { status: true, result: { revision: "fixture" } };
  const subject = runtime(management, request => {
    requests.push(request);
    return Response.json(payload, { headers: { "X-Request-Id": "management-fixture" } });
  });
  (subject.client as any).contractFixture = {
    getActive() {
      return coreResult(subject.client.generatedClient.get(coreOptions(subject.client.generatedClient, { url: "/agentcc/config/" })) as any);
    },
  };
  await expect(subject.call()).resolves.toEqual({ revision: "fixture" });
  expect(requests).toHaveLength(1);
  checkWire(management, requests[0]);
  payload = { status: false, code: "invalid", result: "refused" };
  await expect(subject.call()).rejects.toMatchObject({ statusCode: 400, code: "invalid", requestId: "management-fixture" });
  (subject.client as any).contractFixture.getActive = undefined;
  await expect(subject.call()).rejects.toThrow(/not callable/);
  expect(requests).toHaveLength(2);
});
