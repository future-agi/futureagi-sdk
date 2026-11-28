import * as fs from 'node:fs';
import * as path from 'node:path';

// Use the published property list, not the implementation's alias table.
const fixture = JSON.parse(fs.readFileSync(path.join(__dirname, 'compat-0.1.2.json'), 'utf8'));
const methods: Record<string, [string, unknown[], boolean]> = {
  QueueDetail: ['get', ['q'], false],
  QueueItem: ['listItems', ['q'], true],
  QueueProgress: ['getProgress', ['q'], false],
  QueueAnalytics: ['getAnalytics', ['q'], false],
  QueueAgreement: ['getAgreement', ['q'], false],
  Score: ['getScores', ['trace', 'trace-id'], true],
  ExportToDatasetResponse: ['exportToDataset', ['q', { datasetName: 'export' }], false],
};
const aliases = Object.keys(methods).flatMap(name =>
  fixture.surface[name].instance.properties.filter((p: { name: string }) => /[A-Z]/.test(p.name))
    .map((p: { name: string }) => [name, p.name, p.name.replace(/[A-Z]/g, c => `_${c.toLowerCase()}`)]),
);

const datasetAliases: Record<string, string[]> = {
  Column: ['dataType', 'sourceId', 'isFrozen', 'isVisible', 'evalTags', 'averageScore', 'orderIndex'],
  Cell: ['columnId', 'rowId', 'columnName', 'valueInfos', 'failureReason'],
};
const modernName = (old: string) => old.replace(/[A-Z]/g, c => `_${c.toLowerCase()}`);

beforeEach(() => jest.resetModules());
afterEach(() => jest.restoreAllMocks());

test.each(aliases)('%s.%s reads canonical data and warns once', async (name, old, modern) => {
  const { AnnotationQueue } = require('../queues/client');
  const client = new AnnotationQueue({ fiApiKey: 'test', fiSecretKey: 'test', fiBaseUrl: 'http://localhost' });
  const warn = jest.spyOn(process, 'emitWarning').mockImplementation(() => undefined);
  const [method, args, list] = methods[name];
  const payload = { id: 'q', name: 'q', [modern]: 17, future_field: 'retained' };
  jest.spyOn(client, 'request').mockImplementation(async (_config: unknown, handler: any) =>
    handler._parseSuccess({ status: 200, data: { result: list ? [payload] : payload } }));
  const output = await client[method](...args);
  const row = list ? output[0] : output;
  expect(row[modern]).toBe(17);
  expect(warn).not.toHaveBeenCalled();
  expect(row[old]).toBe(17);
  expect(row[old]).toBe(17);
  expect(row.future_field).toBe('retained');
  expect(warn).toHaveBeenCalledTimes(1);
  expect(warn.mock.calls[0][0]).toContain(modern);
  expect(warn.mock.calls[0][0]).toContain(old);
  expect(warn.mock.calls[0][1]).toBe('DeprecationWarning');
  const again = await client[method](...args);
  expect((list ? again[0] : again)[old]).toBe(17);
  expect(warn).toHaveBeenCalledTimes(1);
});

test.each(aliases)('%s.%s accepts legacy response data without loss', async (name, old, modern) => {
  const { AnnotationQueue } = require('../queues/client');
  const client = new AnnotationQueue({ fiApiKey: 'test', fiSecretKey: 'test', fiBaseUrl: 'http://localhost' });
  const warn = jest.spyOn(process, 'emitWarning').mockImplementation(() => undefined);
  const [method, args, list] = methods[name];
  const payload = { id: 'q', name: 'q', [old]: 17 };
  jest.spyOn(client, 'request').mockImplementation(async (_config: unknown, handler: any) =>
    handler._parseSuccess({ status: 200, data: { result: list ? [payload] : payload } }));
  for (let i = 0; i < 2; i++) {
    const output = await client[method](...args);
    const row = list ? output[0] : output;
    expect(row[modern]).toBe(17);
    expect(row[old]).toBe(17);
  }
  expect(warn).toHaveBeenCalledTimes(1);
});

test.each(['canonical', 'legacy'])('bulk annotations preserve all six fields from %s data', async shape => {
  const { Annotation } = require('../annotations/annotation');
  const client = new Annotation({ fiApiKey: 'test', fiSecretKey: 'test', fiBaseUrl: 'http://localhost' });
  const warn = jest.spyOn(process, 'emitWarning').mockImplementation(() => undefined);
  const fields = fixture.surface.BulkAnnotationResponse.instance.properties
    .filter((p: { name: string }) => /[A-Z]/.test(p.name)).map((p: { name: string }) => p.name);
  const data: Record<string, unknown> = { message: 'ok', unrelated: 'still ignored' };
  for (const field of fields) data[shape === 'legacy' ? field : field.replace(/[A-Z]/g, (c: string) => `_${c.toLowerCase()}`)] = 17;
  // Exercise the real response parser without making a provider/network request.
  const result = (client as any)._parseBulkAnnotationResponse({ result: data });
  expect(result.unrelated).toBeUndefined();
  if (shape === 'canonical') expect(warn).not.toHaveBeenCalled();
  for (const old of fields) {
    expect(result[old]).toBe(17);
    expect(result[old]).toBe(17);
    expect(result[old.replace(/[A-Z]/g, (c: string) => `_${c.toLowerCase()}`)]).toBe(17);
  }
  expect(warn).toHaveBeenCalledTimes(6);
});

test.each(Object.entries(datasetAliases).flatMap(([name, fields]) => fields.map(old => [name, old])))
  ('dataset %s.%s preserves helper inputs and readable attributes', (name, old) => {
    const types = require('../datasets/types');
    const warn = jest.spyOn(process, 'emitWarning').mockImplementation(() => undefined);
    const value: Record<string, unknown> = { dataType: 'text', sourceId: 'source', isFrozen: true,
      isVisible: false, evalTags: ['tag'], averageScore: 0.7, orderIndex: 7, columnId: 'c', rowId: 'r',
      columnName: 'column', valueInfos: [{ value: 1 }], failureReason: 'reason' };
    const helper = types[`create${name}`];
    const modern = modernName(old);
    const canonical = helper({ name: 'column', data_type: 'text', [modern]: value[old] });
    expect(canonical[modern]).toEqual(value[old]);
    expect(warn).not.toHaveBeenCalled();
    expect(canonical[old]).toEqual(value[old]);
    expect(canonical[old]).toEqual(value[old]);
    const legacy = helper({ name: 'column', ...(old === 'dataType' ? {} : { data_type: 'text' }), [old]: value[old] });
    expect(legacy[modern]).toEqual(value[old]);
    expect(legacy[old]).toEqual(value[old]);
    expect(warn).toHaveBeenCalledTimes(1);
    expect(warn.mock.calls[0][0]).toContain(modern);
  });

test('legacy cells retain their identifiers through createRow and CSV', () => {
  const { createRow, DatasetTableUtils } = require('../datasets/types');
  const warn = jest.spyOn(process, 'emitWarning').mockImplementation(() => undefined);
  const cell = { columnId: 'c', rowId: 'r', value: 'retained' };
  const row = createRow({ cells: [cell] });
  expect(row.cells[0].column_id).toBe('c');
  expect(row.cells[0].row_id).toBe('r');
  expect(row.cells[0].columnId).toBe('c');
  expect(cell).toEqual({ columnId: 'c', rowId: 'r', value: 'retained' });
  expect(DatasetTableUtils.toCsv({ id: 'd', columns: [{ id: 'c', name: 'C', dataType: 'text' }], rows: [{ id: 'r', cells: [cell] }] })).toBe('C\nretained');
  const wire = JSON.parse(DatasetTableUtils.toJson({ id: 'd', columns: [{ id: 'c', name: 'C', dataType: 'text' }],
    rows: [{ id: 'r', cells: [cell] }], datasetConfig: { name: 'D', modelType: 'GenerativeLLM', columnOrder: ['c'] } }));
  expect(wire.columns[0].data_type).toBe('text');
  expect(wire.rows[0].cells[0].column_id).toBe('c');
  expect(wire.dataset_config).toMatchObject({ model_type: 'GenerativeLLM', column_order: ['c'] });
  expect(warn).toHaveBeenCalled();
});

test('dataset response parser exposes old column, cell and config properties', () => {
  const { DatasetResponseHandler } = require('../datasets/dataset');
  const { Routes } = require('../utils/routes');
  const warn = jest.spyOn(process, 'emitWarning').mockImplementation(() => undefined);
  const parsed = DatasetResponseHandler._parseSuccess({ config: { url: '/d/get-dataset-table/' }, data: { result: {
    column_config: [{ id: 'c', name: 'C', data_type: 'text', source_id: 's' }],
    table: [{ row_id: 'r', c: { cell_value: 'value', failure_reason: 'reason' } }],
  } } });
  expect(warn).not.toHaveBeenCalled();
  expect(parsed.columns[0].dataType).toBe('text');
  expect(parsed.columns[0].sourceId).toBe('s');
  expect(parsed.rows[0].cells[0].columnId).toBe('c');
  expect(parsed.rows[0].cells[0].failureReason).toBe('reason');
  const config = DatasetResponseHandler._parseSuccess({ config: { url: Routes.dataset_names }, data: { result: { datasets: [{ dataset_id: 'd', name: 'D', model_type: 'GenerativeLLM' }] } } });
  expect(config.modelType).toBe('GenerativeLLM');
});

test.each(['kbId', 'kbName', 'fileIds', 'notUploaded', 'tableData', 'lastError'])
  ('KB response %s accepts legacy data and exposes canonical data', async old => {
    const { KnowledgeBase } = require('../kb/client');
    const { Routes } = require('../utils/routes');
    const client = new KnowledgeBase(undefined, { fiApiKey: 'test', fiSecretKey: 'test', fiBaseUrl: 'http://localhost' });
    const warn = jest.spyOn(process, 'emitWarning').mockImplementation(() => undefined);
    const modern = modernName(old);
    const value = old === 'tableData' ? [{ id: 'k', name: 'K' }] : old === 'fileIds' || old === 'notUploaded' ? ['file'] : 'value';
    let handler: any;
    jest.spyOn(client, 'request').mockImplementation(async (_config: unknown, responseHandler: any) => {
      handler = responseHandler;
      return { result: { table_data: [] } };
    });
    await client.listKbs();
    for (const legacy of [false, true]) {
      const payload = { [legacy ? old : modern]: value };
      const list = old === 'tableData' || old === 'lastError';
      const result = handler._parseSuccess({ config: { method: list ? 'GET' : 'POST', url: Routes.knowledge_base },
        data: { result: old === 'lastError' ? { table_data: [{ id: 'k', name: 'K', ...payload }] } : payload } });
      const row = old === 'lastError' ? result.result.table_data[0] : list ? result.result : result;
      expect(row[modern]).toEqual(value);
      if (!legacy) expect(warn).not.toHaveBeenCalled();
      expect(row[old]).toEqual(value);
      expect(row[old]).toEqual(value);
    }
    expect(warn).toHaveBeenCalledTimes(1);
    expect(warn.mock.calls[0][0]).toContain(modern);
  });

test('dataset constructor and Hugging Face input retain legacy config aliases', async () => {
  const { Dataset } = require('../datasets/dataset');
  const warn = jest.spyOn(process, 'emitWarning').mockImplementation(() => undefined);
  const client = new Dataset({ fiApiKey: 'test', fiSecretKey: 'test', fiBaseUrl: 'http://localhost',
    datasetConfig: { name: 'D', modelType: 'GenerativeLLM', columnOrder: ['c'] } });
  const request = jest.spyOn(client, 'request').mockResolvedValue({ id: 'd', name: 'D', model_type: 'GenerativeLLM' });
  expect(client.getConfig().model_type).toBe('GenerativeLLM');
  expect(client.getConfig().column_order).toEqual(['c']);
  await client.create({ name: 'remote-fixture', numRows: 7 });
  expect(request.mock.calls[0][0]).toMatchObject({ json: { model_type: 'GenerativeLLM', num_rows: 7 } });
  expect(warn.mock.calls.map((call: any[]) => call[0]).join(' ')).toContain('num_rows');
});

test.each(['addLabel', 'removeLabel'])('%s preserves published positional ids and timeout', async method => {
  const { AnnotationQueue } = require('../queues/client');
  const client = new AnnotationQueue({ fiApiKey: 'test', fiSecretKey: 'test', fiBaseUrl: 'http://localhost' });
  const request = jest.spyOn(client, 'request').mockResolvedValue({ ok: true });
  await expect(client[method]('q', 'l', { timeout: 123 })).resolves.toEqual({ ok: true });
  expect(request).toHaveBeenCalledTimes(1);
  expect(request.mock.calls[0][0]).toMatchObject({ timeout: 123 });
  expect(JSON.stringify(request.mock.calls[0][0])).toContain('q');
  expect(JSON.stringify(request.mock.calls[0][0])).toContain('l');
});
