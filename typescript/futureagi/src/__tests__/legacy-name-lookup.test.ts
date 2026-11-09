import axios, { AxiosAdapter } from 'axios';
import { Dataset } from '../datasets/dataset';
import { KnowledgeBase } from '../kb/client';
import { DatasetNotFoundError, SDKException } from '../utils/errors';

const auth = {
    fiApiKey: 'synthetic-api-key',
    fiSecretKey: 'synthetic-secret-key',
    fiBaseUrl: 'https://sdk.invalid',
    retryAttempts: 1,
};

const dataset = (name: string, id = name) => ({ name, dataset_id: id, model_type: 'generative_llm' });
const knowledgeBase = (name: string, id = name) => ({ name, id, files: [] });

describe('legacy exact-name lookup', () => {
    const originalAdapter = axios.defaults.adapter;
    let adapter: jest.MockedFunction<AxiosAdapter>;
    let matches: object[];
    let kb: KnowledgeBase;

    beforeEach(() => {
        matches = [];
        adapter = jest.fn(async config => {
            const data = config.method === 'get'
                ? { result: { datasets: matches, table_data: matches } }
                : config.method === 'post'
                    ? { result: { dataset_id: 'new-dataset', dataset_name: 'qa', dataset_model_type: 'generative_llm' } }
                    : { result: { id: 'exact', name: 'renamed', files: [] } };
            return { status: 200, statusText: 'OK', headers: {}, config, data };
        });
        axios.defaults.adapter = adapter;
        kb = new KnowledgeBase(undefined, auth);
    });

    afterEach(async () => {
        await kb.close();
        axios.defaults.adapter = originalAdapter;
    });

    it('creates the requested dataset instead of binding a substring hit', async () => {
        matches = [dataset('qa-prod')];
        const ds = await Dataset.open('qa', auth);
        try {
            expect(ds.getConfig()).toMatchObject({ id: 'new-dataset', name: 'qa' });
            const writes = adapter.mock.calls.map(([config]) => config).filter(config => config.method === 'post');
            expect(writes).toHaveLength(1);
            expect(JSON.parse(writes[0].data)).toMatchObject({ new_dataset_name: 'qa' });
        } finally { await ds.close(); }
    });

    it.each(['qa-prod', 'QA'])('rejects a non-exact dataset %s when creation is disabled', async name => {
        matches = [dataset(name)];
        await expect(Dataset.open('qa', { ...auth, createIfMissing: false })).rejects.toBeInstanceOf(DatasetNotFoundError);
        expect(adapter.mock.calls.every(([config]) => config.method === 'get')).toBe(true);
    });

    it('selects the exact dataset among substring matches', async () => {
        matches = [dataset('qa-prod'), dataset('qa', 'exact'), dataset('qa-stage')];
        const ds = await Dataset.open('qa', auth);
        try { expect(ds.getConfig()).toMatchObject({ id: 'exact', name: 'qa' }); }
        finally { await ds.close(); }
        expect(adapter).toHaveBeenCalledTimes(1);
    });

    it('keeps duplicate exact dataset names ambiguous without creating another', async () => {
        matches = [dataset('qa', 'one'), dataset('qa', 'two')];
        await expect(Dataset.open('qa', auth)).rejects.toThrow(/multiple/i);
        expect(adapter.mock.calls.every(([config]) => config.method === 'get')).toBe(true);
    });

    it.each(['docs-prod', 'DOCS'])('never renames a non-exact knowledge base %s', async name => {
        matches = [knowledgeBase(name)];
        await expect(kb.updateKb({ kbName: 'docs', newName: 'renamed' })).rejects.toBeInstanceOf(SDKException);
        expect(adapter.mock.calls.every(([config]) => config.method === 'get')).toBe(true);
    });

    it('selects the exact knowledge base rather than the first search hit', async () => {
        matches = [knowledgeBase('docs-prod'), knowledgeBase('docs', 'exact')];
        await kb.updateKb({ kbName: 'docs', newName: 'renamed' });
        const writes = adapter.mock.calls.map(([config]) => config).filter(config => config.method === 'patch');
        expect(writes).toHaveLength(1);
        expect(JSON.parse(writes[0].data)).toMatchObject({ kb_id: 'exact' });
    });

    it('rejects duplicate exact knowledge-base names before writing', async () => {
        matches = [knowledgeBase('docs', 'one'), knowledgeBase('docs', 'two')];
        await expect(kb.updateKb({ kbName: 'docs', newName: 'renamed' })).rejects.toThrow(/multiple|ambiguous/i);
        expect(adapter.mock.calls.every(([config]) => config.method === 'get')).toBe(true);
    });

    it('retains missing-name errors without writes', async () => {
        await expect(Dataset.open('qa', { ...auth, createIfMissing: false })).rejects.toBeInstanceOf(DatasetNotFoundError);
        await expect(kb.updateKb({ kbName: 'docs' })).rejects.toThrow(/not found/i);
        expect(adapter.mock.calls.every(([config]) => config.method === 'get')).toBe(true);
    });
});
