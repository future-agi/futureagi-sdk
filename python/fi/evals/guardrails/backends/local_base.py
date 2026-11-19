"""
Base class for Local Model Backends.

Provides common functionality for running HuggingFace models locally,
either via VLLM server or direct transformers loading.
"""

import os
import time
from abc import abstractmethod
from typing import Any, Dict, List, Optional, Tuple

from fi.evals.guardrails.backends.base import BaseBackend
from fi.evals.guardrails.backends.vllm_client import VLLMClient, get_vllm_url
from fi.evals.guardrails.config import GuardrailModel, RailType
from fi.evals.guardrails.types import GuardrailResult


from ._local_base_local_model_backend_resolve_server_model import _LocalModelBackendResolveServerModelMethods
from ._local_base_local_model_backend_classify_async import _LocalModelBackendClassifyAsyncMethods

class LocalModelBackend(
    _LocalModelBackendResolveServerModelMethods,
    _LocalModelBackendClassifyAsyncMethods,
    BaseBackend,
):
    """
    Base class for local HuggingFace model backends.

    Supports two modes:
    1. VLLM Server Mode: Use external VLLM server for inference
    2. Direct Mode: Load model directly using transformers

    Subclasses must implement:
    - _format_prompt(): Model-specific prompt formatting
    - _parse_response(): Model-specific response parsing
    - HF_MODEL_NAME: HuggingFace model identifier

    Usage:
        class WildGuardBackend(LocalModelBackend):
            HF_MODEL_NAME = "allenai/wildguard"

            def _format_prompt(self, content, context=None):
                return f"Human user:\\n{content}\\n..."

            def _parse_response(self, response):
                # Parse "harmful_request: yes/no" format
                ...
    """

    # Subclasses should override these
    HF_MODEL_NAME: str = ""
    MAX_NEW_TOKENS: int = 128
    TEMPERATURE: float = 0.1

    def __init__(
        self,
        model: GuardrailModel,
        vllm_url: Optional[str] = None,
        device: str = "auto",
        hf_token: Optional[str] = None,
        load_in_8bit: bool = False,
        load_in_4bit: bool = False,
    ):
        """
        Initialize local model backend.

        Args:
            model: The guardrail model enum value
            vllm_url: VLLM server URL (auto-detected from env if not provided)
            device: Device to use ("auto", "cuda", "mps", "cpu")
            hf_token: HuggingFace token for gated models
            load_in_8bit: Use 8-bit quantization (reduces memory)
            load_in_4bit: Use 4-bit quantization (reduces memory further)
        """
        super().__init__(model)

        self._vllm_url = vllm_url or get_vllm_url(model.value)
        self._device = device
        self._hf_token = hf_token or os.environ.get("HF_TOKEN") or os.environ.get("HUGGING_FACE_HUB_TOKEN")
        self._load_in_8bit = load_in_8bit
        self._load_in_4bit = load_in_4bit

        # Lazy-loaded resources
        self._vllm_client: Optional[VLLMClient] = None
        self._transformers_model = None
        self._tokenizer = None

        # Check what's available
        self._use_vllm = False
        if self._vllm_url:
            client = VLLMClient(self._vllm_url)
            if client.health_check():
                self._use_vllm = True
                self._vllm_client = client
                # Resolve which model on the server matches this backend
                self._resolve_server_model()


        # No match found — VLLMClient will fall back to server default


    # Shared keyword-based category inference for local models that
    # return binary safe/unsafe without fine-grained categories.
    _CATEGORY_KEYWORDS = {
        "violence": ["violence", "violent", "kill", "murder", "attack", "weapon", "harm", "bomb", "gun", "hurt"],
        "self_harm": ["suicide", "self-harm", "self harm", "cut myself", "end my life", "kill myself"],
        "hate_speech": ["hate", "racist", "sexist", "discrimination", "discriminate", "slur"],
        "sexual_content": ["sexual", "explicit", "nude", "porn"],
        "harassment": ["harass", "bully", "threaten", "intimidate"],
        "illegal_activity": ["illegal", "drug", "hack", "steal", "fraud", "crime", "counterfeit"],
        "jailbreak": ["jailbreak", "ignore", "bypass", "pretend", "roleplay", "dan"],
        "prompt_injection": ["ignore previous", "new instructions", "system prompt", "override", "injection"],
    }
