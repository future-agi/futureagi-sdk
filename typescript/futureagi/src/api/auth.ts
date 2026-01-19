import axios, { AxiosInstance, AxiosResponse, AxiosRequestConfig, AxiosError } from 'axios';
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

/**
 * Generic response handler for parsing and validating HTTP responses
 */
export abstract class ResponseHandler<T = any, U = any> {
    /**
     * Parse the response into the expected type
     */
    static parse<T, U>(response: AxiosResponse, handlerClass: typeof ResponseHandler): T | U {
        if (!response || response.status !== 200) {
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
                    if (error instanceof DatasetNotFoundError || 
                        error instanceof InvalidAuthError ||
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
