import { APIKeyAuth, ResponseHandler } from './auth';
import { AUTH_ENVVAR_NAME, get_base_url } from '../utils/constants';
import { ModelProvider, ApiKey, RequestConfig, HttpMethod } from './types';
import { Routes } from '../utils/routes';
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
class ProviderAPIKeyResponseHandler extends ResponseHandler<ApiKey | ApiKey[] | ApiKeySetResponse, any> {
    /**
     * Parse successful API key response
     */
    public static _parseSuccess(response: AxiosResponse): ApiKey | ApiKey[] | ApiKeySetResponse {
        const data = response.data;
        const method = response.config.method?.toUpperCase();

        if (method === HttpMethod.POST) {
            return {
                success: true
            } as ApiKeySetResponse;
        } else if (method === HttpMethod.GET) {
            const results = data.results || data;
            if (Array.isArray(results)) {
                return results.map(apiKey => ({
                    provider: apiKey.provider,
                    key: apiKey.key
                } as ApiKey));
            }
            return results;
        } else {
            return data;
        }
    }

    /**
     * Handle API key operation errors
     */
    public static _handleError(response: AxiosResponse): never {
        if (response.status >= 400) {
            const message = response.data?.message || response.statusText || 'API key operation failed';
            throw new Error(`API Key Error [${response.status}]: ${message}`);
        }
        throw new Error('Unknown API key error');
    }
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
class ProviderAPIKeyClient extends APIKeyAuth {
    public apiKey: ApiKey;

    constructor(
        apiKey: ApiKey,
        fiApiKey?: string,
        fiSecretKey?: string,
        fiBaseUrl?: string
    ) {
        super({
            fiApiKey,
            fiSecretKey,
            fiBaseUrl
        });
        this.apiKey = apiKey;
    }

    // Instance methods for chaining
    /**
     * Set the API key and return self for chaining
     */
    async set(): Promise<ProviderAPIKeyClient> {
        if (!this.apiKey.key) {
            throw new Error('API key is required');
        }
        await this._setApiKey(this.apiKey);
        return this;
    }

    /**
     * Get the API key by provider
     */
    async get(): Promise<ApiKey | undefined> {
        if (!this.apiKey.provider) {
            throw new Error('Provider is required');
        }
        const response = await this._getApiKey(this.apiKey.provider);
        if (response) {
            this.apiKey = response;
        }
        return response;
    }

    // Protected internal methods
    /**
     * Internal method for setting API key
     */
    private async _setApiKey(apiKey: ApiKey): Promise<ApiKey> {
        const response = await this.request(
            {
                method: HttpMethod.POST,
                url: `${this.baseUrl}/${Routes.model_hub_api_keys}`,
                json: {
                    provider: apiKey.provider,
                    key: apiKey.key
                }
            } as RequestConfig,
            ProviderAPIKeyResponseHandler
        );
        return response as ApiKey;
    }

    /**
     * Internal method to get API key by provider
     */
    private async _getApiKey(provider: ModelProvider): Promise<ApiKey | undefined> {
        const response = await this.request(
            {
                method: HttpMethod.GET,
                url: `${this.baseUrl}/${Routes.model_hub_api_keys}`
            } as RequestConfig,
            ProviderAPIKeyResponseHandler
        ) as ApiKey[];

        if (Array.isArray(response)) {
            return response.find(apiKey => apiKey.provider === provider);
        }
        return undefined;
    }

    // Class methods for simple operations
    /**
     * Create a new ProviderAPIKeyClient instance
     */
    private static _getInstance(apiKey: ApiKey, options: {
        fiApiKey?: string;
        fiSecretKey?: string;
        fiBaseUrl?: string;
    } = {}): ProviderAPIKeyClient {
        return new ProviderAPIKeyClient(
            apiKey,
            options.fiApiKey,
            options.fiSecretKey,
            options.fiBaseUrl
        );
    }

    /**
     * Class method for simple API key creation
     */
    static async setApiKey(apiKey: ApiKey, options: {
        fiApiKey?: string;
        fiSecretKey?: string;
        fiBaseUrl?: string;
    } = {}): Promise<ApiKey> {
        const instance = this._getInstance(apiKey, options);
        await instance.set();
        return instance.apiKey;
    }

    /**
     * Class method for simple API key retrieval
     */
    static async getApiKey(provider: ModelProvider, options: {
        fiApiKey?: string;
        fiSecretKey?: string;
        fiBaseUrl?: string;
    } = {}): Promise<ApiKey | undefined> {
        const apiKey: ApiKey = { provider };
        const instance = this._getInstance(apiKey, options);
        return await instance.get();
    }

    /**
     * List all API keys for the organization
     */
    static async listApiKeys(options: {
        fiApiKey?: string;
        fiSecretKey?: string;
        fiBaseUrl?: string;
    } = {}): Promise<ApiKey[]> {
        // The apiKey object is required for the constructor, but not used in this method.
        const instance = this._getInstance({} as ApiKey, options);
        const response = await instance.request(
            {
                method: HttpMethod.GET,
                url: `${instance.baseUrl}/${Routes.model_hub_api_keys}`
            } as RequestConfig,
            ProviderAPIKeyResponseHandler
        );
        return Array.isArray(response) ? response : [];
    }
}

/**
 * Singleton API Key Manager for managing FutureAGI credentials (fi_api_key, fi_secret_key)
 */
class APIKeyManager extends APIKeyAuth {
    private static _instance?: APIKeyManager;
    private _initialized = false;

    private constructor() {
        super();
        const fiApiKey = this.getFiApiKey();
        const fiSecretKey = this.getFiSecretKey();

        if (!fiApiKey || !fiSecretKey) {
            console.warn('FutureAGI credentials not found in environment variables. Please set FI_API_KEY and FI_SECRET_KEY.');
        }
    }

    /**
     * Get the singleton instance
     */
    public static getInstance(): APIKeyManager {
        if (!APIKeyManager._instance) {
            APIKeyManager._instance = new APIKeyManager();
        }
        return APIKeyManager._instance;
    }

    /**
     * Get the API URL for key management
     */
    get url(): string {
        return `${this.baseUrl}/${Routes.model_hub_api_keys}`;
    }

    /**
     * Get FutureAGI API key
     */
    getFiApiKey(): string | undefined {
        return this.fiApiKey;
    }

    /**
     * Get FutureAGI secret key
     */
    getFiSecretKey(): string | undefined {
        return this.fiSecretKey;
    }

    /**
     * Check if FutureAGI credentials are configured
     */
    isAuthenticated(): boolean {
        return !!(this.getFiApiKey() && this.getFiSecretKey());
    }

    /**
     * Get authentication headers for FutureAGI API
     */
    getAuthHeaders(): Record<string, string> {
        const apiKey = this.getFiApiKey();
        const secretKey = this.getFiSecretKey();
        
        if (!apiKey || !secretKey) {
            throw new Error('FutureAGI credentials not configured');
        }

        return {
            'X-Api-Key': apiKey,
            'X-Secret-Key': secretKey
        };
    }

    /**
     * Provider API key operations (delegated to ProviderAPIKeyClient)
     */

    /**
     * Set a provider API key via FutureAGI API
     */
    async setProviderApiKey(provider: ModelProvider, key: string): Promise<void> {
        await ProviderAPIKeyClient.setApiKey({ provider, key }, {
            fiApiKey: this.getFiApiKey(),
            fiSecretKey: this.getFiSecretKey()
        });
    }

    /**
     * Get a provider API key via FutureAGI API
     */
    async getProviderApiKey(provider: ModelProvider): Promise<ApiKey | undefined> {
        return await ProviderAPIKeyClient.getApiKey(provider, {
            fiApiKey: this.getFiApiKey(),
            fiSecretKey: this.getFiSecretKey()
        });
    }

    /**
     * List all provider API keys via FutureAGI API
     */
    async listProviderApiKeys(): Promise<ApiKey[]> {
        return await ProviderAPIKeyClient.listApiKeys({
            fiApiKey: this.getFiApiKey(),
            fiSecretKey: this.getFiSecretKey()
        });
    }

    /**
     * Check if a provider API key is configured
     */
    async isProviderConfigured(provider: ModelProvider): Promise<boolean> {
        try {
            const apiKey = await this.getProviderApiKey(provider);
            return !!apiKey;
        } catch (error: any) {
            if (error.message && error.message.includes('404')) {
                return false;
            }
            throw error;
        }
    }

    /**
     * Validate that required provider API keys are present
     */
    async validateRequiredProviders(requiredProviders: ModelProvider[]): Promise<boolean> {
        if (!requiredProviders || requiredProviders.length === 0) {
            return true;
        }

        const results = await Promise.allSettled(
            requiredProviders.map(provider => this.isProviderConfigured(provider))
        );

        const missingProviders = requiredProviders.filter((provider, index) => {
            const result = results[index];
            return result.status === 'rejected' || !result.value;
        });

        if (missingProviders.length > 0) {
            throw new Error(`Missing required provider API keys: ${missingProviders.join(', ')}`);
        }

        return true;
    }

    /**
     * Reset the singleton instance (mainly for testing)
     */
    static resetInstance(): void {
        if (APIKeyManager._instance) {
            APIKeyManager._instance.close();
            APIKeyManager._instance = undefined;
        }
    }
}

/**
 * Factory function to get API key manager instance
 */
function getAPIKeyManager(): APIKeyManager {
    return APIKeyManager.getInstance();
}

/**
 * Helper function to check if a provider is supported
 */
function isSupportedProvider(provider: string): provider is ModelProvider {
    return Object.values(ModelProvider).includes(provider as ModelProvider);
}

/**
 * Get all supported providers
 */
function getSupportedProviders(): ModelProvider[] {
    return Object.values(ModelProvider);
}

export {
    APIKeyManager,
    ProviderAPIKeyClient,
    ProviderAPIKeyResponseHandler,
    getAPIKeyManager,
    isSupportedProvider,
    getSupportedProviders,
    ApiKeyConfig,
    ApiKeySetResponse,
    ApiKey,
    RequestConfig,
    HttpMethod,
    ModelProvider,
};
