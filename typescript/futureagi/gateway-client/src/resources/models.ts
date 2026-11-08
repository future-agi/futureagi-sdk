import type { BaseClient } from "../base-client.js";
import type { Model, ModelList } from "../types/model.js";

export class Models {
  constructor(private _client: BaseClient) {}

  async list(): Promise<ModelList> {
    return this._client.request<ModelList>({
      method: "GET",
      path: "/v1/models",
    });
  }

  async retrieve(modelId: string): Promise<Model> {
    return (this._client as any).request({
      method: "GET",
      path: `/v1/models/${encodeURIComponent(modelId)}`,
    });
  }
}
