"""LocalModelBackend resolve server model operations."""
from __future__ import annotations

from fi.evals.guardrails.backends.local_base import (
    Any, Dict, GuardrailResult, List, Optional, RailType, abstractmethod,
)


class _LocalModelBackendResolveServerModelMethods:
    __slots__ = ()

    def _resolve_server_model(self):
        """Match this backend's model to an available model on the VLLM/ollama server."""
        try:
            available = self._vllm_client.get_models()
        except Exception:
            return

        if not available:
            return

        # Our enum value e.g. "llamaguard-3-1b", "qwen3guard-0.6b"
        our_key = self.model.value.lower()
        # Normalize: strip hyphens/underscores/dots for fuzzy matching
        our_norm = our_key.replace("-", "").replace("_", "").replace(".", "")
        # Also get the HF model name for matching
        hf_name = self._get_hf_model_name().lower()

        for server_model in available:
            sm = server_model.lower()
            sm_norm = sm.replace("-", "").replace("_", "").replace(".", "").replace("/", "").replace(":", "")

            # Exact match on enum value
            if our_key in sm or sm.startswith(our_key):
                self._vllm_client.model = server_model
                return

            # Normalized fuzzy match (e.g. "llamaguard31b" in "llamaguard31b")
            if our_norm in sm_norm or sm_norm in our_norm:
                self._vllm_client.model = server_model
                return

            # HF name match
            if hf_name and (hf_name in sm or sm in hf_name):
                self._vllm_client.model = server_model
                return


    def _get_hf_model_name(self) -> str:
        """Get the HuggingFace model name. Override in subclasses if needed."""
        return self.HF_MODEL_NAME


    def _load_transformers_model(self):
        """Load the model using transformers library."""
        if self._transformers_model is not None:
            return

        try:
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer
        except ImportError:
            raise ImportError(
                "transformers and torch packages required for local model backends. "
                "Install with: pip install torch transformers accelerate"
            )

        model_name = self._get_hf_model_name()

        # Determine device
        if self._device == "auto":
            if torch.cuda.is_available():
                device = "cuda"
            elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                device = "mps"
            else:
                device = "cpu"
        else:
            device = self._device

        # Load tokenizer
        self._tokenizer = AutoTokenizer.from_pretrained(
            model_name,
            token=self._hf_token,
        )

        # Determine dtype and load kwargs
        if device in ("cuda", "mps"):
            dtype = torch.float16
        else:
            dtype = torch.float32

        load_kwargs = {
            "torch_dtype": dtype,
            "token": self._hf_token,
            "low_cpu_mem_usage": True,
        }

        if self._load_in_8bit:
            load_kwargs["load_in_8bit"] = True
        elif self._load_in_4bit:
            load_kwargs["load_in_4bit"] = True

        # Load model
        self._transformers_model = AutoModelForCausalLM.from_pretrained(
            model_name,
            **load_kwargs,
        )

        if not (self._load_in_8bit or self._load_in_4bit):
            self._transformers_model.to(device)

        self._transformers_model.eval()
        self._transformers_device = device


    def _generate_with_transformers(
        self,
        prompt: str,
        max_new_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> str:
        """
        Generate text using local transformers model.

        Args:
            prompt: Input prompt
            max_new_tokens: Max tokens to generate
            temperature: Sampling temperature

        Returns:
            Generated text (response only, not including prompt)
        """
        from fi.evals.guardrails.backends.local_base import (Optional)
        import torch

        self._load_transformers_model()

        max_tokens = max_new_tokens or self.MAX_NEW_TOKENS
        temp = temperature or self.TEMPERATURE

        inputs = self._tokenizer(prompt, return_tensors="pt").to(self._transformers_device)
        prompt_length = inputs.input_ids.shape[1]

        with torch.no_grad():
            outputs = self._transformers_model.generate(
                **inputs,
                max_new_tokens=max_tokens,
                temperature=max(temp, 0.01),
                do_sample=temp > 0,
                pad_token_id=self._tokenizer.eos_token_id,
            )

        # Decode only the generated tokens (excluding prompt)
        generated_tokens = outputs[0][prompt_length:]
        response = self._tokenizer.decode(generated_tokens, skip_special_tokens=True)

        return response


    @abstractmethod
    def _format_prompt(
        self,
        content: str,
        rail_type: RailType,
        context: Optional[str] = None,
    ) -> str:
        """
        Format content into model-specific prompt.

        Args:
            content: Content to classify
            rail_type: Type of rail (input, output, retrieval)
            context: Optional context (e.g., for output rail)

        Returns:
            Formatted prompt string
        """
        from fi.evals.guardrails.backends.local_base import (Optional, RailType, abstractmethod)
        pass


    @abstractmethod
    def _parse_response(
        self,
        response: str,
        content: str,
        rail_type: RailType,
    ) -> List[GuardrailResult]:
        """
        Parse model response into GuardrailResult objects.

        Args:
            response: Raw model response text
            content: Original content that was classified
            rail_type: Type of rail

        Returns:
            List of GuardrailResult objects
        """
        from fi.evals.guardrails.backends.local_base import (
            GuardrailResult, List, RailType, abstractmethod,
        )
        pass


    def classify(
        self,
        content: str,
        rail_type: RailType,
        context: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[GuardrailResult]:
        """
        Classify content using local model.

        Args:
            content: Content to classify
            rail_type: Type of rail
            context: Optional context
            metadata: Optional metadata

        Returns:
            List of GuardrailResult objects
        """
        from fi.evals.guardrails.backends.local_base import (
            Any, Dict, GuardrailResult, List, Optional, RailType, time,
        )
        start_time = time.time()

        # Handle empty content
        if not content or not content.strip():
            return [
                GuardrailResult(
                    passed=True,
                    category="empty",
                    score=0.0,
                    model=self.model_name,
                    reason="Empty or whitespace-only content",
                    action="pass",
                    latency_ms=(time.time() - start_time) * 1000,
                )
            ]

        try:
            # Format prompt
            prompt = self._format_prompt(content, rail_type, context)

            # Generate response
            if self._use_vllm and self._vllm_client:
                # Use chat endpoint — lets the server apply its own chat
                # template (required for ollama, also works with VLLM).
                # Send raw content so safety models use their built-in training
                # rather than getting confused by our prompt template.
                vllm_response = self._vllm_client.chat(
                    messages=[{"role": "user", "content": content}],
                    max_tokens=self.MAX_NEW_TOKENS,
                    temperature=self.TEMPERATURE,
                )
                response_text = vllm_response.text
            else:
                response_text = self._generate_with_transformers(prompt)

            elapsed_ms = (time.time() - start_time) * 1000

            # Parse response
            results = self._parse_response(response_text, content, rail_type)

            # Update latency in results
            for result in results:
                result.latency_ms = elapsed_ms

            return results

        except Exception as e:
            elapsed_ms = (time.time() - start_time) * 1000
            return [
                GuardrailResult(
                    passed=False,
                    category="error",
                    score=0.0,
                    model=self.model_name,
                    reason=f"Local model error: {str(e)}",
                    action="block",
                    latency_ms=elapsed_ms,
                )
            ]
