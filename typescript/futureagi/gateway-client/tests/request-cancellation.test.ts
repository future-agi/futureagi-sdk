import { it } from "@jest/globals";
import * as gateway from "../src/index.js";
import type { RequestOptions } from "../src/client-options.js";

// The intersection keeps the RED tests type-correct against the previous API.
const options: RequestOptions & { signal: AbortSignal } = {
  method: "POST", path: "/test", signal: new AbortController().signal,
};
void options;
const { registerCases } = require("./request-cancellation-cases.cjs") as {
  registerCases(api: typeof gateway, test: (name: string, run: () => Promise<void>) => void): void;
};
registerCases(gateway, (name, run) => { it(name, run); });
