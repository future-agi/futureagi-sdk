import type { BaseClient } from "../base-client.js";
import type { RerankResponse, RerankParams } from "../types/rerank.js";

export class Rerank {
  constructor(private _client: BaseClient) {}

  async rank(params: RerankParams): Promise<RerankResponse> {
    const { extra_headers, ...body } = params;
    return this._client.request<RerankResponse>({
      method: "POST",
      path: "/v1/rerank",
      body,
      headers: extra_headers,
    });
  }
}
