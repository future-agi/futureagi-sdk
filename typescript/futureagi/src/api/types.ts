enum HttpMethod {
    GET = "GET",
    POST = "POST",
    PUT = "PUT",
    DELETE = "DELETE",
    PATCH = "PATCH"
}

interface RequestConfig {
    /** Configuration for an HTTP request */
    method: HttpMethod;
    url: string;
    headers?: Record<string, string>;
    params?: Record<string, any>;
    files?: Record<string, any>;
    data?: Record<string, any>;
    json?: Record<string, any>;
    timeout?: number;
    retry_attempts?: number;
    retry_delay?: number;
}

enum ModelProvider {
    OPENAI = "openai",
    ANTHROPIC = "anthropic",
    GOOGLE = "google",
    AZURE = "azure",
    AWS = "aws",
    COHERE = "cohere",
    FIREWORKS = "fireworks_ai",
    ANYSCALE = "anyscale",
    PERPLEXITY = "perplexity",
    DEEPINFRA = "deepinfra",
    OLLAMA = "ollama",
    CLOUDFLARE = "cloudflare",
    VOYAGE = "voyage",
    DATABRICKS = "databricks",
    TEXT_COMPLETION_OPENAI = "text-completion-openai",
    TEXT_COMPLETION_CODESTRAL = "text-completion-codestral",
    FIREWORKS_EMBEDDING = "fireworks_ai-embedding-models",
    VERTEX_AI_TEXT = "vertex_ai-text-models",
    VERTEX_AI_CHAT = "vertex_ai-chat-models",
    VERTEX_AI_CODE_TEXT = "vertex_ai-code-text-models",
    SAGEMAKER = "sagemaker",
    BEDROCK = "bedrock",
    TOGETHER_AI = "together_ai",
    MISTRAL = "mistral",
    DEEPSEEK = "deepseek",
    CODESTRAL = "codestral",
    GROQ = "groq",
    CEREBRAS = "cerebras",
    FRIENDLIAI = "friendliai",
    AZURE_AI = "azure_ai",
    HUGGINGFACE = "huggingface"
}

interface ApiKey {
    provider?: ModelProvider;
    key?: string;
}

export { HttpMethod, RequestConfig, ModelProvider, ApiKey };