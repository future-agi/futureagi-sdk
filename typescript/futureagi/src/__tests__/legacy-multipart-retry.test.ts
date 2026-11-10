import axios, { AxiosAdapter, AxiosError, AxiosResponse } from 'axios';
import fs from 'fs';
import os from 'os';
import path from 'path';
import { Readable, Writable } from 'stream';
import { HttpClient } from '../api/auth';
import { HttpMethod } from '../api/types';
import { KnowledgeBase } from '../kb/client';
import { SDKException, ServiceUnavailableError } from '../utils/errors';

/** Consume the upload just as a transport would, without opening a connection. */
async function consumeBody(body: any): Promise<Buffer> {
    if (typeof body.pipe !== 'function') {
        return Buffer.from(await new Response(body).arrayBuffer());
    }
    return new Promise((resolve, reject) => {
        const chunks: Buffer[] = [];
        const sink = new Writable({
            write(chunk, _encoding, done) {
                chunks.push(Buffer.from(chunk));
                done();
            }
        });
        body.once('error', reject);
        sink.once('error', reject);
        sink.once('finish', () => resolve(Buffer.concat(chunks)));
        body.pipe(sink);
    });
}

describe('legacy multipart retry safety', () => {
    const originalAdapter = axios.defaults.adapter;
    const contents = Buffer.from('Synthetic upload: café.\n\x00\xff', 'utf8');
    let client: HttpClient | undefined;
    let directory: string;
    let filePath: string;
    let streams: fs.ReadStream[];

    beforeEach(() => {
        directory = fs.mkdtempSync(path.join(os.tmpdir(), 'sdk-upload-retry-'));
        filePath = path.join(directory, 'notes.txt');
        fs.writeFileSync(filePath, contents);
        streams = [];
        const createReadStream = fs.createReadStream;
        jest.spyOn(fs, 'createReadStream').mockImplementation((...args) => {
            const stream = createReadStream(...args);
            streams.push(stream);
            return stream;
        });
    });

    afterEach(async () => {
        await client?.close();
        client = undefined;
        await Promise.all(streams.map(stream => new Promise<void>(resolve => {
            if (stream.closed) return resolve();
            stream.once('close', resolve);
            stream.destroy();
        })));
        axios.defaults.adapter = originalAdapter;
        jest.restoreAllMocks();
        fs.rmSync(directory, { recursive: true, force: true });
    });

    it.each([
        ['create', 503], ['update', 503], ['create', 500], ['update', 500]
    ] as const)('%s surfaces HTTP %i after consuming the upload without a retry or backoff', async (operation, status) => {
        let uploaded: Buffer | undefined;
        let requests = 0;
        const adapter: jest.MockedFunction<AxiosAdapter> = jest.fn(async config => {
            requests += 1;
            // Only consume the first body: attempting to pipe the exhausted form again
            // would hang. Count any retry, but let the regression fail without a timeout.
            if (requests === 1) uploaded = await consumeBody(config.data);
            return { status, statusText: 'Upload failed', headers: {}, config, data: { detail: 'Synthetic upload failure' } };
        });
        axios.defaults.adapter = adapter;
        const kb = new KnowledgeBase(undefined, {
            fiApiKey: 'synthetic-api-key',
            fiSecretKey: 'synthetic-secret-key',
            fiBaseUrl: 'https://sdk.invalid'
        });
        client = kb;
        kb.kb = { id: 'synthetic-kb', name: 'docs', files: [] };
        const sleep = jest.spyOn(kb as any, '_sleep').mockResolvedValue(undefined);
        const request = operation === 'create'
            ? kb.createKb('docs', [filePath])
            : kb.updateKb({ kbName: 'docs', newName: 'renamed', filePaths: [filePath] });
        const error = await request.then(() => undefined, failure => failure);

        expect(uploaded?.includes(contents)).toBe(true);
        expect(uploaded?.toString()).toContain('name="file0"; filename="notes.txt"');
        expect(uploaded?.toString()).toContain(`name="name"\r\n\r\n${operation === 'create' ? 'docs' : 'renamed'}\r\n`);
        if (operation === 'update') {
            expect(uploaded?.toString()).toContain('name="kb_id"\r\n\r\nsynthetic-kb\r\n');
        }
        expect(error).toBeInstanceOf(SDKException);
        expect(error.message).toBe('Synthetic upload failure');
        expect(adapter).toHaveBeenCalledTimes(1);
        expect(sleep).not.toHaveBeenCalled();
        expect(kb.kb).toEqual({ id: 'synthetic-kb', name: 'docs', files: [] });
    });

    it.each(['response', 'axios rejection', 'transport rejection'])('does not replay an arbitrary stream after a %s', async failureMode => {
        let uploaded: Buffer | undefined;
        let requests = 0;
        const originalError = new Error('Synthetic transport failure');
        const adapter: jest.MockedFunction<AxiosAdapter> = jest.fn(async config => {
            requests += 1;
            if (requests === 1) uploaded = await consumeBody(config.data);
            const response: AxiosResponse = {
                status: 503, statusText: 'Unavailable', headers: {}, config,
                data: { detail: 'Synthetic unavailable response' }
            };
            if (failureMode === 'axios rejection') {
                throw new AxiosError('Request failed with status code 503', AxiosError.ERR_BAD_RESPONSE, config, undefined, response);
            }
            if (failureMode === 'transport rejection') throw originalError;
            return response;
        });
        axios.defaults.adapter = adapter;
        client = new HttpClient({ baseUrl: 'https://sdk.invalid', retryAttempts: 3 });
        const sleep = jest.spyOn(client as any, '_sleep').mockResolvedValue(undefined);
        const error = await client.request({
            method: HttpMethod.POST,
            url: '/upload',
            files: { file0: Readable.from([contents]) },
            data: { name: 'docs' },
            retry_attempts: 5
        }).then(() => undefined, failure => failure);

        expect(uploaded?.includes(contents)).toBe(true);
        if (failureMode === 'transport rejection') {
            expect(error).toBe(originalError);
        } else {
            expect(error).toBeInstanceOf(ServiceUnavailableError);
            expect(error.message).toBe('Synthetic unavailable response');
        }
        expect(adapter).toHaveBeenCalledTimes(1);
        expect(sleep).not.toHaveBeenCalled();
    });

    it.each(['json', 'blob', 'text'])('sends the full %s body once without replaying POST after HTTP 503', async kind => {
        const bodies: Buffer[] = [];
        const text = 'Synthetic replayable content.';
        const adapter: jest.MockedFunction<AxiosAdapter> = jest.fn(async config => {
            bodies.push(await consumeBody(config.data));
            return {
                status: bodies.length === 1 ? 503 : 200,
                statusText: bodies.length === 1 ? 'Unavailable' : 'OK',
                headers: {}, config, data: { accepted: true }
            };
        });
        axios.defaults.adapter = adapter;
        client = new HttpClient({ baseUrl: 'https://sdk.invalid', retryAttempts: 2, retryDelay: 1 });
        const sleep = jest.spyOn(client as any, '_sleep').mockResolvedValue(undefined);
        await expect(client.request({
            method: HttpMethod.POST,
            url: '/upload',
            ...(kind === 'json'
                ? { json: { name: text } }
                : { files: { file0: kind === 'blob' ? new Blob([text]) : text }, data: { name: 'docs' } })
        })).rejects.toBeInstanceOf(ServiceUnavailableError);

        expect(adapter).toHaveBeenCalledTimes(1);
        expect(sleep).not.toHaveBeenCalled();
        for (const body of bodies) {
            if (kind === 'json') expect(JSON.parse(body.toString())).toEqual({ name: text });
            else {
                expect(body.includes(Buffer.from(text))).toBe(true);
                expect(body.toString()).toContain('name="file0"');
                expect(body.toString()).toContain('name="name"\r\n\r\ndocs\r\n');
            }
        }
    });
});
