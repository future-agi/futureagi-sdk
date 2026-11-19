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
  ComparisonSelection,
  RunComparisonResponse,
  TrialStability,
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
  Assert<
    Equal<
      Parameters<ExperimentRunsClient["compare"]>[0]["include_trial_stability"],
      boolean | undefined
    >
  >,
  Assert<
    Equal<
      Awaited<
        ReturnType<ExperimentRunsClient["compare"]>
      >["result"]["trial_stability"],
      TrialStability[] | undefined
    >
  >,
  Assert<Equal<TrialStability["baseline"]["score_stddev"], number | null>>,
  Assert<Equal<TrialStability["paired"]["delta_average"], number | null>>,
  Assert<
    Equal<
      Parameters<ExperimentRunsClient["compare"]>[0]["metadata_equals"],
      {
        [key: string]:
          | boolean
          | number
          | string
          | Array<unknown>
          | { [key: string]: unknown }
          | null;
      } | undefined
    >
  >,
  Assert<
    Equal<Parameters<ExperimentRunsClient["compare"]>[0]["split_name"], string | undefined>
  >,
  Assert<
    Equal<
      Awaited<ReturnType<ExperimentRunsClient["compare"]>>["result"]["selection"],
      ComparisonSelection | undefined
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

  it.each(["allowance", "critical"])(
    "returns the %s gate report without making a CI decision",
    async (name) => {
      const response = fixture(`run-comparison-gate-${name}.json`);
      const compare = {
        baseline_run_id: response.result.baseline_run_id,
        candidate_run_id: response.result.candidate_run_id,
        metric_id: response.result.metric_id,
        passing_score: 1,
        release_gate: response.result.release_gate.policy,
      };
      const fetchMock = jest.fn(async (request: Request) => {
        expect(request.method).toBe("POST");
        expect(new URL(request.url).pathname).toBe(
          "/model-hub/experiment-runs/compare/",
        );
        expect(await request.json()).toEqual(compare);
        return jsonResponse(response);
      });
      const result = await clientFor(
        fetchMock as typeof fetch,
      ).experimentRuns.compare(compare);
      expect(result).toEqual(response);
      expect(result.result.release_gate?.verdict).toBe(
        name === "allowance" ? "pass" : "fail",
      );
      expect(fetchMock).toHaveBeenCalledTimes(1);
    },
  );

  it.each([undefined, false, true])(
    "preserves trial-stability opt-in %s and nullable statistics",
    async (flag) => {
      const response = fixture("run-comparison-trial-stability.json");
      if (flag !== true) delete response.result.trial_stability;
      const compare = {
        baseline_run_id: response.result.baseline_run_id,
        candidate_run_id: response.result.candidate_run_id,
        metric_id: response.result.metric_id,
        ...(flag === undefined ? {} : { include_trial_stability: flag }),
      };
      const fetchMock = jest.fn(async (request: Request) => {
        expect(request.method).toBe("POST");
        expect(new URL(request.url).pathname).toBe(
          "/model-hub/experiment-runs/compare/",
        );
        expect(await request.json()).toEqual(compare);
        return jsonResponse(response);
      });
      const parsed = await clientFor(
        fetchMock as typeof fetch,
      ).experimentRuns.compare(compare);
      expect(parsed).toEqual(response);
      const rows = parsed.result.trial_stability;
      if (flag === true) {
        expect(rows?.[0].baseline.score_stddev).toBe(0.5);
        expect(rows?.[0].candidate.score_stddev).toBe(0);
        expect(rows?.[0].paired.delta_average).toBe(0);
        expect(rows?.[1].baseline.missing_trial_count).toBe(2);
        expect(rows?.[1].baseline.score_stddev).toBeNull();
        expect(rows?.[1].paired.delta_average).toBeNull();
      } else {
        expect(rows).toBeUndefined();
      }
      expect(fetchMock).toHaveBeenCalledTimes(1);
    },
  );

  it("accepts stability alongside a failed release gate and preserves an empty result", async () => {
    const response = fixture("run-comparison-gate-critical.json");
    response.result.trial_stability = [];
    const compare = {
      baseline_run_id: response.result.baseline_run_id,
      candidate_run_id: response.result.candidate_run_id,
      metric_id: response.result.metric_id,
      include_trial_stability: true,
      release_gate: response.result.release_gate.policy,
    };
    const fetchMock = jest.fn(async (request: Request) => {
      expect(await request.json()).toEqual(compare);
      return jsonResponse(response);
    });
    const parsed = await clientFor(
      fetchMock as typeof fetch,
    ).experimentRuns.compare(compare);
    expect(parsed.result.trial_stability).toEqual([]);
    expect(parsed.result.release_gate?.verdict).toBe("fail");
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it("sends JSON metadata selectors and parses an optional selection receipt", async () => {
    const response = fixture("run-comparison-missing.json");
    response.result.selection = {
      total_plan_count: 4,
      selected_count: 2,
      metadata_equals: { cohort: "A", enabled: true, weight: 0, expected: null },
      split_name: null,
    };
    const compare = {
      baseline_run_id: response.result.baseline_run_id,
      candidate_run_id: response.result.candidate_run_id,
      metric_id: response.result.metric_id,
      metadata_equals: {
        cohort: "A",
        enabled: true,
        weight: 0,
        expected: null,
        nested: { region: "us" },
        labels: ["holdout", null],
      },
      split_name: "holdout",
    };
    const fetchMock = jest.fn(async (request: Request) => {
      expect(await request.json()).toEqual(compare);
      return jsonResponse(response);
    });
    const parsed = await clientFor(
      fetchMock as typeof fetch,
    ).experimentRuns.compare(compare);
    expect(parsed.result.selection?.selected_count).toBe(2);
    expect(parsed.result.selection?.metadata_equals.expected).toBeNull();
    expect(parsed.result.selection?.split_name).toBeNull();
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it("omits optional metadata selectors when they are not set", async () => {
    const compare = {
      baseline_run_id: RUN,
      candidate_run_id: VERSION,
      metric_id: EXAMPLE,
    };
    const fetchMock = jest.fn(async (request: Request) => {
      expect(await request.json()).toEqual(compare);
      return jsonResponse(fixture("run-comparison-missing.json"));
    });
    await clientFor(fetchMock as typeof fetch).experimentRuns.compare(compare);
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it("keeps a twenty-key JSON metadata selector typed and portable", async () => {
    const response = fixture("run-comparison-missing.json");
    const metadata_equals = Object.fromEntries(
      Array.from({ length: 20 }, (_, index) => [
        String(index),
        { index, nullable: null },
      ]),
    );
    const compare = {
      baseline_run_id: response.result.baseline_run_id,
      candidate_run_id: response.result.candidate_run_id,
      metric_id: response.result.metric_id,
      metadata_equals,
      split_name: "train",
    };
    const fetchMock = jest.fn(async (request: Request) => {
      expect(await request.json()).toEqual(compare);
      return jsonResponse(response);
    });
    await clientFor(fetchMock as typeof fetch).experimentRuns.compare(compare);
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it("preserves runtime unknown policy fields for API rejection instead of dropping them", async () => {
    const compare = {
      baseline_run_id: RUN,
      candidate_run_id: VERSION,
      metric_id: EXAMPLE,
      release_gate: { max_regressions: 0, max_regresions: 100 },
    };
    const fetchMock = jest.fn(async (request: Request) => {
      expect(await request.json()).toEqual(compare);
      return jsonResponse(
        { status: false, error: "Unknown release-gate field" },
        400,
      );
    });
    await expect(
      clientFor(fetchMock as typeof fetch).experimentRuns.compare(compare),
    ).rejects.toBeDefined();
    expect(fetchMock).toHaveBeenCalledTimes(1);
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
