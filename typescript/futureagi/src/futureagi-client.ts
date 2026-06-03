import { API_KEY_ENVVAR_NAME, SECRET_KEY_ENVVAR_NAME } from "./utils/constants";
import { createClient, type Client } from "./generated/openapi/client";
import * as generatedSdk from "./generated/openapi/sdk.gen";
import type * as generatedTypes from "./generated/openapi/types.gen";

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
    throw new Error(
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

const callGenerated = <TResult>(
  client: Client,
  operation: GeneratedOperation<TResult>,
  options: Record<string, unknown> = {},
) => operation(dataOptions(client, options));

export class FutureAGIClient {
  readonly annotationQueues: AnnotationQueuesClient;
  readonly datasets: DatasetsClient;
  readonly evals: EvalsClient;
  readonly experiments: ExperimentsClient;
  readonly simulations: SimulationsClient;
  readonly tracing: TracingClient;
  readonly users: UsersClient;
  readonly alerts: AlertsClient;
  readonly generated: typeof generatedSdk = generatedSdk;
  readonly generatedClient: Client;

  constructor(options: FutureAGIClientOptions = {}) {
    const { apiKey, secretKey } = requireAuth(options);
    const baseUrl =
      options.baseUrl ?? readEnv("FI_BASE_URL") ?? DEFAULT_BASE_URL;

    this.generatedClient = createClient({
      baseUrl,
      fetch: options.fetch,
      headers: {
        "X-Api-Key": apiKey,
        "X-Secret-Key": secretKey,
        ...options.headers,
      },
      responseStyle: "data",
      throwOnError: true,
    });
    this.annotationQueues = new AnnotationQueuesClient(this.generatedClient);
    this.datasets = new DatasetsClient(this.generatedClient);
    this.evals = new EvalsClient(this.generatedClient);
    this.experiments = new ExperimentsClient(this.generatedClient);
    this.simulations = new SimulationsClient(this.generatedClient);
    this.tracing = new TracingClient(this.generatedClient);
    this.users = new UsersClient(this.generatedClient);
    this.alerts = new AlertsClient(this.generatedClient);
  }
}

export class AnnotationQueuesClient {
  readonly items: AnnotationQueueItemsClient;
  readonly discussion: AnnotationQueueDiscussionClient;
  readonly review: AnnotationQueueReviewClient;

  constructor(private readonly client: Client) {
    this.items = new AnnotationQueueItemsClient(client);
    this.discussion = new AnnotationQueueDiscussionClient(client);
    this.review = new AnnotationQueueReviewClient(client);
  }

  list(query?: QueryOf<generatedTypes.ListAnnotationQueuesData>) {
    return generatedSdk.listAnnotationQueues(
      dataOptions(this.client, { query }),
    );
  }

  create(body: BodyOf<generatedTypes.CreateAnnotationQueueData>) {
    return generatedSdk.createAnnotationQueue(
      dataOptions(this.client, { body }),
    );
  }

  get(id: string) {
    return generatedSdk.getAnnotationQueue(
      dataOptions(this.client, { path: { id } }),
    );
  }

  update(id: string, body: BodyOf<generatedTypes.UpdateAnnotationQueueData>) {
    return generatedSdk.updateAnnotationQueue(
      dataOptions(this.client, { path: { id }, body }),
    );
  }

  archive(id: string) {
    return generatedSdk.archiveAnnotationQueue(
      dataOptions(this.client, { path: { id } }),
    );
  }

  updateStatus(
    id: string,
    body: BodyOf<generatedTypes.UpdateAnnotationQueueStatusData>,
  ) {
    return generatedSdk.updateAnnotationQueueStatus(
      dataOptions(this.client, { path: { id }, body }),
    );
  }

  progress(id: string) {
    return generatedSdk.getAnnotationQueueProgress(
      dataOptions(this.client, { path: { id } }),
    );
  }

  analytics(id: string) {
    return generatedSdk.getAnnotationQueueAnalytics(
      dataOptions(this.client, { path: { id } }),
    );
  }

  agreement(id: string) {
    return generatedSdk.getAnnotationQueueAgreement(
      dataOptions(this.client, { path: { id } }),
    );
  }

  exportJson(id: string) {
    return generatedSdk.exportAnnotationQueue(
      dataOptions(this.client, { path: { id } }),
    );
  }

  listExportFields(id: string) {
    return generatedSdk.listAnnotationQueueExportFields(
      dataOptions(this.client, { path: { id } }),
    );
  }

  exportToDataset(
    id: string,
    body: BodyOf<generatedTypes.ExportAnnotationQueueToDatasetData>,
  ) {
    return generatedSdk.exportAnnotationQueueToDataset(
      dataOptions(this.client, { path: { id }, body }),
    );
  }

  addLabel(
    id: string,
    body: BodyOf<generatedTypes.AddAnnotationQueueLabelData>,
  ) {
    return generatedSdk.addAnnotationQueueLabel(
      dataOptions(this.client, { path: { id }, body }),
    );
  }

  removeLabel(
    id: string,
    body: BodyOf<generatedTypes.RemoveAnnotationQueueLabelData>,
  ) {
    return generatedSdk.removeAnnotationQueueLabel(
      dataOptions(this.client, { path: { id }, body }),
    );
  }
}

export class AnnotationQueueItemsClient {
  constructor(private readonly client: Client) {}

  list(
    queueId: string,
    query?: QueryOf<generatedTypes.ListAnnotationQueueItemsData>,
  ) {
    return generatedSdk.listAnnotationQueueItems(
      dataOptions(this.client, { path: { queue_id: queueId }, query }),
    );
  }

  add(
    queueId: string,
    body: BodyOf<generatedTypes.AddAnnotationQueueItemsData>,
  ) {
    return generatedSdk.addAnnotationQueueItems(
      dataOptions(this.client, { path: { queue_id: queueId }, body }),
    );
  }

  assign(
    queueId: string,
    body: BodyOf<generatedTypes.AssignAnnotationQueueItemsData>,
  ) {
    return generatedSdk.assignAnnotationQueueItems(
      dataOptions(this.client, { path: { queue_id: queueId }, body }),
    );
  }

  remove(
    queueId: string,
    body: BodyOf<generatedTypes.RemoveAnnotationQueueItemsData>,
  ) {
    return generatedSdk.removeAnnotationQueueItems(
      dataOptions(this.client, { path: { queue_id: queueId }, body }),
    );
  }

  next(
    queueId: string,
    query?: QueryOf<generatedTypes.GetNextAnnotationQueueItemData>,
  ) {
    return generatedSdk.getNextAnnotationQueueItem(
      dataOptions(this.client, { path: { queue_id: queueId }, query }),
    );
  }

  getDetail(
    queueId: string,
    itemId: string,
    query?: QueryOf<generatedTypes.GetAnnotationQueueItemDetailData>,
  ) {
    return generatedSdk.getAnnotationQueueItemDetail(
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
    return generatedSdk.releaseAnnotationQueueItem(
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
    return generatedSdk.completeAnnotationQueueItem(
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
    return generatedSdk.skipAnnotationQueueItem(
      dataOptions(this.client, {
        path: { queue_id: queueId, id: itemId },
        body,
      }),
    );
  }

  listAnnotations(queueId: string, itemId: string) {
    return generatedSdk.listAnnotationQueueItemAnnotations(
      dataOptions(this.client, { path: { queue_id: queueId, id: itemId } }),
    );
  }

  submitAnnotations(
    queueId: string,
    itemId: string,
    body: BodyOf<generatedTypes.SubmitAnnotationQueueItemAnnotationsData>,
  ) {
    return generatedSdk.submitAnnotationQueueItemAnnotations(
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
    return generatedSdk.importAnnotationQueueItemAnnotations(
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
    return generatedSdk.listAnnotationQueueItemDiscussion(
      dataOptions(this.client, { path: { queue_id: queueId, id: itemId } }),
    );
  }

  comment(
    queueId: string,
    itemId: string,
    body: BodyOf<generatedTypes.CreateAnnotationQueueItemCommentData>,
  ) {
    return generatedSdk.createAnnotationQueueItemComment(
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
    return generatedSdk.resolveAnnotationQueueItemThread(
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
    return generatedSdk.reopenAnnotationQueueItemThread(
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
    return generatedSdk.toggleAnnotationQueueItemCommentReaction(
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
    return generatedSdk.reviewAnnotationQueueItem(
      dataOptions(this.client, {
        path: { queue_id: queueId, id: itemId },
        body,
      }),
    );
  }
}

export class DatasetsClient {
  constructor(private readonly client: Client) {}

  list(query?: LooseQuery) {
    return callGenerated(this.client, generatedSdk.listDatasets, { query });
  }

  listNames(query?: LooseQuery) {
    return callGenerated(this.client, generatedSdk.listDatasetNames, { query });
  }

  getTable(datasetId: string, query?: LooseQuery) {
    return callGenerated(this.client, generatedSdk.getDatasetTable, {
      path: { dataset_id: datasetId },
      query,
    });
  }

  getRow(datasetId: string, body: LooseBody) {
    return callGenerated(this.client, generatedSdk.getDatasetRow, {
      path: { dataset_id: datasetId },
      body,
    });
  }

  getColumns(datasetId: string) {
    return callGenerated(this.client, generatedSdk.getDatasetColumns, {
      path: { dataset_id: datasetId },
    });
  }

  createEmpty(body: LooseBody) {
    return callGenerated(this.client, generatedSdk.createEmptyDataset, {
      body,
    });
  }

  createManual(body: LooseBody) {
    return callGenerated(this.client, generatedSdk.createDatasetManually, {
      body,
    });
  }

  createFromFile(body: LooseBody) {
    return callGenerated(this.client, generatedSdk.createDatasetFromLocalFile, {
      body,
    });
  }

  addRows(datasetId: string, body: LooseBody) {
    return callGenerated(this.client, generatedSdk.addDatasetRows, {
      path: { dataset_id: datasetId },
      body,
    });
  }

  addColumns(datasetId: string, body: LooseBody) {
    return callGenerated(this.client, generatedSdk.addDatasetColumns, {
      path: { dataset_id: datasetId },
      body,
    });
  }

  updateCell(datasetId: string, body: LooseBody) {
    return callGenerated(this.client, generatedSdk.updateDatasetCell, {
      path: { dataset_id: datasetId },
      body,
    });
  }

  deleteRow(datasetId: string, query?: LooseQuery) {
    return callGenerated(this.client, generatedSdk.deleteDatasetRow, {
      path: { dataset_id: datasetId },
      query,
    });
  }

  deleteColumn(datasetId: string, columnId: string) {
    return callGenerated(this.client, generatedSdk.deleteDatasetColumn, {
      path: { dataset_id: datasetId, column_id: columnId },
    });
  }

  download(datasetId: string, query?: LooseQuery) {
    return callGenerated(this.client, generatedSdk.downloadDataset, {
      path: { dataset_id: datasetId },
      query,
    });
  }

  jsonSchema(datasetId: string) {
    return callGenerated(this.client, generatedSdk.getDatasetJsonSchema, {
      path: { dataset_id: datasetId },
    });
  }

  evalStats(datasetId: string, query?: LooseQuery) {
    return callGenerated(this.client, generatedSdk.getDatasetEvalStats, {
      path: { dataset_id: datasetId },
      query,
    });
  }

  annotationSummary(datasetId: string, query?: LooseQuery) {
    return callGenerated(
      this.client,
      generatedSdk.getDatasetAnnotationSummary,
      {
        path: { dataset_id: datasetId },
        query,
      },
    );
  }

  duplicate(datasetId: string, body?: LooseBody) {
    return callGenerated(this.client, generatedSdk.duplicateDataset, {
      path: { dataset_id: datasetId },
      body,
    });
  }

  derivedVariables(datasetId: string) {
    return callGenerated(
      this.client,
      generatedSdk.listDatasetDerivedVariables,
      {
        path: { dataset_id: datasetId },
      },
    );
  }

  baseColumns(query?: LooseQuery) {
    return callGenerated(this.client, generatedSdk.listDatasetBaseColumns, {
      query,
    });
  }
}

export class ExperimentsClient {
  constructor(private readonly client: Client) {}

  list(query?: LooseQuery) {
    return callGenerated(this.client, generatedSdk.listExperiments, { query });
  }

  create(body: LooseBody) {
    return callGenerated(this.client, generatedSdk.createExperiment, { body });
  }

  get(experimentId: string, query?: LooseQuery) {
    return callGenerated(this.client, generatedSdk.getExperiment, {
      path: { experiment_id: experimentId },
      query,
    });
  }

  update(experimentId: string, body: LooseBody) {
    return callGenerated(this.client, generatedSdk.updateExperiment, {
      path: { experiment_id: experimentId },
      body,
    });
  }

  delete(body: LooseBody) {
    return callGenerated(this.client, generatedSdk.deleteExperiments, { body });
  }

  rows(experimentId: string, query?: LooseQuery) {
    return callGenerated(this.client, generatedSdk.listExperimentRows, {
      path: { experiment_id: experimentId },
      query,
    });
  }

  row(experimentId: string, rowId: string, query?: LooseQuery) {
    return callGenerated(this.client, generatedSdk.getExperimentRow, {
      path: { experiment_id: experimentId, row_id: rowId },
      query,
    });
  }

  stats(experimentId: string, query?: LooseQuery) {
    return callGenerated(this.client, generatedSdk.getExperimentStats, {
      path: { experiment_id: experimentId },
      query,
    });
  }

  download(experimentId: string, query?: LooseQuery) {
    return callGenerated(this.client, generatedSdk.downloadExperiment, {
      path: { experiment_id: experimentId },
      query,
    });
  }

  rerun(body: LooseBody) {
    return callGenerated(this.client, generatedSdk.rerunExperiment, { body });
  }

  stop(experimentId: string, body?: LooseBody) {
    return callGenerated(this.client, generatedSdk.stopExperiment, {
      path: { experiment_id: experimentId },
      body,
    });
  }

  compare(experimentId: string, body: LooseBody) {
    return callGenerated(this.client, generatedSdk.compareExperiments, {
      path: { experiment_id: experimentId },
      body,
    });
  }

  comparisons(experimentId: string, query?: LooseQuery) {
    return callGenerated(this.client, generatedSdk.listExperimentComparisons, {
      path: { experiment_id: experimentId },
      query,
    });
  }

  jsonSchema(experimentId: string) {
    return callGenerated(this.client, generatedSdk.getExperimentJsonSchema, {
      path: { experiment_id: experimentId },
    });
  }
}

export class EvalsClient {
  constructor(private readonly client: Client) {}

  listTemplates(
    body: BodyOf<generatedTypes.ModelHubEvalTemplatesListCreateData>,
  ) {
    return generatedSdk.modelHubEvalTemplatesListCreate(
      dataOptions(this.client, { body }),
    );
  }

  createTemplate(
    body: BodyOf<generatedTypes.ModelHubEvalTemplatesCreateV2CreateData>,
  ) {
    return generatedSdk.modelHubEvalTemplatesCreateV2Create(
      dataOptions(this.client, { body }),
    );
  }

  getTemplate(templateId: string) {
    return generatedSdk.modelHubEvalTemplatesDetailList(
      dataOptions(this.client, { path: { template_id: templateId } }),
    );
  }

  updateTemplate(
    templateId: string,
    body: BodyOf<generatedTypes.ModelHubEvalTemplatesUpdateUpdateData>,
  ) {
    return generatedSdk.modelHubEvalTemplatesUpdateUpdate(
      dataOptions(this.client, { path: { template_id: templateId }, body }),
    );
  }

  deleteTemplate(
    body: BodyOf<generatedTypes.ModelHubDeleteEvalTemplateCreateData>,
  ) {
    return generatedSdk.modelHubDeleteEvalTemplateCreate(
      dataOptions(this.client, { body }),
    );
  }

  bulkDeleteTemplates(
    body: BodyOf<generatedTypes.ModelHubEvalTemplatesBulkDeleteCreateData>,
  ) {
    return generatedSdk.modelHubEvalTemplatesBulkDeleteCreate(
      dataOptions(this.client, { body }),
    );
  }

  templateUsage(templateId: string) {
    return generatedSdk.modelHubEvalTemplatesUsageList(
      dataOptions(this.client, { path: { template_id: templateId } }),
    );
  }

  templateVersions(templateId: string) {
    return generatedSdk.modelHubEvalTemplatesVersionsList(
      dataOptions(this.client, { path: { template_id: templateId } }),
    );
  }

  createTemplateVersion(
    templateId: string,
    body: BodyOf<generatedTypes.ModelHubEvalTemplatesVersionsCreateCreateData>,
  ) {
    return generatedSdk.modelHubEvalTemplatesVersionsCreateCreate(
      dataOptions(this.client, { path: { template_id: templateId }, body }),
    );
  }

  restoreTemplateVersion(
    templateId: string,
    versionId: string,
    body: BodyOf<generatedTypes.ModelHubEvalTemplatesVersionsRestoreCreateData> = {},
  ) {
    return generatedSdk.modelHubEvalTemplatesVersionsRestoreCreate(
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
    return generatedSdk.modelHubEvalTemplatesVersionsSetDefaultUpdate(
      dataOptions(this.client, {
        path: { template_id: templateId, version_id: versionId },
        body,
      }),
    );
  }

  listSdkEvals() {
    return generatedSdk.sdkApiV1GetEvalsList(dataOptions(this.client, {}));
  }

  configure(
    body: BodyOf<generatedTypes.SdkApiV1ConfigureEvaluationsCreateData>,
  ) {
    return generatedSdk.sdkApiV1ConfigureEvaluationsCreate(
      dataOptions(this.client, { body }),
    );
  }

  run(body: BodyOf<generatedTypes.SdkApiV1EvalCreateData>) {
    return generatedSdk.sdkApiV1EvalCreate(dataOptions(this.client, { body }));
  }

  getRun(evalId: string) {
    return generatedSdk.sdkApiV1EvalRead(
      dataOptions(this.client, { path: { eval_id: evalId } }),
    );
  }

  runV2(body: BodyOf<generatedTypes.SdkApiV1NewEvalCreateData>) {
    return generatedSdk.sdkApiV1NewEvalCreate(
      dataOptions(this.client, { body }),
    );
  }

  getRunV2(evalId: string) {
    return generatedSdk.sdkApiV1NewEvalList(
      dataOptions(this.client, { query: { eval_id: evalId } }),
    );
  }

  listPipelines(
    query: QueryOf<generatedTypes.SdkApiV1EvaluatePipelineListData>,
  ) {
    return generatedSdk.sdkApiV1EvaluatePipelineList(
      dataOptions(this.client, { query }),
    );
  }

  evaluatePipeline(
    body: BodyOf<generatedTypes.SdkApiV1EvaluatePipelineCreateData>,
  ) {
    return generatedSdk.sdkApiV1EvaluatePipelineCreate(
      dataOptions(this.client, { body }),
    );
  }

  datasetEvals(datasetId: string) {
    return generatedSdk.modelHubDevelopsGetEvalsListList(
      dataOptions(this.client, { path: { dataset_id: datasetId } }),
    );
  }

  datasetEvalStructure(
    datasetId: string,
    evalId: string,
    query: QueryOf<generatedTypes.ModelHubDevelopsGetEvalStructureReadData>,
  ) {
    return generatedSdk.modelHubDevelopsGetEvalStructureRead(
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
    return generatedSdk.modelHubDevelopsPreviewRunEvalCreate(
      dataOptions(this.client, { path: { dataset_id: datasetId }, body }),
    );
  }

  startDatasetEvals(
    datasetId: string,
    body: BodyOf<generatedTypes.ModelHubDevelopsStartEvalsProcessCreateData>,
  ) {
    return generatedSdk.modelHubDevelopsStartEvalsProcessCreate(
      dataOptions(this.client, { path: { dataset_id: datasetId }, body }),
    );
  }

  addDatasetUserEval(
    datasetId: string,
    body: BodyOf<generatedTypes.ModelHubDevelopsAddUserEvalCreateData>,
  ) {
    return generatedSdk.modelHubDevelopsAddUserEvalCreate(
      dataOptions(this.client, { path: { dataset_id: datasetId }, body }),
    );
  }

  editAndRunDatasetUserEval(
    datasetId: string,
    evalId: string,
    body: BodyOf<generatedTypes.ModelHubDevelopsEditAndRunUserEvalCreateData>,
  ) {
    return generatedSdk.modelHubDevelopsEditAndRunUserEvalCreate(
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
    return generatedSdk.modelHubDevelopsStopUserEvalCreate(
      dataOptions(this.client, {
        path: { dataset_id: datasetId, eval_id: evalId },
        body,
      }),
    );
  }

  deleteDatasetUserEval(datasetId: string, evalId: string) {
    return generatedSdk.modelHubDevelopsDeleteUserEvalDelete(
      dataOptions(this.client, {
        path: { dataset_id: datasetId, eval_id: evalId },
      }),
    );
  }

  deleteDatasetTemplateEval(datasetId: string, evalId: string) {
    return generatedSdk.modelHubDevelopsDeleteTemplateEvalDelete(
      dataOptions(this.client, {
        path: { dataset_id: datasetId, eval_id: evalId },
      }),
    );
  }
}

export class SimulationsClient {
  readonly agentDefinitions: SimulationAgentDefinitionsClient;
  readonly runTests: SimulationRunTestsClient;
  readonly testExecutions: SimulationTestExecutionsClient;
  readonly personas: SimulationPersonasClient;
  readonly scenarios: SimulationScenariosClient;

  constructor(private readonly client: Client) {
    this.agentDefinitions = new SimulationAgentDefinitionsClient(client);
    this.runTests = new SimulationRunTestsClient(client);
    this.testExecutions = new SimulationTestExecutionsClient(client);
    this.personas = new SimulationPersonasClient(client);
    this.scenarios = new SimulationScenariosClient(client);
  }

  runs(query?: LooseQuery) {
    return callGenerated(this.client, generatedSdk.listSimulationRuns, {
      query,
    });
  }

  metrics(query?: LooseQuery) {
    return callGenerated(this.client, generatedSdk.listSimulationMetrics, {
      query,
    });
  }

  analytics(query?: LooseQuery) {
    return callGenerated(this.client, generatedSdk.getSimulationAnalytics, {
      query,
    });
  }
}

export class SimulationAgentDefinitionsClient {
  constructor(private readonly client: Client) {}

  list(query?: LooseQuery) {
    return callGenerated(this.client, generatedSdk.listAgentDefinitions, {
      query,
    });
  }

  create(body: LooseBody) {
    return callGenerated(this.client, generatedSdk.createAgentDefinition, {
      body,
    });
  }

  get(agentId: string) {
    return callGenerated(this.client, generatedSdk.getAgentDefinition, {
      path: { agent_id: agentId },
    });
  }

  update(agentId: string, body: LooseBody) {
    return callGenerated(this.client, generatedSdk.updateAgentDefinition, {
      path: { agent_id: agentId },
      body,
    });
  }

  delete(agentId: string) {
    return callGenerated(this.client, generatedSdk.deleteAgentDefinition, {
      path: { agent_id: agentId },
    });
  }
}

export class SimulationRunTestsClient {
  constructor(private readonly client: Client) {}

  active() {
    return callGenerated(this.client, generatedSdk.simulateRunTestsActiveList);
  }

  list(query?: LooseQuery) {
    return callGenerated(this.client, generatedSdk.listRunTests, { query });
  }

  create(body: LooseBody) {
    return callGenerated(this.client, generatedSdk.createRunTest, { body });
  }

  get(runTestId: string) {
    return callGenerated(this.client, generatedSdk.getRunTest, {
      path: { run_test_id: runTestId },
    });
  }

  update(runTestId: string, body: LooseBody) {
    return callGenerated(this.client, generatedSdk.updateRunTest, {
      path: { run_test_id: runTestId },
      body,
    });
  }

  delete(runTestId: string) {
    return callGenerated(this.client, generatedSdk.deleteRunTest, {
      path: { run_test_id: runTestId },
    });
  }

  execute(runTestId: string, body?: LooseBody) {
    return callGenerated(this.client, generatedSdk.executeRunTest, {
      path: { run_test_id: runTestId },
      body,
    });
  }

  status(runTestId: string) {
    return callGenerated(this.client, generatedSdk.getRunTestStatus, {
      path: { run_test_id: runTestId },
    });
  }

  analytics(runTestId: string, query?: LooseQuery) {
    return callGenerated(this.client, generatedSdk.getRunTestAnalytics, {
      path: { run_test_id: runTestId },
      query,
    });
  }

  executions(runTestId: string, query?: LooseQuery) {
    return callGenerated(this.client, generatedSdk.listRunTestExecutions, {
      path: { run_test_id: runTestId },
      query,
    });
  }

  callExecutions(runTestId: string, query?: LooseQuery) {
    return callGenerated(this.client, generatedSdk.listRunTestCallExecutions, {
      path: { run_test_id: runTestId },
      query,
    });
  }

  addEvalConfigs(
    runTestId: string,
    body: BodyOf<generatedTypes.SimulateRunTestsEvalConfigsCreateData>,
  ) {
    return generatedSdk.simulateRunTestsEvalConfigsCreate(
      dataOptions(this.client, { path: { run_test_id: runTestId }, body }),
    );
  }

  deleteEvalConfig(runTestId: string, evalConfigId: string) {
    return generatedSdk.simulateRunTestsEvalConfigsDelete(
      dataOptions(this.client, {
        path: { run_test_id: runTestId, eval_config_id: evalConfigId },
      }),
    );
  }

  evalConfigStructure(runTestId: string, evalConfigId: string) {
    return generatedSdk.simulateRunTestsEvalConfigsGetStructureList(
      dataOptions(this.client, {
        path: { run_test_id: runTestId, eval_config_id: evalConfigId },
      }),
    );
  }

  updateEvalConfig(
    runTestId: string,
    evalConfigId: string,
    body: BodyOf<generatedTypes.SimulateRunTestsEvalConfigsUpdateCreateData>,
  ) {
    return generatedSdk.simulateRunTestsEvalConfigsUpdateCreate(
      dataOptions(this.client, {
        path: { run_test_id: runTestId, eval_config_id: evalConfigId },
        body,
      }),
    );
  }

  evalSummary(runTestId: string, query?: LooseQuery) {
    return callGenerated(
      this.client,
      generatedSdk.simulateRunTestsEvalSummaryList,
      {
        path: { run_test_id: runTestId },
        query,
      },
    );
  }

  evalSummaryComparison(runTestId: string, query?: LooseQuery) {
    return callGenerated(
      this.client,
      generatedSdk.simulateRunTestsEvalSummaryComparisonList,
      {
        path: { run_test_id: runTestId },
        query,
      },
    );
  }

  runNewEvals(
    runTestId: string,
    body: BodyOf<generatedTypes.SimulateRunTestsRunNewEvalsCreateData>,
  ) {
    return generatedSdk.simulateRunTestsRunNewEvalsCreate(
      dataOptions(this.client, { path: { run_test_id: runTestId }, body }),
    );
  }

  scenarios(runTestId: string, query?: LooseQuery) {
    return callGenerated(
      this.client,
      generatedSdk.simulateRunTestsScenariosList,
      {
        path: { run_test_id: runTestId },
        query,
      },
    );
  }

  sdkCode(runTestId: string, query?: LooseQuery) {
    return callGenerated(
      this.client,
      generatedSdk.simulateRunTestsSdkCodeList,
      {
        path: { run_test_id: runTestId },
        query,
      },
    );
  }
}

export class SimulationTestExecutionsClient {
  constructor(private readonly client: Client) {}

  list(query?: LooseQuery) {
    return callGenerated(this.client, generatedSdk.listTestExecutions, {
      query,
    });
  }

  get(testExecutionId: string) {
    return callGenerated(this.client, generatedSdk.getTestExecution, {
      path: { test_execution_id: testExecutionId },
    });
  }

  analytics(testExecutionId: string, query?: LooseQuery) {
    return callGenerated(this.client, generatedSdk.getTestExecutionAnalytics, {
      path: { test_execution_id: testExecutionId },
      query,
    });
  }

  transcripts(testExecutionId: string, query?: LooseQuery) {
    return callGenerated(
      this.client,
      generatedSdk.getTestExecutionTranscripts,
      {
        path: { test_execution_id: testExecutionId },
        query,
      },
    );
  }

  kpis(testExecutionId: string, query?: LooseQuery) {
    return callGenerated(this.client, generatedSdk.getTestExecutionKpis, {
      path: { test_execution_id: testExecutionId },
      query,
    });
  }

  performanceSummary(testExecutionId: string, query?: LooseQuery) {
    return callGenerated(
      this.client,
      generatedSdk.getTestExecutionPerformanceSummary,
      {
        path: { test_execution_id: testExecutionId },
        query,
      },
    );
  }

  cancel(testExecutionId: string, body?: LooseBody) {
    return callGenerated(this.client, generatedSdk.cancelTestExecution, {
      path: { test_execution_id: testExecutionId },
      body,
    });
  }
}

export class SimulationPersonasClient {
  constructor(private readonly client: Client) {}

  list(query?: LooseQuery) {
    return callGenerated(this.client, generatedSdk.listPersonas, { query });
  }

  create(body: LooseBody) {
    return callGenerated(this.client, generatedSdk.createPersona, { body });
  }

  get(id: string) {
    return callGenerated(this.client, generatedSdk.getPersona, {
      path: { id },
    });
  }

  update(id: string, body: LooseBody) {
    return callGenerated(this.client, generatedSdk.updatePersona, {
      path: { id },
      body,
    });
  }

  delete(id: string) {
    return callGenerated(this.client, generatedSdk.deletePersona, {
      path: { id },
    });
  }
}

export class SimulationScenariosClient {
  constructor(private readonly client: Client) {}

  list(query?: LooseQuery) {
    return callGenerated(this.client, generatedSdk.listScenarios, { query });
  }

  create(body: LooseBody) {
    return callGenerated(this.client, generatedSdk.createScenario, { body });
  }

  get(scenarioId: string) {
    return callGenerated(this.client, generatedSdk.getScenario, {
      path: { scenario_id: scenarioId },
    });
  }

  update(scenarioId: string, body: LooseBody) {
    return callGenerated(this.client, generatedSdk.updateScenario, {
      path: { scenario_id: scenarioId },
      body,
    });
  }

  delete(scenarioId: string) {
    return callGenerated(this.client, generatedSdk.deleteScenario, {
      path: { scenario_id: scenarioId },
    });
  }
}

export class TracingClient {
  constructor(private readonly client: Client) {}

  projects(query?: LooseQuery) {
    return callGenerated(this.client, generatedSdk.listTraceProjects, {
      query,
    });
  }

  traces(query?: LooseQuery) {
    return callGenerated(this.client, generatedSdk.listTraces, { query });
  }

  getTrace(id: string) {
    return callGenerated(this.client, generatedSdk.getTrace, {
      path: { id },
    });
  }

  voiceCalls(query?: LooseQuery) {
    return callGenerated(this.client, generatedSdk.listVoiceCalls, { query });
  }

  voiceCallDetail(query?: LooseQuery) {
    return callGenerated(this.client, generatedSdk.getVoiceCallDetail, {
      query,
    });
  }

  properties(query?: LooseQuery) {
    return callGenerated(this.client, generatedSdk.listTraceProperties, {
      query,
    });
  }

  updateTags(id: string, body: LooseBody) {
    return callGenerated(this.client, generatedSdk.updateTraceTags, {
      path: { id },
      body,
    });
  }

  graphMethods(body: LooseBody) {
    return callGenerated(this.client, generatedSdk.getTraceGraphMethods, {
      body,
    });
  }

  sessions(query?: LooseQuery) {
    return callGenerated(this.client, generatedSdk.listTraceSessions, {
      query,
    });
  }

  getSession(id: string) {
    return callGenerated(this.client, generatedSdk.getTraceSession, {
      path: { id },
    });
  }

  sessionGraph(body: LooseBody) {
    return callGenerated(this.client, generatedSdk.getTraceSessionGraphData, {
      body,
    });
  }

  users(query?: LooseQuery) {
    return callGenerated(this.client, generatedSdk.listTraceUsers, { query });
  }

  annotationLabels(query?: LooseQuery) {
    return callGenerated(this.client, generatedSdk.listTraceAnnotationLabels, {
      query,
    });
  }

  bulkAnnotation(body: LooseBody) {
    return callGenerated(this.client, generatedSdk.createBulkTraceAnnotation, {
      body,
    });
  }

  issues(query?: LooseQuery) {
    return callGenerated(this.client, generatedSdk.listErrorFeedIssues, {
      query,
    });
  }

  issue(clusterId: string) {
    return callGenerated(this.client, generatedSdk.getErrorFeedIssue, {
      path: { cluster_id: clusterId },
    });
  }

  issueStats(query?: LooseQuery) {
    return callGenerated(this.client, generatedSdk.getErrorFeedIssueStats, {
      query,
    });
  }
}

export class UsersClient {
  constructor(private readonly client: Client) {}

  current() {
    return callGenerated(this.client, generatedSdk.getCurrentUser);
  }

  organizationMembers(query?: LooseQuery) {
    return callGenerated(this.client, generatedSdk.listOrganizationMembers, {
      query,
    });
  }

  workspaces(query?: LooseQuery) {
    return callGenerated(this.client, generatedSdk.listWorkspaces, { query });
  }

  workspaceMembers(workspaceId: string, query?: LooseQuery) {
    return callGenerated(this.client, generatedSdk.listWorkspaceMembers, {
      path: { workspace_id: workspaceId },
      query,
    });
  }

  switchWorkspace(body: LooseBody) {
    return callGenerated(this.client, generatedSdk.switchWorkspace, { body });
  }
}

export class AlertsClient {
  constructor(private readonly client: Client) {}

  list(query?: LooseQuery) {
    return callGenerated(this.client, generatedSdk.listAlerts, { query });
  }

  create(body: LooseBody) {
    return callGenerated(this.client, generatedSdk.createAlert, { body });
  }

  get(id: string) {
    return callGenerated(this.client, generatedSdk.getAlert, {
      path: { id },
    });
  }

  update(id: string, body: LooseBody) {
    return callGenerated(this.client, generatedSdk.updateAlert, {
      path: { id },
      body,
    });
  }

  delete(id: string) {
    return callGenerated(this.client, generatedSdk.deleteAlert, {
      path: { id },
    });
  }

  metricOptions(query?: LooseQuery) {
    return callGenerated(this.client, generatedSdk.listAlertMetricOptions, {
      query,
    });
  }

  previewGraph(body: LooseBody) {
    return callGenerated(this.client, generatedSdk.previewAlertGraph, { body });
  }

  graph(id: string, query?: LooseQuery) {
    return callGenerated(this.client, generatedSdk.getAlertGraph, {
      path: { id },
      query,
    });
  }

  details(id: string) {
    return callGenerated(this.client, generatedSdk.getAlertDetails, {
      path: { id },
    });
  }

  bulkMute(body: LooseBody) {
    return callGenerated(this.client, generatedSdk.bulkMuteAlerts, { body });
  }

  logs(query?: LooseQuery) {
    return callGenerated(this.client, generatedSdk.listAlertLogs, { query });
  }

  allLogs(query?: LooseQuery) {
    return callGenerated(this.client, generatedSdk.listAllAlertLogs, { query });
  }

  log(id: string) {
    return callGenerated(this.client, generatedSdk.getAlertLog, {
      path: { id },
    });
  }

  logsForAlert(id: string, query?: LooseQuery) {
    return callGenerated(this.client, generatedSdk.listAlertLogsForAlert, {
      path: { id },
      query,
    });
  }

  resolveLogs(body: LooseBody) {
    return callGenerated(this.client, generatedSdk.resolveAlertLogs, { body });
  }
}

export { generatedSdk as futureAGIGeneratedSdk };
