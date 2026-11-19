"""OllamaLLM parse judge response operations."""
from __future__ import annotations

from fi.evals.local.llm import (Any, Dict, List)


class _OllamaLLMParseJudgeResponseMethods:
    __slots__ = ()

    def _parse_judge_response(self, response: str) -> Dict[str, Any]:
        """Parse the LLM judge response into structured format.

        Args:
            response: The raw LLM response text.

        Returns:
            Parsed evaluation result dictionary.
        """
        from fi.evals.local.llm import (Any, Dict, json, re)
        response = response.strip()

        # Try direct JSON parse first
        try:
            result = json.loads(response)
            return self._validate_judge_result(result)
        except json.JSONDecodeError:
            pass

        # Try to extract JSON from markdown code block
        code_block_pattern = r"```(?:json)?\s*([\s\S]*?)```"
        match = re.search(code_block_pattern, response)
        if match:
            try:
                result = json.loads(match.group(1).strip())
                return self._validate_judge_result(result)
            except json.JSONDecodeError:
                pass

        # Try to find JSON object in response
        json_pattern = r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}"
        match = re.search(json_pattern, response, re.DOTALL)
        if match:
            try:
                result = json.loads(match.group())
                return self._validate_judge_result(result)
            except json.JSONDecodeError:
                pass

        # Fallback: try to extract score and reason from text
        score = 0.5
        score_pattern = r"(?:score|rating)[:\s]*([0-9]*\.?[0-9]+)"
        score_match = re.search(score_pattern, response, re.IGNORECASE)
        if score_match:
            try:
                score = float(score_match.group(1))
                # Normalize if score is > 1 (e.g., 1-10 scale)
                if score > 1:
                    score = score / 10
                score = max(0.0, min(1.0, score))
            except ValueError:
                pass

        return {
            "score": score,
            "passed": score >= 0.5,
            "reason": response[:500] if response else "Unable to parse evaluation",
            "parse_error": True,
        }


    def _validate_judge_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and normalize the judge result.

        Args:
            result: Raw parsed result dictionary.

        Returns:
            Validated and normalized result.
        """
        from fi.evals.local.llm import (Any, Dict)
        score = result.get("score", 0.5)

        # Handle various score formats
        if isinstance(score, str):
            try:
                score = float(score)
            except ValueError:
                score = 0.5

        # Normalize score to 0-1 range
        if score > 1:
            score = score / 10 if score <= 10 else score / 100
        score = max(0.0, min(1.0, float(score)))

        passed = result.get("passed")
        if passed is None:
            passed = score >= 0.5
        elif isinstance(passed, str):
            passed = passed.lower() in ("true", "yes", "1", "pass")

        reason = result.get("reason", result.get("explanation", ""))
        if not isinstance(reason, str):
            reason = str(reason)

        return {
            "score": score,
            "passed": bool(passed),
            "reason": reason,
        }


    def batch_judge(
        self,
        evaluations: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Run multiple judge evaluations.

        Args:
            evaluations: List of evaluation specifications, each containing:
                - query: The query
                - response: The response to evaluate
                - criteria: Evaluation criteria
                - context: Optional context

        Returns:
            List of evaluation results.
        """
        from fi.evals.local.llm import (Any, Dict, List)
        results = []
        for eval_spec in evaluations:
            result = self.judge(
                query=eval_spec.get("query", ""),
                response=eval_spec.get("response", ""),
                criteria=eval_spec.get("criteria", ""),
                context=eval_spec.get("context"),
            )
            results.append(result)
        return results
