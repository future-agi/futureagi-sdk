import type * as sdk from "./generated/openapi/sdk.gen";
import type * as types from "./generated/openapi/types.gen";

/** FA's GeneralMethods success body. This is not the fetch client's `data` field. */
export type SuccessEnvelope<T> = { status: boolean; result: T };

/** The server's ExtendedPageNumberPagination body, not an item array. */
export type CatalogPageResult<T> = {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
  total_pages: number;
  current_page: number;
};

/** Alert monitors use zero-based page_number/page_size, not DRF's count/next page. */
export type AlertPageResult<T> = {
  results: T[];
  metadata: {
    total_rows: number;
    page_number: number;
    page_size: number;
    total_pages: number;
  };
};

/** The detail serializer replaces created_by's id with a user and embeds a log page. */
export type AlertDetailsResult = Omit<
  types.UserAlertMonitor,
  "deleted_at" | "deleted" | "organization" | "logs" | "created_by"
> & {
  created_by: types.User | null;
  last_triggered_at: string | null;
  window_start: string | null;
  window_end: string | null;
  logs: AlertPageResult<types.UserAlertMonitorLog>;
};

/**
 * Facade-only response overrides for serializer-only/204 Swagger declarations.
 * The generated SDK remains untouched. Every operation here is new on FutureAGIClient
 * in 0.2.0 (the 0.1.2 package has no FutureAGIClient). Python preserves these bodies;
 * these overrides change types only, never unwrap or otherwise transform runtime data.
 */
type ResponseOverrides = {
  // FA tracer/views/monitor.py:192,568,358,273,444,1001,1010.
  listAlerts: SuccessEnvelope<AlertPageResult<types.UserAlertMonitor>>;
  createAlert: SuccessEnvelope<string>;
  updateAlert: SuccessEnvelope<types.UserAlertMonitor>;
  getAlertDetails: SuccessEnvelope<AlertDetailsResult>;
  bulkMuteAlerts: SuccessEnvelope<{ message: string }>;
  listAllAlertLogs: SuccessEnvelope<types.UserAlertMonitorLog[]>;
  listAlertLogsForAlert: SuccessEnvelope<types.UserAlertMonitorLog[]>;
  // FA tracer/views/monitor.py:888 inherits tfc/settings/settings.py:644's paginator.
  listAlertLogs: CatalogPageResult<types.UserAlertMonitorLog>;
  // FA model_hub/views/annotation_queues.py:3034,3050,3145-3147,4765,4912-4914.
  listAnnotationQueues: CatalogPageResult<types.AnnotationQueue>;
  listAnnotationQueueItems: CatalogPageResult<types.QueueItem>;
  // FA model_hub/views/experiments.py:5706-5711.
  listExperiments: CatalogPageResult<types.ExperimentListV2>;
  // FA model_hub/views/annotation_queues.py:3249: archive returns HTTP 200.
  archiveAnnotationQueue: SuccessEnvelope<{ deleted: boolean; archived: boolean; queue_id: string }>;
  // FA model_hub/views/develop_dataset.py:5349,5280,8917,8949.
  deleteDatasetRow: SuccessEnvelope<string>;
  deleteDatasetColumn: SuccessEnvelope<string>;
  modelHubDevelopsDeleteUserEvalDelete: SuccessEnvelope<string>;
  modelHubDevelopsDeleteTemplateEvalDelete: SuccessEnvelope<string>;
  // FA model_hub/views/experiments.py:5922.
  deleteExperiments: SuccessEnvelope<{ message: string; deleted_count: number }>;

};

// The pinned generator omits its responseStyle type parameter on older operations.
// Select only its success branch: the facade always passes throwOnError: true.
type SuccessBody<T> = T extends { data: infer Data; error?: undefined } ? Data : never;
type Operation = keyof typeof sdk;
type Body<K extends Operation> = K extends keyof ResponseOverrides
  ? ResponseOverrides[K]
  : SuccessBody<Awaited<ReturnType<(typeof sdk)[K]>>>;

/** Internal adapter: usable only with explicit data-only, throwing options. */
export type CatalogDataSdk = {
  [K in Operation]: (
    options: NonNullable<Parameters<(typeof sdk)[K]>[0]> & {
      responseStyle: "data";
      throwOnError: true;
    },
  ) => Promise<Body<K>>;
};
