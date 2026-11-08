import type { BaseClient } from "../base-client.js";
import type { RerankResponse, RerankParams } from "../types/rerank.js";
import { parseAgentCCMetadata } from "../types/shared.js";

export class Rerank {
  constructor(private _client: BaseClient) {}

  async rank(params: RerankParams): Promise<RerankResponse> {
    const { extra_headers, ...body } = params;
    const response = await (this._client as any).requestRaw({
      method: "POST",
      path: "/v1/rerank",
      body,
      headers: extra_headers,
    }) as Response;
    const data = (await response.json()) as RerankResponse;
    data.agentcc = parseAgentCCMetadata(response.headers);
    return data;
  }
}
