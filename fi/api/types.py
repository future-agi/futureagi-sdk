from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel


class HttpMethod(Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"


class RequestConfig(BaseModel):
    """Configuration for an HTTP request"""

    method: HttpMethod
    url: str
    headers: Optional[Dict[str, str]] = {}
    params: Optional[Dict[str, Any]] = {}
    files: Optional[Dict[str, Any]] = {}
    data: Optional[Dict[str, Any]] = {}
    json: Optional[Dict[str, Any]] = {}
    timeout: Optional[int] = None
    retry_attempts: int = 3
    retry_delay: float = 1.0


class ModelProvider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    AZURE = "azure"
    AWS = "aws"
    COHERE = "cohere"
    FIREWORKS = "fireworks_ai"
    ANYSCALE = "anyscale"
    PERPLEXITY = "perplexity"
    DEEPINFRA = "deepinfra"
    OLLAMA = "ollama"
    CLOUDFLARE = "cloudflare"
    VOYAGE = "voyage"
    DATABRICKS = "databricks"
    TEXT_COMPLETION_OPENAI = "text-completion-openai"
    TEXT_COMPLETION_CODESTRAL = "text-completion-codestral"
    FIREWORKS_EMBEDDING = "fireworks_ai-embedding-models"
    VERTEX_AI_TEXT = "vertex_ai-text-models"
    VERTEX_AI_CHAT = "vertex_ai-chat-models"
    VERTEX_AI_CODE_TEXT = "vertex_ai-code-text-models"
    SAGEMAKER = "sagemaker"
    BEDROCK = "bedrock"
    TOGETHER_AI = "together_ai"
    MISTRAL = "mistral"
    DEEPSEEK = "deepseek"
    CODESTRAL = "codestral"
    GROQ = "groq"
    CEREBRAS = "cerebras"
    FRIENDLIAI = "friendliai"
    AZURE_AI = "azure_ai"
    HUGGINGFACE = "huggingface"


class ApiKey(BaseModel):
    provider: Optional[ModelProvider] = None
    key: Optional[str] = None
