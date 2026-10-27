// Hand-written additions to `client.knowledgeBases`.
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

import { KnowledgeBasesResource } from "../_generated/resources";

/** `client.knowledgeBases`: every generated `knowledgeBases.*` method, plus the hand-written additions in this file. */
export class KnowledgeBases extends KnowledgeBasesResource {}
