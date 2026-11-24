import type { BaseClient } from "../base-client";
import type { Batch, BatchList, BatchCreateParams } from "../types/batch";

export class Batches {
  constructor(private _client: BaseClient) {}

  async create(params: BatchCreateParams): Promise<Batch> {
    const { extra_headers, ...body } = params;
    return (this._client as any).request({
      method: "POST",
      path: "/v1/batches",
      body,
      headers: extra_headers,
    });
  }

  async list(query?: { after?: string; limit?: number }): Promise<BatchList> {
    const q: Record<string, string> = {};
    if (query?.after) q.after = query.after;
    if (query?.limit) q.limit = String(query.limit);
    return (this._client as any).request({
      method: "GET",
      path: "/v1/batches",
      query: Object.keys(q).length ? q : undefined,
    });
  }

  async retrieve(batchId: string): Promise<Batch> {
    return (this._client as any).request({
      method: "GET",
      path: `/v1/batches/${encodeURIComponent(batchId)}`,
    });
  }

  async cancel(batchId: string): Promise<Batch> {
    return (this._client as any).request({
      method: "POST",
      path: `/v1/batches/${encodeURIComponent(batchId)}/cancel`,
    });
  }
}
