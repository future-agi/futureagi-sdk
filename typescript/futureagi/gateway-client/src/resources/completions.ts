import type { BaseClient } from "../base-client.js";
import type { Completion, CompletionCreateParams } from "../types/completion.js";
import { perRequestParts } from "../agentcc-params.js";

export class Completions {
  constructor(private _client: BaseClient) {}

  async create(params: CompletionCreateParams): Promise<Completion> {
    const { headers, cleanBody, metadata } = perRequestParts(params as unknown as Record<string, unknown>);
    return this._client.request<Completion>({
      method: "POST",
      path: "/v1/completions",
      body: cleanBody,
      headers,
      metadata,
    });
  }
}
