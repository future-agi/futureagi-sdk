import axios, { AxiosError, type InternalAxiosRequestConfig } from 'axios';
import { APIKeyAuth } from '../api/auth';
import { HttpMethod } from '../api/types';
import { KnowledgeBase } from '../kb/client';
import { Prompt } from '../prompt/client';
import { PromptTemplate } from '../prompt/types';
import { DEFAULT_SETTINGS, DEFAULT_TIMEOUT } from '../utils/constants';

const auth = {
  fiApiKey: 'synthetic-api-key',
  fiSecretKey: 'synthetic-secret-key',
  fiBaseUrl: 'https://api.example.test',
};
const createAxios = axios.create;

/** Drive a delayed in-memory response and its deadline without wall-clock waits or sockets. */
async function finish<T>(pending: Promise<T>) {
  const result = pending.then(value => ({ ok: true, value }), error => ({ ok: false, error }));
  await jest.runAllTimersAsync();
  return result;
}

describe('legacy request timeout defaults', () => {
  let payload: unknown;
  let calls: InternalAxiosRequestConfig[];
  const savedExtra = process.env.FI_EXTRA_HEADERS;

  beforeEach(() => {
    delete process.env.FI_EXTRA_HEADERS;
    jest.useFakeTimers();
    calls = [];
    payload = { results: [{ name: 'example' }] };
    jest.spyOn(axios, 'create').mockImplementation(options => {
      const instance = createAxios(options);
      instance.defaults.adapter = config => {
        calls.push(config);
        return new Promise((resolve, reject) => {
          const response = setTimeout(() => {
            if (deadline !== undefined) clearTimeout(deadline);
            resolve({ data: payload, status: 200, statusText: 'OK', headers: {}, config });
          }, 300);
          const deadline = config.timeout && config.timeout > 0
            ? setTimeout(() => {
              clearTimeout(response);
              reject(new AxiosError('Synthetic response exceeded the request timeout', 'ECONNABORTED', config));
            }, config.timeout)
            : undefined;
        });
      };
      return instance;
    });
  });

  afterEach(() => {
    jest.restoreAllMocks();
    jest.useRealTimers();
    if (savedExtra === undefined) delete process.env.FI_EXTRA_HEADERS;
    else process.env.FI_EXTRA_HEADERS = savedExtra;
  });

  it('defines the shared default as 30 seconds in Axios milliseconds', () => {
    expect(DEFAULT_TIMEOUT).toBe(30_000);
    expect(DEFAULT_SETTINGS.TIMEOUT).toBe(30_000);
  });

  it('allows a prompt-list response after 300 ms without an override or retry', async () => {
    expect(await finish(Prompt.listTemplates(auth))).toEqual({ ok: true, value: payload });
    expect(calls).toHaveLength(1);
    expect(calls[0].timeout).toBe(30_000);
  });

  it('allows a prompt get-by-name response after 300 ms', async () => {
    payload = { result: { name: 'example', version: 'v1', prompt_config: [] } };
    const result = await finish(Prompt.getTemplateByName('example', { ...auth, version: 'v1' }));
    expect(result).toMatchObject({ ok: true, value: { name: 'example', version: 'v1' } });
    expect(calls).toHaveLength(1);
    expect(calls[0].timeout).toBe(30_000);
  });

  it('allows the prompt-generation request to respond after 300 ms', async () => {
    payload = { result: { prompt: 'Synthetic generated prompt' } };
    const client = new Prompt(new PromptTemplate(), auth);
    try {
      const result = await finish(client.generate('Synthetic requirements'));
      expect(result).toMatchObject({ ok: true, value: { template: { messages: [
        { role: 'user', content: 'Synthetic generated prompt' },
      ] } } });
      expect(calls).toHaveLength(1);
      expect(calls[0].method).toBe('post');
      expect(calls[0].timeout).toBe(30_000);
    } finally {
      await client.close();
    }
  });

  it('allows a knowledge-base list response after 300 ms', async () => {
    payload = { result: { table_data: [] } };
    const client = new KnowledgeBase(undefined, auth);
    try {
      expect(await finish(client.listKbs())).toEqual({ ok: true, value: [] });
      expect(calls).toHaveLength(1);
      expect(calls[0].timeout).toBe(30_000);
    } finally {
      await client.close();
    }
  });

  it('preserves an explicit constructor timeout in milliseconds', async () => {
    expect(await finish(Prompt.listTemplates({ ...auth, timeout: 1_000 })))
      .toEqual({ ok: true, value: payload });
    expect(calls).toHaveLength(1);
    expect(calls[0].timeout).toBe(1_000);
  });

  it('preserves a per-request timeout over the constructor default', async () => {
    const client = new APIKeyAuth({ ...auth, timeout: 100 });
    try {
      expect(await finish(client.request({ method: HttpMethod.GET, url: '/example', timeout: 1_000 })))
        .toMatchObject({ ok: true, value: { data: payload } });
      expect(calls).toHaveLength(1);
      expect(calls[0].timeout).toBe(1_000);
    } finally {
      await client.close();
    }
  });

  it('still enforces an explicitly shorter request timeout', async () => {
    const client = new APIKeyAuth({ ...auth, retryAttempts: 1 });
    try {
      expect(await finish(client.request({ method: HttpMethod.GET, url: '/example', timeout: 100 })))
        .toMatchObject({ ok: false, error: expect.any(Error) });
      expect(calls).toHaveLength(1);
      expect(calls[0].timeout).toBe(100);
    } finally {
      await client.close();
    }
  });
});
