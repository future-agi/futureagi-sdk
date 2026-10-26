// Hand-written additions to `client.prompts`.
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

import { PromptsResource } from "../_generated/resources";

export class Prompts extends PromptsResource {}
