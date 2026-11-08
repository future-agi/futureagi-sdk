import type { BaseClient } from "../base-client.js";
import type { Model, ModelList } from "../types/model.js";
import { parseAgentCCMetadata } from "../types/shared.js";

export class Models {
  constructor(private _client: BaseClient) {}

  async list(): Promise<ModelList> {
    const response = await (this._client as any).requestRaw({
      method: "GET",
      path: "/v1/models",
    }) as Response;
    const data = (await response.json()) as ModelList;
    data.agentcc = parseAgentCCMetadata(response.headers);
    return data;
  }

  async retrieve(modelId: string): Promise<Model> {
    return (this._client as any).request({
      method: "GET",
      path: `/v1/models/${encodeURIComponent(modelId)}`,
    });
  }
}
