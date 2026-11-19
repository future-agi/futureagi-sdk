import { Client } from "../client";
import { ResponseValidationError } from "../errors";

function client(data: unknown, strictResponses = true): Client {
  return new Client({ apiKey: "fixture", secretKey: "fixture", strictResponses,
    fetch: async () => new Response(JSON.stringify({status: true, result: data}), {
      status: 200, headers: {"content-type": "application/json"},
    }),
  });
}
const query = { resource_id: "00000000-0000-4000-8000-000000000001", kind: "skill", since: "2026-01-01T00:00:00Z" } as const;

test("strict mode accepts present nullable keys, not omitted or invalid values", async () => {
  await expect(client({fetch: null, load: null}).skills.latestLoad(query)).resolves.toEqual({fetch: null, load: null});
  for (const data of [null, {}, {load: null}, {fetch: null}, {load: null, fetch: []}, {load: null, fetch: {}}]) {
    await expect(client(data).skills.latestLoad(query)).rejects.toBeInstanceOf(ResponseValidationError);
  }
  await expect(client({load: null}, false).skills.latestLoad(query)).resolves.toEqual({load: null});
});

test("per-call strict reads validate without weakening client strict mode", async () => {
  await expect(
    client({fetch: null, load: null}, false).skills.latestLoad(query, {strictResponse: true}),
  ).resolves.toEqual({fetch: null, load: null});
  await expect(
    client({load: null}, false).skills.latestLoad(query, {strictResponse: true}),
  ).rejects.toBeInstanceOf(ResponseValidationError);
  await expect(
    client({load: null}).skills.latestLoad(query, {strictResponse: true}),
  ).rejects.toBeInstanceOf(ResponseValidationError);
});

test("strict context reads reject invalid nested data, and legacy reads stay tolerant", async () => {
  await expect(client({own_draft: null, latest: null, context: [], release_state: {}}).contexts.get(query.resource_id))
    .rejects.toBeInstanceOf(ResponseValidationError);
  await expect(client({unknown: 42}).account.whoami()).resolves.toEqual({unknown: 42});
});
