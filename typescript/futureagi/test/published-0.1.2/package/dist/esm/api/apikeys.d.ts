// Generated public declarations from @future-agi/sdk 0.1.2; do not edit.
import { APIKeyAuth, ResponseHandler } from './auth.js';
import { ModelProvider, ApiKey, RequestConfig, HttpMethod } from './types.js';
import { AxiosResponse } from 'axios';
/**
 * Interface for API key configuration
 */
interface ApiKeyConfig {
    provider: ModelProvider;
    key: string;
    isValid?: boolean;
    lastValidated?: Date;
}
/**
 * Interface for API key set response
 */
interface ApiKeySetResponse {
    success: boolean;
}
/**
 * Response handler for API key operations
 */
declare class ProviderAPIKeyResponseHandler extends ResponseHandler<ApiKey | ApiKey[] | ApiKeySetResponse, any> {
    /**
     * Parse successful API key response
     */
    static _parseSuccess(response: AxiosResponse): ApiKey | ApiKey[] | ApiKeySetResponse;
    /**
     * Handle API key operation errors
     */
    static _handleError(response: AxiosResponse): never;
}
/**
 * Client for API key operations
 *
 * This client can be used in two ways:
 * 1. As class methods for simple one-off operations:
 *    ProviderAPIKeyClient.setApiKey(apiKey)
 *
 * 2. As an instance for chained operations:
 *    client = new ProviderAPIKeyClient(apiKey)
 *    client.set().get()
 */
declare class ProviderAPIKeyClient extends APIKeyAuth {
    apiKey: ApiKey;
    constructor(apiKey: ApiKey, fiApiKey?: string, fiSecretKey?: string, fiBaseUrl?: string);
    /**
     * Set the API key and return self for chaining
     */
    set(): Promise<ProviderAPIKeyClient>;
    /**
     * Get the API key by provider
     */
    get(): Promise<ApiKey | undefined>;
    /**
     * Class method for simple API key creation
     */
    static setApiKey(apiKey: ApiKey, options?: {
        fiApiKey?: string;
        fiSecretKey?: string;
        fiBaseUrl?: string;
    }): Promise<ApiKey>;
    /**
     * Class method for simple API key retrieval
     */
    static getApiKey(provider: ModelProvider, options?: {
        fiApiKey?: string;
        fiSecretKey?: string;
        fiBaseUrl?: string;
    }): Promise<ApiKey | undefined>;
    /**
     * List all API keys for the organization
     */
    static listApiKeys(options?: {
        fiApiKey?: string;
        fiSecretKey?: string;
        fiBaseUrl?: string;
    }): Promise<ApiKey[]>;
}
/**
 * Singleton API Key Manager for managing FutureAGI credentials (fi_api_key, fi_secret_key)
 */
declare class APIKeyManager extends APIKeyAuth {
    /**
     * Get the singleton instance
     */
    static getInstance(): APIKeyManager;
    /**
     * Get the API URL for key management
     */
    get url(): string;
    /**
     * Get FutureAGI API key
     */
    getFiApiKey(): string | undefined;
    /**
     * Get FutureAGI secret key
     */
    getFiSecretKey(): string | undefined;
    /**
     * Check if FutureAGI credentials are configured
     */
    isAuthenticated(): boolean;
    /**
     * Get authentication headers for FutureAGI API
     */
    getAuthHeaders(): Record<string, string>;
    /**
     * Provider API key operations (delegated to ProviderAPIKeyClient)
     */
    /**
     * Set a provider API key via FutureAGI API
     */
    setProviderApiKey(provider: ModelProvider, key: string): Promise<void>;
    /**
     * Get a provider API key via FutureAGI API
     */
    getProviderApiKey(provider: ModelProvider): Promise<ApiKey | undefined>;
    /**
     * List all provider API keys via FutureAGI API
     */
    listProviderApiKeys(): Promise<ApiKey[]>;
    /**
     * Check if a provider API key is configured
     */
    isProviderConfigured(provider: ModelProvider): Promise<boolean>;
    /**
     * Validate that required provider API keys are present
     */
    validateRequiredProviders(requiredProviders: ModelProvider[]): Promise<boolean>;
    /**
     * Reset the singleton instance (mainly for testing)
     */
    static resetInstance(): void;
}
/**
 * Factory function to get API key manager instance
 */
declare function getAPIKeyManager(): APIKeyManager;
/**
 * Helper function to check if a provider is supported
 */
declare function isSupportedProvider(provider: string): provider is ModelProvider;
/**
 * Get all supported providers
 */
declare function getSupportedProviders(): ModelProvider[];
export { APIKeyManager, ProviderAPIKeyClient, ProviderAPIKeyResponseHandler, getAPIKeyManager, isSupportedProvider, getSupportedProviders, ApiKeyConfig, ApiKeySetResponse, ApiKey, RequestConfig, HttpMethod, ModelProvider, };
export type PublishedCall2900 = () => string | undefined;
export type PublishedCall2984 = () => string | undefined;
export type PublishedCall3074 = () => boolean;
export type PublishedCall3175 = () => Record<string, string>;
export type PublishedCall3289 = (provider: ModelProvider, key: string) => Promise<void>;
export type PublishedCall3516 = (provider: ModelProvider) => Promise<ApiKey | undefined>;
export type PublishedCall3657 = () => Promise<ApiKey[]>;
export type PublishedCall3771 = (provider: ModelProvider) => Promise<boolean>;
export type PublishedCall3905 = (requiredProviders: ModelProvider[]) => Promise<boolean>;
export type PublishedCall2728 = () => APIKeyManager;
export type PublishedCall4066 = () => void;
export type PublishedCall1343 = () => Promise<ProviderAPIKeyClient>;
export type PublishedCall1453 = () => Promise<ApiKey | undefined>;
export type PublishedCall1816 = (apiKey: ApiKey, options?: {
    fiApiKey?: string;
    fiSecretKey?: string;
    fiBaseUrl?: string;
}) => Promise<ApiKey>;
export type PublishedCall2039 = (provider: ModelProvider, options?: {
    fiApiKey?: string;
    fiSecretKey?: string;
    fiBaseUrl?: string;
}) => Promise<ApiKey | undefined>;
export type PublishedCall2284 = (options?: {
    fiApiKey?: string;
    fiSecretKey?: string;
    fiBaseUrl?: string;
}) => Promise<ApiKey[]>;
export type PublishedCall608 = (response: AxiosResponse) => ApiKey | ApiKey[] | ApiKeySetResponse;
export type PublishedCall755 = (response: AxiosResponse) => never;
export type PublishedCall4175 = () => APIKeyManager;
export type PublishedCall4433 = () => ModelProvider[];
export type PublishedCall4287 = (provider: string) => provider is ModelProvider;
