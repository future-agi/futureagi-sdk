// Jest for the live wire suite: gateway-client/tests/live/**.
// The default config (../../jest.config.cjs) ignores this directory; this one runs
// only it, against the stack python/tests/gateway/live/stack/run-wire-suite.sh starts on
// a build machine. Without FI_GATEWAY_LIVE_BASE_URL every suite here is skipped.
const path = require("node:path");

/** @type {import('jest').Config} */
module.exports = {
  rootDir: path.resolve(__dirname, "..", ".."),
  testEnvironment: "node",
  testMatch: ["<rootDir>/tests/live/**/*.test.ts"],
  moduleFileExtensions: ["ts", "tsx", "js", "cjs", "mjs", "json"],
  moduleNameMapper: { "^(\\.{1,2}/.*)\\.js$": "$1" },
  transform: {
    "^.+\\.tsx?$": ["ts-jest", { tsconfig: "<rootDir>/tests/live/tsconfig.live.json" }],
  },
  testTimeout: 120000,
};
