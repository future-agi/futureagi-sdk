import type { Client } from "../generated/openapi/client";
import * as sdk from "../generated/openapi/sdk.gen";
import type * as types from "../generated/openapi/types.gen";
import { coreOptions, coreResult } from "../_resources";

/** Knowledge-base fields `update` changes (documents change through `documents`). */
export type KnowledgeBaseUpdate = Pick<types.LegacyKnowledgeBaseMutationRequest, "name">;
/** Zero-based `page_number` / `page_size` and filters for `documents.list`. */
export type KnowledgeBaseDocumentQuery = Omit<types.LegacyKnowledgeBaseFilesRequest, "kb_id">;

/** Documents in one knowledge base. Listing uses a POST with zero-based page_number/page_size fields. */
export class KnowledgeBaseDocumentsClient {
  constructor(private readonly client: Client) {}

  /** List a knowledge base's documents. Pagination: page_number (0-based); page_size (page size). Pass these in the request body. */
  list(kbId: string, query: KnowledgeBaseDocumentQuery = {}) {
    return coreResult(sdk.modelHubKnowledgeBaseFilesCreate(coreOptions(this.client, { body: { ...query, kb_id: kbId } })));
  }
  /** Upload UTF-8 text, without disk access, through the generated update operation. */
  async addText(kbId: string, name: string, text: string) {
    if (!name || /[/\\\r\n\0]/.test(name)) throw new TypeError("document name must be a filename, not a path");
    if (!name.toLowerCase().endsWith(".txt")) throw new TypeError("text documents must use a .txt filename");
    const body = new FormData();
    body.append("kb_id", kbId);
    body.append("file", new Blob([text], { type: "text/plain" }), name);
    // Swagger models only the JSON alternative; the operation also accepts multipart.
    return coreResult(sdk.modelHubKnowledgeBasePartialUpdate(coreOptions(this.client, {
      body: body as unknown as types.LegacyKnowledgeBaseMutationRequest,
      bodySerializer: (value: unknown) => value as FormData,
      headers: { "Content-Type": null },
    })));
  }
  /** Delete documents from a knowledge base by file name. */
  async delete(kbId: string, fileNames: string[]) {
    if (!fileNames.length) throw new TypeError("at least one filename is required");
    // The legacy DELETE body is missing from the generated Swagger schema.
    return coreResult(sdk.modelHubKnowledgeBaseFilesDelete(coreOptions(this.client, {
      body: { kb_id: kbId, file_names: fileNames } as never,
    })));
  }
}

/** Knowledge-base CRUD on the root client's credential and connection pool. */
export class KnowledgeBasesClient {
  /** Documents in a knowledge base: list, add text, delete. */
  readonly documents: KnowledgeBaseDocumentsClient;
  constructor(private readonly client: Client) {
    this.documents = new KnowledgeBaseDocumentsClient(client);
  }
  /** List knowledge bases, optionally filtered by a name search. */
  list(options: { search?: string } = {}) {
    return coreResult(sdk.modelHubKnowledgeBaseListList(coreOptions(this.client, { query: options as never })));
  }
  /** Create an empty knowledge base. */
  create(name: string) {
    return coreResult(sdk.modelHubKnowledgeBaseCreate(coreOptions(this.client, { body: { name } })));
  }
  /** Rename a knowledge base. */
  update(kbId: string, body: KnowledgeBaseUpdate) {
    return coreResult(sdk.modelHubKnowledgeBasePartialUpdate(coreOptions(this.client, { body: { ...body, kb_id: kbId } })));
  }
  /** Delete a knowledge base and its documents. */
  delete(kbId: string) {
    return coreResult(sdk.modelHubKnowledgeBaseDelete(coreOptions(this.client, { body: { kb_ids: [kbId] } as never })));
  }
}
