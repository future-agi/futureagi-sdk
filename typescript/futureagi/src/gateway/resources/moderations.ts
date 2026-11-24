import type { BaseClient } from "../base-client";
import type { ModerationResponse, ModerationCreateParams } from "../types/moderation";
import { parseAgentCCMetadata } from "../types/shared";
import { extractAgentCCParams } from "../agentcc-params";

export class Moderations {
  constructor(private _client: BaseClient) {}

  async create(params: ModerationCreateParams): Promise<ModerationResponse> {
    const { headers, cleanBody } = extractAgentCCParams(params);
    const extraHeaders = params.extra_headers ?? {};
    const response = await (this._client as any).requestRaw({
      method: "POST",
      path: "/v1/moderations",
      body: cleanBody,
      headers: { ...headers, ...extraHeaders },
    }) as Response;
    const data = (await response.json()) as ModerationResponse;
    data.agentcc = parseAgentCCMetadata(response.headers);
    return data;
  }
}
