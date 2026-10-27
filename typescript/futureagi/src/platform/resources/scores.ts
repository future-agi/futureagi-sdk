// Hand-written additions to `client.scores`.
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

import { ScoresResource } from "../_generated/resources";

/** `client.scores`: every generated `scores.*` method, plus the hand-written additions in this file. */
export class Scores extends ScoresResource {}
