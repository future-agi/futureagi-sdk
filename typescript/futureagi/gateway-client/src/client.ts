import { BaseClient, type ClientOptions } from "./base-client.js";
import { Chat } from "./resources/chat/index.js";
import { Embeddings } from "./resources/embeddings.js";
import { Images } from "./resources/images.js";
import { Audio } from "./resources/audio.js";
import { Models } from "./resources/models.js";
import { Completions } from "./resources/completions.js";
import { Files } from "./resources/files.js";
import { Rerank } from "./resources/rerank.js";
import { Session, type SessionOptions } from "./session.js";
import { invokeCallbacks } from "./callbacks.js";
import { mergeMetadata } from "./request-parts.js";

type ScopedSession<Client> = { client: Client; session: Session };

/**
 * AgentCC client — the main entry point for the SDK.
 *
 * @example
 * ```typescript
 * import { AgentCC } from "@future-agi/sdk/gateway";
 *
 * const client = new AgentCC({ apiKey: "sk-..." });
 *
 * const response = await client.chat.completions.create({
 *   model: "gpt-4o",
 *   messages: [{ role: "user", content: "Hello!" }],
 * });
 * ```
 */
export class AgentCC extends BaseClient {
  public readonly chat: Chat;
  public readonly completions: Completions;
  public readonly embeddings: Embeddings;
  public readonly images: Images;
  public readonly audio: Audio;
  public readonly models: Models;
  public readonly files: Files;
  public readonly rerank: Rerank;

  constructor(opts: ClientOptions = {}) {
    super(opts);
    this.chat = new Chat(this);
    this.completions = new Completions(this);
    this.embeddings = new Embeddings(this);
    this.images = new Images(this);
    this.audio = new Audio(this);
    this.models = new Models(this);
    this.files = new Files(this);
    this.rerank = new Rerank(this);
  }

  /**
   * Create a new client with the same config but overridden options.
   */
  withOptions(overrides: Partial<ClientOptions>): this {
    // Subclasses keep their compatibility resources on copies and sessions.
    const Client = this.constructor as new (opts: ClientOptions) => this;
    return new Client({
      apiKey: this._apiKey,
      baseUrl: this._baseUrl,
      timeout: this._timeout,
      maxRetries: this._maxRetries,
      defaultHeaders: { ...this._defaultHeaders },
      defaultQuery: { ...this._defaultQuery },
      sessionId: this._sessionId,
      metadata: this._metadata ? { ...this._metadata } : undefined,
      config: this._config,
      fetch: this._fetch,
      callbacks: this._callbacks.length > 0 ? [...this._callbacks] : undefined,
      retryPolicy: this._retryPolicy,
      redactMessages: this._redactMessages,
      traceContext: this._traceManager?.enabled,
      enableJsonSchemaValidation: this._enableJsonSchemaValidation || undefined,
      dangerouslyAllowBrowser: this._dangerouslyAllowBrowser || undefined,
      ...overrides,
    });
  }

  /**
   * Create a session-scoped client. All requests made through the returned
   * client include session headers and track session-level metrics.
   *
   * @example
   * ```typescript
   * const sess = client.session({ name: "research-agent" });
   * await sess.client.chat.completions.create({...});
   * sess.session.step("summarize");
   * await sess.client.chat.completions.create({...});
   * console.log(sess.session.totalCost, sess.session.requestCount);
   * ```
   */
  session(opts?: SessionOptions): ScopedSession<this> {
    const session = new Session(opts);

    // Create a tracking callback that records cost/tokens per request
    const trackingCallback = new SessionTrackingCallback(session);

    // Create a scoped client with the session headers injected. The session's
    // metadata is not a raw header here: it is merged key by key over the
    // client's metadata (the session's keys winning), and a request's
    // request_metadata is merged over both when it is sent.
    const sessionHeaders = session.toHeaders();
    delete sessionHeaders["x-agentcc-metadata"];
    const scopedClient = this.withOptions({
      defaultHeaders: {
        ...this._defaultHeaders,
        ...sessionHeaders,
      },
      metadata: mergeMetadata(this._metadata, Object.keys(session.metadata).length > 0 ? session.metadata : undefined),
      callbacks: [...this._callbacks, trackingCallback],
    });

    // Fire onSessionStart callbacks
    if (this._callbacks.length > 0) {
      invokeCallbacks(this._callbacks, "onSessionStart", session).catch(
        () => {},
      );
    }

    return { client: scopedClient, session };
  }

  /**
   * Quick health check against the gateway.
   * Returns `true` if the gateway is reachable and healthy.
   */
  async healthCheck(): Promise<boolean> {
    try {
      await this.request({ method: "GET", path: "/healthz" });
      return true;
    } catch {
      return false;
    }
  }
}

// ---------------------------------------------------------------------------
// Internal: session tracking callback
// ---------------------------------------------------------------------------

class SessionTrackingCallback {
  private _session: Session;

  constructor(session: Session) {
    this._session = session;
  }

  onRequestEnd(
    _request: unknown,
    response: { agentcc?: { cost?: number | null; latencyMs?: number } },
  ): void {
    const cost = response?.agentcc?.cost ?? 0;
    this._session.trackRequest(cost, 0);
  }

  // Satisfy CallbackHandler shape — no-ops for all other hooks
  onRequestStart() {}
  onError() {}
  onRetry() {}
  onGuardrailWarning() {}
  onGuardrailBlock() {}
  onCacheHit() {}
  onCostUpdate() {}
  onFallback() {}
  onSessionStart() {}
}
