import type { BaseClient } from "../base-client.js";
import type { ImageResponse, ImageGenerateParams } from "../types/image.js";
import { parseAgentCCMetadata } from "../types/shared.js";
import { perRequestParts } from "../agentcc-params.js";

export class Images {
  constructor(private _client: BaseClient) {}

  async generate(params: ImageGenerateParams): Promise<ImageResponse> {
    const { headers, cleanBody, metadata } = perRequestParts(params as unknown as Record<string, unknown>);
    const response = await (this._client as any).requestRaw({
      method: "POST",
      path: "/v1/images/generations",
      body: cleanBody,
      headers,
      metadata,
    }) as Response;
    const data = (await response.json()) as ImageResponse;
    data.agentcc = parseAgentCCMetadata(response.headers);
    return data;
  }
}
