import http from "node:http";
import { URL } from "node:url";
import {
  Annotation,
  AnnotationQueue,
  APIKeyAuth,
  DataTypeChoices,
  Dataset,
  FutureAGIClient,
  HttpMethod,
  KnowledgeBase,
  ModelConfig,
  ModelProvider,
  ModelTypes,
  Prompt,
  PromptTemplate,
  ProviderAPIKeyClient,
  UserMessage,
} from "../../src";
import type { RequestConfig } from "../../src";

type JsonRecord = Record<string, any>;

interface AdapterState {
  apiKey?: string;
  secretKey?: string;
  baseUrl?: string;
  timeout?: number;
  calls: JsonRecord[];
}

const state: AdapterState = { calls: [] };

const capabilities = [
  "auth_api_key",
  "raw_request",
  "annotation_bulk_log",
  "annotation_metadata_lifecycle",
  "annotation_queue_lifecycle",
  "annotation_queue_management_lifecycle",
  "annotation_score_lifecycle",
  "dataset_lifecycle",
  "dataset_management_lifecycle",
  "knowledge_base_lifecycle",
  "prompt_lifecycle",
  "provider_api_key_lifecycle",
  "futureagi_client_basic",
  "evals_lifecycle",
  "simulation_lifecycle",
  "tracing_lifecycle",
];

const server = http.createServer(async (req, res) => {
  const url = new URL(req.url ?? "/", "http://127.0.0.1");
  try {
    if (req.method === "GET" && url.pathname === "/health") {
      writeJson(res, 200, {
        sdk_name: "futureagi-sdk-typescript",
        sdk_version: process.env.npm_package_version ?? "0.1.2",
        adapter_version: "0.1.0",
        language: "typescript",
        capabilities,
      });
      return;
    }

    if (req.method === "GET" && url.pathname === "/state") {
      writeJson(res, 200, {
        initialized: state.baseUrl != null,
        base_url: state.baseUrl,
        calls: state.calls,
      });
      return;
    }

    const payload = await readJson(req);

    if (req.method === "POST" && url.pathname === "/reset") {
      state.apiKey = undefined;
      state.secretKey = undefined;
      state.baseUrl = undefined;
      state.timeout = undefined;
      state.calls = [];
      writeJson(res, 200, { success: true });
      return;
    }

    if (req.method === "POST" && url.pathname === "/init") {
      state.apiKey = required(payload, "api_key");
      state.secretKey = required(payload, "secret_key");
      state.baseUrl = String(required(payload, "base_url")).replace(/\/$/, "");
      state.timeout = Number(payload.timeout ?? 30);
      state.calls.push({ operation: "init", base_url: state.baseUrl });
      writeJson(res, 200, { success: true });
      return;
    }

    const handlers: Record<
      string,
      (payload: JsonRecord) => Promise<JsonRecord>
    > = {
      "/raw-request": handleRawRequest,
      "/futureagi/basic": handleFutureagiBasic,
      "/evals/lifecycle": handleEvalsLifecycle,
      "/simulation/lifecycle": handleSimulationLifecycle,
      "/tracing/lifecycle": handleTracingLifecycle,
      "/annotation/log": handleAnnotationLog,
      "/annotation/metadata": handleAnnotationMetadata,
      "/annotation-queue/lifecycle": handleAnnotationQueueLifecycle,
      "/annotation-queue/management": handleAnnotationQueueManagement,
      "/annotation-score/lifecycle": handleAnnotationScoreLifecycle,
      "/dataset/lifecycle": handleDatasetLifecycle,
      "/dataset/management": handleDatasetManagement,
      "/knowledge-base/lifecycle": handleKnowledgeBaseLifecycle,
      "/prompt/lifecycle": handlePromptLifecycle,
      "/provider-api-key/lifecycle": handleProviderApiKeyLifecycle,
    };

    const handler = handlers[url.pathname];
    if (req.method === "POST" && handler) {
      writeJson(res, 200, await handler(payload));
      return;
    }

    writeJson(res, 404, { error: "not found" });
  } catch (error: any) {
    writeJson(res, 500, {
      success: false,
      error: error?.message ?? String(error),
    });
  }
});

const port = Number(process.env.PORT ?? 8080);
server.listen(port, "0.0.0.0", () => {
  console.log(
    `futureagi-sdk TypeScript compliance adapter listening on :${port}`,
  );
});

async function handleRawRequest(payload: JsonRecord): Promise<JsonRecord> {
  ensureInitialized();
  const client = new APIKeyAuth(authOptions());
  const path = String(required(payload, "path")).replace(/^\//, "");
  const method =
    HttpMethod[
      String(
        required(payload, "method"),
      ).toUpperCase() as keyof typeof HttpMethod
    ];
  const response = await client.request({
    method,
    url: `${state.baseUrl}/${path}`,
    params: payload.params,
    json: payload.json,
    data: payload.data,
    timeout: payload.timeout ?? state.timeout,
  } as RequestConfig);
  await client.close();
  state.calls.push({ operation: "raw-request", path, method });
  return responsePayload(response);
}

async function handleFutureagiBasic(payload: JsonRecord): Promise<JsonRecord> {
  ensureInitialized();
  const client = futureagiClient();
  const limit = payload.limit ?? 5;
  const currentUser = await client.users.current();
  const workspaces = await client.users.workspaces({ limit });
  const datasets = await client.datasets.list({ limit });
  const simulationRunTests = await client.simulations.runTests.list({ limit });
  const traceProjects = await client.tracing.projects({ limit });
  state.calls.push({ operation: "futureagi/basic" });
  return {
    success: true,
    result: {
      current_user: currentUser,
      workspaces,
      datasets,
      simulation_run_tests: simulationRunTests,
      trace_projects: traceProjects,
    },
  };
}

async function handleEvalsLifecycle(payload: JsonRecord): Promise<JsonRecord> {
  ensureInitialized();
  const client = futureagiClient();
  const templateId = required(payload, "template_id");
  const versionId = required(payload, "version_id");
  const datasetId = required(payload, "dataset_id");
  const evalId = required(payload, "eval_id");
  const sdkEvalId = required(payload, "sdk_eval_id");
  const listed = await client.evals.listTemplates(payload.list_body ?? {});
  const created = await client.evals.createTemplate(payload.template ?? {});
  const fetched = await client.evals.getTemplate(templateId);
  const updated = await client.evals.updateTemplate(
    templateId,
    payload.template_update ?? payload.template ?? {},
  );
  const usage = await client.evals.templateUsage(templateId);
  const versions = await client.evals.templateVersions(templateId);
  const createdVersion = await client.evals.createTemplateVersion(
    templateId,
    payload.version ?? {},
  );
  const restored = await client.evals.restoreTemplateVersion(
    templateId,
    versionId,
  );
  const defaulted = await client.evals.setDefaultTemplateVersion(
    templateId,
    versionId,
  );
  const sdkEvals = await client.evals.listSdkEvals();
  const configured = await client.evals.configure(payload.configure ?? {});
  const sdkRun = await client.evals.runV2(payload.run ?? {});
  const sdkResult = await client.evals.getRunV2(sdkEvalId);
  const datasetEvals = await client.evals.datasetEvals(datasetId);
  const structure = await client.evals.datasetEvalStructure(
    datasetId,
    evalId,
    payload.eval_structure_query ?? { eval_type: "preset" },
  );
  const preview = await client.evals.previewDatasetEval(
    datasetId,
    payload.preview ?? {},
  );
  const started = await client.evals.startDatasetEvals(
    datasetId,
    payload.start ?? {},
  );
  const deleteResult = await client.evals.deleteTemplate(
    payload.delete ?? { eval_id: templateId },
  );
  state.calls.push({ operation: "evals/lifecycle", template_id: templateId });
  return {
    success: true,
    result: {
      listed,
      created,
      fetched,
      updated,
      usage,
      versions,
      created_version: createdVersion,
      restored,
      defaulted,
      sdk_evals: sdkEvals,
      configured,
      sdk_run: sdkRun,
      sdk_result: sdkResult,
      dataset_evals: datasetEvals,
      structure,
      preview,
      started,
      delete: deleteResult,
    },
  };
}

async function handleSimulationLifecycle(
  payload: JsonRecord,
): Promise<JsonRecord> {
  ensureInitialized();
  const client = futureagiClient();
  const agentId = required(payload, "agent_id");
  const personaId = required(payload, "persona_id");
  const scenarioId = required(payload, "scenario_id");
  const runTestId = required(payload, "run_test_id");
  const evalConfigId = required(payload, "eval_config_id");
  const testExecutionId = required(payload, "test_execution_id");
  const runTestName =
    typeof payload.run_test === "object" &&
    payload.run_test !== null &&
    "name" in payload.run_test
      ? String((payload.run_test as JsonRecord).name)
      : "SDK run test";
  const persona = await client.simulations.personas.create(
    payload.persona ?? {},
  );
  const scenario = await client.simulations.scenarios.create(
    payload.scenario ?? {},
  );
  const agent = await client.simulations.agentDefinitions.create(
    payload.agent ?? {},
  );
  const runTest = await client.simulations.runTests.create(
    payload.run_test ?? {},
  );
  const runs = await client.simulations.runs({
    limit: 5,
    run_test_name: runTestName,
  });
  const metrics = await client.simulations.metrics({
    limit: 5,
    run_test_name: runTestName,
  });
  const analytics = await client.simulations.analytics({
    run_test_name: runTestName,
  });
  const fetchedRunTest = await client.simulations.runTests.get(runTestId);
  const evalConfigs = await client.simulations.runTests.addEvalConfigs(
    runTestId,
    payload.eval_configs ?? {},
  );
  const evalStructure = await client.simulations.runTests.evalConfigStructure(
    runTestId,
    evalConfigId,
  );
  const evalSummary = await client.simulations.runTests.evalSummary(runTestId, {
    test_execution_id: testExecutionId,
  });
  const newEvals = await client.simulations.runTests.runNewEvals(
    runTestId,
    payload.run_new_evals ?? {},
  );
  const executed = await client.simulations.runTests.execute(
    runTestId,
    payload.execute ?? {},
  );
  const status = await client.simulations.runTests.status(runTestId);
  const executions = await client.simulations.runTests.executions(runTestId);
  const testExecution =
    await client.simulations.testExecutions.get(testExecutionId);
  const canceled = await client.simulations.testExecutions.cancel(
    testExecutionId,
    payload.cancel ?? {},
  );
  const deletedRunTest = await client.simulations.runTests.delete(runTestId);
  const deletedAgent =
    await client.simulations.agentDefinitions.delete(agentId);
  const deletedScenario = await client.simulations.scenarios.delete(scenarioId);
  const deletedPersona = await client.simulations.personas.delete(personaId);
  state.calls.push({
    operation: "simulation/lifecycle",
    run_test_id: runTestId,
  });
  return {
    success: true,
    result: {
      runs,
      metrics,
      analytics,
      persona,
      scenario,
      agent,
      run_test: runTest,
      fetched_run_test: fetchedRunTest,
      eval_configs: evalConfigs,
      eval_structure: evalStructure,
      eval_summary: evalSummary,
      new_evals: newEvals,
      executed,
      status,
      executions,
      test_execution: testExecution,
      canceled,
      deleted_run_test: deletedRunTest,
      deleted_agent: deletedAgent,
      deleted_scenario: deletedScenario,
      deleted_persona: deletedPersona,
    },
  };
}

async function handleTracingLifecycle(
  payload: JsonRecord,
): Promise<JsonRecord> {
  ensureInitialized();
  const client = futureagiClient();
  const projectId = required(payload, "project_id");
  const traceId = required(payload, "trace_id");
  const sessionId = required(payload, "session_id");
  const clusterId = required(payload, "cluster_id");
  const projects = await client.tracing.projects({ limit: 5 });
  const traces = await client.tracing.traces({
    project_id: projectId,
    limit: 5,
  });
  const trace = await client.tracing.getTrace(traceId);
  const properties = await client.tracing.properties({ project_id: projectId });
  const updatedTags = await client.tracing.updateTags(
    traceId,
    payload.tags ?? {},
  );
  const graphMethods = await client.tracing.graphMethods(
    payload.graph_methods ?? {},
  );
  const sessions = await client.tracing.sessions({
    project_id: projectId,
    limit: 5,
  });
  const session = await client.tracing.getSession(sessionId);
  const sessionGraph = await client.tracing.sessionGraph(
    payload.session_graph ?? {},
  );
  const users = await client.tracing.users({ project_id: projectId, limit: 5 });
  const labels = await client.tracing.annotationLabels({
    project_id: projectId,
  });
  const bulkAnnotation = await client.tracing.bulkAnnotation(
    payload.bulk_annotation ?? {},
  );
  const issues = await client.tracing.issues({
    project_id: projectId,
    limit: 5,
  });
  const issue = await client.tracing.issue(clusterId);
  const issueStats = await client.tracing.issueStats({ project_id: projectId });
  state.calls.push({ operation: "tracing/lifecycle", trace_id: traceId });
  return {
    success: true,
    result: {
      projects,
      traces,
      trace,
      properties,
      updated_tags: updatedTags,
      graph_methods: graphMethods,
      sessions,
      session,
      session_graph: sessionGraph,
      users,
      labels,
      bulk_annotation: bulkAnnotation,
      issues,
      issue,
      issue_stats: issueStats,
    },
  };
}

async function handleAnnotationLog(payload: JsonRecord): Promise<JsonRecord> {
  ensureInitialized();
  const client = new Annotation(authOptions());
  const records = payload.records;
  if (!Array.isArray(records)) {
    throw new Error("records must be a list");
  }
  const result = await client.logAnnotations(records, {
    projectName: payload.project_name,
    timeout: payload.timeout ?? state.timeout,
  });
  await client.close();
  state.calls.push({ operation: "annotation/log", count: records.length });
  return { success: true, result };
}

async function handleAnnotationMetadata(
  payload: JsonRecord,
): Promise<JsonRecord> {
  ensureInitialized();
  const client = new Annotation(authOptions());
  const labels = await client.getLabels({
    projectId: payload.project_id,
    timeout: payload.timeout ?? state.timeout,
  });
  const projects = await client.listProjects({
    projectType: payload.project_type,
    name: payload.project_name,
    timeout: payload.timeout ?? state.timeout,
  });
  await client.close();
  state.calls.push({ operation: "annotation/metadata", labels: labels.length });
  return { success: true, result: { labels, projects } };
}

async function handleAnnotationQueueLifecycle(
  payload: JsonRecord,
): Promise<JsonRecord> {
  ensureInitialized();
  const client = new AnnotationQueue(authOptions());
  const queuePayload = payload.queue ?? {};
  const itemPayload = payload.item ?? {};
  const queue = await client.create({
    name: required(queuePayload, "name"),
    description: queuePayload.description,
    requiresReview: queuePayload.requires_review,
    annotationsRequired: queuePayload.annotations_required,
  });
  const addLabel = await client.addLabel({
    queueId: queue.id,
    labelId: required(payload, "label_id"),
  });
  const addedItems = await client.addItems(queue.id, [
    {
      sourceType: required(itemPayload, "source_type"),
      sourceId: required(itemPayload, "source_id"),
    },
  ]);
  const itemId = required(itemPayload, "id");
  const annotations = annotationInputs(payload.annotations ?? []);
  const submitted = await client.submitAnnotations(
    queue.id,
    itemId,
    annotations,
    { notes: payload.notes },
  );
  const completed = await client.completeItem(queue.id, itemId);
  const progress = await client.getProgress(queue.id);
  const exported = await client.export(queue.id, {
    format: "json",
    status: "completed",
  });
  await client.close();
  state.calls.push({
    operation: "annotation-queue/lifecycle",
    queue_id: queue.id,
  });
  return {
    success: true,
    result: {
      queue,
      add_label: addLabel,
      added_items: addedItems,
      submitted,
      completed,
      progress,
      exported,
    },
  };
}

async function handleAnnotationScoreLifecycle(
  payload: JsonRecord,
): Promise<JsonRecord> {
  ensureInitialized();
  const client = new AnnotationQueue(authOptions());
  const sourceType = required(payload, "source_type");
  const sourceId = required(payload, "source_id");
  const created = await client.createScore({
    sourceType,
    sourceId,
    labelId: required(payload, "label_id"),
    value: payload.value,
    notes: payload.notes,
  });
  const bulk = await client.createScores({
    sourceType,
    sourceId,
    scores: scoreInputs(payload.bulk_scores ?? []),
  });
  const fetched = await client.getScores(sourceType, sourceId);
  await client.close();
  state.calls.push({
    operation: "annotation-score/lifecycle",
    source_id: sourceId,
  });
  return { success: true, result: { created, bulk, fetched } };
}

async function handleAnnotationQueueManagement(
  payload: JsonRecord,
): Promise<JsonRecord> {
  ensureInitialized();
  const client = new AnnotationQueue(authOptions());
  const labelPayload = payload.label ?? {};
  const queuePayload = payload.queue ?? {};
  const itemPayload = payload.item ?? {};
  const userId = payload.user_id;

  const label = await client.createLabel({
    name: required(labelPayload, "name"),
    type: required(labelPayload, "type"),
    settings: labelPayload.settings,
    description: labelPayload.description,
  });
  const labels = await client.listLabels();
  const fetchedLabel = await client.getLabel({ labelId: label.id });
  const queue = await client.create({
    name: required(queuePayload, "name"),
    description: queuePayload.description,
    instructions: queuePayload.instructions,
    requiresReview: queuePayload.requires_review,
    annotationsRequired: queuePayload.annotations_required,
  });
  const queues = await client.list({
    status: queuePayload.status,
    search: queue.name,
  });
  const fetchedQueue = await client.get(queue.id);
  const updatedQueue = await client.update(queue.id, {
    description: queuePayload.updated_description,
  });
  const activatedQueue = await client.activate(queue.id);
  const addLabel = await client.addLabel({
    queueId: queue.id,
    labelId: label.id,
  });
  const addedItems = await client.addItems(queue.id, [
    {
      sourceType: required(itemPayload, "source_type"),
      sourceId: required(itemPayload, "source_id"),
    },
  ]);
  const items = await client.listItems(queue.id, {
    status: itemPayload.status,
    assignedTo: userId,
  });
  const itemId = required(itemPayload, "id");
  const assigned = await client.assignItems(queue.id, [itemId], userId);
  const imported = await client.importAnnotations(
    queue.id,
    itemId,
    annotationInputs(payload.annotations ?? []),
    {
      annotatorId: userId,
    },
  );
  const annotations = await client.getAnnotations(queue.id, itemId);
  const skipped = await client.skipItem(queue.id, itemId);
  const removedItems = await client.removeItems(queue.id, [itemId]);
  const removeLabel = await client.removeLabel({
    queueId: queue.id,
    labelId: label.id,
  });
  const analytics = await client.getAnalytics(queue.id);
  const agreement = await client.getAgreement(queue.id);
  const exportToDataset = await client.exportToDataset(queue.id, {
    datasetName: payload.dataset_name,
    statusFilter: payload.status_filter,
  });
  const completedQueue = await client.completeQueue(queue.id);
  const deletedLabel = await client.deleteLabel({ labelId: label.id });
  const deletedQueue = await client.delete(queue.id);
  await client.close();
  state.calls.push({
    operation: "annotation-queue/management",
    queue_id: queue.id,
  });
  return {
    success: true,
    result: {
      label,
      labels,
      fetched_label: fetchedLabel,
      queue,
      queues,
      fetched_queue: fetchedQueue,
      updated_queue: updatedQueue,
      activated_queue: activatedQueue,
      add_label: addLabel,
      added_items: addedItems,
      items,
      assigned,
      imported,
      annotations,
      skipped,
      removed_items: removedItems,
      remove_label: removeLabel,
      analytics,
      agreement,
      export_to_dataset: exportToDataset,
      completed_queue: completedQueue,
      deleted_label: deletedLabel,
      deleted_queue: deletedQueue,
    },
  };
}

async function handleDatasetLifecycle(
  payload: JsonRecord,
): Promise<JsonRecord> {
  ensureInitialized();
  const columns = payload.columns;
  const rows = payload.rows;
  if (!Array.isArray(columns) || columns.length === 0) {
    throw new Error("columns must be a non-empty list");
  }
  if (!Array.isArray(rows) || rows.length === 0) {
    throw new Error("rows must be a non-empty list");
  }

  const dataset = new Dataset({
    ...authOptions(),
    datasetConfig: {
      name: required(payload, "name"),
      model_type:
        ModelTypes[
          String(required(payload, "model_type")) as keyof typeof ModelTypes
        ],
    },
  });
  await dataset.create();
  await dataset.addColumns(
    columns.map((column) => ({
      name: required(column, "name"),
      data_type:
        DataTypeChoices[
          String(required(column, "data_type")) as keyof typeof DataTypeChoices
        ],
    })),
  );
  await dataset.addRows(rows);
  await dataset.close();
  const datasetConfig = dataset.getConfig();
  state.calls.push({
    operation: "dataset/lifecycle",
    dataset_id: datasetConfig.id,
  });
  return {
    success: true,
    result: {
      dataset: datasetConfig,
      columns_added: columns.length,
      rows_added: rows.length,
    },
  };
}

async function handleDatasetManagement(
  payload: JsonRecord,
): Promise<JsonRecord> {
  ensureInitialized();
  const datasetConfig = await Dataset.getDatasetConfig(
    required(payload, "name"),
    authOptions(),
  );
  const dataset = new Dataset({ ...authOptions(), datasetConfig });
  const columnId = await dataset.getColumnId(
    required(payload, "lookup_column"),
  );
  await dataset.addRunPrompt({
    name: required(payload, "run_prompt_name"),
    model: required(payload, "model"),
    messages: payload.messages ?? [],
  });
  const evalStats = await dataset.getEvalStats();
  await dataset.addOptimization({
    optimizationName: required(payload, "optimization_name"),
    promptColumnName: required(payload, "lookup_column"),
  });
  await dataset.delete();
  await dataset.close();
  state.calls.push({
    operation: "dataset/management",
    dataset_id: datasetConfig.id,
  });
  return {
    success: true,
    result: { column_id: columnId, eval_stats: evalStats, deleted: true },
  };
}

async function handleKnowledgeBaseLifecycle(
  payload: JsonRecord,
): Promise<JsonRecord> {
  ensureInitialized();
  const client = new KnowledgeBase(undefined, authOptions());
  const name = required(payload, "name");
  const updatedName = payload.updated_name ?? name;
  await client.createKb(name);
  await client.updateKb({ kbName: name, newName: updatedName });
  const listed = await client.listKbs(updatedName);
  await client.deleteFilesFromKb({
    kbName: updatedName,
    fileNames: payload.file_names ?? [],
  });
  await client.deleteKb({ kbNames: updatedName });
  await client.close();
  state.calls.push({ operation: "knowledge-base/lifecycle", name });
  return { success: true, result: { listed, deleted: true } };
}

async function handlePromptLifecycle(payload: JsonRecord): Promise<JsonRecord> {
  ensureInitialized();
  const prompt = new Prompt(
    new PromptTemplate({
      name: required(payload, "name"),
      messages: [new UserMessage(required(payload, "message"))],
      model_configuration: new ModelConfig({
        model_name: required(payload, "model"),
      }),
    }),
    authOptions(),
  );
  await prompt.generate(required(payload, "generate_requirements"));
  await prompt.improve(required(payload, "improve_requirements"));
  const compiled = prompt.compile(payload.variables ?? {});
  await prompt.create({ label: payload.label });
  await prompt.commitCurrentVersion(
    payload.commit_message ?? "",
    Boolean(payload.set_default),
  );
  const fetchedTemplate = await Prompt.getTemplateByName(
    required(payload, "name"),
    {
      ...authOptions(),
      label: payload.label,
    },
  );
  const labels = await prompt.labels().list();
  const templateLabels = await Prompt.getTemplateLabels({
    ...authOptions(),
    template_name: required(payload, "name"),
  });
  await prompt.delete();
  await prompt.close();
  state.calls.push({ operation: "prompt/lifecycle", template: payload.name });
  return {
    success: true,
    result: {
      compiled,
      fetched_template: fetchedTemplate,
      labels,
      template_labels: templateLabels,
      deleted: true,
    },
  };
}

async function handleProviderApiKeyLifecycle(
  payload: JsonRecord,
): Promise<JsonRecord> {
  ensureInitialized();
  const provider =
    ModelProvider[
      String(required(payload, "provider")) as keyof typeof ModelProvider
    ];
  await ProviderAPIKeyClient.setApiKey(
    { provider, key: required(payload, "provider_key") },
    authOptions(),
  );
  const listed = await ProviderAPIKeyClient.listApiKeys(authOptions());
  const fetched = await ProviderAPIKeyClient.getApiKey(provider, authOptions());
  state.calls.push({ operation: "provider-api-key/lifecycle", provider });
  return { success: true, result: { listed, fetched } };
}

function annotationInputs(
  items: JsonRecord[],
): Array<{ labelId: string; value: any; scoreSource?: string }> {
  return items.map((item) => ({
    labelId: required(item, "label_id"),
    value: item.value,
    scoreSource: item.score_source,
  }));
}

function scoreInputs(
  items: JsonRecord[],
): Array<{ labelId: string; value: any; scoreSource?: string }> {
  return annotationInputs(items);
}

function authOptions() {
  return {
    fiApiKey: state.apiKey,
    fiSecretKey: state.secretKey,
    fiBaseUrl: state.baseUrl,
    timeout: state.timeout,
  };
}

function futureagiClient(): FutureAGIClient {
  ensureInitialized();
  return new FutureAGIClient({
    apiKey: state.apiKey,
    secretKey: state.secretKey,
    baseUrl: state.baseUrl,
  });
}

function ensureInitialized(): void {
  if (!state.apiKey || !state.secretKey || !state.baseUrl) {
    throw new Error("adapter is not initialized");
  }
}

function required(source: JsonRecord, key: string): any {
  const value = source[key];
  if (value === undefined || value === null || value === "") {
    throw new Error(`missing required field: ${key}`);
  }
  return value;
}

function responsePayload(response: any): JsonRecord {
  if (response && typeof response === "object" && "data" in response) {
    return { success: true, status_code: response.status, body: response.data };
  }
  return { success: true, body: response };
}

function readJson(req: http.IncomingMessage): Promise<JsonRecord> {
  return new Promise((resolve, reject) => {
    const chunks: Buffer[] = [];
    req.on("data", (chunk) => chunks.push(Buffer.from(chunk)));
    req.on("error", reject);
    req.on("end", () => {
      if (chunks.length === 0) {
        resolve({});
        return;
      }
      try {
        resolve(JSON.parse(Buffer.concat(chunks).toString("utf8")));
      } catch (error) {
        reject(error);
      }
    });
  });
}

function writeJson(
  res: http.ServerResponse,
  status: number,
  payload: JsonRecord,
): void {
  const body = Buffer.from(JSON.stringify(payload));
  res.writeHead(status, {
    "content-type": "application/json",
    "content-length": body.length,
  });
  res.end(body);
}
