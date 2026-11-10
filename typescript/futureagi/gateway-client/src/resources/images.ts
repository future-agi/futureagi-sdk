import type { BaseClient } from "../base-client.js";
import type { ImageResponse, ImageGenerateParams } from "../types/image.js";
import { perRequestParts } from "../agentcc-params.js";
import { AgentCCError } from "../errors.js";

export class Images {
  constructor(private _client: BaseClient) {}

  async generate(params: ImageGenerateParams): Promise<ImageResponse> {
    const { headers, cleanBody, metadata } = perRequestParts(params as unknown as Record<string, unknown>);
    const body = { ...cleanBody, ...(params.extra_body as Record<string, unknown> | undefined) };
    if (typeof body.model !== "string" || !body.model.trim()) {
      throw new AgentCCError("model must be a non-empty string for image generation");
    }
    return this._client.request<ImageResponse>({
      method: "POST",
      path: "/v1/images/generations",
      body,
      headers,
      metadata,
    });
  }
}
