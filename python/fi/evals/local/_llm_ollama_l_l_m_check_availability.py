"""OllamaLLM check availability operations."""
from __future__ import annotations

from fi.evals.local.llm import (Any, Dict, List, Optional)


class _OllamaLLMCheckAvailabilityMethods:
    __slots__ = ()

    def _check_availability(self) -> None:
        """Check if Ollama is available and the model is installed."""
        from fi.evals.local.llm import (logger)
        try:
            import requests

            response = requests.get(
                f"{self.config.base_url}/api/tags",
                timeout=5
            )
            response.raise_for_status()

            data = response.json()
            self._models = [m.get("name", "") for m in data.get("models", [])]
            self._available = True

            # Check if requested model is available
            model_base = self.config.model.split(":")[0]
            if not any(model_base in m for m in self._models):
                logger.warning(
                    f"Model '{self.config.model}' not found in Ollama. "
                    f"Available models: {self._models}"
                )

        except Exception as e:
            self._available = False
            logger.warning(f"Ollama not available: {e}")


    def is_available(self) -> bool:
        """Check if Ollama is available.

        Returns:
            True if Ollama is running and accessible.
        """
        if self._available is None:
            self._check_availability()
        return self._available or False


    def list_models(self) -> List[str]:
        """List available models in Ollama.

        Returns:
            List of installed model names.
        """
        from fi.evals.local.llm import (List)
        if self._models is None:
            self._check_availability()
        return self._models or []


    def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """Generate a completion using Ollama.

        Args:
            prompt: The user prompt.
            system: Optional system prompt.
            temperature: Override temperature for this request.
            max_tokens: Override max tokens for this request.

        Returns:
            The generated text response.

        Raises:
            ConnectionError: If Ollama is not available.
            RuntimeError: If generation fails.
        """
        from fi.evals.local.llm import (Optional)
        if not self.is_available():
            raise ConnectionError(
                f"Cannot connect to Ollama at {self.config.base_url}. "
                "Make sure Ollama is running: `ollama serve`"
            )

        import requests

        payload = {
            "model": self.config.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature if temperature is not None else self.config.temperature,
                "num_predict": max_tokens if max_tokens is not None else self.config.max_tokens,
            }
        }

        if system:
            payload["system"] = system

        try:
            response = requests.post(
                f"{self.config.base_url}/api/generate",
                json=payload,
                timeout=self.config.timeout,
            )
            response.raise_for_status()

            return response.json().get("response", "")

        except requests.exceptions.Timeout:
            raise RuntimeError(
                f"Ollama request timed out after {self.config.timeout}s"
            )
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Ollama request failed: {e}")


    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """Chat completion using Ollama's chat API.

        Args:
            messages: List of message dictionaries with 'role' and 'content'.
            temperature: Override temperature for this request.
            max_tokens: Override max tokens for this request.

        Returns:
            The assistant's response.
        """
        from fi.evals.local.llm import (Dict, List, Optional)
        if not self.is_available():
            raise ConnectionError(
                f"Cannot connect to Ollama at {self.config.base_url}. "
                "Make sure Ollama is running: `ollama serve`"
            )

        import requests

        payload = {
            "model": self.config.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature if temperature is not None else self.config.temperature,
                "num_predict": max_tokens if max_tokens is not None else self.config.max_tokens,
            }
        }

        try:
            response = requests.post(
                f"{self.config.base_url}/api/chat",
                json=payload,
                timeout=self.config.timeout,
            )
            response.raise_for_status()

            return response.json().get("message", {}).get("content", "")

        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Ollama chat request failed: {e}")


    def judge(
        self,
        query: str,
        response: str,
        criteria: str,
        context: Optional[str] = None,
        output_format: str = "json",
    ) -> Dict[str, Any]:
        """Use LLM as judge for evaluation.

        Args:
            query: The original query/question.
            response: The response to evaluate.
            criteria: The evaluation criteria/rubric.
            context: Optional context/reference information.
            output_format: Output format ("json" or "text").

        Returns:
            Dictionary with evaluation result:
                - score: Float between 0 and 1
                - passed: Boolean indicating if evaluation passed
                - reason: Explanation of the evaluation
        """
        from fi.evals.local.llm import (Any, Dict, Optional, logger)
        system_prompt = """You are an AI evaluation judge. Evaluate the response based on the given criteria.

Your evaluation must be fair, consistent, and based solely on the criteria provided.

Output your evaluation as JSON with the following format:
{
    "score": <float between 0.0 and 1.0>,
    "passed": <true or false, based on whether score >= 0.5>,
    "reason": "<brief explanation of your evaluation>"
}

Only output the JSON object, nothing else."""

        user_prompt = f"""## Evaluation Criteria
{criteria}

## Query
{query}

## Response to Evaluate
{response}
"""

        if context:
            user_prompt += f"""
## Context/Reference
{context}
"""

        user_prompt += """
## Your Evaluation (JSON only)"""

        try:
            result_text = self.generate(user_prompt, system=system_prompt)
            return self._parse_judge_response(result_text)

        except Exception as e:
            logger.error(f"LLM judge failed: {e}")
            return {
                "score": 0.0,
                "passed": False,
                "reason": f"Evaluation failed: {str(e)}",
                "error": True,
            }
