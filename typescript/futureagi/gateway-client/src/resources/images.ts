import type { BaseClient } from "../base-client.js";
import type { ImageResponse, ImageGenerateParams } from "../types/image.js";
import { perRequestParts } from "../agentcc-params.js";

export class Images {
  constructor(private _client: BaseClient) {}

  async generate(params: ImageGenerateParams): Promise<ImageResponse> {
    const { headers, cleanBody, metadata } = perRequestParts(params as unknown as Record<string, unknown>);
    return this._client.request<ImageResponse>({
      method: "POST",
      path: "/v1/images/generations",
      body: cleanBody,
      headers,
      metadata,
    });
  }
}
