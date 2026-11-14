import axios, { type AxiosAdapter, type AxiosInstance } from 'axios';
import { APIKeyAuth, HttpClient } from '../api/auth';
import { HttpMethod } from '../api/types';

const BASE = 'https://api.example.test/api';
const auth = {
  fiApiKey: 'synthetic-api-key',
  fiSecretKey: 'synthetic-secret-key',
  fiBaseUrl: BASE,
  retryAttempts: 1,
};

type Hop = { url: string; omitHref?: boolean; lowercaseHeaders?: boolean };

/** Offline transport: invoke Axios's configured redirect hook before recording each next hop. */
function redirects(instance: AxiosInstance, hops: Hop[]) {
  const dispatched: Array<{ url: string; headers: Record<string, unknown> }> = [];
  const adapter: AxiosAdapter = async (config) => {
    let headers: Record<string, unknown> = { ...config.headers.toJSON() };
    dispatched.push({ url: axios.getUri(config), headers: { ...headers } });
    for (const hop of hops) {
      const url = new URL(hop.url);
      if (hop.lowercaseHeaders) {
        headers = Object.fromEntries(Object.entries(headers).map(([name, value]) => [name.toLowerCase(), value]));
      }
      const options = {
        ...(hop.omitHref ? {} : { href: url.href }),
        protocol: url.protocol,
        hostname: url.hostname,
        port: url.port,
        path: url.pathname + url.search,
        headers,
      };
      config.beforeRedirect!(options, { headers: { location: url.href }, statusCode: 302 });
      dispatched.push({ url: url.href, headers: { ...headers } });
    }
    return { data: { ok: true }, status: 200, statusText: 'OK', headers: {}, config };
  };
  instance.defaults.adapter = adapter;
  return dispatched;
}

class AuthenticatedProbe extends APIKeyAuth {
  follow(hops: Hop[]) { return redirects(this._axiosInstance, hops); }
}
class AnonymousProbe extends HttpClient {
  follow(hops: Hop[]) { return redirects(this._axiosInstance, hops); }
}
const get = (client: HttpClient) => client.request({ method: HttpMethod.GET, url: '/api/start' });

// All credentials are synthetic, and every request uses the in-memory adapter above.
describe('legacy authenticated redirects', () => {
  const savedExtra = process.env.FI_EXTRA_HEADERS;
  beforeEach(() => { delete process.env.FI_EXTRA_HEADERS; });
  afterEach(() => {
    if (savedExtra === undefined) delete process.env.FI_EXTRA_HEADERS;
    else process.env.FI_EXTRA_HEADERS = savedExtra;
  });

  it.each([
    ['different host', 'https://other.example.test/api/next', false],
    ['subdomain', 'https://sub.api.example.test/api/next', false],
    ['different port', 'https://api.example.test:8443/api/next', false],
    ['HTTPS downgrade', 'http://api.example.test/api/next', false],
    ['options without href', 'https://other.example.test/api/next', true],
  ] as const)('refuses a %s before sending either credential', async (_name, url, omitHref) => {
    const client = new AuthenticatedProbe(auth);
    const sent = client.follow([{ url, omitHref, lowercaseHeaders: true }]);
    try {
      await expect(get(client)).rejects.toThrow(/redirect.*origin/i);
      expect(sent).toHaveLength(1);
      expect(sent[0].headers['X-Api-Key']).toBe(auth.fiApiKey);
      expect(sent[0].headers['X-Secret-Key']).toBe(auth.fiSecretKey);
    } finally {
      await client.close();
    }
  });

  it('refuses an off-origin hop after a same-origin hop, including extra headers', async () => {
    process.env.FI_EXTRA_HEADERS = 'Proxy-Authorization=Bearer synthetic-proxy';
    const client = new AuthenticatedProbe({ ...auth, extraHeaders: { 'X-Team': 'synthetic-team' } });
    const sent = client.follow([
      { url: 'https://api.example.test/api/intermediate' },
      { url: 'https://other.example.test/api/final' },
    ]);
    try {
      await expect(get(client)).rejects.toThrow(/redirect.*origin/i);
      expect(sent).toHaveLength(2);
      expect(sent[1].headers).toMatchObject({
        'X-Api-Key': auth.fiApiKey,
        'X-Secret-Key': auth.fiSecretKey,
        'Proxy-Authorization': 'Bearer synthetic-proxy',
        'X-Team': 'synthetic-team',
      });
    } finally {
      await client.close();
    }
  });

  it.each(['https://api.example.test/api/next', 'https://API.EXAMPLE.TEST:443/api/next']) (
    'preserves credentials and extra headers on a same-origin redirect to %s', async (url) => {
      const client = new AuthenticatedProbe({ ...auth, extraHeaders: { 'X-Team': 'synthetic-team' } });
      const sent = client.follow([{ url }]);
      try {
        await expect(get(client)).resolves.toMatchObject({ status: 200 });
        expect(sent).toHaveLength(2);
        expect(sent[1].headers).toMatchObject({
          'X-Api-Key': auth.fiApiKey,
          'X-Secret-Key': auth.fiSecretKey,
          'X-Team': 'synthetic-team',
        });
      } finally {
        await client.close();
      }
    },
  );

  it('keeps same-origin credentials but strips extra headers outside the base path', async () => {
    const client = new AuthenticatedProbe({ ...auth, extraHeaders: { 'X-Team': 'synthetic-team' } });
    const sent = client.follow([{ url: 'https://api.example.test/outside' }]);
    try {
      await expect(get(client)).resolves.toMatchObject({ status: 200 });
      expect(sent).toHaveLength(2);
      expect(sent[1].headers).toMatchObject({ 'X-Api-Key': auth.fiApiKey, 'X-Secret-Key': auth.fiSecretKey });
      expect(sent[1].headers).not.toHaveProperty('X-Team');
    } finally {
      await client.close();
    }
  });

  it('preserves unauthenticated HttpClient redirects with extra headers stripped', async () => {
    const client = new AnonymousProbe({ baseUrl: BASE, extraHeaders: { 'X-Team': 'synthetic-team' } });
    const sent = client.follow([{ url: 'https://other.example.test/next' }]);
    try {
      await expect(get(client)).resolves.toMatchObject({ status: 200 });
      expect(sent).toHaveLength(2);
      expect(sent[1].headers).not.toHaveProperty('X-Team');
      expect(sent[1].headers).not.toHaveProperty('X-Api-Key');
      expect(sent[1].headers).not.toHaveProperty('X-Secret-Key');
    } finally {
      await client.close();
    }
  });
});
