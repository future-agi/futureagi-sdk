/** A small synthetic contract with every shape the platform tooling reads (no real contract needed). */

export function sampleContract() {
  return {
    openapi: "3.1.0",
    info: { title: "source", version: "1.0.0", description: "built from an internal manifest", "x-omega-contract": { deferred: [] } },
    servers: [{ url: "https://{host}/omega/api", variables: { host: { default: "example.invalid" } }, "x-omega-mode": "hosted" }],
    security: [{ FiKeyPair: [] }],
    "x-omega-deferred": [{ route: "GET /workspace/usage" }],
    tags: [{ name: "Things" }, { name: "Unused" }],
    paths: {
      "/workspace/things": {
        get: {
          operationId: "listThings",
          tags: ["Things"],
          summary: "List things",
          parameters: [{ name: "cursor", in: "query", schema: { type: "string" } }],
          "x-omega-sdk": { family: "platform", method: "things.list" },
          "x-omega-pagination": { style: "cursor", itemsField: "things", cursorParam: "cursor", nextCursorField: "nextCursor" },
          "x-omega-auth-authority": "workspace",
          responses: {
            200: { description: "ok", content: { "application/json": { schema: { $ref: "#/components/schemas/ThingList" } } } },
            404: { description: "nope", "x-omega-error-codes": ["not_found"], content: { "application/json": { schema: { $ref: "#/components/schemas/Error" } } } }
          }
        },
        post: {
          operationId: "createThing",
          tags: ["Things"],
          parameters: [{ $ref: "#/components/parameters/IdempotencyKeyRequired" }],
          "x-omega-sdk": { family: "platform", method: "things.create" },
          "x-omega-idempotent": true,
          "x-omega-idempotency": { durable: false, keyRequired: true, evidence: "server.ts keeps an in-memory map" },
          requestBody: { content: { "application/json": { schema: { $ref: "#/components/schemas/CreateThing" } } } },
          responses: { 201: { description: "made", content: { "application/json": { schema: { $ref: "#/components/schemas/Thing" } } } } }
        }
      },
      "/workspace/things/{id}": {
        delete: {
          operationId: "deleteThing",
          tags: ["Things"],
          "x-omega-sdk": { family: "platform", method: "things.delete" },
          "x-omega-not-found-on-retry-means-applied": true,
          responses: { 200: { description: "gone" } }
        },
        post: {
          operationId: "decideThing",
          tags: ["Unused"],
          "x-omega-sdk": { family: "platform", method: "things.decide" },
          "x-omega-human-only": true,
          responses: { 200: { description: "decided" } }
        }
      },
      "/workspace/things/{id}/events": {
        get: {
          operationId: "streamThing",
          tags: ["Things"],
          "x-omega-sdk": { family: "platform", method: "things.events" },
          "x-omega-stream": { kind: "sse-get", resume: "last-event-id", events: "#/components/schemas/ThingFrame" },
          responses: { 200: { description: "events", content: { "text/event-stream": { schema: { type: "string", "x-omega-frames": { $ref: "#/components/schemas/ThingFrame" } } } } } }
        }
      }
    },
    components: {
      schemas: {
        Error: { title: "Error", type: "object", properties: { code: { type: "string" } } },
        Thing: { title: "Thing", type: "object", properties: { id: { type: "string" }, token: { type: "string", "x-omega-secret": true }, "x-weird": { type: "string" } } },
        ThingList: { title: "ThingList", type: "object", properties: { things: { type: "array", items: { $ref: "#/components/schemas/Thing" } }, nextCursor: { type: ["string", "null"] } } },
        CreateThing: { title: "CreateThing", type: "object", properties: { name: { type: "string" }, kind: { enum: ["a", "b"] } } },
        ThingFrame: { title: "ThingFrame", oneOf: [{ $ref: "#/components/schemas/ThingStarted" }], discriminator: { propertyName: "type", mapping: { started: "#/components/schemas/ThingStarted" } } },
        ThingStarted: { title: "ThingStarted", type: "object", properties: { type: { const: "started" } } },
        Orphan: { title: "Orphan", type: "object", description: "reachable from nothing" }
      },
      parameters: { IdempotencyKeyRequired: { name: "Idempotency-Key", in: "header", required: true, schema: { type: "string" } } },
      securitySchemes: { FiKeyPair: { type: "apiKey", in: "header", name: "X-Api-Key" }, HubToken: { type: "apiKey", in: "header", name: "X-Hub" } }
    }
  };
}

export const SCOPE = { operations: ["platform.things.create", "platform.things.delete", "platform.things.events", "platform.things.list"] };
