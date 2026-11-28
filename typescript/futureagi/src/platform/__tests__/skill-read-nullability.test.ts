import { Client } from "../client";
import { ResponseValidationError } from "../errors";
import type { RequestOptions } from "../transport";

function client(data: unknown, strictResponses = true): Client {
  return new Client({ apiKey: "fixture", secretKey: "fixture", strictResponses, customFetchReceivesKeys: true,
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

const release = { latest_version: null, labels: [], release_revision: 1, security_revision: 1, protected_label_names: [] };
const detailWithoutDraft = {
  latest: null,
  context: { ...release, id: query.resource_id, kind: "agent_context", name: "example", description: "fixture",
    tags: [], metadata_revision: 1, has_draft: false, updated_at: query.since, updated_by: null },
  release_state: { ...release, permissions: { can_publish: false, can_promote: false, can_manage_protection: false,
    can_quarantine: false, can_issue_credentials: false } },
};

const reads = [
  { name: "skills.latestLoad", key: "fetch", partial: { load: null },
    read: (sdk: Client, options: RequestOptions) => sdk.skills.latestLoad(query, options) },
  { name: "contexts.get", key: "own_draft", partial: detailWithoutDraft,
    read: (sdk: Client, options: RequestOptions) => sdk.contexts.get(query.resource_id, options) },
];

describe.each(reads)("$name", ({ key, partial, read }) => {
  test("strict decoding accepts the same payload with an explicit null", async () => {
    const complete = { ...partial, [key]: null };
    await expect(read(client(complete, false), {strictResponse: true})).resolves.toEqual(complete);
  });

  test.each([
    {strict: true, inFlight: false}, {strict: false, inFlight: false},
    {strict: true, inFlight: true}, {strict: false, inFlight: true},
  ])("keeps strict=$strict when options change (fetch started: $inFlight)", async ({strict, inFlight}) => {
    let notifyStarted!: () => void;
    let respond!: (response: Response) => void;
    const started = new Promise<void>(resolve => { notifyStarted = resolve; });
    const response = new Promise<Response>(resolve => { respond = resolve; });
    const sdk = new Client({ apiKey: "fixture", secretKey: "fixture", customFetchReceivesKeys: true, fetch: () => {
      notifyStarted();
      return response;
    } });
    const options: RequestOptions = strict ? {strictResponse: true} : {};
    const pending = read(sdk, options);
    if (inFlight) await started;
    if (strict) delete options.strictResponse;
    else options.strictResponse = true;
    await started;
    respond(new Response(JSON.stringify({status: true, result: partial}), {
      headers: {"content-type": "application/json"},
    }));
    if (strict) await expect(pending).rejects.toBeInstanceOf(ResponseValidationError);
    else await expect(pending).resolves.toEqual(partial);
  });
});
