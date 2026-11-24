import type { BaseClient } from "../base-client";
import type { ImageResponse, ImageGenerateParams } from "../types/image";
import { parseAgentCCMetadata } from "../types/shared";
import { extractAgentCCParams } from "../agentcc-params";

export class Images {
  constructor(private _client: BaseClient) {}

  async generate(params: ImageGenerateParams): Promise<ImageResponse> {
    const { headers, cleanBody } = extractAgentCCParams(params);
    const extraHeaders = params.extra_headers ?? {};
    const response = await (this._client as any).requestRaw({
      method: "POST",
      path: "/v1/images/generations",
      body: cleanBody,
      headers: { ...headers, ...extraHeaders },
    }) as Response;
    const data = (await response.json()) as ImageResponse;
    data.agentcc = parseAgentCCMetadata(response.headers);
    return data;
  }
}
