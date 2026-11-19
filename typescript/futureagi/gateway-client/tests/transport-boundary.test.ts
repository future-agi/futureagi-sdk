import { it } from "@jest/globals";
import * as gateway from "../src/index.js";
import { routeStream } from "../src/react/route.js";

const { registerCases } = require("./transport-boundary-cases.cjs") as {
  registerCases(api: typeof gateway, test: (name: string, run: () => Promise<void>) => void, route: typeof routeStream): void;
};
registerCases(gateway, (name, run) => { it(name, run); }, routeStream);
