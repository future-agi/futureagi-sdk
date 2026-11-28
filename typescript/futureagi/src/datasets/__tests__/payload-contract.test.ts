/**
 * T-067/T-068 SOURCE-pinned contracts, not live/provider qualification.
 * FA e0a4f1f60dbb970c8bd04f2e73f335640fb4ef0f; paths under futureagi/model_hub/:
 * serializers/develop_optimisation.py blob 185d51d0f6ac2d098000a4639b970fc793f997fc
 *   OptimizationDatasetSerializer.Meta.fields :59-72 (inventory below);
 *   :18-30,95-104 validates same-dataset column/metric links.
 * views/develop_optimisation.py blob 237b3432f9811db2e7d1f87adaac4d3c8e9832b6
 *   OptimisationCreateView :48-55 rejects unknown keys; :75-87 consumes name,
 *   prompt_name, column, eval IDs/mapping, model_config and messages.
 * views/run_prompt.py blob 5362bfbb360c99d315022edf03a54055166f1fdd
 *   AddRunPromptColumnView :1724-1729 reads config.run_prompt_config;
 *   :1777-1781 reads the five numeric generation fields from it;
 *   :1752,1761-1762,1771-1789,1807 reads the remaining options from config.
 * serializers/run_prompt.py blob 03904ee722def5c6921b790a6a3a9792cbf40e1e
 *   PromptConfigSerializer :167-182,218-250; AddRunPromptSerializer :366-369.
 * Inventories are transcribed from those pinned server readers, not SDK output.
 */
import { Dataset, DatasetResponseHandler } from '../dataset';
import { DatasetError, DatasetValidationError } from '../../utils/errors';
import { RequestConfig, HttpMethod } from '../../api/types';

const FA_REVISION = 'e0a4f1f60dbb970c8bd04f2e73f335640fb4ef0f';
const GENERATION_FIELDS = ['max_tokens', 'temperature', 'presence_penalty', 'frequency_penalty', 'top_p'];
const OPTIMIZATION_FIELDS = ['id', 'name', 'dataset_id', 'column_id', 'messages', 'user_eval_template_ids',
  'model_config', 'optimize_type', 'user_eval_template_mapping', 'prompt_name', 'created_at', 'status'];
const DEFAULTS = { max_tokens: 500, temperature: 0.5, presence_penalty: 1, frequency_penalty: 1, top_p: 1 };
const DATASET_ID = '11111111-1111-4111-8111-111111111111';
const COLUMN_ID = '22222222-2222-4222-8222-222222222222';
const EVAL_ID = '33333333-3333-4333-8333-333333333333';
const BASE_URL = 'https://payload.invalid';
type RunOptions = Parameters<Dataset['addRunPrompt']>[0];

function fixture(metrics: any[] = [{ id: EVAL_ID }], fallback: any[] = []) {
  // Skip credential discovery only. Every payload and column/eval helper is real.
  const client = Object.create(Dataset.prototype) as Dataset;
  (client as any)._baseUrl = BASE_URL;
  (client as any)._datasetConfig = { id: DATASET_ID, name: 'fixture' };
  const request = jest.spyOn(client, 'request').mockImplementation(async (config: RequestConfig) => {
    expect(config.timeout).toBe(30000);
    if (config.method === HttpMethod.GET) {
      if (config.url === `${BASE_URL}/model-hub/develops/${DATASET_ID}/get-dataset-table/`) {
        expect(config.params).toEqual({ page_size: 1, current_page_index: 0 });
        return { columns: [{ id: COLUMN_ID, name: 'input' }] };
      }
      if (config.url === `${BASE_URL}/model-hub/metrics/by-column/`) {
        expect(config.params).toEqual({ column_id: COLUMN_ID });
        return { result: metrics };
      }
      if (config.url === `${BASE_URL}/model-hub/dataset/${DATASET_ID}/eval-stats/`) {
        return { result: fallback };
      }
    }
    if (config.method === HttpMethod.POST && [
      `${BASE_URL}/model-hub/develops/add_run_prompt_column/`,
      `${BASE_URL}/model-hub/optimisation/create/`,
    ].includes(config.url)) return { result: 'synthetic success' };
    throw new Error(`Unexpected synthetic request: ${config.method} ${config.url}`);
  });
  return { client, request };
}

function posted(request: ReturnType<typeof fixture>['request']) {
  const calls = request.mock.calls.filter(([config]) => config.method === HttpMethod.POST);
  expect(calls).toHaveLength(1);
  expect(calls[0][1]).toBe(DatasetResponseHandler);
  return calls[0][0].json as Record<string, any>;
}

const runOptions = (): RunOptions => ({ name: 'answer', model: 'synthetic-model', messages: [{ role: 'user', content: 'hello' }] });
const optimizeOptions = { optimizationName: 'improve', promptColumnName: 'input' };
afterEach(() => jest.restoreAllMocks());

describe(`run prompt contract at FA ${FA_REVISION}`, () => {
  test.each([
    ['defaults', {}, DEFAULTS],
    ['all-nondefault', { maxTokens: 123, temperature: 0.2, presencePenalty: -0.3, frequencyPenalty: 0.7, topP: 0.8 },
      { max_tokens: 123, temperature: 0.2, presence_penalty: -0.3, frequency_penalty: 0.7, top_p: 0.8 }],
    ['explicit-zero', { maxTokens: 0, temperature: 0, presencePenalty: 0, frequencyPenalty: 0, topP: 0 },
      { max_tokens: 0, temperature: 0, presence_penalty: 0, frequency_penalty: 0, top_p: 0 }],
  ])('nests generation options: %s', async (_name, options, expected) => {
    const { client, request } = fixture();
    expect(await client.addRunPrompt({ ...runOptions(), ...(options as Partial<RunOptions>) })).toBe(client);
    const body = posted(request);
    expect(body.config.run_prompt_config).toEqual(expected);
    for (const key of GENERATION_FIELDS) expect(body.config).not.toHaveProperty(key);
    expect(body).toEqual({ dataset_id: DATASET_ID, name: 'answer', config: {
      model: 'synthetic-model', output_format: 'string', concurrency: 5,
      messages: [{ role: 'user', content: [{ type: 'text', text: 'hello' }] }], run_prompt_config: expected,
    } });
  });

  test.each([
    ['populated-with-false-json-value', { tools: [{ id: EVAL_ID }], toolChoice: 'required',
      responseFormat: { type: 'json_schema', json_schema: { name: 'reply', strict: false, schema: { type: 'object' } } } }],
    ['explicit-empty-and-false', { tools: [], toolChoice: false, responseFormat: {} }],
    ['empty-tool-choice', { toolChoice: '' }],
    ['explicit-null-tool-choice', { toolChoice: null }],
  ])('keeps optional outer fields: %s', async (_name, optional) => {
    const { client, request } = fixture();
    const options = optional as Partial<RunOptions>;
    await client.addRunPrompt({ ...runOptions(), outputFormat: 'object', concurrency: 1, ...options });
    const config = posted(request).config;
    for (const [publicKey, wireKey] of [['tools', 'tools'], ['toolChoice', 'tool_choice'], ['responseFormat', 'response_format']] as const) {
      if (publicKey in options) {
        expect(config).toHaveProperty(wireKey, options[publicKey]);
      } else expect(config).not.toHaveProperty(wireKey);
      expect(config.run_prompt_config ?? {}).not.toHaveProperty(wireKey);
    }
    expect(config.output_format).toBe('object');
    expect(config.concurrency).toBe(1);
    // false/empty toolChoice pins public any forwarding, not serializer acceptance.
  });

  test('omitted and undefined optional fields stay absent', async () => {
    const { client, request } = fixture();
    await client.addRunPrompt({ ...runOptions(), tools: undefined, toolChoice: undefined, responseFormat: undefined });
    for (const key of ['tools', 'tool_choice', 'response_format']) expect(posted(request).config).not.toHaveProperty(key);
  });

  test('message column translation and explicit zero concurrency remain unchanged', async () => {
    const { client, request } = fixture();
    const messages = [{ role: 'system', content: 'read {{input}}' }, { role: 'user', content: [
      { type: 'text', text: 'again {{input}}' }, { type: 'image_url', image_url: { url: 'synthetic' } }, 7,
    ] }];
    // Existing runtime accepts typed content parts despite its narrower public type.
    expect(await client.addRunPrompt({ ...runOptions(), messages: messages as any, concurrency: 0 })).toBe(client);
    expect(posted(request).config.messages).toEqual([
      { role: 'system', content: [{ type: 'text', text: `read {{${COLUMN_ID}}}` }] },
      { role: 'user', content: [{ type: 'text', text: `again {{${COLUMN_ID}}}` },
        { type: 'image_url', image_url: { url: 'synthetic' } }, { type: 'text', text: '7' }] },
    ]);
    expect(posted(request).config.concurrency).toBe(0); // forwarding, not server acceptance
    expect(request).toHaveBeenCalledTimes(3);
  });

  test.each([
    ['empty-name', { name: '' }, 'name cannot be empty'],
    ['empty-model', { model: '' }, 'Model cannot be empty'],
    ['empty-messages', { messages: [] }, 'Messages list cannot be empty'],
  ])('preserves local validation: %s', async (_name, overrides, message) => {
    const { client, request } = fixture();
    await expect(client.addRunPrompt({ ...runOptions(), ...(overrides as Partial<RunOptions>) })).rejects.toThrow(message as string);
    expect(request).not.toHaveBeenCalled();
  });

  test('missing column refuses before POST', async () => {
    const { client, request } = fixture();
    await expect(client.addRunPrompt({ ...runOptions(), messages: [{ role: 'user', content: '{{missing}}' }] })).rejects.toThrow(DatasetError);
    expect(request).toHaveBeenCalledTimes(1);
    expect(request.mock.calls[0][0].method).toBe(HttpMethod.GET);
  });
});

describe(`optimization contract at FA ${FA_REVISION}`, () => {
  test('canonical name and valid same-dataset column/eval mapping were already supported', async () => {
    const { client, request } = fixture([{ id: EVAL_ID }, { id: '' }, {}]);
    expect(await client.addOptimization(optimizeOptions)).toBe(client);
    const body = posted(request);
    expect(body).toMatchObject({ name: 'improve', column_id: COLUMN_ID, dataset_id: DATASET_ID,
      optimize_type: 'PROMPT_TEMPLATE', user_eval_template_ids: [EVAL_ID],
      user_eval_template_mapping: { [EVAL_ID]: EVAL_ID }, model_config: {}, messages: [] });
    expect(Object.keys(body).every(key => OPTIMIZATION_FIELDS.includes(key))).toBe(true);
    expect(body).not.toHaveProperty('optimization_name');
    expect(body).not.toHaveProperty('prompt_column_name');
    expect(request).toHaveBeenCalledTimes(3);
  });

  test('sends prompt_name alongside canonical name without legacy wire keys', async () => {
    const { client, request } = fixture();
    const modelConfig = { temperature: 0, strict: false };
    expect(await client.addOptimization({ ...optimizeOptions, optimizeType: 'HYBRID', modelConfig })).toBe(client);
    expect(posted(request)).toEqual({ name: 'improve', prompt_name: 'input', column_id: COLUMN_ID,
      dataset_id: DATASET_ID, optimize_type: 'HYBRID', model_config: modelConfig, messages: [],
      user_eval_template_ids: [EVAL_ID], user_eval_template_mapping: { [EVAL_ID]: EVAL_ID } });
  });

  test('preserves same-dataset eval-stats fallback and MODEL_PARAMETERS', async () => {
    const { client, request } = fixture([], [{ id: EVAL_ID }, { id: '' }, {}]);
    expect(await client.addOptimization({ ...optimizeOptions, optimizeType: 'MODEL_PARAMETERS' })).toBe(client);
    expect(posted(request)).toMatchObject({ user_eval_template_ids: [EVAL_ID],
      user_eval_template_mapping: { [EVAL_ID]: EVAL_ID }, optimize_type: 'MODEL_PARAMETERS' });
    expect(request).toHaveBeenCalledTimes(4);
  });

  test.each([
    ['empty-name', { optimizationName: '' }], ['empty-column', { promptColumnName: '' }],
    ['invalid-type', { optimizeType: 'INVALID' }],
  ])('preserves local validation: %s', async (_name, overrides) => {
    const { client, request } = fixture();
    await expect(client.addOptimization({ ...optimizeOptions, ...(overrides as object) })).rejects.toThrow(DatasetValidationError);
    expect(request).not.toHaveBeenCalled();
  });

  test('missing column refuses before metrics or POST', async () => {
    const { client, request } = fixture();
    await expect(client.addOptimization({ ...optimizeOptions, promptColumnName: 'missing' })).rejects.toThrow(DatasetError);
    expect(request).toHaveBeenCalledTimes(1);
  });

  test('missing eval templates refuses before POST', async () => {
    const { client, request } = fixture([]);
    await expect(client.addOptimization(optimizeOptions)).rejects.toThrow('No evaluation templates found');
    expect(request.mock.calls.every(([config]) => config.method === HttpMethod.GET)).toBe(true);
  });
});

test('both builders still require a configured dataset', async () => {
  const { client, request } = fixture();
  (client as any)._datasetConfig = null;
  await expect(client.addRunPrompt(runOptions())).rejects.toThrow('configured with an ID');
  await expect(client.addOptimization(optimizeOptions)).rejects.toThrow('configured with an ID');
  expect(request).not.toHaveBeenCalled();
});
