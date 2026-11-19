import { FutureAGIClient } from "../futureagi-client";
import { CredentialsMissingError, PermissionDeniedError, AuthenticationError } from "../_core/errors";

/** Mock-only contracts for the existing evaluation REST facade, not a template-runner export. */
describe("evaluation REST contracts", () => {
  const baseUrl = "http://127.0.0.1:9019";
  const credentials = { apiKey: "personal-fixture-a", secretKey: "personal-fixture-secret-a" };
  const payload = {
    eval_name: "is_json",
    inputs: { output: '{"answer":42}' },
    is_async: false,
    trace_eval: false,
    error_localizer: false,
  };
  const reply = (body: unknown, status = 200) => new Response(JSON.stringify(body), {
    status, headers: { "Content-Type": "application/json", "X-Request-Id": "eval-request" },
  });
  const makeClient = (transport: (request: Request) => Promise<Response>) => new FutureAGIClient({
    ...credentials, baseUrl, retries: 0, fetch: transport as typeof fetch,
  });

  afterEach(() => jest.restoreAllMocks());

  it.each([["{\"answer\":42}", true], ["not json", false]] as const)(
    "preserves the deterministic template input %s and result envelope without an idempotency key", async (input, expected) => {
    const requestBody = { ...payload, inputs: { output: input } };
    const result = { status: true, result: [{ evaluations: [
      { name: "is_json", output: expected, runtime: 0, output_type: "boolean" },
    ] }] };
    const transport = jest.fn(async (request: Request) => {
      expect(request.url).toBe(`${baseUrl}/sdk/api/v1/new-eval/`);
      expect(request.method).toBe("POST");
      expect(request.headers.get("X-Api-Key")).toBe(credentials.apiKey);
      expect(request.headers.get("X-Secret-Key")).toBe(credentials.secretKey);
      expect(request.headers.has("Authorization")).toBe(false);
      expect(request.headers.has("Idempotency-Key")).toBe(false);
      await expect(request.json()).resolves.toEqual(requestBody);
      return reply(result);
    });
    await expect(makeClient(transport).evals.runV2(requestBody)).resolves.toEqual(result);
    expect(transport).toHaveBeenCalledTimes(1);
  });

  it("lists required inputs and reads async results through the generated operations", async () => {
    const registry = { status: true, result: [{ name: "is_json", required_keys: ["output"] }] };
    const execution = { status: true, result: { eval_status: "completed", result: { output: true } } };
    const transport = jest.fn(async (request: Request) => {
      expect(request.method).toBe("GET");
      const url = new URL(request.url);
      if (url.pathname === "/sdk/api/v1/get-evals/") return reply(registry);
      expect(url.pathname).toBe("/sdk/api/v1/new-eval/");
      expect(url.searchParams.get("eval_id")).toBe("11111111-1111-1111-1111-111111111111");
      return reply(execution);
    });
    const client = makeClient(transport);
    await expect(client.evals.listSdkEvals()).resolves.toEqual(registry);
    await expect(client.evals.getRunV2("11111111-1111-1111-1111-111111111111")).resolves.toEqual(execution);
    expect(transport).toHaveBeenCalledTimes(2);
  });

  it.each([[401, AuthenticationError], [403, PermissionDeniedError]] as const)(
    "maps an HTTP %i refusal to a typed error, with no retry or successful result",
    async (status, ErrorType) => {
      const transport = jest.fn(async () => reply({ detail: "Evaluation is not accessible" }, status));
      await expect(makeClient(transport).evals.runV2(payload)).rejects.toBeInstanceOf(ErrorType);
      expect(transport).toHaveBeenCalledTimes(1);
    },
  );

  it("refuses a missing personal credential before calling the transport", async () => {
    const transport = jest.fn();
    const client = new FutureAGIClient({ apiKey: "", secretKey: "", baseUrl, fetch: transport });
    await expect(client.evals.runV2(payload)).rejects.toBeInstanceOf(CredentialsMissingError);
    expect(transport).not.toHaveBeenCalled();
  });

  it("preserves explicit error envelopes rather than manufacturing successful evaluation scores", async () => {
    const envelope = { status: false, result: "Template not available" };
    const transport = jest.fn(async () => reply(envelope));
    await expect(makeClient(transport).evals.runV2(payload)).resolves.toEqual(envelope);
  });
});
