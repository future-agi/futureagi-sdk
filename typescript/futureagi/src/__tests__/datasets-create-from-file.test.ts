import { FutureAGIClient } from "../futureagi-client";
import { createDatasetFromLocalFile } from "../generated/openapi/sdk.gen";

const csv = "question\nhello\n";

function uploadForm(): FormData {
  const form = new FormData();
  form.append("new_dataset_name", "imported");
  form.append("file", new Blob([csv], { type: "text/csv" }), "data.csv");
  return form;
}

function recorder(headers?: Record<string, string>) {
  const fetchMock = jest.fn(async (_request: Request) => new Response(
    JSON.stringify({ status: true, result: { message: "started" } }),
    { status: 200, headers: { "Content-Type": "application/json" } },
  ));
  const client = new FutureAGIClient({
    apiKey: "synthetic-api-key",
    secretKey: "synthetic-secret-key",
    baseUrl: "https://sdk.invalid",
    retries: 0,
    headers,
    fetch: fetchMock as unknown as typeof fetch,
  });
  return { client, fetchMock };
}

async function expectUpload(request: Request): Promise<FormData> {
  expect(request.method).toBe("POST");
  expect(new URL(request.url).pathname).toBe(
    "/model-hub/develops/create-dataset-from-local-file/",
  );
  expect(request.headers.get("Content-Type")).not.toBe("application/json");
  expect(request.headers.get("Content-Type")).toMatch(/^multipart\/form-data;\s*boundary=/i);
  expect(request.headers.get("X-Api-Key")).toBe("synthetic-api-key");
  expect(request.headers.get("X-Secret-Key")).toBe("synthetic-secret-key");
  // The generated fetch client passes a Request, not a RequestInit. Decode its
  // body to check the actual multipart bytes and matching boundary sent to fetch.
  const body = await request.formData();
  expect(body).toBeInstanceOf(FormData);
  expect(body.get("new_dataset_name")).toBe("imported");
  const file = body.get("file") as File;
  expect(file).toBeInstanceOf(Blob);
  expect(file.name).toBe("data.csv");
  expect(file.type).toBe("text/csv");
  expect(await file.text()).toBe(csv);
  return body;
}

describe("dataset file uploads", () => {
  it("preserves native FormData and lets fetch supply the multipart boundary", async () => {
    const { client, fetchMock } = recorder({
      "content-type": "application/json",
      "X-Upload-Test": "synthetic",
    });
    const form = uploadForm();
    const bodies: unknown[] = [];
    client.generatedClient.interceptors.request.use((request, options) => {
      bodies.push(options.body);
      return request;
    });

    await expect(client.datasets.createFromFile(form)).resolves.toEqual({
      status: true,
      result: { message: "started" },
    });

    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(bodies).toHaveLength(1);
    expect(bodies[0]).toBe(form);
    const request = fetchMock.mock.calls[0][0];
    await expectUpload(request);
    expect(request.headers.get("X-Upload-Test")).toBe("synthetic");
    expect(form.get("file")).toBeInstanceOf(Blob);
  });

  it("accepts a typed file object and preserves optional metadata", async () => {
    const { client, fetchMock } = recorder();
    const body = {
      file: uploadForm().get("file") as File,
      new_dataset_name: "imported",
      model_type: "text",
      source: "local",
    };

    await client.datasets.createFromFile(body);

    expect(fetchMock).toHaveBeenCalledTimes(1);
    const form = await expectUpload(fetchMock.mock.calls[0][0]);
    expect(form.get("model_type")).toBe("text");
    expect(form.get("source")).toBe("local");
  });

  it("serializes file objects through the generated operation as multipart too", async () => {
    const { client, fetchMock } = recorder();
    const body = {
      file: uploadForm().get("file") as File,
      new_dataset_name: "imported",
    };

    await createDatasetFromLocalFile({ client: client.generatedClient, body });

    expect(fetchMock).toHaveBeenCalledTimes(1);
    await expectUpload(fetchMock.mock.calls[0][0]);
  });

  it.each([undefined, "not-a-file"])("rejects FormData without a binary file (%s)", async value => {
    const { client, fetchMock } = recorder();
    const form = new FormData();
    form.append("new_dataset_name", "imported");
    if (value !== undefined) form.append("file", value);

    await expect(Promise.resolve().then(() => client.datasets.createFromFile(form)))
      .rejects.toThrow("Dataset uploads require a file.");
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("keeps non-file dataset creation requests as JSON", async () => {
    const { client, fetchMock } = recorder();
    const body = { name: "empty" };

    await client.datasets.createEmpty(body);

    expect(fetchMock).toHaveBeenCalledTimes(1);
    const request = fetchMock.mock.calls[0][0];
    expect(request.headers.get("Content-Type")).toBe("application/json");
    await expect(request.json()).resolves.toEqual(body);
  });
});
