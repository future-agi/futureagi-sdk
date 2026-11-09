import axios, { AxiosAdapter, AxiosRequestConfig } from 'axios';
import fs from 'fs';
import os from 'os';
import path from 'path';
import { Writable } from 'stream';
import { KnowledgeBase } from '../kb/client';
import { SDKException } from '../utils/errors';

async function serialize(body: any): Promise<Buffer> {
    if (typeof body.pipe !== 'function') return Buffer.from(await new Response(body).arrayBuffer());
    return new Promise((resolve, reject) => {
        const chunks: Buffer[] = [];
        const sink = new Writable({ write(chunk, _encoding, done) { chunks.push(Buffer.from(chunk)); done(); } });
        body.on('error', reject);
        sink.on('error', reject);
        sink.on('finish', () => resolve(Buffer.concat(chunks)));
        body.pipe(sink);
    });
}

describe('knowledge-base server multipart field contract', () => {
    const originalAdapter = axios.defaults.adapter;
    const createReadStream = fs.createReadStream;
    const bytes = [Buffer.from('Synthetic notes: café.\n'), Buffer.from([0x25, 0x50, 0x44, 0x46, 0x00, 0x80, 0xff])];
    let directory: string;
    let files: string[];
    let streams: fs.ReadStream[];
    let kb: KnowledgeBase;
    let requests: Array<{ config: AxiosRequestConfig; body: Buffer }>;
    let adapter: jest.MockedFunction<AxiosAdapter>;

    beforeEach(() => {
        directory = fs.mkdtempSync(path.join(os.tmpdir(), 'sdk-kb-fields-'));
        files = [path.join(directory, 'notes.txt'), path.join(directory, 'document.pdf')];
        files.forEach((file, index) => fs.writeFileSync(file, bytes[index]));
        streams = [];
        requests = [];
        jest.spyOn(fs, 'createReadStream').mockImplementation((...args) => {
            const stream = createReadStream(...args);
            streams.push(stream);
            return stream;
        });
        adapter = jest.fn(async config => {
            requests.push({ config, body: await serialize(config.data) });
            return { status: 200, statusText: 'OK', headers: {}, config, data: { result: {
                kb_id: 'synthetic-kb', kb_name: 'docs', file_ids: ['one', 'two'],
                id: 'synthetic-kb', name: 'renamed', files: ['one', 'two'],
            } } };
        });
        axios.defaults.adapter = adapter;
        kb = new KnowledgeBase(undefined, { fiApiKey: 'synthetic-api-key', fiSecretKey: 'synthetic-secret-key', fiBaseUrl: 'https://sdk.invalid' });
    });

    afterEach(async () => {
        await kb.close();
        await Promise.all(streams.map(stream => new Promise<void>(resolve => {
            if (stream.closed) return resolve();
            stream.once('close', resolve);
            stream.destroy();
        })));
        axios.defaults.adapter = originalAdapter;
        jest.restoreAllMocks();
        fs.rmSync(directory, { recursive: true, force: true });
    });

    function expectFiles(count: number, fields: Record<string, string>) {
        expect(adapter).toHaveBeenCalledTimes(1);
        const { body, config } = requests[0];
        const text = body.toString('latin1');
        const names = [...text.matchAll(/name="([^"]+)"; filename="([^"]+)"/g)];
        expect(names.map(match => match[1])).toEqual(Array(count).fill('file'));
        expect(names.map(match => match[2])).toEqual(files.slice(0, count).map(file => path.basename(file)));
        for (const data of bytes.slice(0, count)) {
            expect(body.includes(Buffer.concat([Buffer.from('\r\n\r\n'), data, Buffer.from('\r\n')]))).toBe(true);
        }
        for (const [name, value] of Object.entries(fields)) expect(text).toContain(`name="${name}"\r\n\r\n${value}\r\n`);
        const contentType = String(config.headers?.['Content-Type']);
        expect(contentType).toMatch(/^multipart\/form-data;\s*boundary=/i);
        const boundary = /boundary=(?:"([^"]+)"|([^;]+))/i.exec(contentType)!;
        const marker = boundary[1] || boundary[2];
        expect(text.startsWith(`--${marker}\r\n`)).toBe(true);
        expect(text).toContain(`\r\n--${marker}--\r\n`);
    }

    it.each([1, 2])('creates with %i repeated file parts containing actual bytes', async count => {
        await kb.createKb('docs', files.slice(0, count));
        expectFiles(count, { name: 'docs' });
        expect(requests[0].config.method).toBe('post');
        expect(kb.kb?.id).toBe('synthetic-kb');
    });

    it.each([1, 2])('updates with %i repeated file parts and the selected id', async count => {
        kb.kb = { id: 'synthetic-kb', name: 'docs', files: [] };
        await kb.updateKb({ kbName: 'docs', newName: 'renamed', filePaths: files.slice(0, count) });
        expectFiles(count, { name: 'renamed', kb_id: 'synthetic-kb' });
        expect(requests[0].config.method).toBe('patch');
    });

    it('keeps requests without files as JSON', async () => {
        await kb.createKb('empty');
        expect(adapter).toHaveBeenCalledTimes(1);
        expect(requests[0].config.headers?.['Content-Type']).toBe('application/json');
        expect(JSON.parse(requests[0].body.toString())).toEqual({ name: 'empty' });
    });

    it('does not retry a consumed multipart body after a transport failure', async () => {
        const failure = new SDKException('synthetic transport failure');
        adapter.mockImplementation(async config => {
            requests.push({ config, body: await serialize(config.data) });
            throw failure;
        });
        await expect(kb.createKb('docs', files)).rejects.toBe(failure);
        expect(adapter).toHaveBeenCalledTimes(1);
        expect(requests[0].body.includes(bytes[0])).toBe(true);
    });
});
