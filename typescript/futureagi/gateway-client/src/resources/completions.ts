import type { BaseClient } from "../base-client.js";
import type { Completion, CompletionCreateParams } from "../types/completion.js";
import { parseAgentCCMetadata } from "../types/shared.js";
import { perRequestParts } from "../agentcc-params.js";

export class Completions {
  constructor(private _client: BaseClient) {}

  async create(params: CompletionCreateParams): Promise<Completion> {
    const { headers, cleanBody, metadata } = perRequestParts(params as unknown as Record<string, unknown>);
    const response = await (this._client as any).requestRaw({
      method: "POST",
      path: "/v1/completions",
      body: cleanBody,
      headers,
      metadata,
    }) as Response;
    const data = (await response.json()) as Completion;
    data.agentcc = parseAgentCCMetadata(response.headers);
    return data;
  }
}
