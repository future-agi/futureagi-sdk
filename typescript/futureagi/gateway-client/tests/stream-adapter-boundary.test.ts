import { it } from "@jest/globals";
import * as gateway from "../src/index.js";
import * as next from "../src/nextjs.js";
import * as route from "../src/react/route.js";
import * as express from "../src/express.js";

const adapters = { ...next, ...route, ...express };
const { registerCases } = require("./stream-adapter-boundary-cases.cjs") as {
  registerCases(api: typeof gateway, helpers: typeof adapters, test: (name: string, run: () => Promise<void>) => void): void;
};
registerCases(gateway, adapters, (name, run) => { it(name, run); });
