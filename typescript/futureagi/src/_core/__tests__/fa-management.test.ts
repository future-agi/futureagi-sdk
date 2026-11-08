import fs from "node:fs";
import path from "node:path";
import ts from "typescript";
import { FutureAGIClient } from "../../futureagi-client";
import { BadRequestError, ConfigurationError, PermissionDeniedError, UnexpectedRedirectError } from "../errors";
import { GatewayConfigWarningError } from "../fa-management";

const rows: Array<Record<string, any>> = JSON.parse(fs.readFileSync(path.resolve(__dirname, "../../../../../openapi/fa-mgmt/generated/operations.json"), "utf8"));
const camel = (s: string) => s.replace(/_([a-z])/gu, (_, letter: string) => letter.toUpperCase());
function make(handler: (request: Request) => Response | Promise<Response>, options = {}) {
  return new FutureAGIClient({ apiKey: "fixture-api", secretKey: "fixture-secret", baseUrl: "http://localhost:9012", retries: 0,
    workspaceId: "workspace-fixture", organizationId: "organization-fixture", fetch: (async (input: any, init?: RequestInit) => handler(new Request(input, init))) as typeof fetch, ...options });
}

it.each(rows)("$name preserves the generated method, path, body and authentication", async (row: any) => {
  const calls: Request[] = [];
  const client = make(request => {
    calls.push(request);
    expect(request.headers.get("x-api-key")).toBe("fixture-api");
    expect(request.headers.get("x-secret-key")).toBe("fixture-secret");
    expect(request.headers.get("x-workspace-id")).toBe("workspace-fixture");
    expect(request.headers.get("x-organization-id")).toBe("organization-fixture");
    expect(request.headers.has("authorization")).toBe(false);
    expect(request.headers.has("idempotency-key")).toBe(false);
    const data = row.page ? { count: 1, next: null, results: [{ id: "answer", user: "person" }] } : { id: "answer", user: "person" };
    return Response.json({ status: true, result: data }, { headers: { "x-request-id": "request-fixture" } });
  });
  const parts = row.name.split(".").map(camel);
  let target: any = client;
  for (const p of parts.slice(0, -1)) target = target[p];
  const args: any[] = row.path_params.filter((p: string) => !(p in (row.fixed_path ?? {}))).map(() => "sample");
  if (row.body_arg) args.push(row.name.startsWith("gateway.config.") ? { cache: { enabled: true, default_ttl: null } } : { display_name: "sample" });
  expect(target[parts.at(-1)].length).toBe(args.length);
  const value = await target[parts.at(-1)](...args).withResponse();
  expect(value.requestId).toBe("request-fixture");
  expect(calls).toHaveLength(1);
  expect(calls[0]!.method).toBe(row.method);
  let expected = row.path;
  for (const p of row.path_params) expected = expected.replace(`{${p}}`, row.fixed_path?.[p] ?? "sample");
  expect(new URL(calls[0]!.url).pathname).toBe(expected);
  if (row.body_arg && row.name.startsWith("gateway.config.")) expect(await calls[0]!.json()).toEqual({ cache: { enabled: true, default_ttl: null } });
  expect(row.page ? value.data.items : value.data).toEqual(row.page ? [{ id: "answer", user: "person" }] : { id: "answer", user: "person" });
});

it.each(["link", "totals"])("walks three DRF pages without following a supplied origin: %s", async mode => {
  const seen: Request[] = [];
  const client = make(request => {
    seen.push(request);
    const url = new URL(request.url);
    const page = Number(url.searchParams.get("page"));
    expect(url.host).toBe("localhost:9012");
    expect(url.searchParams.get("limit")).toBe("1");
    const value: any = { results: [{ id: page, user: "person" }], count: 3, current_page: page, total_pages: 3 };
    if (mode === "link") value.next = page < 3 ? `https://untrusted.invalid/wrong?page=${page + 1}` : null;
    return Response.json({ status: true, result: value });
  });
  const items = [];
  for await (const item of await client.gateway.keys.list({ limit: 1 })) items.push(item.id);
  expect(items).toEqual([1, 2, 3]);
  expect(seen).toHaveLength(3);
});

it.each([["KEY_LIMIT_NOT_ENFORCED", 400, BadRequestError], ["secret_in_config", 400, BadRequestError], ["permission_denied", 403, PermissionDeniedError]])("preserves FA error code %s", async (code, status, ErrorClass) => {
  const client = make(() => Response.json({ status: false, result: { error_code: code, message: "denied" } }, { status: status as number, headers: { "x-request-id": "request-fixture" } }));
  try {
    await client.gateway.config.update({ cache: { enabled: true } });
    throw new Error("expected rejection");
  } catch (error) {
    expect(error).toBeInstanceOf(ErrorClass as any);
    expect((error as any).code).toBe(code);
    expect((error as any).requestId).toBe("request-fixture");
  }
});

it("keeps warnings explicit and supports strict mode after mutation", async () => {
  const client = make(() => Response.json({ status: true, result: { version: 3, gateway_synced: false, warnings: [{ code: "unsupported_routing_key" }] } }));
  expect(await client.gateway.config.update({ cache: { enabled: true } })).toMatchObject({ version: 3, gateway_synced: false, hasWarnings: true });
  await expect(client.gateway.config.update({ cache: { enabled: true } }, {}, { strict: true })).rejects.toBeInstanceOf(GatewayConfigWarningError);
});

it.each(["credential-fixture-sensitive", "abc"])("masks credential reads and reflected write errors: %s", async secret => {
  const client = make(() => Response.json({ status: true, result: { credentials: { api_key: secret, short: "abc", nested: [secret] }, name: "safe" } }));
  const value = await client.gateway.providerCredentials.get("provider");
  expect(JSON.stringify(value)).not.toContain(secret);
  expect(JSON.stringify(value)).not.toContain("abc");
  expect(value.name).toBe("safe");
  const bad = make(() => Response.json({ code: "invalid_credential", message: `invalid ${secret}` }, { status: 400 }));
  try {
    await bad.gateway.providerCredentials.rotate("provider", { credentials: { api_key: secret } });
    throw new Error("expected rejection");
  } catch (error) {
    expect(error).toBeInstanceOf(BadRequestError);
    expect(String(error)).not.toContain(secret);
    expect(JSON.stringify(error)).not.toContain(secret);
  }
});

it.each([{ apiKey: "sk-agentcc-fixture" }, { platformToken: "token-fixture" }])("rejects wrong credential modes before sending", async options => {
  const client = make(() => { throw new Error("must not send"); }, options);
  await expect(client.gateway.config.getActive()).rejects.toBeInstanceOf(ConfigurationError);
});

it.each([{ user: "other" }, { owner: "org" }, { rate_limit_rpm: 30 }, { metadata: { allowed_ips: [] } }])("refuses key ownership rebinding and unsupported limits", async patch => {
  const client = make(() => { throw new Error("must not send"); });
  expect("create" in client.gateway.keys).toBe(false);
  expect("sync" in client.gateway.keys).toBe(false);
  await expect(client.gateway.keys.update("key", patch)).rejects.toBeInstanceOf(ConfigurationError);
});

it("does not present legacy organization keys as personal", async () => {
  const client = make(() => Response.json({ status: true, result: { id: "legacy", user: null } }));
  await expect(client.gateway.keys.get("legacy")).rejects.toMatchObject({ code: "non_personal_gateway_key" });
});

it("refuses redirects and propagates copy settings", async () => {
  const client = make(() => new Response(null, { status: 302, headers: { location: "https://untrusted.invalid/" } }));
  await expect(client.withOptions({ timeoutMs: 20, retries: 0 }).gateway.config.getActive()).rejects.toBeInstanceOf(UnexpectedRedirectError);
});

it("documents createVersion as replacement with omitted sections reset", () => {
  const source = fs.readFileSync(path.resolve(__dirname, "../../generated/fa-management/gateway.ts"), "utf8");
  const parsed = ts.createSourceFile("gateway.ts", source, ts.ScriptTarget.Latest, true);
  const config = parsed.statements.filter(ts.isClassDeclaration).find(node => node.name?.text === "GatewayConfig")!;
  const method = config.members.filter(ts.isMethodDeclaration).find(node => node.name.getText(parsed) === "createVersion")!;
  const docs = ts.getJSDocCommentsAndTags(method).map(node => node.getText(parsed)).join("\n");
  expect(docs).toContain("omitted sections reset to server defaults");
  expect(docs).toContain("not copied from the active version");
  expect(docs).toContain("config.update");
  expect(docs).not.toContain("omitted sections are retained");
});

it("intersects configuration write types with the management request schema", () => {
  const directory = path.resolve(__dirname, "../../../../../openapi/fa-mgmt");
  const read = (file: string) => JSON.parse(fs.readFileSync(path.join(directory, file), "utf8"));
  const swagger = read("swagger.json");
  const admin = read("admin.schema.json").$defs;
  const excluded = read("surface.json").untyped_config_fields;
  const expected = Object.keys(admin.OrgConfig.properties).filter(name => name in swagger.definitions.GatewayConfigPatchRequest.properties && !excluded.OrgConfig.includes(name)).sort();
  const source = fs.readFileSync(path.resolve(__dirname, "../../generated/fa-management/models.ts"), "utf8");
  const parsed = ts.createSourceFile("models.ts", source, ts.ScriptTarget.Latest, true);
  const interfaces = parsed.statements.filter(ts.isInterfaceDeclaration);
  const fields = (name: string) => interfaces.find(node => node.name.text === name)!.members.map(member => {
    const key = member.name!;
    return ts.isStringLiteral(key) ? key.text : key.getText(parsed);
  }).sort();
  expect(fields("ConfigSections")).toEqual(expected);
  for (const section of expected) {
    const ref = admin.OrgConfig.properties[section].$ref;
    if (ref) {
      const name = ref.split("/").at(-1);
      expect(fields(name)).toEqual(Object.keys(admin[name].properties ?? {}).filter(field => !(excluded[name] ?? []).includes(field)).sort());
    }
  }
});

it.each(["x", "xy", "abc", 'xy"\\', "credential-fixture-sensitive"].flatMap(secret =>
  ["create", "update", "rotate"].map(method => ({ secret, method }))))("scrubs reflected credential values in $method responses: $secret", async ({ secret, method }) => {
  const body = { credentials: { api_key: secret } };
  const response = { credentials: { api_key: secret }, diagnostic: `accepted ${secret}`,
    details: [{ [`echo_${secret}`]: `submitted ${secret}` }], name: "safe" };
  const client = make(async request => {
    expect(await request.json()).toEqual(body);
    return Response.json({ status: true, result: response });
  });
  const credentials = client.gateway.providerCredentials;
  const call = method === "create" ? credentials.create(body) : method === "update" ? credentials.update("provider", body) : credentials.rotate("provider", body);
  const result = await call.withResponse();
  expect(result.data.diagnostic).toBe("accepted [redacted]");
  // JSON keys are wire schema, not credential values, even when they collide.
  expect(result.data.details).toEqual([{ [`echo_${secret}`]: "submitted [redacted]" }]);
  expect(result.data.name).toBe("safe");
  expect(result.data.credentials).toEqual({ api_key: "[REDACTED]" });
  expect(Object.keys(result.data)).toEqual(Object.keys(response));
  expect(response.diagnostic).toBe(`accepted ${secret}`);
});
