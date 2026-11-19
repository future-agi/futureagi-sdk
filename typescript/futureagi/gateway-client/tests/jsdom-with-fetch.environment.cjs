// jsdom, plus the fetch API and streams a browser page has.
//
// jest-environment-jsdom 29 gives a page's window, document and navigator
// but not fetch, Response, ReadableStream or TextEncoder, which every browser
// has and the gateway client needs (vitest's jsdom environment, which
// @agentcc/react 1.0 ran under, keeps Node's). This copies Node's own into
// the page. Used by the React subpath's tests and the D-18 browser test.
"use strict";
const { TestEnvironment } = require("jest-environment-jsdom");

const FROM_NODE = [
  "fetch", "Request", "Response", "Headers", "FormData", "Blob", "File",
  "ReadableStream", "WritableStream", "TransformStream",
  "TextEncoder", "TextDecoder", "TextEncoderStream", "TextDecoderStream",
  "AbortController", "AbortSignal", "structuredClone",
];

class JsdomWithFetchEnvironment extends TestEnvironment {
  constructor(config, context) {
    super(config, context);
    for (const name of FROM_NODE) {
      if (typeof globalThis[name] !== "undefined") this.global[name] = globalThis[name];
    }
  }
}

module.exports = JsdomWithFetchEnvironment;
