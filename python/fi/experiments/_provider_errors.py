"""A provider's answer that says a model was retired, made into a clear error.

On 10-23 OpenAI retired ``gpt-4.1-nano``: every chat call answered HTTP 404 ``model_not_found``, "The model
`gpt-4.1-nano` has been deprecated", while ``GET /v1/models`` still listed it. A generic "judge HTTP 404" or a trial's
bare ``NotFoundError`` does not tell the user what happened or what to do, so the SDK names the model and says the
provider retired it:

- ``judge()`` raises :class:`fi.experiments.errors.ModelRetiredError` (internal: no run ends with it) from its own
  call, so every row's judge score is an error naming the model, and the judge stops calling a model it knows is
  retired at that endpoint, concurrent rows included;
- a trial whose task raised a provider's retirement answer (the ``openai`` / ``httpx`` exception, or one that wraps
  it) records an error message that starts with the same words, before the provider's own text;
- the run's closing lines say the sentence once, per evaluator and per error type.

What counts as a retirement (a retirement word alone is not enough, as providers also deprecate
parameters and endpoints):

- an HTTP 400, 404 or 410 whose error code is a retirement code (Groq's 400 ``model_decommissioned``); or
- an HTTP 404 or 410, or the code ``model_not_found``, whose message says deprecated, decommissioned, retired,
  discontinued or no longer available **about a model**: in the same clause as a mention of a model (OpenAI's 404
  ``model_not_found`` "The model `gpt-4.1-nano` has been deprecated", or the requested model's id), or "this model
  has been retired".

So OpenAI's 400 "The 'functions' parameter is deprecated", a 400 "'max_tokens' is deprecated for this endpoint" and a
404 "The endpoint /v1/engines is deprecated" stay the provider's own errors, as does a 404 for a model name that never
existed (it says none of the words).

This module imports nothing from ``fi.utils`` or ``fi.api``.
"""

from __future__ import annotations

import json
import re
from typing import Any, NamedTuple, Optional

RETIRED_CODES = ("model_decommissioned", "model_deprecated", "model_retired")
RETIRED_WORDS = ("deprecated", "decommissioned", "retired", "discontinued", "no longer available",
                 "no longer supported", "has been shut down", "end of life", "end-of-life")
_STATUSES = (400, 404, 410)
_GONE_STATUSES = (404, 410)  # a retirement word counts on these (or on model_not_found) only when it is about a model
_MODEL_NOT_FOUND = "model_not_found"
_MODEL_IN_TEXT = re.compile(r"model\s*[:=]?\s*[`'\"]([^`'\"\s]{1,200})[`'\"]", re.IGNORECASE)
# "this model has been retired", "the model is deprecated": the word's subject is a model, in one clause
_MODEL_IS_RETIRED = re.compile(r"\b(?:this|that|the|requested|your)\s+model\s+(?:is|was|has\s+been|have\s+been)\s+"
                               r"(?:now\s+|permanently\s+)?(?:deprecated|decommissioned|retired|discontinued|shut\s+down|"
                               r"no\s+longer\s+(?:available|supported))\b", re.IGNORECASE)


class Retirement(NamedTuple):
    status: int
    code: Optional[str]
    message: str
    model: Optional[str]


def _error_object(body: Any) -> dict:
    """The provider's error object from a decoded body, ``{"error": {...}}`` or the error object itself."""
    if isinstance(body, (bytes, str)):
        try:
            body = json.loads(body)
        except (TypeError, ValueError):
            return {"message": body.decode("utf-8", "replace") if isinstance(body, bytes) else body}
    if not isinstance(body, dict):
        return {}
    err = body.get("error", body)
    if isinstance(err, str):
        return {"message": err, "code": body.get("code"), "type": body.get("type")}
    return err if isinstance(err, dict) else {}


def _mentions(message: str, model: Optional[str]) -> list[tuple[int, int]]:
    """Where the message names a model: ``model `X``` (any model), and the requested model as a whole id (a short id
    such as "m" is not every word's letter)."""
    spans = [m.span() for m in _MODEL_IN_TEXT.finditer(message)]
    if model and model.strip():
        whole = re.compile(r"(?<![\w./-])" + re.escape(model.strip()) + r"(?![\w./-])", re.IGNORECASE)
        spans += [m.span() for m in whole.finditer(message)]
    return spans


_CLAUSE_END = re.compile(r"[;\n]|[.!?](?=\s|$)")  # "gpt-4.1" and "platform.openai.com" end no clause


def _word_about_a_model(message: str, model: Optional[str]) -> bool:
    """Whether a retirement word is in the same clause as a mention of a model (L-SDK2f second review: a message that
    names a model in one clause and deprecates an endpoint in another, "The model `x` does not exist; the endpoint
    /v1/engines is deprecated", is not a retirement), or the clause says "this model has been retired"."""
    if _MODEL_IS_RETIRED.search(message):
        return True
    for start, end in _mentions(message, model):
        left = max((m.end() for m in _CLAUSE_END.finditer(message, 0, start)), default=0)
        right = _CLAUSE_END.search(message, end)
        clause = message[left:right.start() if right else len(message)].lower()
        if any(w in clause for w in RETIRED_WORDS):
            return True
    return False


def retirement(status: Optional[int], body: Any, model: Optional[str] = None) -> Optional[Retirement]:
    """The retirement in a provider's answer (``status`` and its body), or None when the answer says no such thing.
    ``model`` is the model the request named: the answer is about it when its message names it."""
    if status not in _STATUSES:
        return None
    err = _error_object(body)
    code = str(err.get("code") or "").strip() or None
    message = str(err.get("message") or "").strip()
    in_message = _MODEL_IN_TEXT.search(message)
    if (code or "").lower() not in RETIRED_CODES:
        if not (status in _GONE_STATUSES or (code or "").lower() == _MODEL_NOT_FOUND):
            return None  # a 400 with a word: a parameter's or an endpoint's deprecation, not the model's
        text = " ".join(x for x in (str(err.get("type") or ""), message)).lower()
        if not any(w in text for w in RETIRED_WORDS):
            return None
        if not _word_about_a_model(message, model):  # "The endpoint /v1/engines is deprecated": about something else
            return None
    named = model or (in_message.group(1) if in_message else None)
    return Retirement(int(status), code, message[:300], named)


def _request_model(obj: Any) -> Optional[str]:
    request = getattr(obj, "request", None) or getattr(getattr(obj, "response", None), "request", None)
    try:
        sent = json.loads(request.content)
    except Exception:  # no request, a streamed body, not JSON
        return None
    model = sent.get("model") if isinstance(sent, dict) else None
    return str(model) if model else None


def from_exception(exc: BaseException) -> Optional[Retirement]:
    """The retirement a task's exception carries: an ``openai`` / ``anthropic`` status error (``status_code`` and
    ``body``), an ``httpx.HTTPStatusError`` (its ``response``), or either one as the cause of a wrapping exception."""
    seen: set[int] = set()
    current: Optional[BaseException] = exc
    while current is not None and id(current) not in seen and len(seen) < 6:
        seen.add(id(current))
        response = getattr(current, "response", None)
        status = getattr(current, "status_code", None)
        if not isinstance(status, int) or isinstance(status, bool):
            status = getattr(response, "status_code", None)
        if isinstance(status, int) and not isinstance(status, bool):
            body = getattr(current, "body", None)
            if body is None and response is not None:
                try:
                    body = response.json()
                except Exception:
                    body = getattr(response, "text", None)
            if body is None:
                body = {"message": str(current)}
            requested = _request_model(current)
            found = retirement(status, body, model=requested)
            if found is not None:
                return found
        current = current.__cause__ or current.__context__
    return None


_WHAT_TO_DO = "Name a model the provider still serves; a retired model can still be listed by the provider's /models call."
_SENTENCE = re.compile(r"the model .{1,240}? was retired by .{1,700}?" + re.escape(_WHAT_TO_DO), re.DOTALL)


def describe(found: Retirement, provider: Optional[str] = None) -> str:
    """One sentence naming the model and what to do, with the provider's own answer."""
    who = f"the provider at {provider}" if provider else "the provider"  # one pair of parentheses
    model = repr(found.model) if found.model else "the requested model"
    code = f" {found.code}" if found.code else ""
    said = f': "{found.message}"' if found.message else ""
    return f"the model {model} was retired by {who} (HTTP {found.status}{code}{said}). {_WHAT_TO_DO}"


def sentence_in(text: Optional[str]) -> Optional[str]:
    """The :func:`describe` sentence inside an error text (a judge score's explanation, a trial's message), or None.
    The run's closing lines print it once."""
    found = _SENTENCE.search(text or "")
    return found.group(0) if found else None
