import { it } from "@jest/globals";
import * as gateway from "../src/index.js";

// Use the exact same assertions against source and both emitted module formats.
const { registerCases } = require("./unknown-dispatch-cases.cjs") as {
  registerCases(api: typeof gateway, test: (name: string, run: () => Promise<void>) => void): void;
};
registerCases(gateway, (name, run) => { it(name, run); });
