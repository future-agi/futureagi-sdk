import axios, { AxiosAdapter } from 'axios';
import fs from 'fs';
import os from 'os';
import path from 'path';
import { Dataset } from '../datasets/dataset';
import { DatasetTable } from '../datasets/types';
import { DatasetError } from '../utils/errors';

function page(start: number, count: number, metadata?: Record<string, unknown>) {
    return { result: {
        column_config: [{ id: 'question', name: 'Question', data_type: 'text', origin_type: 'others' }],
        table: Array.from({ length: count }, (_, index) => ({
            row_id: `row-${start + index}`, order: start + index,
            question: { cell_value: `Question ${start + index}` },
        })),
        metadata,
    } };
}

describe('legacy dataset download pagination', () => {
    const originalAdapter = axios.defaults.adapter;
    let adapter: jest.MockedFunction<AxiosAdapter>;
    let ds: Dataset;
    let directory: string;
    let pages: Record<number, ReturnType<typeof page>>;

    beforeEach(() => {
        directory = fs.mkdtempSync(path.join(os.tmpdir(), 'sdk-download-pages-'));
        pages = {
            0: page(0, 500, { has_more: true, next_page_index: 1 }),
            1: page(500, 1, { has_more: false, next_page_index: null }),
        };
        adapter = jest.fn(async config => {
            const index = config.params.current_page_index as number;
            if (!(index in pages)) throw new Error(`Unexpected page ${index}`);
            return { status: 200, statusText: 'OK', headers: {}, config, data: pages[index] };
        });
        axios.defaults.adapter = adapter;
        ds = new Dataset({
            fiApiKey: 'synthetic-api-key', fiSecretKey: 'synthetic-secret-key',
            fiBaseUrl: 'https://sdk.invalid', retryAttempts: 1,
            datasetConfig: { id: 'synthetic-dataset', name: 'questions' },
        });
    });

    afterEach(async () => {
        await ds.close();
        axios.defaults.adapter = originalAdapter;
        fs.rmSync(directory, { recursive: true, force: true });
    });

    it('loads all 501 rows rather than the first server page', async () => {
        const table = await ds.download(undefined, true) as DatasetTable;
        expect(table.rows).toHaveLength(501);
        expect(table.rows.map(row => row.cells[0].value)).toEqual(Array.from({ length: 501 }, (_, i) => `Question ${i}`));
        expect(table.metadata).toMatchObject({ has_more: false, next_page_index: null });
        expect(adapter.mock.calls.map(([config]) => config.params.current_page_index)).toEqual([0, 1]);
    });

    it('writes every page to CSV and keeps the chainable return', async () => {
        const output = path.join(directory, 'all.csv');
        expect(await ds.download(output)).toBe(ds);
        const lines = fs.readFileSync(output, 'utf8').trim().split('\n');
        expect(lines).toHaveLength(502);
        expect(lines[0]).toBe('Question');
        expect(lines[501]).toBe('Question 500');
        expect(adapter).toHaveBeenCalledTimes(2);
    });

    it('uses the advertised next index through more than two pages', async () => {
        pages = {
            0: page(0, 1, { has_more: true, next_page_index: 2 }),
            2: page(1, 1, { has_more: true, next_page_index: 4 }),
            4: page(2, 1, { has_more: false }),
        };
        const table = await ds.download(undefined, true) as DatasetTable;
        expect(table.rows.map(row => row.cells[0].value)).toEqual(['Question 0', 'Question 1', 'Question 2']);
        expect(adapter.mock.calls.map(([config]) => config.params.current_page_index)).toEqual([0, 2, 4]);
    });

    it.each([undefined, { has_more: false }])('keeps one-page and empty responses compatible (%j)', async metadata => {
        pages = { 0: page(0, 0, metadata) };
        const table = await ds.download(undefined, true) as DatasetTable;
        expect(table.rows).toEqual([]);
        expect(adapter).toHaveBeenCalledTimes(1);
    });

    it.each([undefined, null, 0, -1, 0.5, '1'])('rejects invalid continuation %p without writing a partial file', async next => {
        pages = { 0: page(0, 1, { has_more: true, next_page_index: next }) };
        const output = path.join(directory, 'partial.csv');
        await expect(ds.download(output)).rejects.toBeInstanceOf(DatasetError);
        expect(fs.existsSync(output)).toBe(false);
        expect(adapter).toHaveBeenCalledTimes(1);
    });

    it('rejects a backwards continuation instead of looping', async () => {
        pages[1] = page(500, 1, { has_more: true, next_page_index: 0 });
        await expect(ds.download(undefined, true)).rejects.toBeInstanceOf(DatasetError);
        expect(adapter).toHaveBeenCalledTimes(2);
    });

    it('does not overwrite an existing export when a later page fails', async () => {
        const output = path.join(directory, 'all.csv');
        fs.writeFileSync(output, 'previous export');
        const failure = new DatasetError('Later page unavailable');
        const normal = adapter.getMockImplementation()!;
        adapter.mockImplementation(async config => {
            if (config.params.current_page_index === 1) throw failure;
            return normal(config);
        });
        await expect(ds.download(output)).rejects.toBe(failure);
        expect(fs.readFileSync(output, 'utf8')).toBe('previous export');
    });

    it('does not report an explicitly incomplete last page as a completed export', async () => {
        pages = { 0: page(0, 1, { has_more: false, query_complete: false }) };
        await expect(ds.download(undefined, true)).rejects.toBeInstanceOf(DatasetError);
    });
});
