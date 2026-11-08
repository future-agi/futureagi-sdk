// Generated public declarations from @future-agi/sdk 0.1.2; do not edit.
import { AxiosInstance, AxiosResponse } from 'axios';
import { BoundedExecutor } from '../utils/executor.js';
import { RequestConfig } from './types.js';
/**
 * Generic response handler for parsing and validating HTTP responses
 */
export declare abstract class ResponseHandler<T = any, U = any> {
    /**
     * Parse the response into the expected type
     */
    static parse<T, U>(response: AxiosResponse, handlerClass: typeof ResponseHandler): T | U;
    /**
     * Parse successful response - to be implemented by subclasses
     */
    static _parseSuccess(response: AxiosResponse): any;
    /**
     * Handle error responses - to be implemented by subclasses
     */
    static _handleError(response: AxiosResponse): never;
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
export declare class HttpClient {
    constructor(config?: HttpClientConfig);
    /**
     * Make an HTTP request with retries and response handling
     */
    request<T = any>(config: RequestConfig, responseHandler?: typeof ResponseHandler): Promise<T | AxiosResponse>;
    /**
     * Close the client and cleanup resources
     */
    close(): Promise<void>;
    /**
     * Get the base URL
     */
    get baseUrl(): string;
    /**
     * Get the default timeout
     */
    get defaultTimeout(): number;
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
export declare class APIKeyAuth extends HttpClient {
    constructor(config?: APIKeyAuthConfig);
    /**
     * Get the current API key
     */
    get fiApiKey(): string | undefined;
    /**
     * Get the current secret key
     */
    get fiSecretKey(): string | undefined;
    /**
     * Get authentication headers
     */
    get headers(): Record<string, string>;
}
/**
 * Factory function to create authenticated HTTP client
 */
export declare function createAuthenticatedClient(config?: APIKeyAuthConfig): APIKeyAuth;
declare const _default: {
    ResponseHandler: typeof ResponseHandler;
    HttpClient: typeof HttpClient;
    APIKeyAuth: typeof APIKeyAuth;
    createAuthenticatedClient: typeof createAuthenticatedClient;
};
export default _default;
export type PublishedCall1582 = <T = any>(config: RequestConfig, responseHandler?: typeof ResponseHandler) => Promise<T | AxiosResponse>;
export type PublishedCall1849 = () => Promise<void>;
export type PublishedCall297 = <T, U>(response: AxiosResponse, handlerClass: typeof ResponseHandler) => T | U;
export type PublishedCall456 = (response: AxiosResponse) => any;
export type PublishedCall595 = (response: AxiosResponse) => never;
export type PublishedCall2771 = (config?: APIKeyAuthConfig) => APIKeyAuth;
