import { it } from "@jest/globals";
import * as gateway from "../src/index.js";

const { registerCases } = require("./body-failure-guidance-cases.cjs") as {
  registerCases(api: typeof gateway, test: (name: string, run: () => Promise<void>) => void): void;
};
registerCases(gateway, (name, run) => { it(name, run); });
