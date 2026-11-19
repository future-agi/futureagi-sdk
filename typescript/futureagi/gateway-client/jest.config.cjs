// Jest for the gateway data-plane client (typescript/futureagi/gateway-client).
//
// The sources use ES module syntax with ".js"-suffixed relative imports (the
// way they compile for Node ESM); ts-jest transpiles them to CommonJS for the
// test run and the mapper drops the suffix. Tests run in Node's own globals
// (fetch, Response, ReadableStream, TextDecoderStream), which jest 29's node
// environment copies into each test context (tests/environment.test.ts).
// The React subpath's tests and the D-18 browser test opt into
// tests/jsdom-with-fetch.environment.cjs (jsdom plus the fetch API a browser
// page has) with a docblock.
//
// tests/parity/** (the golden recorder and comparator, run with node --test)
// and tests/live/** (gated live-gateway suites) are not part of this run.
/** @type {import('jest').Config} */
module.exports = {
  rootDir: __dirname,
  testEnvironment: "node",
  testMatch: ["<rootDir>/tests/**/*.test.ts", "<rootDir>/tests/**/*.test.tsx"],
  testPathIgnorePatterns: ["/node_modules/", "<rootDir>/tests/parity/", "<rootDir>/tests/live/"],
  moduleFileExtensions: ["ts", "tsx", "js", "cjs", "mjs", "json"],
  moduleNameMapper: { "^(\\.{1,2}/.*)\\.js$": "$1" },
  transform: {
    "^.+\\.tsx?$": ["ts-jest", { tsconfig: "<rootDir>/tsconfig.test.json" }],
  },
  testTimeout: 30000,
};
