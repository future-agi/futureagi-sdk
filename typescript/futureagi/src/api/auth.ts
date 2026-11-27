import axios, { AxiosInstance, AxiosResponse, AxiosRequestConfig, AxiosError, AxiosAdapter, AxiosHeaders, CanceledError, InternalAxiosRequestConfig } from 'axios';
import { PassThrough, pipeline } from 'node:stream';
import http from 'node:http';
import https from 'node:https';
import net from 'node:net';
import tls from 'node:tls';
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
import { RequestConfig, HttpMethod, ModelProvider } from './types';
import { carriesKey, isCredentialHeader, directHttpAgent, flattenHeaders, hasUserinfo, insecureHttpAllowed, insecureHttpCause, insecureHttpError, isLoopback, isTunnelRefusal, ownProxyAuthorization, plainHttpRoute, proxyFor, tlsSettingsOf, tunnelAgent } from '../utils/plain-http';

// The plain-http rule (see utils/plain-http) for the axios sender. A request is judged when it is sent: by the adapter
// (after every interceptor and transformRequest has run) and again by the agent when the Node request is created, so a
// key added by an interceptor or a transform is seen, and so is one added by an adapter wrapper that hands the request
// to the client's adapter or to axios's http adapter. A keyed plain-http request that is sent goes through axios's
// http adapter with the SDK's own agent and no proxy, in a request the SDK creates with `http.ClientRequest`. A keyed
// https request for which a proxy applies (the axios `proxy` option, or the proxy variables of the environment as axios
// reads them) is sent through that proxy only inside a CONNECT tunnel, with TLS to its host inside the tunnel: the
// axios http adapter (also in place of the axios fetch adapter) sends it with a tunnel agent of the SDK and no axios
// proxy. A keyed https request that would otherwise reach a proxy in absolute form (a key added after this judgement) is
// refused when Node creates it.
//
// Redirects are followed here, one hop at a time, whatever the adapter: each hop is judged again. A hop to the origin
// of the first request keeps its headers. A hop to any other origin (another host or port, or https to http) is sent
// without the key headers and axios `auth`; when it is plain http and the request carried a key, it is refused unless
// its host is loopback and the opt-in is set.

const JUDGED = Symbol('futureagi.plainHttp');
const HOP = Symbol('futureagi.redirectHop');

type Tagged = { [JUDGED]?: true };

/** What the hops of one request share: the origin of the first request and whether it carried a key, the redirects
 * left, and the caller's `validateStatus`, `transport`, `httpAgent`, `httpsAgent` and `proxy` (the direct and tunnel
 * routes replace those, and the other requests get a judging `transport` that wraps the caller's, for one hop only). */
interface HopState {
    origin: string;
    keyed: boolean;
    remaining: number;
    follow: boolean;
    validateStatus: InternalAxiosRequestConfig['validateStatus'];
    transport: unknown;
    httpAgent: unknown;
    httpsAgent: unknown;
    proxy: InternalAxiosRequestConfig['proxy'];
    /** The Proxy-Authorization the caller set on the first request (for the CONNECT of hops within its origin). */
    proxyAuthorization?: string;
}

type HopConfig = InternalAxiosRequestConfig & { [HOP]?: HopState };

const REDIRECT_STATUSES = new Set([300, 301, 302, 303, 307, 308]);
const DROPPED_ON_OTHER_ORIGIN = ['X-Api-Key', 'X-Secret-Key', 'Authorization', 'Proxy-Authorization', 'Cookie'];

/** The URL of the request as axios sends it (a protocol-relative url is read against the base). */
function requestUrl(config: InternalAxiosRequestConfig): string {
    let uri = axios.getUri(config);
    try {
        uri = new URL(uri, config.baseURL).href;
    } catch {
        /* judged as written */
    }
    return uri;
}

function originOf(url: string): string {
    try {
        return new URL(url).origin.toLowerCase();
    } catch {
        return url;
    }
}

/** The headers of the request that was sent: a Node `ClientRequest` or a fetch `Request`. */
function sentHeaders(request: unknown): Record<string, unknown> {
    const sent = request as { getHeaders?: () => Record<string, unknown>; headers?: unknown } | null | undefined;
    if (sent && typeof sent.getHeaders === 'function') {
        return sent.getHeaders();
    }
    return sent ? flattenHeaders([sent.headers]) : {};
}

/** Whether sent headers carry a key, leaving out a Proxy-Authorization equal to `ownProxyAuth`, the value axios builds
 * from the chosen proxy's own user name and password: that one is addressed to the proxy, not a key of the request. */
function carriesKeyFor(headers: Record<string, unknown>, ownProxyAuth: string | undefined): boolean {
    if (ownProxyAuth === undefined) {
        return carriesKey(headers);
    }
    const rest: Record<string, unknown> = {};
    for (const [name, value] of Object.entries(headers)) {
        const text = Array.isArray(value) ? value.join(',') : String(value ?? '');
        if (!(name.trim().toLowerCase() === 'proxy-authorization' && text === ownProxyAuth)) {
            rest[name] = value;
        }
    }
    return carriesKey(rest);
}

/** The Proxy-Authorization value axios builds for a request to `url` from its proxy's own auth, or `undefined`. */
function ownProxyAuthFor(url: string, configProxy: unknown): string | undefined {
    try {
        return ownProxyAuthorization(proxyFor(url, configProxy));
    } catch {
        return undefined;
    }
}

/** The most of a streamed body kept for a 307 or 308 hop when `maxBodyLength` is not set. */
const BODY_COPY_LIMIT = 10 * 1024 * 1024;

/** Streamed bodies that were sent on without a full copy: a 307 or 308 hop cannot send them again. */
const partialBodies = new WeakSet<object>();

/** Streamed bodies whose reading has started: a later attempt cannot send them again. */
const readSources = new WeakSet<object>();

type StreamLike = {
    pipe?: unknown; on?: unknown; once?: unknown; removeListener?: unknown; resume?: () => void; pause?: () => void; destroy?: (error?: Error) => void;
    getHeaders?: () => Record<string, string>; readableEnded?: boolean; readableDidRead?: boolean; destroyed?: boolean; errored?: unknown;
    _released?: boolean;
};

/** Whether `data` is a Node stream (a `form-data` object included). */
function isStream(data: unknown): data is StreamLike {
    return !!data && typeof (data as StreamLike).pipe === 'function' && typeof (data as StreamLike).on === 'function';
}

/** Whether a stream body has been read (in full or in part), ended, destroyed or failed: it cannot be sent again. */
function bodyConsumed(data: unknown): boolean {
    if (!isStream(data)) {
        return false;
    }
    return !!(data.readableEnded || data.readableDidRead || data.destroyed || data.errored || data._released === true || partialBodies.has(data as object) || readSources.has(data as object));
}

/** The error axios gives for a canceled request (its CanceledError takes the message and then the config). */
function canceled(config: InternalAxiosRequestConfig): Error {
    return new (CanceledError as unknown as new (message: string | undefined, config: unknown) => Error)(undefined, config);
}

/** The error axios gives for a body over `maxBodyLength` when it follows redirects (its follow-redirects code). */
function bodyTooLong(config: InternalAxiosRequestConfig): AxiosError {
    return new AxiosError('Request body larger than maxBodyLength limit', 'ERR_FR_MAX_BODY_LENGTH_EXCEEDED', config);
}

/**
 * A request body that is a Node stream (a `form-data` object included), read so that a 307 or 308 hop can send it
 * again; the `form-data` headers (its boundary) are set on the request first. Other bodies are returned as they are.
 * The copy holds at most `maxBodyLength` bytes, or 10 MB when that is not set: a body over a given `maxBodyLength` is
 * refused with code ERR_FR_MAX_BODY_LENGTH_EXCEEDED; a longer body without one is sent as a stream with no copy. A
 * stream that was already read is refused at once. Reading is bounded by the request's `timeout`, `signal` and
 * `cancelToken`; when one of them ends it, the source stream is destroyed.
 */
async function replayableBody(config: InternalAxiosRequestConfig): Promise<unknown> {
    const data = config.data;
    if (!isStream(data)) {
        return data;
    }
    if (typeof data.getHeaders === 'function') {
        config.headers.set(data.getHeaders());
    }
    if (bodyConsumed(data)) {
        throw new AxiosError('The request body stream was already read, so it cannot be sent.', AxiosError.ERR_BAD_REQUEST, config);
    }
    const explicit = typeof config.maxBodyLength === 'number' && config.maxBodyLength > -1;
    const limit = explicit ? (config.maxBodyLength as number) : BODY_COPY_LIMIT;
    const stream = data as unknown as NodeJS.ReadableStream & StreamLike;
    const chunks: Buffer[] = [];
    let size = 0;
    return new Promise<unknown>((resolve, reject) => {
        let timer: ReturnType<typeof setTimeout> | undefined;
        const signal = config.signal as AbortSignal | undefined;
        const token = config.cancelToken as { reason?: unknown; subscribe?(listener: (reason: unknown) => void): void; unsubscribe?(listener: (reason: unknown) => void): void } | undefined;
        const onData = (chunk: Buffer | string) => {
            const piece = Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk);
            chunks.push(piece);
            size += piece.length;
            if (size <= limit) {
                return;
            }
            if (explicit) {
                lose(bodyTooLong(config));
                return;
            }
            // Over the copy limit: the rest of the body is passed on as it arrives, with no copy.
            cleanup();
            stream.pause?.();
            const rest = new PassThrough();
            for (const held of chunks) {
                rest.write(held);
            }
            chunks.length = 0;
            partialBodies.add(rest);
            // A source that fails or closes before its end ends the rest with that error, so the request settles.
            pipeline(stream as unknown as NodeJS.ReadableStream, rest, () => undefined);
            resolve(rest);
        };
        const onEnd = () => {
            cleanup();
            resolve(Buffer.concat(chunks));
        };
        const onError = (error: unknown) => {
            cleanup();
            reject(error);
        };
        const onClose = () => lose(new AxiosError('The request body stream closed before its end.', AxiosError.ERR_BAD_REQUEST, config));
        const onAbort = () => lose(canceled(config));
        const onCancel = (reason: unknown) => lose(reason || canceled(config));
        function cleanup() {
            if (timer !== undefined) {
                clearTimeout(timer);
            }
            stream.removeListener('data', onData);
            stream.removeListener('end', onEnd);
            stream.removeListener('error', onError);
            stream.removeListener('close', onClose);
            signal?.removeEventListener?.('abort', onAbort);
            token?.unsubscribe?.(onCancel);
        }
        function lose(error: unknown) {
            cleanup();
            stream.on('error', () => undefined);
            stream.destroy?.();
            reject(error);
        }
        if (signal?.aborted) {
            onAbort();
            return;
        }
        if (token?.reason) {
            onCancel(token.reason);
            return;
        }
        readSources.add(stream as object);
        stream.on('data', onData);
        stream.on('end', onEnd);
        stream.on('error', onError);
        stream.on('close', onClose);
        signal?.addEventListener?.('abort', onAbort, { once: true });
        token?.subscribe?.(onCancel);
        if (config.timeout) {
            const clarify = (config.transitional as { clarifyTimeoutError?: boolean } | undefined)?.clarifyTimeoutError;
            timer = setTimeout(
                () => lose(new AxiosError(config.timeoutErrorMessage || `timeout of ${config.timeout}ms exceeded`, clarify ? AxiosError.ETIMEDOUT : AxiosError.ECONNABORTED, config)),
                config.timeout,
            );
        }
        stream.resume?.();
    });
}

/** Let go of the body of a redirect response that is not passed on. */
function discardBody(data: unknown): void {
    const body = data as { destroy?: () => void; cancel?: () => Promise<void> } | null | undefined;
    if (body && typeof body.destroy === 'function') {
        body.destroy();
    } else if (body && typeof body.cancel === 'function') {
        body.cancel().catch(() => undefined);
    }
}

/** A request target in absolute form (`scheme://host/path`), as axios writes it for a request to a proxy. */
const ABSOLUTE_FORM = /^[a-z][a-z0-9+.-]*:\/\//i;

/** A transport for the axios http adapter that creates the request with `http.ClientRequest` and `agent`, so a
 * process-wide wrapper of `http.request` or `https.request` does not pick its agent, and refuses it when its agent is
 * not `agent` or when it is addressed to a proxy. */
function agentTransport(agent: http.Agent, how: string, timeout?: number): { request(options: http.RequestOptions, callback: (response: http.IncomingMessage) => void): http.ClientRequest } {
    return {
        request(options, callback) {
            // A request in absolute form is addressed to a proxy: one that an adapter function set after the request was judged.
            if (ABSOLUTE_FORM.test(String(options.path ?? ''))) {
                throw insecureHttpError(`The request to ${originOf(String(options.path))} cannot be sent ${how}: it is addressed to a proxy set after the client read the request.`);
            }
            // `timeout` also bounds the wait for a connection (a proxy tunnel included), before axios's own timer starts.
            const request = new http.ClientRequest({ ...options, agent, ...(timeout ? { timeout } : {}) }, callback);
            if ((request as unknown as { agent?: unknown }).agent !== agent) {
                request.on('error', () => undefined); // the refusal below is the outcome; a late socket error is not
                request.destroy();
                throw insecureHttpError(`The request to ${options.hostname || options.host} cannot be sent ${how}: the HTTP agent was replaced.`);
            }
            return request;
        },
    };
}

/** The config of the next hop of a redirect, or the refusal. */
function nextHop(config: HopConfig, state: HopState, response: AxiosResponse, keyed: boolean, allowInsecureHttp: unknown): HopConfig {
    const from = requestUrl(config);
    const target = new URL(String(response.headers.location), from);
    const headers = new AxiosHeaders(config.headers);
    let method = (config.method || 'get').toLowerCase();
    let data = config.data;
    if ((response.status === 303 && method !== 'head') || ((response.status === 301 || response.status === 302) && method === 'post')) {
        method = 'get';
        data = undefined;
        headers.delete('Content-Type');
        headers.delete('Content-Length');
    }
    const otherOrigin = originOf(target.href) !== state.origin;
    const carried = otherOrigin && (state.keyed || keyed || carriesKeyFor(sentHeaders(response.request), ownProxyAuthFor(from, state.proxy)) || config.auth != null || hasUserinfo(from));
    // The body of a request that carried a key may hold one too (a provider key, for example): a hop to another origin
    // that keeps the body (a 307 or 308, a 300, or a 301 or 302 of a method other than POST) is not followed.
    if (carried && data !== undefined && data !== null && data !== '') {
        throw insecureHttpError(`The redirect to ${target.host} was not followed: it would send the body of a request that carries credentials to another origin.`);
    }
    if (data !== undefined && isStream(data)) {
        throw bodyTooLong(config); // a streamed body over the copy limit cannot be sent again
    }
    let auth = config.auth;
    if (otherOrigin) {
        if (carried && target.protocol === 'http:' && !(isLoopback(target) && insecureHttpAllowed(allowInsecureHttp))) {
            throw insecureHttpError(`The redirect to ${target.host} was not followed: it leaves ${state.origin} for plain http with credentials.`);
        }
        for (const name of DROPPED_ON_OTHER_ORIGIN) {
            headers.delete(name);
        }
        for (const name of Object.keys(headers.toJSON())) {
            if (isCredentialHeader(name)) {
                headers.delete(name);
            }
        }
        auth = undefined;
    }
    return {
        ...config,
        url: target.href,
        baseURL: undefined,
        params: undefined,
        method,
        data,
        auth,
        headers,
        transport: state.transport,
        httpAgent: state.httpAgent,
        httpsAgent: state.httpsAgent,
        proxy: state.proxy,
        [HOP]: { ...state, keyed: state.keyed || keyed, remaining: state.remaining - 1 },
    };
}

/** A response the redirect loop hands back, settled the way the caller's `validateStatus` asks. */
function settled(response: AxiosResponse, state: HopState): AxiosResponse {
    const status = response.status;
    if (!status || !state.validateStatus || state.validateStatus(status)) {
        return response;
    }
    throw new AxiosError(
        'Request failed with status code ' + status,
        [AxiosError.ERR_BAD_REQUEST, AxiosError.ERR_BAD_RESPONSE][Math.floor(status / 100) - 4],
        response.config,
        response.request,
        response,
    );
}

/** `inner` judged when it is called: refused, sent directly through the http adapter, or handed to `inner`; and a
 * redirect followed hop by hop as described above. */
function judgedAdapter(inner: InternalAxiosRequestConfig['adapter'], allowInsecureHttp: unknown): AxiosAdapter {
    if (typeof inner === 'function' && (inner as Tagged)[JUDGED]) {
        return inner;
    }
    const adapter: AxiosAdapter & Tagged = async (config: HopConfig) => {
        // Headers in `fetchOptions` replace the request headers in the axios fetch adapter: they are read as request
        // headers here (a name in both takes the `fetchOptions` value), so every credential in them is judged.
        const fetchHeaders = (config.fetchOptions as { headers?: unknown } | undefined)?.headers;
        if (fetchHeaders !== undefined && fetchHeaders !== null) {
            config.headers = AxiosHeaders.from(config.headers);
            config.headers.set(flattenHeaders([fetchHeaders]), true);
            const { headers: _folded, ...fetchOptions } = config.fetchOptions as Record<string, unknown>;
            config.fetchOptions = fetchOptions;
        }
        const url = requestUrl(config);
        const keyed = carriesKey(flattenHeaders([config.headers], config.method || 'get')) || config.auth != null || hasUserinfo(url);
        const route = plainHttpRoute(url, keyed, allowInsecureHttp);
        const callerRedirect = (config.fetchOptions as { redirect?: unknown } | undefined)?.redirect;
        const first = config[HOP] === undefined;
        const state: HopState = config[HOP] || {
            origin: originOf(url),
            keyed,
            remaining: config.maxRedirects ?? 21,
            follow: config.maxRedirects !== 0 && callerRedirect !== 'manual' && callerRedirect !== 'error',
            validateStatus: config.validateStatus,
            transport: (config as { transport?: unknown }).transport,
            httpAgent: config.httpAgent,
            httpsAgent: config.httpsAgent,
            proxy: config.proxy,
        };
        if (first && state.follow && !['get', 'head'].includes((config.method || 'get').toLowerCase())) {
            config.data = await replayableBody(config);
        }
        // The redirect is answered here, not by follow-redirects or by fetch.
        config.maxRedirects = 0;
        config.beforeRedirect = undefined;
        if (callerRedirect !== 'error') {
            config.fetchOptions = { ...config.fetchOptions, redirect: 'manual' };
        }
        config.validateStatus = (status: number) => REDIRECT_STATUSES.has(status) || !state.validateStatus || state.validateStatus(status);
        let send: AxiosAdapter;
        // A keyed https request for which a proxy applies (as the axios http adapter chooses it) goes to that proxy only
        // as CONNECT, with TLS to its host inside the tunnel. (A keyed plain-http request that is sent goes directly.)
        // axios sends a request with `socketPath` to that socket, with no proxy.
        // Every hop of a request that started keyed goes the same way, also once its key headers are dropped.
        const proxy = (keyed || state.keyed) && route !== 'direct' && /^https:/i.test(url) && !config.socketPath ? proxyFor(url, state.proxy) : null;
        if (proxy !== null) {
            // A Proxy-Authorization the caller set is for the proxy: it goes on the CONNECT (when the proxy has no user
            // name and password of its own), and not inside the tunnel to the host.
            config.headers = AxiosHeaders.from(config.headers);
            const callerProxyAuth =
                Object.entries(flattenHeaders([config.headers])).find(([name]) => name.trim().toLowerCase() === 'proxy-authorization')?.[1] ??
                (originOf(url) === state.origin ? state.proxyAuthorization : undefined);
            config.headers.delete('Proxy-Authorization');
            if (first) {
                state.proxyAuthorization = callerProxyAuth;
            }
            if (proxy.auth === undefined && callerProxyAuth !== undefined && callerProxyAuth.trim() !== '') {
                proxy.authorization = callerProxyAuth;
            }
            const settings = tlsSettingsOf(state.httpsAgent);
            const agent = tunnelAgent({ http, https, net, tls }, proxy, true, settings, settings ? (state.httpsAgent as object) : undefined);
            config.proxy = false;
            config.httpAgent = agent;
            config.httpsAgent = agent;
            (config as { transport?: unknown }).transport = agentTransport(agent, 'through the proxy tunnel', config.timeout);
            // The axios fetch adapter does not take an agent: the request goes through the http adapter instead.
            const chosen = axios.getAdapter(inner || axios.defaults.adapter);
            send = chosen === axios.getAdapter('fetch') ? axios.getAdapter('http') : chosen;
        } else if (route === 'direct') {
            // No proxy is on this route: a Proxy-Authorization the caller or an interceptor set does not go to the host.
            config.headers = AxiosHeaders.from(config.headers);
            config.headers.delete('Proxy-Authorization');
            const agent = directHttpAgent(http);
            config.proxy = false;
            config.httpAgent = agent;
            (config as { transport?: unknown }).transport = agentTransport(agent, 'directly over plain http');
            send = axios.getAdapter('http');
        } else {
            // A key or a proxy added after this point (by an adapter function of the caller's) is read again when the
            // request is created, on the agent that sends it, so a keyed request (or a hop of one) that would reach a
            // proxy chosen there outside a tunnel is refused. The agents stay as the caller set them: axios reads them and
            // `transport` after the adapter function has run, so an agent that the function sets is the one that sends
            // the request, and it is the one judged.
            (config as { transport?: unknown }).transport = judgedTransport((config as { transport?: unknown }).transport, allowInsecureHttp, keyed || state.keyed);
            send = axios.getAdapter(inner || axios.defaults.adapter);
        }
        const response = await send(config);
        if (!state.follow || !REDIRECT_STATUSES.has(response.status) || !response.headers?.location) {
            return settled(response, state);
        }
        if (state.remaining <= 0) {
            throw new AxiosError('Maximum number of redirects exceeded', 'ERR_FR_TOO_MANY_REDIRECTS', config, response.request, response);
        }
        discardBody(response.data);
        return adapter(nextHop(config, state, response, keyed, allowInsecureHttp));
    };
    adapter[JUDGED] = true;
    return adapter;
}

type AgentInternals = http.Agent & Tagged & { addRequest(request: http.ClientRequest, options: Record<string, unknown>): void };
type RequestInternals = http.ClientRequest & { _header?: string | null; onSocket(socket: unknown, error?: Error): void };
type Transport = { request(options: http.RequestOptions, callback?: (response: http.IncomingMessage) => void): http.ClientRequest };

/** The `transport` of the caller's that a judging transport wraps (`undefined`: none). */
const callerTransports = new WeakMap<object, Transport | undefined>();

/** A transport for the axios http adapter that creates each request with the agent axios chose for it, read by
 * `judgedAgent` for that request only: the caller's `httpsAgent` for a request that goes over TLS (to its host or to an
 * https proxy) and `httpAgent` for the others, as the config holds them when axios reads them, else the global agent of
 * that protocol (a fresh agent of it for `agent: false`). The request is created by `callerTransport` when it is given,
 * else by `https` or `http` as axios chooses them. `chainKeyed`: see `judgedAgent`. */
function judgedTransport(callerTransport: unknown, allowInsecureHttp: unknown, chainKeyed: boolean): Transport {
    const own = (callerTransport !== null && typeof callerTransport === 'object' && callerTransports.has(callerTransport)
        ? callerTransports.get(callerTransport)
        : callerTransport) as Transport | undefined;
    const transport: Transport = {
        request(options, callback) {
            const secure = /https:?/.test(String(options.protocol ?? ''));
            const protocolModule = secure ? https : http;
            const given = options.agent as http.Agent | false | null | undefined;
            const chosen = given === undefined || given === null ? protocolModule.globalAgent : given === false ? new protocolModule.Agent() : given;
            const agent = typeof (chosen as Partial<AgentInternals>).addRequest === 'function' ? judgedAgent(chosen, allowInsecureHttp, secure, chainKeyed) : chosen;
            return (own ?? protocolModule).request({ ...options, agent }, callback);
        },
    };
    callerTransports.set(transport, own);
    return transport;
}

/** `inner` with the request judged when Node creates it: its headers then hold every key, including the Authorization
 * made from axios `auth` or a user name in the URL. A keyed plain-http request is refused (no connection is made) or
 * handed to the direct agent; a keyed request for an https address that would reach a proxy outside a tunnel (in
 * absolute form) is refused; any other request goes to `inner` as it is. `secure`: `inner` makes TLS connections.
 * Other functions read through the wrapper run with `inner` as `this`, so methods with private fields keep working.
 * A Proxy-Authorization on a request in absolute form is addressed to the proxy it goes to, and is not read as a key.
 * `chainKeyed`: the request is a hop of a keyed request, so in absolute form it counts as keyed. */
function judgedAgent(inner: http.Agent, allowInsecureHttp: unknown, secure = false, chainKeyed = false): http.Agent {
    if ((inner as AgentInternals)[JUDGED]) {
        return inner;
    }
    return new Proxy(inner as AgentInternals, {
        get(target, name) {
            if (name === JUDGED) {
                return true;
            }
            if (name === 'addRequest') {
                return (request: RequestInternals, options: Record<string, unknown>) => {
                    const absolute = ABSOLUTE_FORM.test(request.path);
                    const headers = request.getHeaders();
                    const judged = absolute ? Object.fromEntries(Object.entries(headers).filter(([name]) => name.trim().toLowerCase() !== 'proxy-authorization')) : headers;
                    if (!carriesKey(judged) && !(absolute && chainKeyed)) {
                        return target.addRequest(request, options);
                    }
                    if (absolute && !/^http:/i.test(request.path)) {
                        return request.onSocket(null, insecureHttpError(`The request to ${originOf(request.path)} was not sent: it carries credentials and would reach a proxy outside a CONNECT tunnel.`));
                    }
                    if (!absolute && secure) {
                        return target.addRequest(request, options);
                    }
                    const host = String(options.host || options.hostname || 'localhost');
                    const url = absolute ? request.path : `http://${host.includes(':') && !host.startsWith('[') ? `[${host}]` : host}:${options.port || 80}${request.path}`;
                    let route: string;
                    try {
                        route = plainHttpRoute(url, true, allowInsecureHttp);
                    } catch (error) {
                        return request.onSocket(null, error as Error);
                    }
                    if (route !== 'direct') {
                        return target.addRequest(request, options);
                    }
                    if (request._header) {
                        return request.onSocket(null, insecureHttpError(`The request to ${new URL(url).host} cannot be sent directly over plain http.`));
                    }
                    const destination = new URL(url);
                    const hostname = destination.hostname.replace(/^\[|\]$/g, '');
                    request.path = destination.pathname + destination.search;
                    request.removeHeader('proxy-authorization');
                    return (directHttpAgent(http) as AgentInternals).addRequest(request, { ...options, host: hostname, hostname, port: Number(destination.port) || 80, path: request.path });
                };
            }
            const value: unknown = Reflect.get(target, name, target);
            return typeof value === 'function' && name !== 'constructor' ? value.bind(target) : value;
        },
    });
}

/** Error codes of a request that is refused rather than failed: sending it again gives the same answer. */
const NOT_RETRIED = new Set([
    AxiosError.ERR_BAD_REQUEST, AxiosError.ERR_BAD_OPTION, AxiosError.ERR_BAD_OPTION_VALUE, AxiosError.ERR_CANCELED, AxiosError.ERR_INVALID_URL,
    'ERR_FR_MAX_BODY_LENGTH_EXCEEDED', 'ERR_FR_TOO_MANY_REDIRECTS', 'ERR_TLS_CERT_ALTNAME_INVALID', 'DEPTH_ZERO_SELF_SIGNED_CERT',
    'SELF_SIGNED_CERT_IN_CHAIN', 'UNABLE_TO_VERIFY_LEAF_SIGNATURE', 'UNABLE_TO_GET_ISSUER_CERT', 'UNABLE_TO_GET_ISSUER_CERT_LOCALLY',
    'CERT_HAS_EXPIRED', 'CERT_NOT_YET_VALID', 'CERT_REVOKED', 'CERT_UNTRUSTED', 'CERT_REJECTED', 'CERT_SIGNATURE_FAILURE',
    'HOSTNAME_MISMATCH', 'ERR_SSL_WRONG_VERSION_NUMBER',
]);

/** Whether an error without an HTTP response is a refusal (see `NOT_RETRIED`, and a proxy's refusal of a tunnel). */
function notRetried(error: AxiosError): boolean {
    return (error.code !== undefined && NOT_RETRIED.has(error.code)) || isTunnelRefusal(error);
}

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
    defaultHeaders?: Record<string, string>;
    timeout?: number;
    maxQueue?: number;
    maxWorkers?: number;
    retryAttempts?: number;
    retryDelay?: number;
    /** Send keyed requests over plain http to hosts that are not loopback (also FI_ALLOW_INSECURE_HTTP=1). */
    allowInsecureHttp?: boolean;
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

    constructor(config: HttpClientConfig = {}) {
        this._baseUrl = (config.baseUrl || get_base_url()).replace(/\/$/, '');
        this._defaultTimeout = config.timeout || DEFAULT_SETTINGS.TIMEOUT;
        this._defaultRetryAttempts = config.retryAttempts || 3;
        this._defaultRetryDelay = config.retryDelay || 1000;

        // Create axios instance with default configuration
        this._axiosInstance = axios.create({
            baseURL: this._baseUrl,
            timeout: this._defaultTimeout,
            headers: {
                'Content-Type': 'application/json',
                'User-Agent': '@future-agi/sdk',
                ...config.defaultHeaders,
            },
            // Enable connection pooling
            maxRedirects: 5,
            validateStatus: () => true, // Handle all status codes manually
        });

        // Create bounded executor for managing concurrent requests
        this._executor = new BoundedExecutor(
            config.maxQueue || DEFAULT_SETTINGS.MAX_QUEUE,
            config.maxWorkers || DEFAULT_SETTINGS.MAX_WORKERS
        );

        this._setupInterceptors(config.allowInsecureHttp);
    }

    /**
     * Setup request and response interceptors
     */
    private _setupInterceptors(allowInsecureHttp?: boolean): void {
        this._axiosInstance.defaults.adapter = judgedAdapter(this._axiosInstance.defaults.adapter, allowInsecureHttp);
        // Request interceptor for logging and debugging
        this._axiosInstance.interceptors.request.use(
            (config) => {
                // An adapter given for this request is judged as well; the last transform covers one set after this point.
                config.adapter = judgedAdapter(config.adapter, allowInsecureHttp);
                const transforms = config.transformRequest === undefined ? [] : Array.isArray(config.transformRequest) ? config.transformRequest : [config.transformRequest];
                config.transformRequest = [
                    ...transforms,
                    function judgedAtSend(this: InternalAxiosRequestConfig, data: unknown) {
                        this.adapter = judgedAdapter(this.adapter, allowInsecureHttp);
                        return data;
                    },
                ];
                // Add request timestamp for performance monitoring
                (config as any).startTime = Date.now();
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
     * Make an HTTP request with retries and response handling
     */
    async request<T = any>(
        config: RequestConfig, 
        responseHandler?: typeof ResponseHandler
    ): Promise<T | AxiosResponse> {
        const requestConfig: AxiosRequestConfig = {
            method: config.method,
            url: config.url,
            headers: config.headers,
            params: config.params,
            data: config.json || config.data,
            timeout: config.timeout || this._defaultTimeout,
            ...(config.responseType ? { responseType: config.responseType } : {}),
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

                    if (responseHandler) {
                        return ResponseHandler.parse<T, any>(response, responseHandler);
                    }
                    
                    // Handle errors if no custom handler
                    if (response.status >= 400) {
                        ResponseHandler._handleError(response);
                    }

                    return response;
                } catch (error) {
                    // Don't retry certain errors
                    const refusal = insecureHttpCause(error); // also when an HTTP library wrapped it
                    if (refusal) {
                        throw refusal;
                    }
                    if (error instanceof DatasetNotFoundError || 
                        error instanceof InvalidAuthError ||
                        (error instanceof AxiosError && error.response?.status === 401)) {
                        throw error;
                    }

                    // A request that got no HTTP response keeps its own error and code; a refusal is not sent again.
                    const unanswered = error instanceof AxiosError && !error.response;
                    if (error instanceof AxiosError && (unanswered || error.code === 'ERR_FR_TOO_MANY_REDIRECTS') && notRetried(error)) {
                        throw error;
                    }

                    // Last attempt, or a streamed body that was read and cannot be sent again - throw the error
                    if (attempt === retryAttempts - 1 || bodyConsumed(requestConfig.data)) {
                        if (error instanceof AxiosError && error.response) {
                            ResponseHandler._handleError(error.response);
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
        const fiApiKey = config.fiApiKey ?? process.env[AUTH_ENVVAR_NAME.API_KEY];
        const fiSecretKey = config.fiSecretKey ?? process.env[AUTH_ENVVAR_NAME.SECRET_KEY];

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
