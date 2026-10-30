// Hand-written additions to `client.sessions`.
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

import { SessionsResource } from "./base";

/** `client.sessions`: every generated `sessions.*` method, plus the hand-written additions in this file. */
export class Sessions extends SessionsResource {}
