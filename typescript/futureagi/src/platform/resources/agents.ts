// Hand-written additions to `client.agents`.
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

import { AgentsResource } from "./base";

/** `client.agents`: every generated `agents.*` method, plus the hand-written additions in this file. */
export class Agents extends AgentsResource {}
