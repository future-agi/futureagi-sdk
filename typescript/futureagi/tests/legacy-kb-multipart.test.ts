import axios, { AxiosAdapter, AxiosRequestConfig } from 'axios';
import fs from 'fs';
import os from 'os';
import path from 'path';
import { Writable } from 'stream';
import { KnowledgeBase } from '../src/kb/client';
import { HttpClient } from '../src/api/auth';
import { HttpMethod } from '../src/api/types';

/** Serialize the real request body without opening an HTTP connection. */
async function serializeBody(body: any): Promise<Buffer> {
    if (typeof body.pipe === 'function') {
        return new Promise((resolve, reject) => {
            const chunks: Buffer[] = [];
            const sink = new Writable({
                write(chunk, _encoding, done) {
                    chunks.push(Buffer.from(chunk));
                    done();
                }
            });
            body.on('error', reject);
            sink.on('error', reject);
            sink.on('finish', () => resolve(Buffer.concat(chunks)));
            body.pipe(sink);
        });
    }
    return Buffer.from(await new Response(body).arrayBuffer());
}

describe('legacy knowledge-base multipart uploads', () => {
    const originalAdapter = axios.defaults.adapter;
    const createReadStream = fs.createReadStream;
    const text = Buffer.from('Synthetic notes: café.\n');
    const binary = Buffer.from([0x25, 0x50, 0x44, 0x46, 0x00, 0x80, 0xff, 0x0a]);
    let directory: string;
    let files: string[];
    let client: KnowledgeBase | HttpClient;
    let streams: fs.ReadStream[];
    let requests: Array<{ config: AxiosRequestConfig; body: Buffer }>;
    let adapter: jest.MockedFunction<AxiosAdapter>;

    beforeEach(() => {
        directory = fs.mkdtempSync(path.join(os.tmpdir(), 'sdk-kb-upload-'));
        files = [path.join(directory, 'notes.txt'), path.join(directory, 'document.pdf')];
        fs.writeFileSync(files[0], text);
        fs.writeFileSync(files[1], binary);
        streams = [];
        requests = [];
        jest.spyOn(fs, 'createReadStream').mockImplementation((...args) => {
            const stream = createReadStream(...args);
            streams.push(stream);
            return stream;
        });
        adapter = jest.fn(async config => {
            requests.push({ config, body: await serializeBody(config.data) });
            return {
                status: 200,
                statusText: 'OK',
                headers: {},
                config,
                data: { result: {
                    kb_id: 'synthetic-kb', kb_name: 'docs', file_ids: ['file-1', 'file-2'],
                    id: 'synthetic-kb', name: 'renamed', files: ['file-1', 'file-2']
                } }
            };
        });
        axios.defaults.adapter = adapter;
        client = new KnowledgeBase(undefined, {
            fiApiKey: 'synthetic-api-key',
            fiSecretKey: 'synthetic-secret-key',
            fiBaseUrl: 'https://sdk.invalid'
        });
    });

    afterEach(async () => {
        await client.close();
        await Promise.all(streams.map(stream => new Promise<void>(resolve => {
            if (stream.closed) return resolve();
            stream.once('close', resolve);
            stream.destroy();
        })));
        axios.defaults.adapter = originalAdapter;
        jest.restoreAllMocks();
        fs.rmSync(directory, { recursive: true, force: true });
    });

    function expectMultipart(fields: Record<string, string>): void {
        expect(adapter).toHaveBeenCalledTimes(1);
        const { config, body } = requests[0];
        for (const [index, bytes] of [text, binary].entries()) {
            expect(body.toString('latin1')).toContain(`name="file${index}"; filename="${path.basename(files[index])}"`);
            expect(body.includes(Buffer.concat([Buffer.from('\r\n\r\n'), bytes, Buffer.from('\r\n')]))).toBe(true);
        }
        for (const [name, value] of Object.entries(fields)) {
            expect(body.toString()).toContain(`name="${name}"\r\n\r\n${value}\r\n`);
        }
        const contentType = String(config.headers?.['Content-Type']);
        expect(contentType).toMatch(/^multipart\/form-data;\s*boundary=/i);
        const boundary = /boundary=(?:"([^"]+)"|([^;]+))/i.exec(contentType);
        expect(boundary).not.toBeNull();
        const marker = boundary![1] || boundary![2];
        expect(body.subarray(0, marker.length + 4).toString()).toBe(`--${marker}\r\n`);
        expect(body.toString('latin1')).toContain(`\r\n--${marker}--\r\n`);
        expect(config.headers?.['X-Api-Key']).toBe('synthetic-api-key');
        expect(config.headers?.['X-Secret-Key']).toBe('synthetic-secret-key');
    }

    it('creates a knowledge base with the selected file bytes, filenames and matching boundary', async () => {
        const kb = client as KnowledgeBase;
        await kb.createKb('docs', files);
        expectMultipart({ name: 'docs' });
        expect(requests[0].config.method).toBe('post');
        expect(kb.kb?.id).toBe('synthetic-kb');
    });

    it('updates a knowledge base with the selected files and metadata', async () => {
        const kb = client as KnowledgeBase;
        kb.kb = { id: 'synthetic-kb', name: 'docs', files: [] };
        await kb.updateKb({ kbName: 'docs', newName: 'renamed', filePaths: files });
        expectMultipart({ name: 'renamed', kb_id: 'synthetic-kb' });
        expect(requests[0].config.method).toBe('patch');
        expect(kb.kb?.name).toBe('renamed');
    });

    it('keeps requests without files as JSON', async () => {
        await (client as KnowledgeBase).createKb('empty');
        expect(adapter).toHaveBeenCalledTimes(1);
        expect(requests[0].config.headers?.['Content-Type']).toBe('application/json');
        expect(JSON.parse(requests[0].body.toString())).toEqual({ name: 'empty' });
    });

    it('preserves custom headers while replacing a JSON content type for file uploads', async () => {
        await client.close();
        client = new HttpClient({ baseUrl: 'https://sdk.invalid', retryAttempts: 1 });
        await client.request({
            method: HttpMethod.POST,
            url: '/upload',
            files: { file0: fs.createReadStream(files[0]) },
            data: { name: 'docs' },
            headers: { 'Content-Type': 'application/json', 'X-Upload-Test': 'synthetic' }
        });
        expect(adapter).toHaveBeenCalledTimes(1);
        expect(requests[0].config.headers?.['X-Upload-Test']).toBe('synthetic');
        expect(requests[0].config.headers?.['Content-Type']).toMatch(/^multipart\/form-data;\s*boundary=/i);
        expect(requests[0].body.includes(text)).toBe(true);
    });
});
