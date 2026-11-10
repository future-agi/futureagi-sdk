import axios, { AxiosAdapter, AxiosError } from 'axios';
import { Readable } from 'stream';
import { HttpClient, ResponseHandler } from '../api/auth';
import { HttpMethod } from '../api/types';
import { Annotation } from '../annotations/annotation';
import { SDKException } from '../utils/errors';

const writes = [HttpMethod.POST, HttpMethod.PATCH, HttpMethod.PUT, HttpMethod.DELETE];
const failures = ['timeout', 'post-send reset', 'HTTP 500', 'HTTP 503'] as const;
type Failure = typeof failures[number];

function ambiguousFailure(failure: Failure): jest.MockedFunction<AxiosAdapter> {
    return jest.fn(async config => {
        // The request has been sent; its response may have been lost after the write.
        const request = { socket: { bytesWritten: 128 } };
        if (failure === 'timeout' || failure === 'post-send reset') {
            throw new AxiosError(
                'Synthetic ambiguous transport failure',
                failure === 'timeout' ? 'ECONNABORTED' : 'ECONNRESET',
                config,
                request
            );
        }
        return {
            status: failure === 'HTTP 500' ? 500 : 503,
            statusText: 'Synthetic failure', headers: {}, config,
            data: { detail: 'Synthetic ambiguous server failure' }
        };
    });
}

describe('legacy write retry safety', () => {
    const originalAdapter = axios.defaults.adapter;
    const savedExtraHeaders = process.env.FI_EXTRA_HEADERS;
    let client: HttpClient | undefined;

    beforeEach(() => {
        delete process.env.FI_EXTRA_HEADERS;
    });

    afterEach(async () => {
        await client?.close();
        client = undefined;
        axios.defaults.adapter = originalAdapter;
        jest.restoreAllMocks();
        if (savedExtraHeaders === undefined) delete process.env.FI_EXTRA_HEADERS;
        else process.env.FI_EXTRA_HEADERS = savedExtraHeaders;
    });

    describe.each(writes)('%s', method => {
        it.each(failures)('does not replay a write after %s', async failure => {
            const adapter = ambiguousFailure(failure);
            axios.defaults.adapter = adapter;
            client = new HttpClient({ baseUrl: 'https://sdk.invalid', retryAttempts: 3 });
            const sleep = jest.spyOn(client as any, '_sleep').mockResolvedValue(undefined);

            await expect(client.request({
                method, url: '/records', json: { value: 'synthetic record' }
            })).rejects.toBeInstanceOf(Error);

            expect(adapter).toHaveBeenCalledTimes(1);
            expect(sleep).not.toHaveBeenCalled();
        });

        it.each(['ECONNREFUSED', 'ENOTFOUND', 'EAI_AGAIN'])(
            'can retry a connection failure before send (%s)', async code => {
                let attempts = 0;
                const adapter: jest.MockedFunction<AxiosAdapter> = jest.fn(async config => {
                    if (++attempts === 1) {
                        throw new AxiosError('Synthetic connection failure before send', code, config);
                    }
                    return { status: 200, statusText: 'OK', headers: {}, config, data: { accepted: true } };
                });
                axios.defaults.adapter = adapter;
                client = new HttpClient({ baseUrl: 'https://sdk.invalid', retryAttempts: 3, retryDelay: 7 });
                const sleep = jest.spyOn(client as any, '_sleep').mockResolvedValue(undefined);

                await expect(client.request({
                    method, url: '/records', json: { value: 'synthetic record' }
                })).resolves.toMatchObject({ status: 200 });

                expect(adapter).toHaveBeenCalledTimes(2);
                expect(sleep).toHaveBeenCalledTimes(1);
                expect(sleep).toHaveBeenCalledWith(7);
            }
        );
    });

    it.each(failures)('preserves bounded GET retries after %s', async failure => {
        const adapter = ambiguousFailure(failure);
        axios.defaults.adapter = adapter;
        client = new HttpClient({ baseUrl: 'https://sdk.invalid', retryAttempts: 3, retryDelay: 7 });
        const sleep = jest.spyOn(client as any, '_sleep').mockResolvedValue(undefined);

        await expect(client.request({ method: HttpMethod.GET, url: '/records' }))
            .rejects.toBeInstanceOf(Error);

        expect(adapter).toHaveBeenCalledTimes(3);
        expect(sleep.mock.calls).toEqual([[7], [14]]);
    });

    describe.each(['HEAD' as HttpMethod, 'OPTIONS' as HttpMethod])('%s', method => {
        it.each(failures)('preserves bounded retries after %s', async failure => {
            const adapter = ambiguousFailure(failure);
            axios.defaults.adapter = adapter;
            client = new HttpClient({ baseUrl: 'https://sdk.invalid', retryAttempts: 3, retryDelay: 7 });
            const sleep = jest.spyOn(client as any, '_sleep').mockResolvedValue(undefined);

            await expect(client.request({ method, url: '/records' })).rejects.toBeInstanceOf(Error);
            expect(adapter).toHaveBeenCalledTimes(3);
            expect(sleep.mock.calls).toEqual([[7], [14]]);
        });
    });

    describe.each([HttpMethod.GET, ...writes])('%s HTTP responses', method => {
        it.each([400, 401, 403, 404, 422])('does not retry permanent HTTP %i errors', async status => {
            const adapter: jest.MockedFunction<AxiosAdapter> = jest.fn(async config => ({
                status, statusText: 'Synthetic permanent failure', headers: {}, config, data: {}
            }));
            axios.defaults.adapter = adapter;
            client = new HttpClient({ baseUrl: 'https://sdk.invalid' });
            const sleep = jest.spyOn(client as any, '_sleep').mockResolvedValue(undefined);

            await expect(client.request({ method, url: '/records' })).rejects.toBeInstanceOf(Error);
            expect(adapter).toHaveBeenCalledTimes(1);
            expect(sleep).not.toHaveBeenCalled();
        });

        it.each([408, 429, 502, 504])('only retries a read after HTTP %i', async status => {
            const adapter: jest.MockedFunction<AxiosAdapter> = jest.fn(async config => {
                throw new AxiosError('Synthetic HTTP failure', AxiosError.ERR_BAD_RESPONSE, config, undefined, {
                    status, statusText: 'Synthetic transient failure', headers: {}, config, data: {}
                });
            });
            axios.defaults.adapter = adapter;
            client = new HttpClient({ baseUrl: 'https://sdk.invalid', retryAttempts: 3, retryDelay: 7 });
            const sleep = jest.spyOn(client as any, '_sleep').mockResolvedValue(undefined);

            await expect(client.request({ method, url: '/records' })).rejects.toBeInstanceOf(Error);
            expect(adapter).toHaveBeenCalledTimes(method === HttpMethod.GET ? 3 : 1);
            expect(sleep.mock.calls).toEqual(method === HttpMethod.GET ? [[7], [14]] : []);
        });
    });

    it.each([undefined, AxiosError.ERR_CANCELED, AxiosError.ERR_BAD_OPTION_VALUE, 'ERR_INVALID_URL'])(
        'does not retry a GET with an unknown or permanent error (%s)', async code => {
            const adapter: jest.MockedFunction<AxiosAdapter> = jest.fn(async config => {
                if (code === undefined) throw new Error('Synthetic parser or interceptor error');
                throw new AxiosError('Synthetic non-transient failure', code, config);
            });
            axios.defaults.adapter = adapter;
            client = new HttpClient({ baseUrl: 'https://sdk.invalid' });
            const sleep = jest.spyOn(client as any, '_sleep').mockResolvedValue(undefined);

            await expect(client.request({ method: HttpMethod.GET, url: '/records' })).rejects.toBeInstanceOf(Error);
            expect(adapter).toHaveBeenCalledTimes(1);
            expect(sleep).not.toHaveBeenCalled();
        }
    );

    it.each(['ECONNREFUSED', 'ENOTFOUND', 'EAI_AGAIN'])('bounds persistent pre-send %s retries', async code => {
        const adapter: jest.MockedFunction<AxiosAdapter> = jest.fn(async config => {
            throw new AxiosError('Synthetic pre-send failure', code, config);
        });
        axios.defaults.adapter = adapter;
        client = new HttpClient({ baseUrl: 'https://sdk.invalid' });
        const sleep = jest.spyOn(client as any, '_sleep').mockResolvedValue(undefined);

        await expect(client.request({
            method: HttpMethod.POST, url: '/records', retry_attempts: 2, retry_delay: 7
        })).rejects.toBeInstanceOf(Error);
        expect(adapter).toHaveBeenCalledTimes(2);
        expect(sleep.mock.calls).toEqual([[7]]);
    });

    it.each(['ECONNREFUSED', 'ENOTFOUND', 'EAI_AGAIN'])('never replays a POST after a redirect then %s', async code => {
        const adapter: jest.MockedFunction<AxiosAdapter> = jest.fn(async config => {
            config.beforeRedirect!({
                href: 'https://sdk.invalid/redirected', headers: {}
            }, { statusCode: 307, headers: { location: '/redirected' } });
            throw new AxiosError('Synthetic failure on the redirected connection', code, config);
        });
        axios.defaults.adapter = adapter;
        client = new HttpClient({ baseUrl: 'https://sdk.invalid' });
        const sleep = jest.spyOn(client as any, '_sleep').mockResolvedValue(undefined);

        await expect(client.request({ method: HttpMethod.POST, url: '/records' })).rejects.toBeInstanceOf(Error);
        expect(adapter).toHaveBeenCalledTimes(1);
        expect(sleep).not.toHaveBeenCalled();
    });

    it('does not mistake a response-handler failure for a pre-send failure', async () => {
        class FailingHandler extends ResponseHandler {
            static _parseSuccess(): never {
                throw new AxiosError('Synthetic handler failure', 'ENOTFOUND');
            }
        }
        const adapter: jest.MockedFunction<AxiosAdapter> = jest.fn(async config => ({
            status: 200, statusText: 'OK', headers: {}, config, data: {}
        }));
        axios.defaults.adapter = adapter;
        client = new HttpClient({ baseUrl: 'https://sdk.invalid' });
        const sleep = jest.spyOn(client as any, '_sleep').mockResolvedValue(undefined);

        await expect(client.request({ method: HttpMethod.POST, url: '/records' }, FailingHandler))
            .rejects.toBeInstanceOf(Error);
        expect(adapter).toHaveBeenCalledTimes(1);
        expect(sleep).not.toHaveBeenCalled();
    });

    it('keeps a one-shot multipart body single-attempt even for a pre-send failure', async () => {
        const adapter: jest.MockedFunction<AxiosAdapter> = jest.fn(async config => {
            throw new AxiosError('Synthetic pre-send failure', 'ECONNREFUSED', config);
        });
        axios.defaults.adapter = adapter;
        client = new HttpClient({ baseUrl: 'https://sdk.invalid' });
        const sleep = jest.spyOn(client as any, '_sleep').mockResolvedValue(undefined);

        await expect(client.request({
            method: HttpMethod.POST, url: '/upload', files: { file0: Readable.from(['synthetic data']) }
        })).rejects.toBeInstanceOf(Error);
        expect(adapter).toHaveBeenCalledTimes(1);
        expect(sleep).not.toHaveBeenCalled();
    });

    it.each(failures)('does not duplicate bulk annotations after %s', async failure => {
        const adapter = ambiguousFailure(failure);
        axios.defaults.adapter = adapter;
        const annotations = new Annotation({
            fiApiKey: 'synthetic-api-key',
            fiSecretKey: 'synthetic-secret-key',
            fiBaseUrl: 'https://sdk.invalid'
        });
        client = annotations;
        const sleep = jest.spyOn(annotations as any, '_sleep').mockResolvedValue(undefined);
        jest.spyOn(console, 'log').mockImplementation(() => undefined);

        await expect(annotations.logAnnotations([{
            'context.span_id': 'synthetic-span',
            'annotation.notes': 'Synthetic annotation note'
        }])).rejects.toBeInstanceOf(SDKException);

        expect(adapter).toHaveBeenCalledTimes(1);
        expect(sleep).not.toHaveBeenCalled();
        const sent = adapter.mock.calls[0][0];
        expect(sent.method).toBe('post');
        expect(sent.url).toBe('https://sdk.invalid/tracer/bulk-annotation/');
        expect(JSON.parse(sent.data)).toEqual({ records: [{
            observation_span_id: 'synthetic-span', annotations: [],
            notes: [{ text: 'Synthetic annotation note' }]
        }] });
    });
});
