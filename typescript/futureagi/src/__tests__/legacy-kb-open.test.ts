import { spawnSync } from 'child_process';
import { KnowledgeBase } from '../kb/client';
import { KnowledgeBaseOptions } from '../kb/types';
import { InvalidAuthError, SDKException } from '../utils/errors';

const auth = { fiApiKey: 'synthetic-api-key', fiSecretKey: 'synthetic-secret-key', fiBaseUrl: 'https://sdk.invalid' };
// The assertions compile on older releases so RED reflects behavior, not missing declarations.
type ReadyKnowledgeBase = KnowledgeBase & { ready: Promise<void> };
const open = (name: string) => (KnowledgeBase as typeof KnowledgeBase & {
    open(name: string, options?: KnowledgeBaseOptions): Promise<KnowledgeBase>;
}).open(name, auth);

describe('awaitable knowledge-base initialization', () => {
    afterEach(() => jest.restoreAllMocks());

    it('does not emit an unhandled rejection when a named constructor lookup fails', () => {
        const child = spawnSync(process.execPath, ['--unhandled-rejections=strict', '-e', `
            const fs = require('fs');
            const ts = require('typescript');
            require.extensions['.ts'] = (mod, filename) => {
                const source = ts.transpileModule(fs.readFileSync(filename, 'utf8'), {
                    compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2020, esModuleInterop: true }
                }).outputText;
                mod._compile(source, filename);
            };
            const { KnowledgeBase } = require(process.argv[1]);
            KnowledgeBase.prototype.request = async () => ({ result: { table_data: [] } });
            const kb = new KnowledgeBase('missing', ${JSON.stringify(auth)});
            setImmediate(async () => { await kb.close(); process.stdout.write('constructor survived'); });
        `, require.resolve('../kb/client')], { encoding: 'utf8', timeout: 15000 });
        expect(child.error).toBeUndefined();
        expect({ status: child.status, stderr: child.stderr }).toEqual({ status: 0, stderr: '' });
        expect(child.stdout).toBe('constructor survived');
    });

    it('exposes readiness and assigns the resolved knowledge base before it completes', async () => {
        let resolve!: (value: unknown) => void;
        jest.spyOn(KnowledgeBase.prototype, 'request').mockImplementation(() => new Promise(done => { resolve = done; }));
        const kb = new KnowledgeBase('docs', auth) as ReadyKnowledgeBase;
        try {
            expect(kb.ready).toBeInstanceOf(Promise);
            expect(kb.kb).toBeUndefined();
        } finally {
            resolve({ result: { table_data: [{ id: 'docs-id', name: 'docs', files: [] }] } });
            await kb.ready;
            await kb.close();
        }
        expect(kb.kb).toMatchObject({ id: 'docs-id', name: 'docs' });
    });

    it('opens a ready instance with one lookup', async () => {
        const request = jest.spyOn(KnowledgeBase.prototype, 'request').mockResolvedValue({ result: { table_data: [{ id: 'docs-id', name: 'docs' }] } });
        const kb = await open('docs');
        try {
            expect(kb.kb).toMatchObject({ id: 'docs-id', name: 'docs' });
            expect(request).toHaveBeenCalledTimes(1);
        } finally { await kb.close(); }
    });

    it.each([new InvalidAuthError(), new SDKException('lookup unavailable')])('preserves the original lookup failure (%s)', async failure => {
        jest.spyOn(KnowledgeBase.prototype, 'request').mockRejectedValue(failure);
        await expect(open('docs')).rejects.toBe(failure);
    });

    it('returns a missing-name failure through the factory promise', async () => {
        jest.spyOn(KnowledgeBase.prototype, 'request').mockResolvedValue({ result: { table_data: [] } });
        await expect(open('missing')).rejects.toThrow(/not found/i);
    });

    it('waits for named initialization before deleting the cached knowledge base', async () => {
        let resolve!: (value: unknown) => void;
        const request = jest.spyOn(KnowledgeBase.prototype, 'request')
            .mockImplementationOnce(() => new Promise(done => { resolve = done; }))
            .mockResolvedValue({});
        const kb = new KnowledgeBase('docs', auth);
        const deletion = kb.deleteKb();
        resolve({ result: { table_data: [{ id: 'docs-id', name: 'docs' }] } });
        try {
            await expect(deletion).resolves.toBe(kb);
            expect(request).toHaveBeenLastCalledWith(expect.objectContaining({ json: { kb_ids: ['docs-id'] } }), expect.anything());
            expect(kb.kb).toBeUndefined();
        } finally { await kb.close(); }
    });

    it('keeps unnamed construction ready without a lookup', async () => {
        const request = jest.spyOn(KnowledgeBase.prototype, 'request');
        const kb = new KnowledgeBase(undefined, auth) as ReadyKnowledgeBase;
        try {
            expect(kb.ready).toBeInstanceOf(Promise);
            await kb.ready;
            expect(request).not.toHaveBeenCalled();
        } finally { await kb.close(); }
    });
});
