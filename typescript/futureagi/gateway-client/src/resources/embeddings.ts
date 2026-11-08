import type { BaseClient } from "../base-client.js";
import type { EmbeddingResponse, EmbeddingCreateParams } from "../types/embedding.js";
import { parseAgentCCMetadata } from "../types/shared.js";
import { perRequestParts } from "../agentcc-params.js";

export class Embeddings {
  constructor(private _client: BaseClient) {}

  async create(params: EmbeddingCreateParams): Promise<EmbeddingResponse> {
    const { headers, cleanBody, metadata } = perRequestParts(params as unknown as Record<string, unknown>);
    const response = await (this._client as any).requestRaw({
      method: "POST",
      path: "/v1/embeddings",
      body: cleanBody,
      headers,
      metadata,
    }) as Response;
    const data = (await response.json()) as EmbeddingResponse;
    data.agentcc = parseAgentCCMetadata(response.headers);
    return data;
  }
}
