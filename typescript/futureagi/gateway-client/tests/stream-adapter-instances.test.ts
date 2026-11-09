import { it, jest } from "@jest/globals";
import assert from "node:assert/strict";
import * as gateway from "../src/index.js";
import * as next from "../src/nextjs.js";
import * as route from "../src/react/route.js";
import * as express from "../src/express.js";

type Copy = { api: typeof gateway; adapters: typeof next & typeof route & typeof express };
const { registerInstanceCases } = require("./stream-adapter-boundary-cases.cjs") as {
  registerInstanceCases(clientApi: typeof gateway, adapterApi: typeof gateway, adapters: Copy["adapters"], test: (name: string, run: () => Promise<void>) => void): void;
};

// A separate module registry is a separate evaluation of every module: the
// situation of a second install, or of a CommonJS and an ES module build.
function copy(): Copy {
  let loaded: Copy | undefined;
  jest.isolateModules(() => {
    loaded = {
      api: require("../src/index.js"),
      adapters: { ...require("../src/nextjs.js"), ...require("../src/react/route.js"), ...require("../src/express.js") },
    };
  });
  return loaded as Copy;
}
const first = copy();
const second = copy();

it("two copies are separate module instances", () => {
  assert.notEqual(first.api.StreamError, second.api.StreamError);
  assert.notEqual(first.api.StreamError, gateway.StreamError);
});
registerInstanceCases(first.api, second.api, second.adapters, (name, run) => { it(`first client, second adapter: ${name}`, run); });
registerInstanceCases(second.api, first.api, first.adapters, (name, run) => { it(`second client, first adapter: ${name}`, run); });
