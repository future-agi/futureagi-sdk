// Hand-written additions to `client.datasets`.
//
// Scaffolded once by sdkgen/generate.py and never overwritten: methods added here survive
// regeneration. The generated methods live in `../_generated/resources`.
//
//   export class Datasets extends DatasetsResource {
//     async getByName(name: string) {
//       ...                                              // compose generated methods, or
//       return this._t.raw("GET", "/some/path/", {});    // call an endpoint the catalog lacks
//     }
//   }

import { DatasetsResource } from "../_generated/resources";

/** `client.datasets`: every generated `datasets.*` method, plus the hand-written additions in this file. */
export class Datasets extends DatasetsResource {}
