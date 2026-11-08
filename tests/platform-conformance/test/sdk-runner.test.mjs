// The SDK runner shell's outcome rules that no stand-in server exercises.
import assert from "node:assert/strict";
import { test } from "node:test";
import { statuslessFailures } from "../runners/sdk/run.mjs";

const raised = (errorClass) => ({ status: null, errorClass, code: null });

test("a statusless SDK error never satisfies a 2xx expectation", () => {
  assert.match(statuslessFailures({ status: 200 }, raised("SDKException"))[0], /expected status 200; the SDK raised SDKException/);
  assert.match(statuslessFailures({ status: [200, 201] }, raised("APIConnectionError"))[0], /200\|201/);
});

test("a statusless error meets an error status only through the error class the case names", () => {
  assert.deepEqual(statuslessFailures({ status: 404, errorClass: "NotFoundError" }, raised("NotFoundError")), []);
  assert.match(statuslessFailures({ status: 404 }, raised("NotFoundError"))[0], /names no error class to match/);
});

test("an outcome with a status, or a case with no status, is left to checkOutcome", () => {
  assert.deepEqual(statuslessFailures({ status: 200 }, { status: 404, errorClass: "NotFoundError" }), []);
  assert.deepEqual(statuslessFailures({ errorClass: "HostNotAllowedError" }, raised("HostNotAllowedError")), []);
  assert.deepEqual(statuslessFailures({ status: 200 }, { status: null, errorClass: null }), []);
});
