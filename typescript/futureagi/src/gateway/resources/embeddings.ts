import type { BaseClient } from "../base-client";
import type { EmbeddingResponse, EmbeddingCreateParams } from "../types/embedding";
import { parseAgentCCMetadata } from "../types/shared";
import { extractAgentCCParams } from "../agentcc-params";

export class Embeddings {
  constructor(private _client: BaseClient) {}

  async create(params: EmbeddingCreateParams): Promise<EmbeddingResponse> {
    const { headers, cleanBody } = extractAgentCCParams(params);
    const extraHeaders = params.extra_headers ?? {};
    const response = await (this._client as any).requestRaw({
      method: "POST",
      path: "/v1/embeddings",
      body: cleanBody,
      headers: { ...headers, ...extraHeaders },
    }) as Response;
    const data = (await response.json()) as EmbeddingResponse;
    data.agentcc = parseAgentCCMetadata(response.headers);
    return data;
  }
}
