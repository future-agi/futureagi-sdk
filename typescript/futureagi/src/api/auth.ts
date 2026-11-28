// Evaluated before axios, whose fetch adapter makes a `Request` when it loads (CommonJS evaluates modules in this
// order): the runtime's undici classes are read from the agent the runtime makes for that module, and the runtime
// makes one only when its copy of undici loads.
import '../_core/dispatcher-provenance';
import axios, { AxiosInstance, AxiosResponse, AxiosRequestConfig, AxiosError, AxiosHeaders, type InternalAxiosRequestConfig } from 'axios';
import { Agent as HttpAgent } from 'node:http';
import { Agent as HttpsAgent } from 'node:https';
import { types as utilTypes } from 'node:util';
import { BoundedExecutor } from '../utils/executor';
import { 
    MissingAuthError, 
    DatasetNotFoundError, 
    InvalidAuthError,
    RateLimitError,
    ServerError,
    ServiceUnavailableError 
} from '../utils/errors';
import { 
    AUTH_ENVVAR_NAME, 
    DEFAULT_SETTINGS, 
    get_base_url 
} from '../utils/constants';
import { HttpMethod } from './types';
import { ExtraHeaders, ExtraHeadersError, isPlatformUrl, type ExtraHeadersInput } from '../extra-headers';
import type { RequestConfig } from './types';
import { checkHttpSecurity, isLoopback } from '../_core/http-security';
import { headerRecord, headersCarryKey, normalizeHeaders, queryCarriesKey, type HeaderSource } from '../_core/key-headers';
import { ConfigurationError, UnexpectedRedirectError } from '../_core/errors';
import { loopbackLookup } from '../_core/loopback';

/**
 * The agents of a request to a loopback host: they carry no environment proxy (the runtime's own agents read one under
 * `NODE_USE_ENV_PROXY`, which `proxy: false` does not switch off) and resolve `localhost` as 127.0.0.1 or ::1 alone.
 */
let loopbackAgents: { httpAgent: HttpAgent; httpsAgent: HttpsAgent } | undefined;
const directAgents = (): { httpAgent: HttpAgent; httpsAgent: HttpsAgent } => (loopbackAgents ??= {
    httpAgent: new HttpAgent({ lookup: loopbackLookup } as ConstructorParameters<typeof HttpAgent>[0]),
    httpsAgent: new HttpsAgent({ lookup: loopbackLookup } as ConstructorParameters<typeof HttpsAgent>[0]),
});

/**
 * The agent of a keyed plain-http request to a host that is not loopback. The runtime's global agent reads the
 * environment proxy under `NODE_USE_ENV_PROXY` whatever axios's `proxy` option says; an agent of its own does not, so the
 * request connects to its host and no proxy sees it.
 */
let plainAgent: HttpAgent | undefined;
const directPlainAgent = (): HttpAgent => (plainAgent ??= new HttpAgent());

/**
 * Whether the headers of a request, taken together (each layer, in any letter case), carry a Future AGI key: an
 * `X-Api-Key`, `X-Secret-Key` or `Authorization` header, or a header whose value holds `FI_API_KEY` / `FI_SECRET_KEY`
 * from the environment. A request with any of them is a keyed request. Headers in axios's `common` layer and in the layer
 * named for the request's method are part of the request's headers, so they are read too.
 */
const carriesCredentials = (method: string, ...layers: HeaderSource[]): boolean => headersCarryKey(layers, { axiosMethod: method });

/** One of axios's own adapters by name, or undefined where the runtime has none (xhr in Node.js). */
const builtinAdapter = (name: string): unknown => { try { return axios.getAdapter(name as never); } catch { return undefined; } };
/**
 * axios's own http adapter, by identity. It is the one adapter that reads the `proxy`, agent and `maxRedirects` settings
 * the SDK gives a keyed request, so a keyed request goes through it. Any other adapter (axios's 'fetch' or 'xhr', from
 * this or another copy of axios, or an adapter function of the caller's) decides for itself the redirects it follows
 * and the proxy it uses, so a keyed request on one is refused unless the caller opts in.
 */
const HTTP_ADAPTER = builtinAdapter('http');
/** axios's 'fetch' and 'xhr' adapters of the SDK's own axios, by identity. */
const AXIOS_FETCH_XHR = new Set([builtinAdapter('fetch'), builtinAdapter('xhr')].filter((a) => a !== undefined && a !== HTTP_ADAPTER));
/** The adapter names axios gives its 'fetch' and 'xhr' adapters, in every copy and build of axios. */
const FETCH_XHR_NAMES = new Set(['fetch', 'xhr']);

/**
 * The 'fetch' or 'xhr' name of an adapter that is axios's own 'fetch' or 'xhr' adapter (of the SDK's axios, or named so
 * by another copy or build of axios), or undefined for any other adapter.
 */
const fetchXhrName = (adapter: unknown): string | undefined => {
    let name: unknown;
    try { name = (adapter as { adapterName?: unknown } | null)?.adapterName; } catch { name = undefined; }
    if (typeof name === 'string' && FETCH_XHR_NAMES.has(name.toLowerCase())) return name;
    return AXIOS_FETCH_XHR.has(adapter) ? 'fetch' : undefined;
};

/** The refusal of a keyed request on an adapter other than axios's http adapter, made before any connection. */
const adapterRefused = (what: string): ConfigurationError => new ConfigurationError(
    `a request that carries API keys is not sent with ${what}: the SDK applies the request's proxy, agent and redirect ` +
        "settings through axios's http adapter (the default in Node.js) alone, and another adapter may follow redirects and use the " +
        'environment proxy whatever they say; remove the adapter setting, or set customAdapterReceivesKeys: true on the client ' +
        'if the adapter is yours and may receive the keys',
    'keyed_adapter_unsupported',
);

/** Marks the config of a request that was judged keyed on its final headers. */
const KEYED_SEND = Symbol('futureagi.keyedSend');

/**
 * The SDK's adapter wrappers, each with the adapter setting it wraps. A config the SDK already sent (`response.config`,
 * `error.config`) holds a wrapper as its adapter; sent again, it is judged on the adapter that wrapper holds.
 */
const WRAPPED = new WeakMap<object, unknown>();

/** The refusal of a request whose config does not take the settings the SDK gives it, made before any connection. */
const configRefused = (what: string): ConfigurationError => new ConfigurationError(
    `a request is not sent when ${what}: the SDK sets the adapter of every request, and the route (no transport, no ` +
        'redirect, no proxy, its own agents) of a request that carries API keys, as own properties of its config that stay as set; ' +
        'remove the accessor, the non-configurable property or the Proxy from the request config',
    'keyed_config_unsupported',
);

/** Sets each value as an own property of the config that no later assignment or definition replaces. */
const pinOwn = (config: object, values: Record<string, unknown>): void => {
    for (const [name, value] of Object.entries(values)) {
        try {
            Object.defineProperty(config, name, { value, writable: false, configurable: false, enumerable: true });
        } catch {
            throw configRefused(`its config does not take the SDK's '${name}' setting`);
        }
    }
};

/** Fold fetch's header option into the headers shared by the adapters, after Axios transforms the request. */
function mergeFetchHeaders(config: InternalAxiosRequestConfig, adapter?: 'http' | 'fetch'): void {
    const options = config.fetchOptions as Record<string, unknown> | undefined;
    const { headers: source, ...fetchOptions } = options ?? {};
    if (source != null) {
        const headers = new AxiosHeaders(config.headers).set(headerRecord(source as HeaderSource), true);
        if (adapter !== undefined) pinOwn(config, { headers, fetchOptions });
        else {
            config.headers = headers;
            config.fetchOptions = fetchOptions;
        }
    } else if (adapter === 'fetch') {
        // Axios passes these options to fetch as RequestInit. Keep a second header source out of that call.
        pinOwn(config, { fetchOptions: options == null ? options : fetchOptions });
    }
}

const PROXY_AUTHORIZATION = 'proxy-authorization';

/** Remove every `Proxy-Authorization` field of a header record or `AxiosHeaders`, in any letter case. */
function dropProxyAuthorization(headers: unknown): void {
    if (headers === null || typeof headers !== 'object') return;
    for (const name of Object.keys(headers)) {
        if (name.trim().toLowerCase() === PROXY_AUTHORIZATION) delete (headers as Record<string, unknown>)[name];
    }
}

/** The `protocol//host:port` of a proxy as axios's http adapter writes it into the request options. */
function proxyAddress(protocol: unknown, host: unknown, port: unknown): string {
    const scheme = typeof protocol === 'string' && protocol !== '' ? (protocol.endsWith(':') ? protocol : `${protocol}:`) : 'http:';
    return `${scheme.toLowerCase()}//${String(host ?? '').toLowerCase()}:${port === undefined || port === null ? '' : String(port)}`;
}

/**
 * Per-call headers held in a plain record (of any realm, including one with `forEach` and `get` fields), or not given:
 * the form that merges into the client's headers field by field, as Axios merges a plain object.
 */
const isHeaderRecord = (source: unknown): boolean => {
    if (source === undefined) return true;
    if (source === null || typeof source !== 'object' || Array.isArray(source)) return false;
    const prototype = Object.getPrototypeOf(source) as object | null;
    if (prototype !== null && Object.getPrototypeOf(prototype) !== null) return false;
    return !(Symbol.iterator in source) && !(Symbol.toStringTag in source);
};

/** The request methods axios names a header layer after. */
const METHODS = ['get', 'post', 'put', 'patch', 'delete', 'head', 'options'] as const;
const JSON_CONTENT_TYPE = 'application/json';
const contentTypeEntry = (headers?: Record<string, unknown>): [string, unknown] | undefined =>
    Object.entries(headers ?? {}).reverse().find(([name, value]) => name.toLowerCase() === 'content-type' && value !== undefined);

/**
 * Generic response handler for parsing and validating HTTP responses
 */
export abstract class ResponseHandler<T = any, U = any> {
    /**
     * Parse the response into the expected type
     */
    static parse<T, U>(response: AxiosResponse, handlerClass: typeof ResponseHandler): T | U {
        if (!response || response.status < 200 || response.status >= 300) {
            handlerClass._handleError(response);
        }
        return handlerClass._parseSuccess(response);
    }

    /**
     * Parse successful response - to be implemented by subclasses
     */
    public static _parseSuccess(response: AxiosResponse): any {
        throw new Error("Method '_parseSuccess' must be implemented by subclass.");
    }

    /**
     * Handle error responses - to be implemented by subclasses
     */
    public static _handleError(response: AxiosResponse): never {
        const status = response?.status || 500;
        let message: string | undefined;
        if (response?.data) {
            const d: any = response.data;
            message = d.message || d.detail || d.result;

            // If nothing explicit, stringify the whole payload so callers see something meaningful
            if (!message) {
                try {
                    message = JSON.stringify(d);
                } catch {
                    /* ignore */
                }
            }
        }

        if (!message) {
            const url = response?.config?.url ? ` – ${response.config.url}` : '';
            message = (response?.statusText && response.statusText.trim().length > 0)
                ? response.statusText
                : `HTTP ${status}${url}`;
        }

        switch (status) {
            case 401:
            case 403:
                throw new InvalidAuthError(message);
            case 404:
                throw new DatasetNotFoundError(message);
            case 429:
                throw new RateLimitError(message);
            case 503:
                throw new ServiceUnavailableError(message);
            case 500:
            case 502:
            case 504:
                throw new ServerError(message);
            default:
                throw new Error(`HTTP ${status}: ${message}`);
        }
    }
}

/**
 * Configuration options for HttpClient
 */
export interface HttpClientConfig {
    baseUrl?: string;
    /** Typed as a record. A `Headers`, a `Map` or a list of [name, value] pairs from untyped code is read once, when the client is built, into the same record. */
    defaultHeaders?: Record<string, string>;
    /**
     * Headers for every request under `baseUrl`, added to `FI_EXTRA_HEADERS` and winning over it for
     * the same name. Not `X-Api-Key`, `X-Secret-Key` or `Authorization`, and not another host or a
     * redirect to one (extra-headers.ts).
     */
    extraHeaders?: ExtraHeadersInput;
    /**
     * Send API keys over plain `http://` to a host that is not loopback. Without it (and without
     * `FI_ALLOW_INSECURE_HTTP` set to exactly `1`) such a base URL is refused before any connection. Not
     * for a Future AGI host, whatever the setting.
     */
    allowInsecureHttp?: boolean;
    /**
     * Send a request that carries API keys through an adapter other than axios's `http` adapter: axios's `fetch` or
     * `xhr` adapter (from any copy of axios) or an adapter function of yours. The SDK applies the `proxy`, agent and
     * `maxRedirects` settings of a keyed request through the `http` adapter alone; another adapter decides the redirects
     * it follows and the proxy it uses. Without this option such a request is refused before any connection with
     * `ConfigurationError` code `keyed_adapter_unsupported`. Set it only for an adapter you own.
     */
    customAdapterReceivesKeys?: boolean;
    timeout?: number;
    maxQueue?: number;
    maxWorkers?: number;
    retryAttempts?: number;
    retryDelay?: number;
}

/**
 * Base HTTP client with improved request handling, connection pooling, and async execution
 */
export class HttpClient {
    protected readonly _baseUrl: string;
    protected readonly _axiosInstance: AxiosInstance;
    protected readonly _executor: BoundedExecutor;
    protected readonly _defaultTimeout: number;
    protected readonly _defaultRetryAttempts: number;
    protected readonly _defaultRetryDelay: number;
    protected readonly _extraHeaders: ExtraHeaders;
    protected readonly _allowInsecureHttp: boolean | undefined;
    /** The caller's opt-in to send keyed requests through an adapter other than axios's http adapter. */
    protected readonly _customAdapterReceivesKeys: boolean;
    private readonly _defaultHeaders: Record<string, unknown>;
    /** The client carries API keys in the default headers of some method layer. Each request is judged on its own final headers, whatever this says. */
    protected readonly _keyed: boolean;

    constructor(config: HttpClientConfig = {}) {
        this._baseUrl = (config.baseUrl || get_base_url()).replace(/\/$/, '');
        this._extraHeaders = new ExtraHeaders(this._baseUrl, config.extraHeaders);
        this._allowInsecureHttp = config.allowInsecureHttp;
        this._customAdapterReceivesKeys = config.customAdapterReceivesKeys === true;
        // every container form becomes one record here: the keyed decision and the headers axios sends are the same
        this._defaultHeaders = normalizeHeaders(config.defaultHeaders as HeaderSource);
        this._keyed = METHODS.some((method) => carriesCredentials(method, this._defaultHeaders));
        this._defaultTimeout = config.timeout || DEFAULT_SETTINGS.TIMEOUT;
        this._defaultRetryAttempts = config.retryAttempts || 3;
        this._defaultRetryDelay = config.retryDelay || 1000;

        // Create axios instance with default configuration
        this._axiosInstance = axios.create({
            baseURL: this._baseUrl,
            timeout: this._defaultTimeout,
            headers: {
                'Content-Type': JSON_CONTENT_TYPE,
                'User-Agent': '@future-agi/sdk',
                ...this._defaultHeaders,
            } as Record<string, string>,
            // Enable connection pooling
            // each request is judged on its own headers: a keyed one sets maxRedirects 0 itself
            maxRedirects: 5,
            // FI_EXTRA_HEADERS: a redirect off the base URL loses them, one under it keeps them
            beforeRedirect: this._redirectGuard,
            validateStatus: () => true, // Handle all status codes manually
        });

        // Create bounded executor for managing concurrent requests
        this._executor = new BoundedExecutor(
            config.maxQueue || DEFAULT_SETTINGS.MAX_QUEUE,
            config.maxWorkers || DEFAULT_SETTINGS.MAX_WORKERS
        );

        this._setupInterceptors();
    }

    /**
     * Setup request and response interceptors
     */
    private _setupInterceptors(): void {
        // Request interceptor for logging and debugging
        this._axiosInstance.interceptors.request.use(
            (config) => {
                // Add request timestamp for performance monitoring
                (config as any).startTime = Date.now();
                // FI_EXTRA_HEADERS / extraHeaders, read now, on URLs under the base URL only
                const extra = this._extraHeaders.forUrl(this._axiosInstance.getUri(config));
                for (const [name, value] of Object.entries(extra)) {
                    if (!config.headers.has(name)) config.headers.set(name, value);
                }
                // The last request interceptor to run (axios runs them in reverse order of registration, and this one is
                // registered first): the headers hold whatever an interceptor of the caller added. The adapter judges
                // the headers that go on the wire, after any transform too. A request that carries a key goes through
                // axios's http adapter (by identity, as the final config resolves it, a name or a list of names
                // included); on any other adapter it is refused before any connection, unless customAdapterReceivesKeys
                // is set. An adapter function of the caller's may add a key the judge does not see, so a request
                // through one is routed as keyed.
                // The wrapper is an own property of the config that a transform or a later assignment does not
                // replace; a config that does not take it is refused. A wrapper of the SDK's (a config sent again) is
                // judged on the adapter it holds.
                const inner = config.adapter ?? this._axiosInstance.defaults.adapter;
                const wrapper = (final: InternalAxiosRequestConfig): Promise<AxiosResponse> => {
                    let adapter: unknown = axios.getAdapter(inner as Parameters<typeof axios.getAdapter>[0]);
                    while (typeof adapter === 'function' && WRAPPED.has(adapter)) {
                        adapter = axios.getAdapter(WRAPPED.get(adapter) as Parameters<typeof axios.getAdapter>[0]);
                    }
                    const http = adapter === HTTP_ADAPTER;
                    const named = http ? undefined : fetchXhrName(adapter);
                    mergeFetchHeaders(final, http ? 'http' : named?.toLowerCase() === 'fetch' ? 'fetch' : undefined);
                    const carries = this._finalCarriesKey(final);
                    if (carries && utilTypes.isProxy(final)) throw configRefused('its config is a Proxy and it carries API keys');
                    if (carries && !http && !this._customAdapterReceivesKeys) {
                        throw adapterRefused(named !== undefined ? `axios's '${named}' adapter` : "an adapter function other than axios's http adapter");
                    }
                    if (carries || (!http && named === undefined)) this._routeKeyed(final, http || !carries);
                    this._routeProxyAuthorization(final, http);
                    return (adapter as (config: InternalAxiosRequestConfig) => Promise<AxiosResponse>)(final);
                };
                WRAPPED.set(wrapper, inner);
                pinOwn(config, { adapter: wrapper });
                return config;
            },
            (error) => Promise.reject(error)
        );

        // Response interceptor for logging and performance monitoring
        this._axiosInstance.interceptors.response.use(
            (response) => {
                const duration = Date.now() - ((response.config as any).startTime || 0);
                // Could add logging here for production monitoring
                return response;
            },
            (error) => Promise.reject(error)
        );
    }

    /**
     * The decision on the headers the request is about to send: whether they carry a key, whether or not the call or the
     * client's defaults carried one (an interceptor or a transform may have added it). axios's `auth` option is an
     * `Authorization` header the adapter writes later, so a request that has it is keyed too, as is one with a key in its
     * query or params.
     */
    private _finalCarriesKey(config: InternalAxiosRequestConfig): boolean {
        const method = String(config.method ?? 'get').toLowerCase();
        const target = this._targetOf(config.url ?? '', config.baseURL);
        return Boolean(config.auth) || carriesCredentials(method, config.headers as HeaderSource, this._extraHeadersFor(target)) || queryCarriesKey(target, config.params);
    }

    /**
     * The route of a keyed request, set on its final config after every interceptor ran: it is judged for plain http and
     * goes to its host directly, with no proxy hop and no redirect. On axios's http adapter, axios's `transport` option
     * names the module the adapter sends with and wins over `maxRedirects` and `beforeRedirect` (the follow-redirects
     * module follows redirects whatever they say), so it is removed and the adapter sends with Node's own http or https
     * module. The same holds for a request routed as keyed because an adapter function of the caller's may add a key to
     * it; an opted-in adapter that receives keys decides its redirects itself.
     */
    private _routeKeyed(config: InternalAxiosRequestConfig, dropTransport: boolean): void {
        const target = this._targetOf(config.url ?? '', config.baseURL);
        checkHttpSecurity(target, 'keys', this._allowInsecureHttp, false, true);
        // own properties that no later assignment replaces and that shadow the config's prototype: code the adapter
        // runs (a paramsSerializer) does not restore a transport or redirects
        pinOwn(config, {
            ...(dropTransport ? { transport: undefined } : {}),
            maxRedirects: 0,
            beforeRedirect: this._redirectGuard,
            proxy: false,
            ...(isLoopback(target) ? directAgents() : { httpAgent: directPlainAgent() }),
        });
        (config as unknown as Record<symbol, unknown>)[KEYED_SEND] = true;
    }

    /**
     * `Proxy-Authorization` goes to a proxy alone. On axios's http adapter, a plain `http://` request sent through the
     * proxy named in its `proxy` option is written to that proxy, and the field goes with it; a redirect hop keeps it
     * through that same proxy to a plain `http://` URL alone. Every other send reaches its host, directly or inside a
     * CONNECT tunnel (axios tunnels `https://` through a proxy, and the proxy environment is routed by axios or the
     * runtime's agent), and carries no `Proxy-Authorization` from the call, the client's default headers, `fetchOptions`
     * or an interceptor. A value that `extraHeaders` or `FI_EXTRA_HEADERS` sets for a URL under the base URL is sent to
     * that URL directly, and not to a forward proxy.
     */
    private _routeProxyAuthorization(config: InternalAxiosRequestConfig, http: boolean): void {
        const target = this._targetOf(config.url ?? '', config.baseURL);
        const extra = Object.entries(this._extraHeadersFor(target)).find(([name]) => name.toLowerCase() === PROXY_AUTHORIZATION);
        const proxy = http && /^http:/iu.test(target) ? this._axiosProxyOf(config) : undefined;
        const headers = config.headers as unknown as Record<string, unknown>;
        if (proxy === undefined) {
            dropProxyAuthorization(headers);
            if (extra !== undefined) headers[extra[0]] = extra[1];
            return;
        }
        if (extra !== undefined) {
            for (const name of Object.keys(headers)) {
                if (name.trim().toLowerCase() === PROXY_AUTHORIZATION && headers[name] === extra[1]) delete headers[name];
            }
        }
        if (config.maxRedirects === 0 || !Object.keys(headers).some((name) => name.trim().toLowerCase() === PROXY_AUTHORIZATION)) return;
        const prior = config.beforeRedirect;
        type Hop = Parameters<NonNullable<InternalAxiosRequestConfig['beforeRedirect']>>;
        const hop = (options: Hop[0], details: Hop[1]): void => {
            if (typeof prior === 'function') prior(options, details);
            const path = typeof options.path === 'string' ? options.path : '';
            const through = /^http:\/\//iu.test(path) ? proxyAddress(options.protocol, options.hostname ?? options.host, options.port) : undefined;
            if (through !== proxy) {
                dropProxyAuthorization(options.headers);
                const href = typeof options.href === 'string' ? options.href : '';
                const scoped = href === '' ? undefined : Object.entries(this._extraHeadersFor(href)).find(([name]) => name.toLowerCase() === PROXY_AUTHORIZATION);
                if (scoped !== undefined && through === undefined) (options.headers as Record<string, unknown>)[scoped[0]] = scoped[1];
            }
        };
        try {
            pinOwn(config, { beforeRedirect: hop });
        } catch {
            // a config that does not take the hop check sends no Proxy-Authorization
            dropProxyAuthorization(headers);
        }
    }

    /** The proxy (`protocol//host:port`) named in a request's axios `proxy` option, or undefined for none. */
    private _axiosProxyOf(config: InternalAxiosRequestConfig): string | undefined {
        if (config.socketPath) return undefined;
        const option = config.proxy as (AxiosRequestConfig['proxy'] & { hostname?: string }) | null | undefined;
        if (!option) return undefined;
        const own = (key: string): unknown => (Object.prototype.hasOwnProperty.call(option, key) ? (option as unknown as Record<string, unknown>)[key] : undefined);
        const host = own('hostname') ?? own('host');
        if (typeof host !== 'string' || host === '') return undefined;
        return proxyAddress(own('protocol'), host, own('port'));
    }

    /** The redirect guard of the client's requests, the instance default `beforeRedirect`. */
    private readonly _redirectGuard = (options: Record<string, any>, details: { statusCode?: number }): void => this._guardRedirect(options, details);

    /** Refuse every redirect on a request that carries API credentials, the same origin included. Extra headers stay
     * under the base URL and are stripped elsewhere (follow-redirects keeps custom headers on every host). */
    private _guardRedirect(options: Record<string, any>, details?: { statusCode?: number }): void {
        const port = options.port ? `:${options.port}` : '';
        const href = options.href || `${options.protocol}//${options.hostname}${port}${options.path || '/'}`;
        const headers: Record<string, unknown> = options.headers || (options.headers = {});
        const present = new Set(Object.keys(headers).map((k) => k.toLowerCase()));
        if (present.has('x-api-key') || present.has('x-secret-key') || present.has('authorization') || carriesCredentials('get', headers)) {
            throw this._redirectRefused(details?.statusCode ?? 0);
        }
        if (isPlatformUrl(href, this._baseUrl)) {
            for (const [name, value] of Object.entries(this._extraHeaders.forUrl(href))) {
                if (!present.has(name.toLowerCase())) headers[name] = value;
            }
            return;
        }
        const names = new Set(this._extraHeaders.names().map((n) => n.toLowerCase()));
        for (const key of Object.keys(headers)) {
            if (names.has(key.toLowerCase())) delete headers[key];
        }
    }

    /**
     * Make an HTTP request with retries and response handling
     */
    async request<T = any>(
        config: RequestConfig, 
        responseHandler?: typeof ResponseHandler
    ): Promise<T | AxiosResponse> {
        const target = this._targetOf(config.url);
        // the call's own headers, in whatever container form, as the one record that is judged and sent
        const source = config.headers as HeaderSource;
        const callHeaders = normalizeHeaders(source);
        const method = String(config.method ?? 'get').toLowerCase();
        const data = config.json || config.data;
        const defaults = this._axiosInstance.defaults.headers;
        if (!isHeaderRecord(source) && !contentTypeEntry(callHeaders) && !contentTypeEntry(this._defaultHeaders)) {
            const top = contentTypeEntry(defaults);
            if (top?.[0] === 'Content-Type' && top[1] === JSON_CONTENT_TYPE) {
                // Headers in any form but a record (pairs, a Map, a Set, an iterator, a Headers, a forEach/get container,
                // null) take the Content-Type of explicit Axios layers, not the SDK's JSON setting: a bodyless request
                // has none, Axios sets JSON for an object body, and a string body is sent as given.
                const layer = (defaults as unknown as Record<string, Record<string, unknown> | undefined>)[method];
                callHeaders['Content-Type'] = (contentTypeEntry(layer) ?? contentTypeEntry(defaults.common))?.[1];
            }
        }
        const keyed = carriesCredentials(method, defaults as HeaderSource, callHeaders, this._extraHeadersFor(target)) || queryCarriesKey(target, config.params);
        if (keyed) {
            // proxies are off for plain http below, so none is judged here
            checkHttpSecurity(target, 'keys', this._allowInsecureHttp, false, true);
        }
        const requestConfig: AxiosRequestConfig = {
            method: config.method,
            url: config.url,
            headers: callHeaders as AxiosRequestConfig['headers'],
            params: config.params,
            data,
            timeout: config.timeout || this._defaultTimeout,
            ...(config.responseType ? { responseType: config.responseType } : {}),
            // a keyed request does not use axios's own proxy hop (it hands an https request to the proxy as a plain-http
            // one and rewrites the Host header); a request to loopback or over plain http connects straight to its host,
            // and any other https request is routed by the runtime's environment proxy (CONNECT) when that is on. On
            // axios's http adapter it follows no redirect; the adapter judges the final config, removes a `transport`
            // and refuses any other adapter unless customAdapterReceivesKeys is set.
            ...(keyed ? { proxy: false as const } : {}),
            ...(keyed && isLoopback(target) ? directAgents() : {}),
            ...(keyed && !isLoopback(target) ? { httpAgent: directPlainAgent() } : {}), // used for an http request only
            ...(keyed ? { maxRedirects: 0 } : {}),
        };

        // Handle file uploads
        if (config.files && Object.keys(config.files).length > 0) {
            const formData = new FormData();
            Object.entries(config.files).forEach(([key, file]) => {
                formData.append(key, file);
            });
            if (config.data) {
                Object.entries(config.data).forEach(([key, value]) => {
                    formData.append(key, value);
                });
            }
            requestConfig.data = formData;
            requestConfig.headers = {
                ...requestConfig.headers,
                'Content-Type': 'multipart/form-data',
            };
        }

        const retryAttempts = config.retry_attempts || this._defaultRetryAttempts;
        const retryDelay = config.retry_delay || this._defaultRetryDelay;

        // Execute request with bounded concurrency
        return this._executor.submit(async () => {
            for (let attempt = 0; attempt < retryAttempts; attempt++) {
                try {
                    const response = await this._axiosInstance.request(requestConfig);
                    if ((keyed || (response.config as unknown as Record<symbol, unknown>)?.[KEYED_SEND] === true) && response.status >= 300 && response.status < 400) {
                        throw this._redirectRefused(response.status, response.headers?.location as string | undefined);
                    }

                    if (responseHandler) {
                        return ResponseHandler.parse<T, any>(response, responseHandler);
                    }
                    
                    // Handle errors if no custom handler
                    if (response.status >= 400) {
                        ResponseHandler._handleError(response);
                    }

                    return response;
                } catch (error) {
                    // Don't retry certain errors (a malformed FI_EXTRA_HEADERS / extraHeaders sent
                    // nothing and fails the same way every time: at once, as in Python)
                    if (error instanceof ConfigurationError ||
                        error instanceof DatasetNotFoundError ||
                        error instanceof InvalidAuthError ||
                        error instanceof ExtraHeadersError ||
                        error instanceof UnexpectedRedirectError ||
                        (error instanceof AxiosError && error.response?.status === 401)) {
                        throw error;
                    }

                    // Last attempt - throw the error
                    if (attempt === retryAttempts - 1) {
                        if (error instanceof AxiosError) {
                            ResponseHandler._handleError(error.response!);
                        }
                        throw error;
                    }

                    // Wait before retry
                    await this._sleep(retryDelay * Math.pow(2, attempt)); // Exponential backoff
                }
            }

            throw new Error('Unexpected end of retry loop');
        });
    }

    /** The FI_EXTRA_HEADERS a request to `url` carries, for the keyed decision; a malformed setting is reported where the headers are added. */
    private _extraHeadersFor(url: string): Record<string, string> {
        try { return this._extraHeaders.forUrl(url); } catch { return {}; }
    }

    /** The URL text of a request as the caller wrote it: an absolute URL as given, else the base URL as written plus the path. */
    private _targetOf(url: string, base?: string): string {
        const root = base === undefined || base === '' ? this._baseUrl : base.replace(/\/$/u, '');
        if (/^(?:[A-Za-z][A-Za-z\d+\-.]*:)?\/\//u.test(url)) return url.startsWith('//') ? `${root.split('//')[0]}${url}` : url;
        return `${root}/${url.replace(/^\/+/u, '')}`;
    }

    /** The refusal of a 3xx answer to a keyed request. It names the target host only, not its path or query. */
    private _redirectRefused(status: number, location?: string): UnexpectedRedirectError {
        let host: string | undefined;
        try { host = location === undefined ? undefined : new URL(location, this._baseUrl).host; } catch { host = undefined; }
        return new UnexpectedRedirectError(
            `Refusing authenticated redirect: the server answered ${status || 'with a redirect'} and a request that carries API keys does not follow a redirect, ` +
                `not even within the configured origin (target host: ${host ?? 'unknown'})`,
            status,
            host,
        );
    }

    /**
     * Helper method for sleep/delay
     */
    private async _sleep(ms: number): Promise<void> {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    /**
     * Close the client and cleanup resources
     */
    async close(): Promise<void> {
        await this._executor.shutdown(true);
    }

    /**
     * Get the base URL
     */
    get baseUrl(): string {
        return this._baseUrl;
    }

    /**
     * Get the default timeout
     */
    get defaultTimeout(): number {
        return this._defaultTimeout;
    }
}

/**
 * Configuration for API Key authentication
 */
export interface APIKeyAuthConfig extends HttpClientConfig {
    fiApiKey?: string;
    fiSecretKey?: string;
    fiBaseUrl?: string;
}

/**
 * HTTP client with API key authentication
 */
export class APIKeyAuth extends HttpClient {
    protected _fiApiKey?: string;
    protected _fiSecretKey?: string;

    constructor(config: APIKeyAuthConfig = {}) {
        const fiApiKey = config.fiApiKey || process.env[AUTH_ENVVAR_NAME.API_KEY];
        const fiSecretKey = config.fiSecretKey || process.env[AUTH_ENVVAR_NAME.SECRET_KEY];

        if (!fiApiKey || !fiSecretKey) {
            throw new MissingAuthError(fiApiKey, fiSecretKey);
        }

        super({
            ...config,
            baseUrl: config.fiBaseUrl || config.baseUrl,
            defaultHeaders: {
                'X-Api-Key': fiApiKey,
                'X-Secret-Key': fiSecretKey,
                ...config.defaultHeaders,
            },
        });

        // Set class-level credentials
        this._fiApiKey = fiApiKey;
        this._fiSecretKey = fiSecretKey;
    }

    /**
     * Get the current API key
     */
    get fiApiKey(): string | undefined {
        return this._fiApiKey;
    }

    /**
     * Get the current secret key
     */
    get fiSecretKey(): string | undefined {
        return this._fiSecretKey;
    }

    /**
     * Get authentication headers
     */
    get headers(): Record<string, string> {
        return {
            'X-Api-Key': this._fiApiKey!,
            'X-Secret-Key': this._fiSecretKey!,
        };
    }
}

/**
 * Factory function to create authenticated HTTP client
 */
export function createAuthenticatedClient(config?: APIKeyAuthConfig): APIKeyAuth {
    return new APIKeyAuth(config);
}

export default {
    ResponseHandler,
    HttpClient,
    APIKeyAuth,
    createAuthenticatedClient,
};
