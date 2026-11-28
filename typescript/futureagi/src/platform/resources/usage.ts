// Hand-written additions to `client.usage`.
//
// Scaffolded once by sdkgen/generate.py and never overwritten: methods added here survive
// regeneration. The generated methods live in `./base`.
//
//   export class Datasets extends DatasetsResource {
//     async getByName(name: string) {
//       ...                                              // compose generated methods, or
//       return this._t.raw("GET", "/some/path/", {});    // call an endpoint the catalog lacks
//     }
//   }

import { NotFoundError } from "../errors";
import type { UsageOverviewResult } from "../models";
import type { RequestOptions } from "../transport";
import { UsageResource, type UsageOverviewParams } from "./base";

/** The deployment does not provide the usage overview endpoint. */
export class UsageOverviewUnavailableError extends NotFoundError {}

/** `client.usage`: every generated `usage.*` method, plus the hand-written additions in this file. */
export class Usage extends UsageResource {
  async overview(params: UsageOverviewParams = {}, options?: RequestOptions): Promise<UsageOverviewResult> {
    try {
      return await super.overview(params, options);
    } catch (error) {
      if (!(error instanceof NotFoundError)) throw error;
      throw new UsageOverviewUnavailableError(
        "This deployment does not provide the usage overview endpoint (GET /usage/v2/usage-overview/).",
        error.status, error.body, error.requestId,
      );
    }
  }
}
