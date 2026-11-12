"""EvalResponseHandler parse success operations."""
from __future__ import annotations

from fi.evals.evaluator import (Any, BatchRunResult, Dict, Response)

# The keys of the platform's error body that carry its sentence, in the order they are read.
_SENTENCE_KEYS = ("message", "detail", "error")
_EXCERPT_CHARS = 200
# What a 403 adds after the server's sentence and the status.
_KEY_HINT = "Check your API key and secret key."


def _says(sentence: str, field: str, text: str) -> bool:
    """Whether the sentence already is this field error: its text alone, or the text after the field's
    path without ``non_field_errors`` segments (``eval_config.non_field_errors`` reads ``eval_config``)."""
    path = ".".join(part for part in str(field).split(".") if part != "non_field_errors")
    return sentence == text or (bool(path) and sentence == f"{path}: {text}")


def _server_sentence(body: Any) -> str:
    """The sentence of an error body ``{"status": false, "message"/"detail"/"error": ...}``, then the
    field errors it lists under ``details`` (or ``errors``) that the sentence does not already say;
    "" when the body has neither."""
    if not isinstance(body, dict):
        return ""
    sentence = next((body[key].strip() for key in _SENTENCE_KEYS
                     if isinstance(body.get(key), str) and body[key].strip()), "")
    fields = body.get("details") if isinstance(body.get("details"), dict) else body.get("errors")
    reasons = []
    for field, messages in (fields.items() if isinstance(fields, dict) else ()):
        texts = [m.strip() for m in (messages if isinstance(messages, list) else [messages])
                 if isinstance(m, str) and m.strip() and not _says(sentence, field, m.strip())]
        if texts and field not in _SENTENCE_KEYS:
            text = " ".join(texts)
            reasons.append(text if field == "non_field_errors" else f"{field}: {text}")
    return ": ".join(part for part in (sentence, "; ".join(reasons)) if part)


def _refusal_reason(response: Response) -> str:
    """What a refused evaluation tells the caller: the server's sentence, then the HTTP status. A body
    without a sentence gives a short excerpt of itself, never the whole body."""
    try:
        sentence = _server_sentence(response.json())
    except ValueError:
        sentence = ""
    if sentence:
        return f"{sentence} (HTTP {response.status_code})"
    excerpt = " ".join((response.text or "").split())
    if not excerpt:
        return f"The evaluation request failed with HTTP {response.status_code} and an empty body."
    if len(excerpt) > _EXCERPT_CHARS:
        excerpt = excerpt[:_EXCERPT_CHARS].rstrip() + "..."
    return f"The evaluation request failed with HTTP {response.status_code}: {excerpt}"


class _EvalResponseHandlerParseSuccessMethods:
    __slots__ = ()

    @classmethod
    def _parse_success(cls, response: Response) -> BatchRunResult:
        from fi.evals.evaluator import (BatchRunResult, Response)
        return cls.convert_to_batch_results(response.json())


    @classmethod
    def _handle_error(cls, response: Response) -> None:
        from fi.evals.evaluator import (InvalidAuthError, Response)
        reason = _refusal_reason(response)
        if response.status_code == 403:
            raise InvalidAuthError(message=f"{reason} {_KEY_HINT}")
        raise Exception(reason)


    @classmethod
    def convert_to_batch_results(cls, response: Dict[str, Any]) -> BatchRunResult:
        """
        Convert API response to BatchRunResult

        Args:
            response: Raw API response dictionary

        Returns:
            BatchRunResult containing evaluation results
        """
        from fi.evals.evaluator import (Any, BatchRunResult, Dict, EvalResult)
        eval_results = []

        # The revamped backend (post 2026-04-12) returns pure snake_case:
        #   {"result": [{"evaluations": [
        #       {"name", "reason", "runtime", "output", "output_type",
        #        "eval_id", "model"?, "error_localizer_enabled"?,
        #        "error_localizer"?}
        #   ]}]}
        # Async / error-localization paths may return the eval wrapped in
        # {"eval_status": "...", "result": <eval>} — handle that too.
        for result in response.get("result", []) or []:
            if isinstance(result, dict) and "evaluations" in result:
                entries = result.get("evaluations", []) or []
            else:
                entries = [result] if isinstance(result, dict) else []

            for evaluation in entries:
                if not isinstance(evaluation, dict):
                    continue
                eval_results.append(
                    EvalResult(
                        name=evaluation.get("name", ""),
                        output=evaluation.get("output", evaluation.get("value")),
                        reason=evaluation.get("reason", ""),
                        runtime=evaluation.get("runtime", 0),
                        output_type=evaluation.get("output_type", ""),
                        eval_id=evaluation.get("eval_id", ""),
                        model=evaluation.get("model"),
                        error_localizer_enabled=evaluation.get(
                            "error_localizer_enabled"
                        ),
                        error_localizer=evaluation.get("error_localizer"),
                    )
                )

        return BatchRunResult(eval_results=eval_results)
