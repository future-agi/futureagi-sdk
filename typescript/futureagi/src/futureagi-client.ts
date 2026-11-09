import { Agents } from "./agents/client";
import { Environments } from "./environments/client";
import { Models } from "./generated/catalog/models";
import { TracingClient } from "./tracing";
export { TracingClient } from "./tracing";
import { Optimizations } from "./generated/catalog/optimizations";
import { Workspaces } from "./generated/catalog/workspaces";
import { API_KEY_ENVVAR_NAME, SECRET_KEY_ENVVAR_NAME } from "./utils/constants";
import { SDKException } from "./utils/errors";
import { createClient, formDataBodySerializer, type Client } from "./generated/openapi/client";
import {
  FACADE_DEFAULT_QUEUE_CALL,
  FACADE_DEFAULT_QUEUE_METHOD,
  FACADE_DEFAULT_SCOPE_KEYS,
  DEFAULT_QUEUE_SCOPE_IDS,
  refuseScopeIds,
  withDefaultLabels,
  createBody as annotationQueueCreateBody,
  defaultQueueBody as annotationQueueDefaultBody,
} from "./queues/create-body";
import * as generatedSdk from "./generated/openapi/sdk.gen";
import type * as generatedTypes from "./generated/openapi/types.gen";
import type { CatalogDataSdk } from "./catalog-response-types";
import { PLATFORM_OPERATIONS } from "./generated/platform/policy.gen";
import { CONNECTOR_OPERATIONS } from "./_core/connector-policy";
import { Connectors } from "./connectors";
import { Integrations } from "./integrations";
import { Credentials } from "./credentials";
import { DEFAULT_TIMEOUT_MS, resilientFetch } from "./transport";
import { KnowledgeBasesClient } from "./knowledge-bases";
import { PromptsClient } from "./prompts";
import { ScoresClient, type AnnotationLabelsClient } from "./scores";
import { apiError, connectionError, isWrongRegionResponse } from "./_core/error-map";
import { managementOrigin, scrubManagementValue } from "./_core/fa-management";
import { Gateway as ManagementGateway } from "./generated/fa-management/gateway";
import { MANAGEMENT_OPERATIONS } from "./generated/fa-management/policy";
import { CredentialsMissingError, FutureAGIAPIError, UnexpectedRedirectError } from "./_core/errors";
import { resolvePlatformOrigin, selectorHeaders } from "./_core/origins";
import { DEFAULT_STREAM_IDLE_MS, PlatformCore, type PlatformShared } from "./_core/platform-base";
import { ExtraHeaders, ExtraHeadersError, withExtraHeaders, type ExtraHeadersInput } from "./extra-headers";
export { ExtraHeadersError, EXTRA_HEADERS_ENV } from "./extra-headers";
import {
  caseRecordsSize,
  decodeVersionJsonl,
  encodeVersionJsonl,
  VERSION_JSONL_MAX_BYTES,
  VERSION_JSONL_MAX_ITEMS,
  type LegacyRowsPolicy,
} from "./datasets/version-jsonl";

type QueryOf<T> = T extends { query?: infer TQuery }
  ? NonNullable<TQuery>
  : never;
type BodyOf<T> = T extends { body: infer TBody } ? TBody : never;
type LooseQuery = Record<string, unknown>;
type LooseBody = unknown;
type GeneratedOperation<TResult = unknown> = (options: any) => TResult;

export type FutureAGIClientOptions = {
  apiKey?: string;
  secretKey?: string;
  fiApiKey?: string;
  fiSecretKey?: string;
  baseUrl?: string;
  headers?: Record<string, string>;
  fetch?: typeof fetch;
  /** Per-request timeout; default 30 000 ms. */
  timeoutMs?: number;
  /** Retries for 429/503 (any method) and 502/504 (idempotent methods); default 3. */
  retries?: number;
  /** The platform origin; default `FI_PLATFORM_BASE_URL`, else `{baseUrl}/omega/api`. */
  platformBaseUrl?: string;
  /** Sent as `X-Workspace-Id` on platform calls; default `FI_WORKSPACE_ID`, else the key's own workspace. */
  workspaceId?: string;
  /** Sent as `X-Organization-Id` on platform calls; default `FI_ORGANIZATION_ID`. */
  organizationId?: string;
  /** A self-hosted Omega EE's Bearer token (`FI_PLATFORM_TOKEN`); never together with a key pair. */
  platformToken?: string;
  /** Let the keys go to a platform origin outside the Future AGI zone (`FI_ALLOW_CUSTOM_PLATFORM_URL=1`). */
  allowCustomPlatformUrl?: boolean;
  /** Allow non-loopback HTTP for Bearer platform calls (FI_ALLOW_INSECURE_HTTP=1); false overrides env.
   * Keys mode warns without refusing; credential provenance is still required. */
  allowInsecureHttp?: boolean;
  /**
   * Headers for every request to `baseUrl`, added to `FI_EXTRA_HEADERS` and winning over it for the
   * same name (`Name=value` text or a record). Never `X-Api-Key`, `X-Secret-Key` or `Authorization`,
   * never another host (extra-headers.ts).
   */
  extraHeaders?: ExtraHeadersInput;
};

const DEFAULT_BASE_URL = "https://api.futureagi.com";

function readEnv(name: string): string | undefined {
  const maybeProcess = (
    globalThis as { process?: { env?: Record<string, string | undefined> } }
  ).process;
  return maybeProcess?.env?.[name];
}

function requireAuth(options: FutureAGIClientOptions): {
  apiKey: string;
  secretKey: string;
} {
  const apiKey =
    options.apiKey ?? options.fiApiKey ?? readEnv(API_KEY_ENVVAR_NAME);
  const secretKey =
    options.secretKey ?? options.fiSecretKey ?? readEnv(SECRET_KEY_ENVVAR_NAME);

  if (!apiKey || !secretKey) {
    throw new CredentialsMissingError(
      `FutureAGIClient requires credentials. Pass apiKey/secretKey or set ${API_KEY_ENVVAR_NAME} and ${SECRET_KEY_ENVVAR_NAME}.`,
    );
  }

  return { apiKey, secretKey };
}

const dataOptions = <T extends object>(client: Client, options: T) => ({
  ...options,
  client,
  responseStyle: "data" as const,
  throwOnError: true as const,
});

// All uses of this view pass dataOptions: only the response body is returned.
// Keep the low-level generated API and its default fields response style separate.
const dataSdk = generatedSdk as unknown as CatalogDataSdk;

const callGenerated = <TResult>(
  client: Client,
  operation: GeneratedOperation<TResult>,
  options: Record<string, unknown> = {},
) => operation(dataOptions(client, options));

/**
 * The typed error for a core-namespace failure: an HTTP error maps through the shared status table with
 * the body's fields copied onto it (so `e.detail` keeps working); a fetch failure is
 * `APIConnectionError` / `APITimeoutError`; an SDK error passes through unchanged.
 */
function typedError(error: unknown, response: Response | undefined, request: Request | undefined, baseUrl: string): unknown {
  if (error instanceof SDKException || error instanceof ExtraHeadersError) return error;
  if (response !== undefined && (response.type === "opaqueredirect" || (response.status >= 300 && response.status < 400))) {
    return redirectError(response, request, baseUrl);
  }
  if (response !== undefined && response.ok) {
    // a success status whose body did not parse (hey-api's JSON.parse threw)
    return new FutureAGIAPIError(response.status, undefined, { code: "invalid_json", message: "the server's response was not JSON" });
  }
  if (response !== undefined) {
    const payload = error === "" ? undefined : error;
    return apiError(response.status, payload, response.headers, {
      assignBody: true, wrongRegion: isWrongRegionResponse(response.status, payload),
    });
  }
  let origin = baseUrl;
  try {
    origin = new URL(baseUrl).origin;
  } catch {
    // keep the configured string
  }
  return connectionError(error, { origin });
}

/**
 * A 3xx on a core call. The generated client is built with `redirect: "manual"`, so a redirect is never
 * followed and the keys never reach another origin (Python's core client does not follow redirects
 * either). The error names the target host only, the same class a platform call throws.
 */
function redirectError(response: Response, request: Request | undefined, baseUrl: string): UnexpectedRedirectError {
  const from = request?.url ?? (response.url || baseUrl);
  const location = response.headers.get("location");
  let host: string | undefined;
  try {
    host = location !== null ? new URL(location, from).host : undefined;
  } catch {
    host = undefined;
  }
  let operation: string | undefined;
  try {
    operation = request !== undefined ? `${request.method} ${new URL(request.url).pathname}` : undefined;
  } catch {
    operation = undefined;
  }
  return new UnexpectedRedirectError(
    `${operation ?? "request"}: the server answered ${response.status} and the SDK never follows a redirect (target host: ${host ?? "unknown"})`,
    response.status,
    host,
    response.headers.get("x-request-id") ?? undefined,
    operation,
  );
}

/**
 * Simulation APIs are not offered in this release.
 * Core facade methods resolve to the server body, not fetch metadata (`data`, `request`,
 * `response`). FA success envelopes and DRF pagination envelopes are retained; dedicated
 * resource namespaces that unwrap `result` document that behavior separately.
 */
export class FutureAGIClient {
  readonly annotationLabels: AnnotationLabelsClient;
  readonly knowledgeBases: KnowledgeBasesClient;
  readonly optimizations: Optimizations;
  /** The paginated platform model catalog, separate from gateway model inference. */
  readonly models: Models;
  readonly prompts: PromptsClient;
  /** Managed Console agents and their schedules. */
  readonly agents: Agents;
  /** Workspace environment profiles. */
  readonly environments: Environments;
  readonly scores: ScoresClient;
  readonly workspaces: Workspaces;
  readonly annotationQueues: AnnotationQueuesClient;
  readonly datasets: DatasetsClient;
  readonly experimentRuns: ExperimentRunsClient;
  readonly evals: EvalsClient;
  /** The experiments v2 REST API (renamed from `experiments`). */
  readonly experimentsV2: ExperimentsClient;
  readonly tracing: TracingClient;
  readonly users: UsersClient;
  readonly alerts: AlertsClient;
  readonly generated: typeof generatedSdk = generatedSdk;
  readonly generatedClient: Client;

  readonly #options: FutureAGIClientOptions;
  private platformShared: PlatformShared;
  private platformCore?: PlatformCore;
  private managementShared: PlatformShared;
  private managementCore?: PlatformCore;

  /** Gateway management with personal platform credentials, separate from model calls. */
  get gateway(): ManagementGateway {
    this.managementCore ??= new PlatformCore(this.managementShared, {
      timeoutMs: this.#options.timeoutMs ?? DEFAULT_TIMEOUT_MS,
      streamIdleTimeoutMs: DEFAULT_STREAM_IDLE_MS,
      ...(this.#options.retries !== undefined ? { retries: this.#options.retries } : {}),
    });
    return new ManagementGateway(this.managementCore);
  }

  /**
   * Never throws for missing keys: they are resolved on the first request (options, then
   * FI_API_KEY / FI_SECRET_KEY). Requests time out after 30 s. 429 and pre-send network errors are
   * retried on every method; 502/503/504 and other network errors on idempotent methods only, so a
   * POST create is never repeated after a 5xx (transport.ts).
   *
   * Redirects are never followed on any namespace (`redirect: "manual"`): a 3xx throws
   * `UnexpectedRedirectError` naming the target host only, and the keys stay on the configured origin.
   *
   * Errors are typed on every namespace: each status throws the same class a platform
   * namespace throws (`NotFoundError`, `CoreRateLimitError`, ...), with the response body's fields copied
   * onto the error, and a failure with no response throws `APIConnectionError` / `APITimeoutError`.
   * The platform origin is resolved, and its host guard run, on the first platform call.
   * `FI_EXTRA_HEADERS` and `extraHeaders` go on every request to `baseUrl`, read when it is sent
   * (extra-headers.ts), on core and platform namespaces alike (a platform origin under `baseUrl`).
   */
  constructor(options: FutureAGIClientOptions = {}) {
    this.#options = { ...options };
    const baseUrl =
      options.baseUrl ?? readEnv("FI_BASE_URL") ?? DEFAULT_BASE_URL;
    // checked now; the setting is read per request, before the retrying transport (an error is never retried).
    // Core and platform calls share it: a platform origin under baseUrl (the derived one) gets the headers.
    const extra = new ExtraHeaders(baseUrl, options.extraHeaders);
    this.platformShared = {
      // Supplemental contracts never replace certified platform operation objects.
      table: { ...CONNECTOR_OPERATIONS, ...PLATFORM_OPERATIONS },
      resolveOrigin: () => {
        const { apiKey = this.#options.fiApiKey, secretKey = this.#options.fiSecretKey } = this.#options;
        return resolvePlatformOrigin({
          ...this.#options,
          ...(apiKey !== undefined ? { apiKey } : {}),
          ...(secretKey !== undefined ? { secretKey } : {}),
          baseUrl,
        });
      },
      ...(options.fetch !== undefined ? { fetch: options.fetch } : {}),
      ...(options.retries !== undefined ? { retries: options.retries } : {}),
      extraHeaders: extra,
    };

    this.managementShared = {
      ...this.platformShared,
      table: MANAGEMENT_OPERATIONS,
      errorScrubber: scrubManagementValue,
      resolveOrigin: () => managementOrigin(baseUrl, requireAuth(options), selectorHeaders(options), options.platformToken ?? readEnv("FI_PLATFORM_TOKEN")),
    };

    this.generatedClient = createClient({
      baseUrl,
      fetch: withExtraHeaders(resilientFetch({
        fetch: options.fetch,
        timeoutMs: options.timeoutMs ?? DEFAULT_TIMEOUT_MS,
        retries: options.retries,
        resolveCredentials: () => requireAuth(options),
      }), extra),
      headers: { ...options.headers },
      // never follow a redirect: fetch would forward X-Api-Key / X-Secret-Key to the target origin
      redirect: "manual",
      responseStyle: "data",
      throwOnError: true,
    });
    this.agents = new Agents(this);
    this.environments = new Environments(this);
    this.knowledgeBases = new KnowledgeBasesClient(this.generatedClient);
    this.prompts = new PromptsClient(this.generatedClient);
    this.scores = new ScoresClient(this.generatedClient);
    this.annotationLabels = this.scores.labels;
    this.annotationQueues = new AnnotationQueuesClient(this.generatedClient);
    this.datasets = new DatasetsClient(this.generatedClient);
    this.experimentRuns = new ExperimentRunsClient(this.generatedClient);
    this.evals = new EvalsClient(this.generatedClient);
    this.experimentsV2 = new ExperimentsClient(this.generatedClient);
    const catalogHeaders = () => selectorHeaders(options);
    this.tracing = new TracingClient(this.generatedClient, catalogHeaders);
    this.users = new UsersClient(this.generatedClient);
    this.alerts = new AlertsClient(this.generatedClient);
    this.optimizations = new Optimizations(this.generatedClient, catalogHeaders);
    this.models = new Models(this.generatedClient, catalogHeaders);
    this.workspaces = new Workspaces(this.generatedClient, catalogHeaders);
    this.generatedClient.interceptors.error.use((error, response, request) => typedError(error, response, request, baseUrl));
  }

  /**
   * A copy with another default `timeoutMs` and/or `retries`. It shares the credentials and the platform
   * origin; requests go through the same `fetch` (and so the same connection pool).
   */
  withOptions(options: { timeoutMs?: number; retries?: number }): FutureAGIClient {
    const copy = new FutureAGIClient({ ...this.#options, ...options });
    copy.platformShared = this.platformShared; // one resolved origin; the copy's own settings carry the new defaults
    copy.managementShared = this.managementShared;
    return copy;
  }

  /** Workspace MCP connections; the SDK never completes OAuth. */
  get connectors(): Connectors { return new Connectors(this); }

  /** Data connections and their sync history. */
  get integrations(): Integrations { return new Integrations(this.generatedClient, () => selectorHeaders(this.#options)); }

  /** Read credential metadata; mutations remain in the Console. */
  get credentials(): Credentials { return new Credentials(this); }

  /** @internal The platform executor (`src/_core/platform-base.ts`); platform namespaces call it. */
  get _platform(): PlatformCore {
    this.platformCore ??= new PlatformCore(this.platformShared, {
      timeoutMs: this.#options.timeoutMs ?? DEFAULT_TIMEOUT_MS,
      streamIdleTimeoutMs: DEFAULT_STREAM_IDLE_MS,
      ...(this.#options.retries !== undefined ? { retries: this.#options.retries } : {}),
    });
    return this.platformCore;
  }

  /** @deprecated Renamed `experimentsV2`; this alias will be removed. */
  get experiments(): ExperimentsClient {
    return this.experimentsV2;
  }
}

/** Queue create body; omitted label_ids uses the supplied scope's default queue labels. */
export type CreateAnnotationQueueBody = Omit<
  BodyOf<generatedTypes.CreateAnnotationQueueData>,
  "label_ids" | "annotator_roles"
> & {
  /** At least one label id. Omission reuses the supplied scope's default queue labels,
   * with a DeprecationWarning; no single scope or no usable labels raises DefaultQueueLabelError
   * (import from `@future-agi/sdk`). The lookup can create or restore the default queue even
   * if the label check then fails. */
  label_ids?: Array<string>;
  /** Roles per user id in `annotator_ids`: "annotator", "reviewer", "manager", or a list of them. */
  annotator_roles?: Record<string, string | Array<string>>;
  /**
   * Not sent (read-only on create). When label_ids is omitted, identifies the default queue
   * used to obtain labels; otherwise warns that this cannot scope the new queue.
   * To use the default queue itself, call `getOrCreateDefault({ project_id })`.
   */
  project?: string | null;
  /** Not sent on create; accepted for default-label lookup, as `project`.
   * To use the default queue itself, call `getOrCreateDefault({ dataset_id })`. */
  dataset?: string | null;
  /** Not sent on create; accepted for default-label lookup, as `project`.
   * To use the default queue itself, call `getOrCreateDefault({ agent_definition_id })`. */
  agent_definition?: string | null;
};

type QueueDefaultRequestBody = BodyOf<generatedTypes.ModelHubAnnotationQueuesGetOrCreateDefaultData>;

/** Exactly one key of `T`, required and non-null; the others absent. */
type ExactlyOne<T> = {
  [K in keyof T]-?: { [P in K]-?: NonNullable<T[P]> } & {
    [P in Exclude<keyof T, K>]?: never;
  };
}[keyof T];

/** The body of `annotationQueues.getOrCreateDefault`: exactly one of the scope ids. */
export type AnnotationQueueDefaultScope = ExactlyOne<QueueDefaultRequestBody>;

export class AnnotationQueuesClient {
  readonly items: AnnotationQueueItemsClient;
  readonly discussion: AnnotationQueueDiscussionClient;
  readonly review: AnnotationQueueReviewClient;

  constructor(private readonly client: Client) {
    this.items = new AnnotationQueueItemsClient(client);
    this.discussion = new AnnotationQueueDiscussionClient(client);
    this.review = new AnnotationQueueReviewClient(client);
  }

  /** Return a DRF queue page including total_pages and current_page.
   * Pagination: page_size (page size); limit (page size); page (1-based). page_size is a supported size alias; limit takes precedence when both are supplied. */
  list(query?: QueryOf<generatedTypes.ListAnnotationQueuesData>) {
    return dataSdk.listAnnotationQueues(
      dataOptions(this.client, { query }),
    );
  }

  /**
   * Create an annotation queue (POST /model-hub/annotation-queues/).
   *
   * `name` is required; supply `label_ids` with at least one annotation label id. Omitting
   * labels emits one DeprecationWarning and reuses getOrCreateDefault for exactly one of
   * project, dataset or agent_definition. This can create or restore that default queue even
   * if the label check then fails. No single scope or no usable labels raises DefaultQueueLabelError
   * (an SDKException, importable from `@future-agi/sdk`).
   * It never invents labels or scopes the new queue. Explicit null/empty labels are invalid.
   * With explicit labels, `project`,
   * `dataset` and `agent_definition` are read-only on the server and never applied on create:
   * they are dropped with a deprecation warning and remain accepted for compatibility.
   * `project_id`, `dataset_id` or `agent_definition_id` in the body are rejected (`SDKException`)
   * with the `getOrCreateDefault` call to use instead: the server never applies them to the
   * queue (it only uses them to scope its duplicate-name check).
   */
  async create(body: CreateAnnotationQueueBody) {
    refuseScopeIds(body, "annotationQueues.create()", FACADE_DEFAULT_SCOPE_KEYS, FACADE_DEFAULT_QUEUE_METHOD);
    body = await withDefaultLabels(
      body, "label_ids", DEFAULT_QUEUE_SCOPE_IDS,
      (scope) => this.getOrCreateDefault(scope as unknown as AnnotationQueueDefaultScope),
      "annotationQueues.create()",
    );
    return dataSdk.createAnnotationQueue(
      dataOptions(this.client, {
        // The generated type reads the serializer's JSONField child as an object; the server
        // takes a role or a list of roles per user (normalize_annotator_roles).
        body: annotationQueueCreateBody(
          body,
          "annotationQueues.create()",
          FACADE_DEFAULT_QUEUE_CALL,
          FACADE_DEFAULT_QUEUE_METHOD,
        ) as BodyOf<generatedTypes.CreateAnnotationQueueData>,
      }),
    );
  }

  /**
   * The default annotation queue of a project, dataset or agent definition
   * (POST /model-hub/annotation-queues/get-or-create-default/). Give exactly one id; anything
   * else is rejected (`SDKException`) before any request. The server returns the active default
   * queue, restores an archived one, or creates it (`result.action` is `"fetched"`, `"restored"`
   * or `"created"`), with its labels. Default queues are open to every member of the organization.
   */
  async getOrCreateDefault(
    scope: AnnotationQueueDefaultScope,
  ): Promise<generatedTypes.QueueDefaultResponse> {
    // dataOptions() asks for responseStyle "data", so the call resolves to the response body;
    // the generated signature does not carry the response style, hence the cast.
    return (await dataSdk.modelHubAnnotationQueuesGetOrCreateDefault(
      dataOptions(this.client, {
        body: annotationQueueDefaultBody(
          scope,
          "annotationQueues.getOrCreateDefault()",
          FACADE_DEFAULT_SCOPE_KEYS,
        ) as QueueDefaultRequestBody,
      }),
    )) as unknown as generatedTypes.QueueDefaultResponse;
  }

  get(id: string) {
    return dataSdk.getAnnotationQueue(
      dataOptions(this.client, { path: { id } }),
    );
  }

  update(id: string, body: BodyOf<generatedTypes.UpdateAnnotationQueueData>) {
    return dataSdk.updateAnnotationQueue(
      dataOptions(this.client, { path: { id }, body }),
    );
  }

  /** Archive a queue; return {status, result: {deleted, archived, queue_id}} (HTTP 200). */
  archive(id: string) {
    return dataSdk.archiveAnnotationQueue(
      dataOptions(this.client, { path: { id } }),
    );
  }

  updateStatus(
    id: string,
    body: BodyOf<generatedTypes.UpdateAnnotationQueueStatusData>,
  ) {
    return dataSdk.updateAnnotationQueueStatus(
      dataOptions(this.client, { path: { id }, body }),
    );
  }

  progress(id: string) {
    return dataSdk.getAnnotationQueueProgress(
      dataOptions(this.client, { path: { id } }),
    );
  }

  analytics(id: string) {
    return dataSdk.getAnnotationQueueAnalytics(
      dataOptions(this.client, { path: { id } }),
    );
  }

  agreement(id: string) {
    return dataSdk.getAnnotationQueueAgreement(
      dataOptions(this.client, { path: { id } }),
    );
  }

  exportJson(id: string) {
    return dataSdk.exportAnnotationQueue(
      dataOptions(this.client, { path: { id } }),
    );
  }

  listExportFields(id: string) {
    return dataSdk.listAnnotationQueueExportFields(
      dataOptions(this.client, { path: { id } }),
    );
  }

  exportToDataset(
    id: string,
    body: BodyOf<generatedTypes.ExportAnnotationQueueToDatasetData>,
  ) {
    return dataSdk.exportAnnotationQueueToDataset(
      dataOptions(this.client, { path: { id }, body }),
    );
  }

  addLabel(
    id: string,
    body: BodyOf<generatedTypes.AddAnnotationQueueLabelData>,
  ) {
    return dataSdk.addAnnotationQueueLabel(
      dataOptions(this.client, { path: { id }, body }),
    );
  }

  removeLabel(
    id: string,
    body: BodyOf<generatedTypes.RemoveAnnotationQueueLabelData>,
  ) {
    return dataSdk.removeAnnotationQueueLabel(
      dataOptions(this.client, { path: { id }, body }),
    );
  }
}

export class AnnotationQueueItemsClient {
  constructor(private readonly client: Client) {}

  /** Return a DRF queue-item page including total_pages and current_page.
   * Pagination: limit (page size); page (1-based). */
  list(
    queueId: string,
    query?: QueryOf<generatedTypes.ListAnnotationQueueItemsData>,
  ) {
    return dataSdk.listAnnotationQueueItems(
      dataOptions(this.client, { path: { queue_id: queueId }, query }),
    );
  }

  add(
    queueId: string,
    body: BodyOf<generatedTypes.AddAnnotationQueueItemsData>,
  ) {
    return dataSdk.addAnnotationQueueItems(
      dataOptions(this.client, { path: { queue_id: queueId }, body }),
    );
  }

  assign(
    queueId: string,
    body: BodyOf<generatedTypes.AssignAnnotationQueueItemsData>,
  ) {
    return dataSdk.assignAnnotationQueueItems(
      dataOptions(this.client, { path: { queue_id: queueId }, body }),
    );
  }

  remove(
    queueId: string,
    body: BodyOf<generatedTypes.RemoveAnnotationQueueItemsData>,
  ) {
    return dataSdk.removeAnnotationQueueItems(
      dataOptions(this.client, { path: { queue_id: queueId }, body }),
    );
  }

  /** Pagination: no supported paging parameters. Use exclude or before for item navigation, not numbered pages. */
  next(
    queueId: string,
    query?: QueryOf<generatedTypes.GetNextAnnotationQueueItemData>,
  ) {
    return dataSdk.getNextAnnotationQueueItem(
      dataOptions(this.client, { path: { queue_id: queueId }, query }),
    );
  }

  getDetail(
    queueId: string,
    itemId: string,
    query?: QueryOf<generatedTypes.GetAnnotationQueueItemDetailData>,
  ) {
    return dataSdk.getAnnotationQueueItemDetail(
      dataOptions(this.client, {
        path: { queue_id: queueId, id: itemId },
        query,
      }),
    );
  }

  release(
    queueId: string,
    itemId: string,
    body: BodyOf<generatedTypes.ReleaseAnnotationQueueItemData> = {},
  ) {
    return dataSdk.releaseAnnotationQueueItem(
      dataOptions(this.client, {
        path: { queue_id: queueId, id: itemId },
        body,
      }),
    );
  }

  complete(
    queueId: string,
    itemId: string,
    body: BodyOf<generatedTypes.CompleteAnnotationQueueItemData> = {},
  ) {
    return dataSdk.completeAnnotationQueueItem(
      dataOptions(this.client, {
        path: { queue_id: queueId, id: itemId },
        body,
      }),
    );
  }

  skip(
    queueId: string,
    itemId: string,
    body: BodyOf<generatedTypes.SkipAnnotationQueueItemData> = {},
  ) {
    return dataSdk.skipAnnotationQueueItem(
      dataOptions(this.client, {
        path: { queue_id: queueId, id: itemId },
        body,
      }),
    );
  }

  listAnnotations(queueId: string, itemId: string) {
    return dataSdk.listAnnotationQueueItemAnnotations(
      dataOptions(this.client, { path: { queue_id: queueId, id: itemId } }),
    );
  }

  submitAnnotations(
    queueId: string,
    itemId: string,
    body: BodyOf<generatedTypes.SubmitAnnotationQueueItemAnnotationsData>,
  ) {
    return dataSdk.submitAnnotationQueueItemAnnotations(
      dataOptions(this.client, {
        path: { queue_id: queueId, id: itemId },
        body,
      }),
    );
  }

  importAnnotations(
    queueId: string,
    itemId: string,
    body: BodyOf<generatedTypes.ImportAnnotationQueueItemAnnotationsData>,
  ) {
    return dataSdk.importAnnotationQueueItemAnnotations(
      dataOptions(this.client, {
        path: { queue_id: queueId, id: itemId },
        body,
      }),
    );
  }
}

export class AnnotationQueueDiscussionClient {
  constructor(private readonly client: Client) {}

  list(queueId: string, itemId: string) {
    return dataSdk.listAnnotationQueueItemDiscussion(
      dataOptions(this.client, { path: { queue_id: queueId, id: itemId } }),
    );
  }

  comment(
    queueId: string,
    itemId: string,
    body: BodyOf<generatedTypes.CreateAnnotationQueueItemCommentData>,
  ) {
    return dataSdk.createAnnotationQueueItemComment(
      dataOptions(this.client, {
        path: { queue_id: queueId, id: itemId },
        body,
      }),
    );
  }

  resolveThread(
    queueId: string,
    itemId: string,
    threadId: string,
    body: BodyOf<generatedTypes.ResolveAnnotationQueueItemThreadData> = {},
  ) {
    return dataSdk.resolveAnnotationQueueItemThread(
      dataOptions(this.client, {
        path: { queue_id: queueId, id: itemId, thread_id: threadId },
        body,
      }),
    );
  }

  reopenThread(
    queueId: string,
    itemId: string,
    threadId: string,
    body: BodyOf<generatedTypes.ReopenAnnotationQueueItemThreadData> = {},
  ) {
    return dataSdk.reopenAnnotationQueueItemThread(
      dataOptions(this.client, {
        path: { queue_id: queueId, id: itemId, thread_id: threadId },
        body,
      }),
    );
  }

  react(
    queueId: string,
    itemId: string,
    commentId: string,
    body: BodyOf<generatedTypes.ToggleAnnotationQueueItemCommentReactionData>,
  ) {
    return dataSdk.toggleAnnotationQueueItemCommentReaction(
      dataOptions(this.client, {
        path: { queue_id: queueId, id: itemId, comment_id: commentId },
        body,
      }),
    );
  }
}

export class AnnotationQueueReviewClient {
  constructor(private readonly client: Client) {}

  submit(
    queueId: string,
    itemId: string,
    body: BodyOf<generatedTypes.ReviewAnnotationQueueItemData>,
  ) {
    return dataSdk.reviewAnnotationQueueItem(
      dataOptions(this.client, {
        path: { queue_id: queueId, id: itemId },
        body,
      }),
    );
  }
}

export class DatasetVersionsClient {
  constructor(private readonly client: Client) {}

  /** Pagination: limit (page size); offset (0-based). */
  list(
    datasetId: string,
    query?: QueryOf<generatedTypes.ListDatasetVersionsData>,
  ) {
    return generatedSdk.listDatasetVersions<true, "data">(
      dataOptions(this.client, { path: { dataset_id: datasetId }, query }),
    );
  }

  /** Pagination: limit (page size); offset (0-based). */
  get(
    datasetId: string,
    versionId: string,
    query?: QueryOf<generatedTypes.GetDatasetVersionData>,
  ) {
    return generatedSdk.getDatasetVersion<true, "data">(
      dataOptions(this.client, {
        path: { dataset_id: datasetId, version_id: versionId },
        query,
      }),
    );
  }

  /** One attempt. Retrying snapshot creation can create another version. */
  create(
    datasetId: string,
    body: BodyOf<generatedTypes.CreateDatasetVersionData>,
  ) {
    return generatedSdk.createDatasetVersion<true, "data">(
      dataOptions(this.client, { path: { dataset_id: datasetId }, body }),
    );
  }

  async exportJsonl(datasetId: string, versionId: string): Promise<string> {
    let offset = 0;
    let version: generatedTypes.DatasetVersionRead | undefined;
    let receivedBytes = 0;
    const items: generatedTypes.DatasetVersionItemRead[] = [];
    while (true) {
      const page = await this.get(datasetId, versionId, { limit: 500, offset });
      const result = page.result;
      if (
        String(result.version.id).toLowerCase() !== versionId.toLowerCase() ||
        String(result.version.dataset).toLowerCase() !== datasetId.toLowerCase()
      )
        throw new Error("Version page identity changed");
      if (version && JSON.stringify(version) !== JSON.stringify(result.version))
        throw new Error("Version metadata changed between pages");
      version = result.version;
      const count = version.item_count;
      if (
        typeof count !== "number" ||
        !Number.isInteger(count) ||
        count < 0 ||
        count > VERSION_JSONL_MAX_ITEMS
      )
        throw new Error("Invalid version item_count");
      if (result.offset !== offset || (result.has_more && !result.items.length))
        throw new Error("Version pagination is incomplete");
      receivedBytes += caseRecordsSize(result.items);
      if (receivedBytes > VERSION_JSONL_MAX_BYTES)
        throw new Error("Version pages exceed archive byte limit");
      items.push(...result.items);
      offset += result.items.length;
      if (items.length > count || (result.has_more && items.length >= count))
        throw new Error("Version pagination exceeds the declared item_count");
      if (!result.has_more) return encodeVersionJsonl(version, items);
    }
  }

  async importJsonl(
    datasetId: string,
    source: string | Uint8Array,
    options: { parentVersionId?: string; legacyRows?: LegacyRowsPolicy } = {},
  ) {
    const body = await decodeVersionJsonl(source, datasetId, options);
    return this.create(datasetId, body);
  }
}

export class DatasetsClient {
  readonly versions: DatasetVersionsClient;

  constructor(private readonly client: Client) {
    this.versions = new DatasetVersionsClient(client);
  }

  /** Pagination: page (0-based); page_size (page size). */
  list(query?: LooseQuery) {
    return callGenerated(this.client, dataSdk.listDatasets, { query });
  }

  listNames(query?: LooseQuery) {
    return callGenerated(this.client, dataSdk.listDatasetNames, { query });
  }

  /** Pagination: page_size (page size); current_page_index (0-based); cursor (opaque continuation token). */
  getTable(datasetId: string, query?: LooseQuery) {
    return callGenerated(this.client, dataSdk.getDatasetTable, {
      path: { dataset_id: datasetId },
      query,
    });
  }

  getRow(datasetId: string, body: LooseBody) {
    return callGenerated(this.client, dataSdk.getDatasetRow, {
      path: { dataset_id: datasetId },
      body,
    });
  }

  getColumns(datasetId: string) {
    return callGenerated(this.client, dataSdk.getDatasetColumns, {
      path: { dataset_id: datasetId },
    });
  }

  createEmpty(body: LooseBody) {
    return callGenerated(this.client, dataSdk.createEmptyDataset, {
      body,
    });
  }

  createManual(body: LooseBody) {
    return callGenerated(this.client, dataSdk.createDatasetManually, {
      body,
    });
  }

  /** Upload a file with optional dataset metadata, or pass native FormData. */
  createFromFile(body: BodyOf<generatedTypes.CreateDatasetFromLocalFileData> | FormData) {
    const form = body instanceof FormData
      ? body
      : formDataBodySerializer.bodySerializer(body);
    if (!(form.get("file") instanceof Blob)) {
      throw new TypeError("Dataset uploads require a file.");
    }
    return callGenerated(this.client, dataSdk.createDatasetFromLocalFile, {
      body: form,
      // Preserve FormData rather than JSON-stringifying or rebuilding its parts.
      bodySerializer: null,
      // Clear inherited JSON headers so Request supplies the multipart boundary.
      headers: { "Content-Type": null },
    });
  }

  addRows(datasetId: string, body: LooseBody) {
    return callGenerated(this.client, dataSdk.addDatasetRows, {
      path: { dataset_id: datasetId },
      body,
    });
  }

  addColumns(datasetId: string, body: LooseBody) {
    return callGenerated(this.client, dataSdk.addDatasetColumns, {
      path: { dataset_id: datasetId },
      body,
    });
  }

  updateCell(datasetId: string, body: LooseBody) {
    return callGenerated(this.client, dataSdk.updateDatasetCell, {
      path: { dataset_id: datasetId },
      body,
    });
  }

  /** Return the success envelope containing the row deletion message. */
  deleteRow(datasetId: string, query?: LooseQuery) {
    return callGenerated(this.client, dataSdk.deleteDatasetRow, {
      path: { dataset_id: datasetId },
      query,
    });
  }

  /** Return the success envelope containing the column deletion message. */
  deleteColumn(datasetId: string, columnId: string) {
    return callGenerated(this.client, dataSdk.deleteDatasetColumn, {
      path: { dataset_id: datasetId, column_id: columnId },
    });
  }

  download(datasetId: string, query?: LooseQuery) {
    return callGenerated(this.client, dataSdk.downloadDataset, {
      path: { dataset_id: datasetId },
      query,
    });
  }

  jsonSchema(datasetId: string) {
    return callGenerated(this.client, dataSdk.getDatasetJsonSchema, {
      path: { dataset_id: datasetId },
    });
  }

  evalStats(datasetId: string, query?: LooseQuery) {
    return callGenerated(this.client, dataSdk.getDatasetEvalStats, {
      path: { dataset_id: datasetId },
      query,
    });
  }

  annotationSummary(datasetId: string, query?: LooseQuery) {
    return callGenerated(
      this.client,
      dataSdk.getDatasetAnnotationSummary,
      {
        path: { dataset_id: datasetId },
        query,
      },
    );
  }

  duplicate(datasetId: string, body?: LooseBody) {
    return callGenerated(this.client, dataSdk.duplicateDataset, {
      path: { dataset_id: datasetId },
      body,
    });
  }

  derivedVariables(datasetId: string) {
    return callGenerated(
      this.client,
      dataSdk.listDatasetDerivedVariables,
      {
        path: { dataset_id: datasetId },
      },
    );
  }

  baseColumns(query?: LooseQuery) {
    return callGenerated(this.client, dataSdk.listDatasetBaseColumns, {
      query,
    });
  }
}

export class ExperimentRunsClient {
  constructor(private readonly client: Client) {}

  /** One attempt; explicit replay requires the same run UUID and payload. */
  create(body: BodyOf<generatedTypes.CreateExternalExperimentRunData>) {
    return generatedSdk.createExternalExperimentRun<true, "data">(
      dataOptions(this.client, { body }),
    );
  }

  /** One attempt; explicit replay requires the same receipt keys and payload. */
  ingestResults(
    runId: string,
    body: BodyOf<generatedTypes.IngestExternalExperimentResultsData>,
  ) {
    return generatedSdk.ingestExternalExperimentResults<true, "data">(
      dataOptions(this.client, { path: { run_id: runId }, body }),
    );
  }

  compare(body: BodyOf<generatedTypes.CompareExperimentRunsData>) {
    return generatedSdk.compareExperimentRuns<true, "data">(
      dataOptions(this.client, { body }),
    );
  }
}

export class ExperimentsClient {
  constructor(private readonly client: Client) {}

  /** Return a DRF experiment page including total_pages and current_page.
   * Pagination: limit (page size); page (1-based). */
  list(query?: LooseQuery) {
    return callGenerated(this.client, dataSdk.listExperiments, { query });
  }

  create(body: LooseBody) {
    return callGenerated(this.client, dataSdk.createExperiment, { body });
  }

  get(experimentId: string, query?: LooseQuery) {
    return callGenerated(this.client, dataSdk.getExperiment, {
      path: { experiment_id: experimentId },
      query,
    });
  }

  update(experimentId: string, body: LooseBody) {
    return callGenerated(this.client, dataSdk.updateExperiment, {
      path: { experiment_id: experimentId },
      body,
    });
  }

  /** Return {status, result: {message, deleted_count}} after deleting experiments. */
  delete(body: LooseBody) {
    return callGenerated(this.client, dataSdk.deleteExperiments, { body });
  }

  /** Pagination: page_size (page size); current_page_index (0-based). */
  rows(experimentId: string, query?: LooseQuery) {
    return callGenerated(this.client, dataSdk.listExperimentRows, {
      path: { experiment_id: experimentId },
      query,
    });
  }

  /** Pagination: page_size (page size); current_page_index (0-based). */
  row(experimentId: string, rowId: string, query?: LooseQuery) {
    return callGenerated(this.client, dataSdk.getExperimentRow, {
      path: { experiment_id: experimentId, row_id: rowId },
      query,
    });
  }

  stats(experimentId: string, query?: LooseQuery) {
    return callGenerated(this.client, dataSdk.getExperimentStats, {
      path: { experiment_id: experimentId },
      query,
    });
  }

  download(experimentId: string, query?: LooseQuery) {
    return callGenerated(this.client, dataSdk.downloadExperiment, {
      path: { experiment_id: experimentId },
      query,
    });
  }

  rerun(body: LooseBody) {
    return callGenerated(this.client, dataSdk.rerunExperiment, { body });
  }

  stop(experimentId: string, body?: LooseBody) {
    return callGenerated(this.client, dataSdk.stopExperiment, {
      path: { experiment_id: experimentId },
      body,
    });
  }

  compare(experimentId: string, body: LooseBody) {
    return callGenerated(this.client, dataSdk.compareExperiments, {
      path: { experiment_id: experimentId },
      body,
    });
  }

  comparisons(experimentId: string, query?: LooseQuery) {
    return callGenerated(this.client, dataSdk.listExperimentComparisons, {
      path: { experiment_id: experimentId },
      query,
    });
  }

  jsonSchema(experimentId: string) {
    return callGenerated(this.client, dataSdk.getExperimentJsonSchema, {
      path: { experiment_id: experimentId },
    });
  }
}

export class EvalsClient {
  constructor(private readonly client: Client) {}

  /** Pagination: page (0-based); page_size (page size). Pass these in the request body. */
  listTemplates(
    body: BodyOf<generatedTypes.ModelHubEvalTemplatesListCreateData>,
  ) {
    return dataSdk.modelHubEvalTemplatesListCreate(
      dataOptions(this.client, { body }),
    );
  }

  createTemplate(
    body: BodyOf<generatedTypes.ModelHubEvalTemplatesCreateV2CreateData>,
  ) {
    return dataSdk.modelHubEvalTemplatesCreateV2Create(
      dataOptions(this.client, { body }),
    );
  }

  getTemplate(templateId: string) {
    return dataSdk.modelHubEvalTemplatesDetailList(
      dataOptions(this.client, { path: { template_id: templateId } }),
    );
  }

  updateTemplate(
    templateId: string,
    body: BodyOf<generatedTypes.ModelHubEvalTemplatesUpdateUpdateData>,
  ) {
    return dataSdk.modelHubEvalTemplatesUpdateUpdate(
      dataOptions(this.client, { path: { template_id: templateId }, body }),
    );
  }

  deleteTemplate(
    body: BodyOf<generatedTypes.ModelHubDeleteEvalTemplateCreateData>,
  ) {
    return dataSdk.modelHubDeleteEvalTemplateCreate(
      dataOptions(this.client, { body }),
    );
  }

  bulkDeleteTemplates(
    body: BodyOf<generatedTypes.ModelHubEvalTemplatesBulkDeleteCreateData>,
  ) {
    return dataSdk.modelHubEvalTemplatesBulkDeleteCreate(
      dataOptions(this.client, { body }),
    );
  }

  /** Pagination: page (0-based); page_size (page size). This facade uses the default page; use the low-level operation to supply pagination parameters. */
  templateUsage(templateId: string) {
    return dataSdk.modelHubEvalTemplatesUsageList(
      dataOptions(this.client, { path: { template_id: templateId } }),
    );
  }

  templateVersions(templateId: string) {
    return dataSdk.modelHubEvalTemplatesVersionsList(
      dataOptions(this.client, { path: { template_id: templateId } }),
    );
  }

  createTemplateVersion(
    templateId: string,
    body: BodyOf<generatedTypes.ModelHubEvalTemplatesVersionsCreateCreateData>,
  ) {
    return dataSdk.modelHubEvalTemplatesVersionsCreateCreate(
      dataOptions(this.client, { path: { template_id: templateId }, body }),
    );
  }

  restoreTemplateVersion(
    templateId: string,
    versionId: string,
    body: BodyOf<generatedTypes.ModelHubEvalTemplatesVersionsRestoreCreateData> = {},
  ) {
    return dataSdk.modelHubEvalTemplatesVersionsRestoreCreate(
      dataOptions(this.client, {
        path: { template_id: templateId, version_id: versionId },
        body,
      }),
    );
  }

  setDefaultTemplateVersion(
    templateId: string,
    versionId: string,
    body: BodyOf<generatedTypes.ModelHubEvalTemplatesVersionsSetDefaultUpdateData> = {},
  ) {
    return dataSdk.modelHubEvalTemplatesVersionsSetDefaultUpdate(
      dataOptions(this.client, {
        path: { template_id: templateId, version_id: versionId },
        body,
      }),
    );
  }

  listSdkEvals() {
    return dataSdk.sdkApiV1GetEvalsList(dataOptions(this.client, {}));
  }

  configure(
    body: BodyOf<generatedTypes.SdkApiV1ConfigureEvaluationsCreateData>,
  ) {
    return dataSdk.sdkApiV1ConfigureEvaluationsCreate(
      dataOptions(this.client, { body }),
    );
  }

  run(body: BodyOf<generatedTypes.SdkApiV1EvalCreateData>) {
    return dataSdk.sdkApiV1EvalCreate(dataOptions(this.client, { body }));
  }

  getRun(evalId: string) {
    return dataSdk.sdkApiV1EvalRead(
      dataOptions(this.client, { path: { eval_id: evalId } }),
    );
  }

  runV2(body: BodyOf<generatedTypes.SdkApiV1NewEvalCreateData>) {
    return dataSdk.sdkApiV1NewEvalCreate(
      dataOptions(this.client, { body }),
    );
  }

  getRunV2(evalId: string) {
    return dataSdk.sdkApiV1NewEvalList(
      dataOptions(this.client, { query: { eval_id: evalId } }),
    );
  }

  listPipelines(
    query: QueryOf<generatedTypes.SdkApiV1EvaluatePipelineListData>,
  ) {
    return dataSdk.sdkApiV1EvaluatePipelineList(
      dataOptions(this.client, { query }),
    );
  }

  evaluatePipeline(
    body: BodyOf<generatedTypes.SdkApiV1EvaluatePipelineCreateData>,
  ) {
    return dataSdk.sdkApiV1EvaluatePipelineCreate(
      dataOptions(this.client, { body }),
    );
  }

  datasetEvals(datasetId: string) {
    return dataSdk.modelHubDevelopsGetEvalsListList(
      dataOptions(this.client, { path: { dataset_id: datasetId } }),
    );
  }

  datasetEvalStructure(
    datasetId: string,
    evalId: string,
    query: QueryOf<generatedTypes.ModelHubDevelopsGetEvalStructureReadData>,
  ) {
    return dataSdk.modelHubDevelopsGetEvalStructureRead(
      dataOptions(this.client, {
        path: { dataset_id: datasetId, eval_id: evalId },
        query,
      }),
    );
  }

  previewDatasetEval(
    datasetId: string,
    body: BodyOf<generatedTypes.ModelHubDevelopsPreviewRunEvalCreateData>,
  ) {
    return dataSdk.modelHubDevelopsPreviewRunEvalCreate(
      dataOptions(this.client, { path: { dataset_id: datasetId }, body }),
    );
  }

  startDatasetEvals(
    datasetId: string,
    body: BodyOf<generatedTypes.ModelHubDevelopsStartEvalsProcessCreateData>,
  ) {
    return dataSdk.modelHubDevelopsStartEvalsProcessCreate(
      dataOptions(this.client, { path: { dataset_id: datasetId }, body }),
    );
  }

  /**
   * Selecting Turing/Protect models requires an Enterprise licence including those models on
   * self-hosted servers; cloud plan checks are separate. A self-hosted model-gate denial raises
   * PaymentRequiredError (HTTP 402 ENTITLEMENT_DENIED), not LicenseRequiredError. Select another
   * model or ask the server administrator to enable the licensed models. Code evaluations are
   * exempt from this model gate.
   */
  addDatasetUserEval(
    datasetId: string,
    body: BodyOf<generatedTypes.ModelHubDevelopsAddUserEvalCreateData>,
  ) {
    return dataSdk.modelHubDevelopsAddUserEvalCreate(
      dataOptions(this.client, { path: { dataset_id: datasetId }, body }),
    );
  }

  /**
   * Selecting Turing/Protect models requires an Enterprise licence including those models on
   * self-hosted servers; cloud plan checks are separate. A self-hosted model-gate denial raises
   * PaymentRequiredError (HTTP 402 ENTITLEMENT_DENIED), not LicenseRequiredError. Select another
   * model or ask the server administrator to enable the licensed models. Code evaluations are
   * exempt from this model gate.
   */
  editAndRunDatasetUserEval(
    datasetId: string,
    evalId: string,
    body: BodyOf<generatedTypes.ModelHubDevelopsEditAndRunUserEvalCreateData>,
  ) {
    return dataSdk.modelHubDevelopsEditAndRunUserEvalCreate(
      dataOptions(this.client, {
        path: { dataset_id: datasetId, eval_id: evalId },
        body,
      }),
    );
  }

  stopDatasetUserEval(
    datasetId: string,
    evalId: string,
    body: BodyOf<generatedTypes.ModelHubDevelopsStopUserEvalCreateData> = {},
  ) {
    return dataSdk.modelHubDevelopsStopUserEvalCreate(
      dataOptions(this.client, {
        path: { dataset_id: datasetId, eval_id: evalId },
        body,
      }),
    );
  }

  /** Return the success envelope containing the evaluation deletion message. */
  deleteDatasetUserEval(datasetId: string, evalId: string) {
    return dataSdk.modelHubDevelopsDeleteUserEvalDelete(
      dataOptions(this.client, {
        path: { dataset_id: datasetId, eval_id: evalId },
      }),
    );
  }

  /** Return the success envelope containing the evaluation-template deletion message. */
  deleteDatasetTemplateEval(datasetId: string, evalId: string) {
    return dataSdk.modelHubDevelopsDeleteTemplateEvalDelete(
      dataOptions(this.client, {
        path: { dataset_id: datasetId, eval_id: evalId },
      }),
    );
  }
}

export class UsersClient {
  constructor(private readonly client: Client) {}

  current() {
    return callGenerated(this.client, dataSdk.getCurrentUser);
  }

  /** Pagination: page (1-based); limit (page size). */
  organizationMembers(query?: LooseQuery) {
    return callGenerated(this.client, dataSdk.listOrganizationMembers, {
      query,
    });
  }

  /** Pagination: page (1-based); limit (page size). */
  workspaces(query?: LooseQuery) {
    return callGenerated(this.client, dataSdk.listWorkspaces, { query });
  }

  /** Pagination: page (1-based); limit (page size). */
  workspaceMembers(workspaceId: string, query?: LooseQuery) {
    return callGenerated(this.client, dataSdk.listWorkspaceMembers, {
      path: { workspace_id: workspaceId },
      query,
    });
  }

  switchWorkspace(body: LooseBody) {
    return callGenerated(this.client, dataSdk.switchWorkspace, { body });
  }
}

export class AlertsClient {
  constructor(private readonly client: Client) {}

  /** Return {status, result: {results, metadata}}; metadata uses page_number/page_size.
   * Pagination: page_number (0-based); page_size (page size). */
  list(query?: LooseQuery) {
    return callGenerated(this.client, dataSdk.listAlerts, { query });
  }

  /** Return {status, result}: result is the creation message, not an alert object. */
  create(body: LooseBody) {
    return callGenerated(this.client, dataSdk.createAlert, { body });
  }

  /** Return the bare alert object (the server uses DRF retrieve, not a success envelope). */
  get(id: string) {
    return callGenerated(this.client, dataSdk.getAlert, {
      path: { id },
    });
  }

  /** Return {status, result}: result is the updated alert object. */
  update(id: string, body: LooseBody) {
    return callGenerated(this.client, dataSdk.updateAlert, {
      path: { id },
      body,
    });
  }

  /** Delete an alert; HTTP 204 has no JSON response body. */
  delete(id: string) {
    return callGenerated(this.client, dataSdk.deleteAlert, {
      path: { id },
    });
  }

  /** Return the server success envelope containing metric options.
   * Pagination: no supported paging parameters. */
  metricOptions(query?: LooseQuery) {
    return callGenerated(this.client, dataSdk.listAlertMetricOptions, {
      query,
    });
  }

  /** Return the server success envelope containing preview graph data. */
  previewGraph(body: LooseBody) {
    return callGenerated(this.client, dataSdk.previewAlertGraph, { body });
  }

  /** Return the server success envelope containing graph data. */
  graph(id: string, query?: LooseQuery) {
    return callGenerated(this.client, dataSdk.getAlertGraph, {
      path: { id },
      query,
    });
  }

  /** Return {status, result}: detail fields include the creator object and a paginated logs field.
   * Pagination: page_number (0-based); page_size (page size). These parameters page the nested logs list. */
  details(id: string, query?: LooseQuery) {
    return callGenerated(this.client, dataSdk.getAlertDetails, {
      path: { id },
      query,
    });
  }

  /** Return {status, result: {message}}; this is not the mute request body. */
  bulkMute(body: LooseBody) {
    return callGenerated(this.client, dataSdk.bulkMuteAlerts, { body });
  }

  /** Return the bare DRF log page with total_pages/current_page, without a status/result wrapper.
   * Pagination: limit (page size); page (1-based). */
  logs(query?: LooseQuery) {
    return callGenerated(this.client, dataSdk.listAlertLogs, { query });
  }

  /** Return {status, result}: result is the complete log array, not a DRF page.
   * Pagination: no supported paging parameters. */
  allLogs(query?: LooseQuery) {
    return callGenerated(this.client, dataSdk.listAllAlertLogs, { query });
  }

  /** Return the bare log object, without a status/result wrapper. */
  log(id: string) {
    return callGenerated(this.client, dataSdk.getAlertLog, {
      path: { id },
    });
  }

  /** Return {status, result}: result is an array of logs for this alert. */
  logsForAlert(id: string, query?: LooseQuery) {
    return callGenerated(this.client, dataSdk.listAlertLogsForAlert, {
      path: { id },
      query,
    });
  }

  /** Return the success envelope containing the log resolution message. */
  resolveLogs(body: LooseBody) {
    return callGenerated(this.client, dataSdk.resolveAlertLogs, { body });
  }
}

export { generatedSdk as futureAGIGeneratedSdk };
