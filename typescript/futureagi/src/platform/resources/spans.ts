// Hand-written additions to `client.spans`.
//
// Scaffolded once by sdkgen/generate.py and never overwritten: methods added here survive
// regeneration. The generated methods live in `../_generated/resources`.

import { SpansResource } from "../_generated/resources";
import type { RequestOptions } from "../transport";

const INGEST_PATH = "/tracer/observation-span/create_otel_span/";

/** `client.spans`: every generated `spans.*` method, plus `ingest()`. */
export class Spans extends SpansResource {
  /**
   * Send spans straight to the tracer (`{ ids: [...] }`), without the traceAI exporter.
   *
   * POST /tracer/observation-span/create_otel_span/
   *
   * Hand-written: the endpoint takes a JSON *array*, which the catalog cannot express.
   * Send one span for a brand-new project first; the backend creates the project from
   * parallel threads, so a first batch of several spans can race on its unique constraint.
   */
  ingest(spans: Array<Record<string, unknown>>, options?: RequestOptions): Promise<{ ids?: string[] }> {
    return this._t.raw("POST", INGEST_PATH, { body: [...spans] }, options) as Promise<{ ids?: string[] }>;
  }
}
