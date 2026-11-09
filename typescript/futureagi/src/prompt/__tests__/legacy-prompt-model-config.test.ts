import axios, { AxiosAdapter, AxiosRequestConfig } from 'axios';
import { Prompt } from '../client';
import { ModelConfig, PromptTemplate, UserMessage } from '../types';
import { Routes } from '../../utils/routes';

const operations = ['create', 'createNewVersion', 'saveCurrentDraft'] as const;
type Operation = typeof operations[number];
const baseUrl = 'https://sdk.invalid';
const templateId = 'synthetic-prompt';
const templateName = 'configured-prompt';
const draftRoute = Routes.add_new_draft.replace('{template_id}', templateId);
const saveRoute = Routes.run_template.replace('{template_id}', templateId);
const commitRoute = Routes.commit_template.replace('{template_id}', templateId);
const routes: Record<Operation, string> = {
  create: Routes.create_template,
  createNewVersion: draftRoute,
  saveCurrentDraft: saveRoute,
};
const defaultConfiguration = {
  model: 'gpt-4o-mini',
  temperature: 0.7,
  top_p: 1,
  frequency_penalty: 0,
  presence_penalty: 0,
};

describe('legacy prompt model configuration persistence', () => {
  const originalAdapter = axios.defaults.adapter;
  let client: Prompt | undefined;
  let requests: Array<{ config: AxiosRequestConfig; body: any }>;
  let adapter: jest.MockedFunction<AxiosAdapter>;

  beforeEach(() => {
    client = undefined;
    requests = [];
    // Legacy Prompt uses Axios, so capture the serialized JSON at its adapter boundary.
    adapter = jest.fn(async config => {
      requests.push({
        config,
        body: config.data === undefined ? undefined : JSON.parse(config.data),
      });
      let data: Record<string, any>;
      switch (config.url) {
        case `${baseUrl}/${Routes.get_template_version_history}`:
          data = { results: [{ template_version: 'v1', is_draft: true }] };
          break;
        case `${baseUrl}/${Routes.create_template}`:
          data = { result: { id: templateId, name: templateName, template_version: 'v1' } };
          break;
        case `${baseUrl}/${Routes.prompt_label_get_by_name}`:
          data = { result: {
            id: templateId,
            name: templateName,
            version: 'v1',
            prompt_config: [{ messages: [], configuration: defaultConfiguration }],
          } };
          break;
        case `${baseUrl}/${draftRoute}`:
          data = { result: [{ template_version: 'v2' }] };
          break;
        case `${baseUrl}/${commitRoute}`:
        case `${baseUrl}/${saveRoute}`:
          data = { result: {} };
          break;
        default:
          throw new Error(`Unexpected prompt request: ${config.method} ${config.url}`);
      }
      return { status: 200, statusText: 'OK', headers: {}, config, data };
    });
    axios.defaults.adapter = adapter;
  });

  afterEach(async () => {
    try {
      await client?.close();
    } finally {
      axios.defaults.adapter = originalAdapter;
    }
  });

  async function persist(operation: Operation, modelConfig?: ModelConfig): Promise<Record<string, any>> {
    client = new Prompt(new PromptTemplate({
      name: templateName,
      messages: [new UserMessage('Look up the topic and return JSON.')],
      model_configuration: modelConfig,
      ...(operation === 'create' ? {} : { id: templateId, version: 'v1' }),
    }), {
      fiApiKey: 'synthetic-api-key',
      fiSecretKey: 'synthetic-secret-key',
      fiBaseUrl: baseUrl,
      retryAttempts: 1,
    });

    await client[operation]();

    const expectedRoutes = operation === 'create'
      ? [Routes.create_template]
      : operation === 'createNewVersion'
        ? [Routes.get_template_version_history, commitRoute, draftRoute]
        : [Routes.get_template_version_history, saveRoute];
    expect(requests.map(({ config }) => config.url)).toEqual(
      expectedRoutes.map(route => `${baseUrl}/${route}`),
    );
    expect(adapter).toHaveBeenCalledTimes(expectedRoutes.length);
    const writes = requests.filter(({ config }) => config.url === `${baseUrl}/${routes[operation]}`);
    expect(writes).toHaveLength(1);
    expect(writes[0].config.method).toBe('post');
    expect(typeof writes[0].config.data).toBe('string');
    const body = operation === 'createNewVersion' ? writes[0].body.new_prompts[0] : writes[0].body;
    return body.prompt_config[0].configuration;
  }

  it.each(operations)('%s preserves structured output, tool choice and tools along with existing fields', async operation => {
    const responseFormat = { type: 'json_object' };
    const tools = [{
      name: 'lookup',
      config: { type: 'object', properties: { topic: { type: 'string' } }, required: ['topic'] },
    }];
    const configuration = await persist(operation, new ModelConfig({
      model_name: 'gpt-4o',
      temperature: 0,
      max_tokens: 128,
      top_p: 0.85,
      frequency_penalty: -0.5,
      presence_penalty: 0.25,
      response_format: responseFormat,
      tool_choice: 'auto',
      tools,
    }));
    expect(configuration).toEqual({
      model: 'gpt-4o',
      temperature: 0,
      max_tokens: 128,
      top_p: 0.85,
      frequency_penalty: -0.5,
      presence_penalty: 0.25,
      response_format: responseFormat,
      tool_choice: 'auto',
      tools,
    });
  });

  it.each(operations)('%s omits optional settings when they were not provided', async operation => {
    expect(await persist(operation, new ModelConfig())).toEqual(defaultConfiguration);
  });

  it.each(operations)('%s keeps the existing fallback when no model configuration is supplied', async operation => {
    expect(await persist(operation)).toEqual({ model: 'gpt-4o-mini' });
  });

  it('keeps absent optional settings omitted after loading and saving a draft', async () => {
    const template = await Prompt.getTemplateByName(templateName, {
      version: 'v1',
      fiApiKey: 'synthetic-api-key',
      fiSecretKey: 'synthetic-secret-key',
      fiBaseUrl: baseUrl,
      retryAttempts: 1,
    });
    expect(template.model_configuration).toBeInstanceOf(ModelConfig);
    requests = [];
    adapter.mockClear();
    expect(await persist('saveCurrentDraft', template.model_configuration)).toEqual(defaultConfiguration);
  });

  it.each(operations)('%s preserves explicitly supplied null settings', async operation => {
    expect(await persist(operation, new ModelConfig({
      response_format: null,
      tool_choice: null,
      tools: null,
    }))).toEqual({
      ...defaultConfiguration,
      response_format: null,
      tool_choice: null,
      tools: null,
    });
  });

  it.each(operations)('%s preserves a string format and an explicitly empty tool list', async operation => {
    expect(await persist(operation, new ModelConfig({
      response_format: 'text',
      tool_choice: 'none',
      tools: [],
    }))).toEqual({
      ...defaultConfiguration,
      response_format: 'text',
      tool_choice: 'none',
      tools: [],
    });
  });
});
