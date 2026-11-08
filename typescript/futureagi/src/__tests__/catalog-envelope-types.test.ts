import type * as Facade from "../futureagi-client";
import type * as Types from "../generated/openapi/types.gen";

// Compile-time equality, including any/unknown and unwanted fetch metadata.
type Equal<A, B> = (<T>() => T extends A ? 1 : 2) extends
  (<T>() => T extends B ? 1 : 2) ? true : false;
type Assert<T extends true> = T;
type Envelope<T> = { status: boolean; result: T };
type MonitorPage<T> = {
  results: T[];
  metadata: { total_rows: number; page_number: number; page_size: number; total_pages: number };
};
type DrfPage<T> = {
  count: number; next: string | null; previous: string | null; results: T[];
  total_pages: number; current_page: number;
};
type MonitorDetails = Omit<Types.UserAlertMonitor, "deleted_at" | "deleted" | "organization" | "logs" | "created_by"> & {
  created_by: Types.User | null;
  last_triggered_at: string | null;
  window_start: string | null;
  window_end: string | null;
  logs: MonitorPage<Types.UserAlertMonitorLog>;
};

// Each assertion is independently named so tsc diagnostics identify the public method.
// Swagger's serializer-only responses are deliberately not the oracle for these methods.

// These facade namespaces are outside futureagi-client.ts's class declarations.
// FA develop_annotations.py:160,392-400; scores.py:346,379-381; prompt_template.py:648,697-698,3270-3276;
// prompt_labels.py:67 inherits settings.py:644's ExtendedPageNumberPagination.
// Both annotation-label aliases must be checked, not only the ScoresClient class.
type AnnotationLabels_list = Assert<Equal<Awaited<ReturnType<Facade.FutureAGIClient["annotationLabels"]["list"]>>, DrfPage<Types.AnnotationsLabels>>>;
type ScoresLabels_list = Assert<Equal<Awaited<ReturnType<Facade.FutureAGIClient["scores"]["labels"]["list"]>>, DrfPage<Types.AnnotationsLabels>>>;
type Scores_list = Assert<Equal<Awaited<ReturnType<Facade.FutureAGIClient["scores"]["list"]>>, DrfPage<Types.Score>>>;
type Prompts_list = Assert<Equal<Awaited<ReturnType<Facade.FutureAGIClient["prompts"]["list"]>>, DrfPage<Types.PromptTemplate>>>;
type PromptLabels_list = Assert<Equal<Awaited<ReturnType<Facade.FutureAGIClient["prompts"]["labels"]["list"]>>, DrfPage<Types.PromptLabel>>>;
type PromptVersions_list = Assert<Equal<Awaited<ReturnType<Facade.FutureAGIClient["prompts"]["versions"]["list"]>>, DrfPage<Types.PromptHistoryExecution>>>;

type AnnotationQueuesClient_list = Assert<Equal<Awaited<ReturnType<Facade.AnnotationQueuesClient["list"]>>, DrfPage<Types.AnnotationQueue>>>;
type AnnotationQueuesClient_create = Assert<Equal<Awaited<ReturnType<Facade.AnnotationQueuesClient["create"]>>, Types.CreateAnnotationQueueResponse>>;
type AnnotationQueuesClient_getOrCreateDefault = Assert<Equal<Awaited<ReturnType<Facade.AnnotationQueuesClient["getOrCreateDefault"]>>, Types.ModelHubAnnotationQueuesGetOrCreateDefaultResponse>>;
type AnnotationQueuesClient_get = Assert<Equal<Awaited<ReturnType<Facade.AnnotationQueuesClient["get"]>>, Types.GetAnnotationQueueResponse>>;
type AnnotationQueuesClient_update = Assert<Equal<Awaited<ReturnType<Facade.AnnotationQueuesClient["update"]>>, Types.UpdateAnnotationQueueResponse>>;
type AnnotationQueuesClient_archive = Assert<Equal<Awaited<ReturnType<Facade.AnnotationQueuesClient["archive"]>>, Envelope<{ deleted: boolean; archived: boolean; queue_id: string }>>>;
type AnnotationQueuesClient_updateStatus = Assert<Equal<Awaited<ReturnType<Facade.AnnotationQueuesClient["updateStatus"]>>, Types.UpdateAnnotationQueueStatusResponse>>;
type AnnotationQueuesClient_progress = Assert<Equal<Awaited<ReturnType<Facade.AnnotationQueuesClient["progress"]>>, Types.GetAnnotationQueueProgressResponse>>;
type AnnotationQueuesClient_analytics = Assert<Equal<Awaited<ReturnType<Facade.AnnotationQueuesClient["analytics"]>>, Types.GetAnnotationQueueAnalyticsResponse>>;
type AnnotationQueuesClient_agreement = Assert<Equal<Awaited<ReturnType<Facade.AnnotationQueuesClient["agreement"]>>, Types.GetAnnotationQueueAgreementResponse>>;
type AnnotationQueuesClient_exportJson = Assert<Equal<Awaited<ReturnType<Facade.AnnotationQueuesClient["exportJson"]>>, Types.ExportAnnotationQueueResponse>>;
type AnnotationQueuesClient_listExportFields = Assert<Equal<Awaited<ReturnType<Facade.AnnotationQueuesClient["listExportFields"]>>, Types.ListAnnotationQueueExportFieldsResponse>>;
type AnnotationQueuesClient_exportToDataset = Assert<Equal<Awaited<ReturnType<Facade.AnnotationQueuesClient["exportToDataset"]>>, Types.ExportAnnotationQueueToDatasetResponse>>;
type AnnotationQueuesClient_addLabel = Assert<Equal<Awaited<ReturnType<Facade.AnnotationQueuesClient["addLabel"]>>, Types.AddAnnotationQueueLabelResponse>>;
type AnnotationQueuesClient_removeLabel = Assert<Equal<Awaited<ReturnType<Facade.AnnotationQueuesClient["removeLabel"]>>, Types.RemoveAnnotationQueueLabelResponse>>;
type AnnotationQueueItemsClient_list = Assert<Equal<Awaited<ReturnType<Facade.AnnotationQueueItemsClient["list"]>>, DrfPage<Types.QueueItem>>>;
type AnnotationQueueItemsClient_add = Assert<Equal<Awaited<ReturnType<Facade.AnnotationQueueItemsClient["add"]>>, Types.AddAnnotationQueueItemsResponse>>;
type AnnotationQueueItemsClient_assign = Assert<Equal<Awaited<ReturnType<Facade.AnnotationQueueItemsClient["assign"]>>, Types.AssignAnnotationQueueItemsResponse>>;
type AnnotationQueueItemsClient_remove = Assert<Equal<Awaited<ReturnType<Facade.AnnotationQueueItemsClient["remove"]>>, Types.RemoveAnnotationQueueItemsResponse>>;
type AnnotationQueueItemsClient_next = Assert<Equal<Awaited<ReturnType<Facade.AnnotationQueueItemsClient["next"]>>, Types.GetNextAnnotationQueueItemResponse>>;
type AnnotationQueueItemsClient_getDetail = Assert<Equal<Awaited<ReturnType<Facade.AnnotationQueueItemsClient["getDetail"]>>, Types.GetAnnotationQueueItemDetailResponse>>;
type AnnotationQueueItemsClient_release = Assert<Equal<Awaited<ReturnType<Facade.AnnotationQueueItemsClient["release"]>>, Types.ReleaseAnnotationQueueItemResponse>>;
type AnnotationQueueItemsClient_complete = Assert<Equal<Awaited<ReturnType<Facade.AnnotationQueueItemsClient["complete"]>>, Types.CompleteAnnotationQueueItemResponse>>;
type AnnotationQueueItemsClient_skip = Assert<Equal<Awaited<ReturnType<Facade.AnnotationQueueItemsClient["skip"]>>, Types.SkipAnnotationQueueItemResponse>>;
type AnnotationQueueItemsClient_listAnnotations = Assert<Equal<Awaited<ReturnType<Facade.AnnotationQueueItemsClient["listAnnotations"]>>, Types.ListAnnotationQueueItemAnnotationsResponse>>;
type AnnotationQueueItemsClient_submitAnnotations = Assert<Equal<Awaited<ReturnType<Facade.AnnotationQueueItemsClient["submitAnnotations"]>>, Types.SubmitAnnotationQueueItemAnnotationsResponse>>;
type AnnotationQueueItemsClient_importAnnotations = Assert<Equal<Awaited<ReturnType<Facade.AnnotationQueueItemsClient["importAnnotations"]>>, Types.ImportAnnotationQueueItemAnnotationsResponse>>;
type AnnotationQueueDiscussionClient_list = Assert<Equal<Awaited<ReturnType<Facade.AnnotationQueueDiscussionClient["list"]>>, Types.ListAnnotationQueueItemDiscussionResponse>>;
type AnnotationQueueDiscussionClient_comment = Assert<Equal<Awaited<ReturnType<Facade.AnnotationQueueDiscussionClient["comment"]>>, Types.CreateAnnotationQueueItemCommentResponse>>;
type AnnotationQueueDiscussionClient_resolveThread = Assert<Equal<Awaited<ReturnType<Facade.AnnotationQueueDiscussionClient["resolveThread"]>>, Types.ResolveAnnotationQueueItemThreadResponse>>;
type AnnotationQueueDiscussionClient_reopenThread = Assert<Equal<Awaited<ReturnType<Facade.AnnotationQueueDiscussionClient["reopenThread"]>>, Types.ReopenAnnotationQueueItemThreadResponse>>;
type AnnotationQueueDiscussionClient_react = Assert<Equal<Awaited<ReturnType<Facade.AnnotationQueueDiscussionClient["react"]>>, Types.ToggleAnnotationQueueItemCommentReactionResponse>>;
type AnnotationQueueReviewClient_submit = Assert<Equal<Awaited<ReturnType<Facade.AnnotationQueueReviewClient["submit"]>>, Types.ReviewAnnotationQueueItemResponse>>;
type DatasetVersionsClient_list = Assert<Equal<Awaited<ReturnType<Facade.DatasetVersionsClient["list"]>>, Types.ListDatasetVersionsResponse>>;
type DatasetVersionsClient_get = Assert<Equal<Awaited<ReturnType<Facade.DatasetVersionsClient["get"]>>, Types.GetDatasetVersionResponse>>;
type DatasetVersionsClient_create = Assert<Equal<Awaited<ReturnType<Facade.DatasetVersionsClient["create"]>>, Types.CreateDatasetVersionResponse>>;
type DatasetsClient_list = Assert<Equal<Awaited<ReturnType<Facade.DatasetsClient["list"]>>, Types.ListDatasetsResponse>>;
type DatasetsClient_listNames = Assert<Equal<Awaited<ReturnType<Facade.DatasetsClient["listNames"]>>, Types.ListDatasetNamesResponse>>;
type DatasetsClient_getTable = Assert<Equal<Awaited<ReturnType<Facade.DatasetsClient["getTable"]>>, Types.GetDatasetTableResponse>>;
type DatasetsClient_getRow = Assert<Equal<Awaited<ReturnType<Facade.DatasetsClient["getRow"]>>, Types.GetDatasetRowResponse>>;
type DatasetsClient_getColumns = Assert<Equal<Awaited<ReturnType<Facade.DatasetsClient["getColumns"]>>, Types.GetDatasetColumnsResponse>>;
type DatasetsClient_createEmpty = Assert<Equal<Awaited<ReturnType<Facade.DatasetsClient["createEmpty"]>>, Types.CreateEmptyDatasetResponse>>;
type DatasetsClient_createManual = Assert<Equal<Awaited<ReturnType<Facade.DatasetsClient["createManual"]>>, Types.CreateDatasetManuallyResponse>>;
type DatasetsClient_createFromFile = Assert<Equal<Awaited<ReturnType<Facade.DatasetsClient["createFromFile"]>>, Types.CreateDatasetFromLocalFileResponse>>;
type DatasetsClient_addRows = Assert<Equal<Awaited<ReturnType<Facade.DatasetsClient["addRows"]>>, Types.AddDatasetRowsResponse>>;
type DatasetsClient_addColumns = Assert<Equal<Awaited<ReturnType<Facade.DatasetsClient["addColumns"]>>, Types.AddDatasetColumnsResponse>>;
type DatasetsClient_updateCell = Assert<Equal<Awaited<ReturnType<Facade.DatasetsClient["updateCell"]>>, Types.UpdateDatasetCellResponse>>;
type DatasetsClient_deleteRow = Assert<Equal<Awaited<ReturnType<Facade.DatasetsClient["deleteRow"]>>, Envelope<string>>>;
type DatasetsClient_deleteColumn = Assert<Equal<Awaited<ReturnType<Facade.DatasetsClient["deleteColumn"]>>, Envelope<string>>>;
type DatasetsClient_download = Assert<Equal<Awaited<ReturnType<Facade.DatasetsClient["download"]>>, Types.DownloadDatasetResponse>>;
type DatasetsClient_jsonSchema = Assert<Equal<Awaited<ReturnType<Facade.DatasetsClient["jsonSchema"]>>, Types.GetDatasetJsonSchemaResponse>>;
type DatasetsClient_evalStats = Assert<Equal<Awaited<ReturnType<Facade.DatasetsClient["evalStats"]>>, Types.GetDatasetEvalStatsResponse>>;
type DatasetsClient_annotationSummary = Assert<Equal<Awaited<ReturnType<Facade.DatasetsClient["annotationSummary"]>>, Types.GetDatasetAnnotationSummaryResponse>>;
type DatasetsClient_duplicate = Assert<Equal<Awaited<ReturnType<Facade.DatasetsClient["duplicate"]>>, Types.DuplicateDatasetResponse>>;
type DatasetsClient_derivedVariables = Assert<Equal<Awaited<ReturnType<Facade.DatasetsClient["derivedVariables"]>>, Types.ListDatasetDerivedVariablesResponse>>;
type DatasetsClient_baseColumns = Assert<Equal<Awaited<ReturnType<Facade.DatasetsClient["baseColumns"]>>, Types.ListDatasetBaseColumnsResponse>>;
type ExperimentRunsClient_create = Assert<Equal<Awaited<ReturnType<Facade.ExperimentRunsClient["create"]>>, Types.CreateExternalExperimentRunResponse>>;
type ExperimentRunsClient_ingestResults = Assert<Equal<Awaited<ReturnType<Facade.ExperimentRunsClient["ingestResults"]>>, Types.IngestExternalExperimentResultsResponse>>;
type ExperimentRunsClient_compare = Assert<Equal<Awaited<ReturnType<Facade.ExperimentRunsClient["compare"]>>, Types.CompareExperimentRunsResponse>>;
type ExperimentsClient_list = Assert<Equal<Awaited<ReturnType<Facade.ExperimentsClient["list"]>>, DrfPage<Types.ExperimentListV2>>>;
type ExperimentsClient_create = Assert<Equal<Awaited<ReturnType<Facade.ExperimentsClient["create"]>>, Types.CreateExperimentResponse>>;
type ExperimentsClient_get = Assert<Equal<Awaited<ReturnType<Facade.ExperimentsClient["get"]>>, Types.GetExperimentResponse>>;
type ExperimentsClient_update = Assert<Equal<Awaited<ReturnType<Facade.ExperimentsClient["update"]>>, Types.UpdateExperimentResponse>>;
type ExperimentsClient_delete = Assert<Equal<Awaited<ReturnType<Facade.ExperimentsClient["delete"]>>, Envelope<{ message: string; deleted_count: number }>>>;
type ExperimentsClient_rows = Assert<Equal<Awaited<ReturnType<Facade.ExperimentsClient["rows"]>>, Types.ListExperimentRowsResponse>>;
type ExperimentsClient_row = Assert<Equal<Awaited<ReturnType<Facade.ExperimentsClient["row"]>>, Types.GetExperimentRowResponse>>;
type ExperimentsClient_stats = Assert<Equal<Awaited<ReturnType<Facade.ExperimentsClient["stats"]>>, Types.GetExperimentStatsResponse>>;
type ExperimentsClient_download = Assert<Equal<Awaited<ReturnType<Facade.ExperimentsClient["download"]>>, Types.DownloadExperimentResponse>>;
type ExperimentsClient_rerun = Assert<Equal<Awaited<ReturnType<Facade.ExperimentsClient["rerun"]>>, Types.RerunExperimentResponse>>;
type ExperimentsClient_stop = Assert<Equal<Awaited<ReturnType<Facade.ExperimentsClient["stop"]>>, Types.StopExperimentResponse>>;
type ExperimentsClient_compare = Assert<Equal<Awaited<ReturnType<Facade.ExperimentsClient["compare"]>>, Types.CompareExperimentsResponse>>;
type ExperimentsClient_comparisons = Assert<Equal<Awaited<ReturnType<Facade.ExperimentsClient["comparisons"]>>, Types.ListExperimentComparisonsResponse>>;
type ExperimentsClient_jsonSchema = Assert<Equal<Awaited<ReturnType<Facade.ExperimentsClient["jsonSchema"]>>, Types.GetExperimentJsonSchemaResponse>>;
type EvalsClient_listTemplates = Assert<Equal<Awaited<ReturnType<Facade.EvalsClient["listTemplates"]>>, Types.ModelHubEvalTemplatesListCreateResponse>>;
type EvalsClient_createTemplate = Assert<Equal<Awaited<ReturnType<Facade.EvalsClient["createTemplate"]>>, Types.ModelHubEvalTemplatesCreateV2CreateResponse>>;
type EvalsClient_getTemplate = Assert<Equal<Awaited<ReturnType<Facade.EvalsClient["getTemplate"]>>, Types.ModelHubEvalTemplatesDetailListResponse>>;
type EvalsClient_updateTemplate = Assert<Equal<Awaited<ReturnType<Facade.EvalsClient["updateTemplate"]>>, Types.ModelHubEvalTemplatesUpdateUpdateResponse>>;
type EvalsClient_deleteTemplate = Assert<Equal<Awaited<ReturnType<Facade.EvalsClient["deleteTemplate"]>>, Types.ModelHubDeleteEvalTemplateCreateResponse>>;
type EvalsClient_bulkDeleteTemplates = Assert<Equal<Awaited<ReturnType<Facade.EvalsClient["bulkDeleteTemplates"]>>, Types.ModelHubEvalTemplatesBulkDeleteCreateResponse>>;
type EvalsClient_templateUsage = Assert<Equal<Awaited<ReturnType<Facade.EvalsClient["templateUsage"]>>, Types.ModelHubEvalTemplatesUsageListResponse>>;
type EvalsClient_templateVersions = Assert<Equal<Awaited<ReturnType<Facade.EvalsClient["templateVersions"]>>, Types.ModelHubEvalTemplatesVersionsListResponse>>;
type EvalsClient_createTemplateVersion = Assert<Equal<Awaited<ReturnType<Facade.EvalsClient["createTemplateVersion"]>>, Types.ModelHubEvalTemplatesVersionsCreateCreateResponse>>;
type EvalsClient_restoreTemplateVersion = Assert<Equal<Awaited<ReturnType<Facade.EvalsClient["restoreTemplateVersion"]>>, Types.ModelHubEvalTemplatesVersionsRestoreCreateResponse>>;
type EvalsClient_setDefaultTemplateVersion = Assert<Equal<Awaited<ReturnType<Facade.EvalsClient["setDefaultTemplateVersion"]>>, Types.ModelHubEvalTemplatesVersionsSetDefaultUpdateResponse>>;
type EvalsClient_listSdkEvals = Assert<Equal<Awaited<ReturnType<Facade.EvalsClient["listSdkEvals"]>>, Types.SdkApiV1GetEvalsListResponse>>;
type EvalsClient_configure = Assert<Equal<Awaited<ReturnType<Facade.EvalsClient["configure"]>>, Types.SdkApiV1ConfigureEvaluationsCreateResponse>>;
type EvalsClient_run = Assert<Equal<Awaited<ReturnType<Facade.EvalsClient["run"]>>, Types.SdkApiV1EvalCreateResponse>>;
type EvalsClient_getRun = Assert<Equal<Awaited<ReturnType<Facade.EvalsClient["getRun"]>>, Types.SdkApiV1EvalReadResponse>>;
type EvalsClient_runV2 = Assert<Equal<Awaited<ReturnType<Facade.EvalsClient["runV2"]>>, Types.SdkApiV1NewEvalCreateResponse>>;
type EvalsClient_getRunV2 = Assert<Equal<Awaited<ReturnType<Facade.EvalsClient["getRunV2"]>>, Types.SdkApiV1NewEvalListResponse>>;
type EvalsClient_listPipelines = Assert<Equal<Awaited<ReturnType<Facade.EvalsClient["listPipelines"]>>, Types.SdkApiV1EvaluatePipelineListResponse>>;
type EvalsClient_evaluatePipeline = Assert<Equal<Awaited<ReturnType<Facade.EvalsClient["evaluatePipeline"]>>, Types.SdkApiV1EvaluatePipelineCreateResponse>>;
type EvalsClient_datasetEvals = Assert<Equal<Awaited<ReturnType<Facade.EvalsClient["datasetEvals"]>>, Types.ModelHubDevelopsGetEvalsListListResponse>>;
type EvalsClient_datasetEvalStructure = Assert<Equal<Awaited<ReturnType<Facade.EvalsClient["datasetEvalStructure"]>>, Types.ModelHubDevelopsGetEvalStructureReadResponse>>;
type EvalsClient_previewDatasetEval = Assert<Equal<Awaited<ReturnType<Facade.EvalsClient["previewDatasetEval"]>>, Types.ModelHubDevelopsPreviewRunEvalCreateResponse>>;
type EvalsClient_startDatasetEvals = Assert<Equal<Awaited<ReturnType<Facade.EvalsClient["startDatasetEvals"]>>, Types.ModelHubDevelopsStartEvalsProcessCreateResponse>>;
type EvalsClient_addDatasetUserEval = Assert<Equal<Awaited<ReturnType<Facade.EvalsClient["addDatasetUserEval"]>>, Types.ModelHubDevelopsAddUserEvalCreateResponse>>;
type EvalsClient_editAndRunDatasetUserEval = Assert<Equal<Awaited<ReturnType<Facade.EvalsClient["editAndRunDatasetUserEval"]>>, Types.ModelHubDevelopsEditAndRunUserEvalCreateResponse>>;
type EvalsClient_stopDatasetUserEval = Assert<Equal<Awaited<ReturnType<Facade.EvalsClient["stopDatasetUserEval"]>>, Types.ModelHubDevelopsStopUserEvalCreateResponse>>;
type EvalsClient_deleteDatasetUserEval = Assert<Equal<Awaited<ReturnType<Facade.EvalsClient["deleteDatasetUserEval"]>>, Envelope<string>>>;
type EvalsClient_deleteDatasetTemplateEval = Assert<Equal<Awaited<ReturnType<Facade.EvalsClient["deleteDatasetTemplateEval"]>>, Envelope<string>>>;
type UsersClient_current = Assert<Equal<Awaited<ReturnType<Facade.UsersClient["current"]>>, Types.GetCurrentUserResponse>>;
type UsersClient_organizationMembers = Assert<Equal<Awaited<ReturnType<Facade.UsersClient["organizationMembers"]>>, Types.ListOrganizationMembersResponse>>;
type UsersClient_workspaces = Assert<Equal<Awaited<ReturnType<Facade.UsersClient["workspaces"]>>, Types.ListWorkspacesResponse>>;
type UsersClient_workspaceMembers = Assert<Equal<Awaited<ReturnType<Facade.UsersClient["workspaceMembers"]>>, Types.ListWorkspaceMembersResponse>>;
type UsersClient_switchWorkspace = Assert<Equal<Awaited<ReturnType<Facade.UsersClient["switchWorkspace"]>>, Types.SwitchWorkspaceResponse>>;
type AlertsClient_list = Assert<Equal<Awaited<ReturnType<Facade.AlertsClient["list"]>>, Envelope<MonitorPage<Types.UserAlertMonitor>>>>;
type AlertsClient_create = Assert<Equal<Awaited<ReturnType<Facade.AlertsClient["create"]>>, Envelope<string>>>;
type AlertsClient_get = Assert<Equal<Awaited<ReturnType<Facade.AlertsClient["get"]>>, Types.GetAlertResponse>>;
type AlertsClient_update = Assert<Equal<Awaited<ReturnType<Facade.AlertsClient["update"]>>, Envelope<Types.UserAlertMonitor>>>;
type AlertsClient_delete = Assert<Equal<Awaited<ReturnType<Facade.AlertsClient["delete"]>>, Types.DeleteAlertResponse>>;
type AlertsClient_metricOptions = Assert<Equal<Awaited<ReturnType<Facade.AlertsClient["metricOptions"]>>, Types.ListAlertMetricOptionsResponse>>;
type AlertsClient_previewGraph = Assert<Equal<Awaited<ReturnType<Facade.AlertsClient["previewGraph"]>>, Types.PreviewAlertGraphResponse>>;
type AlertsClient_graph = Assert<Equal<Awaited<ReturnType<Facade.AlertsClient["graph"]>>, Types.GetAlertGraphResponse>>;
type AlertsClient_details = Assert<Equal<Awaited<ReturnType<Facade.AlertsClient["details"]>>, Envelope<MonitorDetails>>>;
type AlertsClient_bulkMute = Assert<Equal<Awaited<ReturnType<Facade.AlertsClient["bulkMute"]>>, Envelope<{ message: string }>>>;
type AlertsClient_logs = Assert<Equal<Awaited<ReturnType<Facade.AlertsClient["logs"]>>, DrfPage<Types.UserAlertMonitorLog>>>;
type AlertsClient_allLogs = Assert<Equal<Awaited<ReturnType<Facade.AlertsClient["allLogs"]>>, Envelope<Types.UserAlertMonitorLog[]>>>;
type AlertsClient_log = Assert<Equal<Awaited<ReturnType<Facade.AlertsClient["log"]>>, Types.GetAlertLogResponse>>;
type AlertsClient_logsForAlert = Assert<Equal<Awaited<ReturnType<Facade.AlertsClient["logsForAlert"]>>, Envelope<Types.UserAlertMonitorLog[]>>>;
type AlertsClient_resolveLogs = Assert<Equal<Awaited<ReturnType<Facade.AlertsClient["resolveLogs"]>>, Types.ResolveAlertLogsResponse>>;

test("catalog response types are checked by tsc and ts-jest", () => {
  expect(121).toBeGreaterThan(100);
});
