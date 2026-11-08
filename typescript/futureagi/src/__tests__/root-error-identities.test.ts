import type { AxiosResponse } from "axios";
import * as Root from "../index";
import * as Core from "../_core/errors";
import * as Legacy from "../utils/errors";
import { apiError } from "../_core/error-map";
import { DatasetResponseHandler } from "../datasets/dataset";
import { FutureAGIClient } from "../futureagi-client";

const names = ["RateLimitError", "ServerError"] as const;
const statuses = [429, 500, 501, 502, 504, 599];
const nameFor = (status: number) => status === 429 ? "RateLimitError" : "ServerError";
const root = Root as unknown as Record<string, unknown>;
const core = Core as unknown as Record<string, unknown>;

function datasetFailure(status: number): unknown {
  try {
    DatasetResponseHandler._handleError({
      status, statusText: "fixture failure", data: { message: "fixture failure" },
    } as AxiosResponse);
  } catch (error) {
    return error;
  }
  return undefined;
}

it.each(names)("released root identity: %s", (name) => {
  expect(root[name]).toBe(Legacy[name]);
  expect(root[`Dataset${name}`]).toBe(Legacy[name]);
});

it.each(statuses)("released dataset %i matches the root constructor", (status) => {
  const error = datasetFailure(status);
  expect(error).toBeInstanceOf(Legacy[nameFor(status)]);
  expect(error).toBeInstanceOf(Legacy.DatasetError);
  expect(error).toBeInstanceOf(Legacy.SDKException);
  expect(error).toBeInstanceOf(root[nameFor(status)] as typeof Legacy.DatasetError);
});

it.each(statuses)("released dataset %i enters the root catch branch", (status) => {
  let caught = false;
  try {
    DatasetResponseHandler._handleError({ status, data: { message: "fixture failure" } } as AxiosResponse);
  } catch (error) {
    caught = error instanceof (root[nameFor(status)] as typeof Legacy.DatasetError);
  }
  expect(caught).toBe(true);
});

it.each(names)("root construction retains the released %s contract", (name) => {
  expect(root[name]).toBe(Legacy[name]); // Guard before calling the released signature on RED.
  const Constructor = root[name] as typeof Legacy.RateLimitError;
  const cause = new Error("fixture cause");
  const error = new Constructor("fixture message", cause);
  expect(error).toBeInstanceOf(Legacy[name]);
  expect(error).toBeInstanceOf(Legacy.DatasetError);
  expect(error.message).toBe("fixture message");
  expect(error.customMessage).toBe("fixture message");
  expect(error.cause).toBe(cause);
  expect(error.name).toBe(name);
  expect(error.getErrorCode()).toBe(name === "RateLimitError" ? "RATE_LIMIT_EXCEEDED" : "SERVER_ERROR");
});

it.each([429, 500, 502, 503, 599])("core transport %i uses the renamed root class", async (status) => {
  const name = `Core${nameFor(status)}`;
  // No static import of a missing name and no instanceof with undefined on the base.
  expect(typeof root[name]).toBe("function");
  expect(root[name]).toBe(core[name]);
  const Constructor = root[name] as typeof Core.FutureAGIAPIError;
  const fetchMock = jest.fn(async () => new Response(JSON.stringify({ detail: "fixture failure" }), {
    status, headers: { "content-type": "application/json" },
  }));
  const client = new FutureAGIClient({
    apiKey: "fixture-api", secretKey: "fixture-secret", baseUrl: "http://127.0.0.1:9",
    retries: 0, fetch: fetchMock as typeof fetch,
  });
  let error: unknown;
  let caught = false;
  try {
    await client.annotationQueues.list({ limit: 1 });
  } catch (failure) {
    error = failure;
    caught = failure instanceof Constructor;
  }
  expect(caught).toBe(true);
  expect(error).toBeInstanceOf(Constructor);
  expect(error).toBeInstanceOf(Core.FutureAGIAPIError);
  expect(error).toBeInstanceOf(Legacy.SDKException);
  expect(error).toMatchObject({ name, statusCode: status });
  expect(error).not.toBeInstanceOf(Legacy.DatasetError);
  expect(fetchMock).toHaveBeenCalledTimes(1);
});

it.each([429, 500])("released root names never select the core constructor: %i", (status) => {
  const error = apiError(status, { detail: "fixture failure" });
  expect(root[nameFor(status)]).not.toBe(error.constructor);
  expect(error).not.toBeInstanceOf(root[nameFor(status)] as typeof Legacy.DatasetError);
});

it.each(names)("dataset errors do not enter the renamed core catch branch: %s", (name) => {
  expect(typeof root[`Core${name}`]).toBe("function");
  const Constructor = root[`Core${name}`] as typeof Core.FutureAGIAPIError;
  const error = new Legacy[name]("fixture failure");
  expect(error).not.toBeInstanceOf(Constructor);
  expect(error).not.toBeInstanceOf(Core.FutureAGIAPIError);
});

it("dataset 503 retains its separate released classification", () => {
  const error = datasetFailure(503);
  expect(error).toBeInstanceOf(Legacy.ServiceUnavailableError);
  expect(error).toBeInstanceOf(Legacy.DatasetError);
  expect(error).not.toBeInstanceOf(Legacy.ServerError);
});
