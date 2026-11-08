import type { BaseClient } from "../base-client.js";
import type {
  Transcription,
  Translation,
  TranscriptionCreateParams,
  TranslationCreateParams,
  SpeechCreateParams,
} from "../types/audio.js";
import { parseAgentCCMetadata } from "../types/shared.js";

class Transcriptions {
  constructor(private _client: BaseClient) {}

  async create(params: TranscriptionCreateParams): Promise<Transcription> {
    const form = new FormData();
    form.append("file", params.file as Blob);
    form.append("model", params.model);
    if (params.language) form.append("language", params.language);
    if (params.prompt) form.append("prompt", params.prompt);
    if (params.response_format) form.append("response_format", params.response_format);
    if (params.temperature != null) form.append("temperature", String(params.temperature));

    const response = await (this._client as any).requestRaw({
      method: "POST",
      path: "/v1/audio/transcriptions",
      body: form,
      headers: params.extra_headers,
    }) as Response;
    const data = (await response.json()) as Transcription;
    data.agentcc = parseAgentCCMetadata(response.headers);
    return data;
  }
}

class Translations {
  constructor(private _client: BaseClient) {}

  async create(params: TranslationCreateParams): Promise<Translation> {
    const form = new FormData();
    form.append("file", params.file as Blob);
    form.append("model", params.model);
    if (params.prompt) form.append("prompt", params.prompt);
    if (params.response_format) form.append("response_format", params.response_format);
    if (params.temperature != null) form.append("temperature", String(params.temperature));

    const response = await (this._client as any).requestRaw({
      method: "POST",
      path: "/v1/audio/translations",
      body: form,
      headers: params.extra_headers,
    }) as Response;
    const data = (await response.json()) as Translation;
    data.agentcc = parseAgentCCMetadata(response.headers);
    return data;
  }
}

class Speech {
  constructor(private _client: BaseClient) {}

  /** Create speech from text. Returns the raw Response (audio bytes). */
  async create(params: SpeechCreateParams): Promise<Response> {
    const { extra_headers, ...body } = params;
    return (this._client as any).requestRaw({
      method: "POST",
      path: "/v1/audio/speech",
      body,
      headers: extra_headers,
    });
  }
}

export class Audio {
  public readonly transcriptions: Transcriptions;
  public readonly translations: Translations;
  public readonly speech: Speech;

  constructor(client: BaseClient) {
    this.transcriptions = new Transcriptions(client);
    this.translations = new Translations(client);
    this.speech = new Speech(client);
  }
}
