import { readFileSync } from "node:fs";
import { resolve } from "node:path";

import {
  FutureAGIClient,
  type DatasetVersionsClient,
  type ExperimentRunsClient,
} from "../futureagi-client";
import type {
  CreateExternalExperimentRunData,
  DatasetVersionCreateResponse,
  DatasetVersionDetailResponse,
  DatasetVersionListResponse,
  ExternalRunCreateResponse,
  ExternalRunResultsResponse,
  IngestExternalExperimentResultsData,
  RunComparisonResponse,
} from "../generated/openapi/types.gen";

// Compile the consumer-visible results exactly: no fields wrapper, undefined,
// or any escape hatch can satisfy these assertions.
type Equal<Left, Right> =
  (<T>() => T extends Left ? 1 : 2) extends <T>() => T extends Right ? 1 : 2
    ? true
    : false;
type Assert<Condition extends true> = Condition;
type LifecycleResponseTypes = [
  Assert<
    Equal<
      Awaited<ReturnType<DatasetVersionsClient["list"]>>,
      DatasetVersionListResponse
    >
  >,
  Assert<
    Equal<
      Awaited<ReturnType<DatasetVersionsClient["get"]>>,
      DatasetVersionDetailResponse
    >
  >,
  Assert<
    Equal<
      Awaited<ReturnType<DatasetVersionsClient["create"]>>,
      DatasetVersionCreateResponse
    >
  >,
  Assert<
    Equal<
      Awaited<ReturnType<ExperimentRunsClient["create"]>>,
      ExternalRunCreateResponse
    >
  >,
  Assert<
    Equal<
      Awaited<ReturnType<ExperimentRunsClient["ingestResults"]>>,
      ExternalRunResultsResponse
    >
  >,
  Assert<
    Equal<
      Awaited<ReturnType<ExperimentRunsClient["compare"]>>,
      RunComparisonResponse
    >
  >,
];

const DATASET = "00000000-0000-4000-8000-000000000001";
const VERSION = "00000000-0000-4000-8000-000000000002";
const RUN = "00000000-0000-4000-8000-000000000003";
const EXAMPLE = "00000000-0000-4000-8000-000000000004";
const fixture = (name: string) =>
  JSON.parse(
    readFileSync(
      resolve(
        __dirname,
        "../../../../tests/fixtures/dataset-experiments",
        name,
      ),
      "utf8",
    ),
  );
const jsonResponse = (data: unknown, status = 200) =>
  new Response(JSON.stringify(data), {
    status,
    headers: { "Content-Type": "application/json" },
  });
const clientFor = (handler: typeof fetch) =>
  new FutureAGIClient({
    apiKey: "local-api",
    secretKey: "local-secret",
    baseUrl: "http://api.test",
    fetch: handler,
  });

describe("dataset and external run lifecycle", () => {
  it.each([false, 0, "text", ["text", null], { nested: null }])(
    "preserves snapshot JSON %j and accepts 201 with one attempt",
    async (input) => {
      const body = {
        items: [
          { input, expected: null, metadata: { nested: [null, false, 0] } },
        ],
      };
      const response = fixture("dataset-snapshot-created.json");
      const fetchMock = jest.fn(async (request: Request) => {
        expect(request.method).toBe("POST");
        expect(new URL(request.url).pathname).toBe(
          `/model-hub/datasets/${DATASET}/versions/`,
        );
        expect(request.headers.get("X-Api-Key")).toBe("local-api");
        expect(request.headers.get("X-Secret-Key")).toBe("local-secret");
        expect(await request.json()).toEqual(body);
        return jsonResponse(response, 201);
      });
      await expect(
        clientFor(fetchMock as typeof fetch).datasets.versions.create(
          DATASET,
          body,
        ),
      ).resolves.toEqual(response);
      expect(fetchMock).toHaveBeenCalledTimes(1);
    },
  );

  it("passes version list/detail pagination and preserves scalar/null responses", async () => {
    const responses = [
      fixture("dataset-version-list.json"),
      fixture("dataset-version-detail.json"),
    ];
    let index = 0;
    const fetchMock = jest.fn(async (request: Request) => {
      const url = new URL(request.url);
      expect(request.method).toBe("GET");
      expect(url.searchParams.get("limit")).toBe("2");
      expect(url.searchParams.get("offset")).toBe("3");
      expect(url.pathname).toBe(
        `/model-hub/datasets/${DATASET}/versions/${index ? `${VERSION}/` : ""}`,
      );
      return jsonResponse(responses[index++]);
    });
    const client = clientFor(fetchMock as typeof fetch);
    await expect(
      client.datasets.versions.list(DATASET, { limit: 2, offset: 3 }),
    ).resolves.toEqual(responses[0]);
    await expect(
      client.datasets.versions.get(DATASET, VERSION, { limit: 2, offset: 3 }),
    ).resolves.toEqual(responses[1]);
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });

  it("sends exact external identities/receipts and retains missing evidence", async () => {
    const create: CreateExternalExperimentRunData["body"] = {
      run_id: RUN,
      dataset_version_id: VERSION,
      expected_items: [{ example_id: EXAMPLE, trial_number: 1 }],
      model_config: { scalar: false, array: [1, null] },
      metadata: {},
    };
    const upload: IngestExternalExperimentResultsData["body"] = {
      items: [
        {
          example_id: EXAMPLE,
          trial_number: 1,
          receipt_key: "delivery-one",
          status: "completed",
          output: [false, 0, null],
          error: null,
          trace_id: null,
          root_span_id: null,
          score_refs: [],
        },
      ],
    };
    const compare = {
      baseline_run_id: RUN,
      candidate_run_id: VERSION,
      metric_id: EXAMPLE,
      passing_score: null,
    };
    const expected = [
      [
        "/model-hub/experiment-runs/",
        create,
        fixture("external-run-created.json"),
      ],
      [
        `/model-hub/experiment-runs/${RUN}/results/`,
        upload,
        fixture("external-run-results.json"),
      ],
      [
        "/model-hub/experiment-runs/compare/",
        compare,
        fixture("run-comparison-missing.json"),
      ],
    ];
    let index = 0;
    const fetchMock = jest.fn(async (request: Request) => {
      const [path, body, response] = expected[index++];
      expect(request.method).toBe("POST");
      expect(new URL(request.url).pathname).toBe(path);
      expect(await request.json()).toEqual(body);
      return jsonResponse(response);
    });
    const client = clientFor(fetchMock as typeof fetch);
    await expect(client.experimentRuns.create(create)).resolves.toEqual(
      expected[0][2],
    );
    await expect(
      client.experimentRuns.ingestResults(RUN, upload),
    ).resolves.toEqual(expected[1][2]);
    await expect(client.experimentRuns.compare(compare)).resolves.toEqual(
      expected[2][2],
    );
    expect(fetchMock).toHaveBeenCalledTimes(3);
  });

  it.each(["timeout", "invalid-json", "conflict"])(
    "does not retry snapshot after %s",
    async (failure) => {
      const fetchMock = jest.fn(async () => {
        if (failure === "timeout") throw new TypeError("response lost");
        if (failure === "invalid-json")
          return new Response("not-json", {
            status: 201,
            headers: { "Content-Type": "application/json" },
          });
        return jsonResponse({ status: false, message: "conflict" }, 409);
      });
      await expect(
        clientFor(fetchMock as typeof fetch).datasets.versions.create(DATASET, {
          items: [],
        }),
      ).rejects.toBeDefined();
      expect(fetchMock).toHaveBeenCalledTimes(1);
    },
  );
});
