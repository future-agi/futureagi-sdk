import type { BaseClient } from "../base-client.js";
import type { EmbeddingResponse, EmbeddingCreateParams } from "../types/embedding.js";
import { perRequestParts } from "../agentcc-params.js";

export class Embeddings {
  constructor(private _client: BaseClient) {}

  async create(params: EmbeddingCreateParams): Promise<EmbeddingResponse> {
    const { headers, cleanBody, metadata } = perRequestParts(params as unknown as Record<string, unknown>);
    return this._client.request<EmbeddingResponse>({
      method: "POST",
      path: "/v1/embeddings",
      body: cleanBody,
      headers,
      metadata,
    });
  }
}
