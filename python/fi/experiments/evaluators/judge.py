"""``judge()``: any OpenAI-compatible chat-completions model as a judge, outside the platform.

``evaluators.judge("Is the refund policy followed?", model="gpt-4.1-mini",
api_key_env="OPENAI_API_KEY", base_url=None)``. The key is read from ``api_key_env`` at call time
and not stored.

The judge's ``timeout_s`` (60 seconds by default) configures its HTTP request timeout, not a
deadline for all of its requests and retries together. It is independent of the ``run`` / ``arun``
``timeout_s``, which bounds only the task's attempts in each trial, not evaluators. A judge
request timeout produces an error score; it does not extend or reuse the task's timeout.

**The default judge model is ``gpt-4.1-mini``** (``DEFAULT_JUDGE_MODEL``). In a live evaluation on 14 held-out
criteria pairs with 6 OpenAI seeds, the checklist prompt had **2 misses in 84 verdicts, against 4 in 84** for the
earlier one-verdict prompt. These are two samples, not a paired replay: the prompts differ and OpenAI's
fingerprints differed between the runs, and 4 vs 2 is no significant difference (one-sided Fisher p = 0.34). The kind
of miss changed. The old prompt failed a reply that meets the CRITERIA because it does not answer all of the INPUT
("Thanks for checking! Flight LX318 is on time." under "polite, and at most 12 words", 4 of 6 seeds); the checklist
did not (0 of 6). **Its own known miss:** it can miscount sentences. "Flight LX318 is on time and leaves from gate
B12." under "Is the gate in the reply correct, and is the reply a single sentence?" was read as two sentences in 2 of 6
seeds; the earlier prompt counted it correctly on all 6 seeds. The SDK computes sentence counts for parts marked as
counts. Across all 39 controls (14 held-out and 25 development pairs), the checklist prompt had 2 misses in 234
verdicts, compared with 7 in 234 for the earlier prompt. The requirement that every control pass on every run was
RED in 2 of its 3 runs on this judge: one run had the sentence-count miss and the other had a response from a
smaller model with no verdict. The evaluation uses a rate threshold: each control must pass in at least 5 of 6
seeded runs, and each held-out set may have at most 5% misses, with each miss documented. Write CRITERIA that say what
they check, and inspect the verdicts. A cheaper ``model=`` may miss more length, tone and privacy checks;
check one on your own controls first. A part answer that holds no verdict is an error score, not a pass. Any other
key than ``OPENAI_API_KEY`` needs ``model=`` too. **A retired model** (the provider's 404 ``model_not_found`` "has
been deprecated") gives every row a ``ModelRetiredError`` score naming it, after one call (``_provider_errors``).

Where the key goes: with ``api_key_env="OPENAI_API_KEY"`` (the default) the base URL defaults to
``$OPENAI_BASE_URL`` or ``https://api.openai.com/v1``. Any other key (Groq, Together, xAI, your
own) needs ``base_url=``: a provider's key is not sent to OpenAI by default.

OpenAI reasoning models (``o1``/``o3``/``o4-*``, ``gpt-5*``) take ``max_completion_tokens`` (which
also counts reasoning tokens) and only the default temperature, so neither ``max_tokens`` nor
``temperature`` is sent to them.

**The CRITERIA are a checklist, and each part is judged on its own.** The judge reads its CRITERIA once (one cached
call per judge, with its own ``experiment.judge.criteria`` span) and splits them into parts. For each part the read
identifies what to check, whether the part asks about correctness, whether it needs the INPUT, and whether it is
required. For each row, the judge sends one verdict request **per part that needs the model**, showing only what
that part needs:
- the OUTPUT for every part;
- the INPUT when the part needs it (for example "does the reply answer the question?"). So a reply that meets
  "Is the reply a single sentence?" is not failed because it leaves out something the INPUT asked for. A part that
  asks about correctness on a row with **no EXPECTED** receives the INPUT: with no reference, an answer is judged
  right or wrong against what it answers;
- EXPECTED only when the part asks about correctness. So CRITERIA about tone, length, format, language or what the
  OUTPUT must not reveal are judged on the OUTPUT alone, and an expected answer cannot pass a rude reply as polite
  because its facts match.

The SDK, not the model, combines the parts. The score is the share of parts met, and the verdict passes exactly when
every required part is met (a part is optional only when the CRITERIA say "ideally" or "if possible"). With
``passing_score=``, the score decides instead. A part answer with no true/false verdict, or a read the SDK cannot
parse, is an error score, not a made-up verdict. A 429 or 5xx answer is retried up to 3 times, waiting what the
answer asks (at most 30 s), before it is an error score (``_judge_http``). The judge adds no requirement of its own:
answering all of the INPUT, completeness or helpfulness count only when the CRITERIA ask for them.

**What it decided is shown, and one run keeps one checklist.** The read's checklist decides for every row what each
part sees, so a run says it: ``result.metadata["judge_criteria"]`` (the parts, and whether this run's rows had
EXPECTED) and ``Judge`` lines in the run's closing lines. The run journals the checklist before any
row is judged on it, and a resume judges its remaining rows on the journaled one; it reads nothing again
(``fi.experiments._judge_checklists``).

**A count is made by code, not by the model.** When the criteria read finds a part that counts the OUTPUT's words,
sentences, characters, list items or lines against a number ("Is the reply a single sentence?", "at most 12 words",
"at least 3 list items"), it marks the part's unit and bound, and the SDK counts. A count-only part makes no verdict
request, and its reason shows the count ("counted by the SDK, not the model: 1 sentence ("..."); the part asks exactly
1 sentence: met."). ``_judge_count`` describes each unit. For a dict or list OUTPUT, the SDK counts text values and
ignores keys. The model judges a length with no number ("short").

**The criteria read determines whether a part is count-only.** When a part asks for more than a count, the judge
sends it to the model with a COUNT note telling the model to assess the other requirements without counting. The part
is met only if the SDK's count satisfies the bound and the model finds the other requirements met. A part that needs
INPUT or EXPECTED is not count-only. The SDK's count does not by itself decide such a part: the criteria read can
mark a pure count as mixed, and then the model judges it as well.

**Meaning, not wording.** When EXPECTED is used, it is a reference for the facts, not the phrasing. The prompt tells
the model to accept paraphrases that preserve the facts, reject missing or contradictory facts, and check any other
requirements the part states. Choose a judge model that can compare meaning and follow the CRITERIA.

**What it costs.** A judge's cost scales with the number of parts its CRITERIA hold: one criteria read per judge
(cached, journaled for a resume), then for every row one verdict request per part the model is asked; a count-only
part asks nothing. CRITERIA of 4 parts cost about 4 times one request per row.

**Its own span.** In a traced run each row's verdict (all its part requests) is one child span of the
trial's root span, ``experiment.judge`` (kind EVALUATOR): the model asked and answered, tokens and cost summed over
the parts (cost when the run has a price for the model), latency, the parts met of the parts asked, and the verdict
(score, pass, reason), or the error. The criteria read has its own span, with the parts it found.
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import time
from typing import Any, Callable, Optional

import httpx

from fi._core.proxy_routing import SdkDirectAsyncTransport
from fi.experiments import _provider_errors
from fi.experiments.errors import ModelRetiredError, UsageError
from fi.experiments.evaluators import _judge_http
from fi.experiments.evaluators._base import EvalContext, Evaluator, error_score
from fi.experiments.evaluators._judge_count import decide
from fi.experiments.evaluators._judge_prompt import (  # noqa: F401 - re-exported: the prompts and parsers
    CRITERIA_SYSTEM,
    SYSTEM,
    Part,
    combine,
    parse_asks_correctness,
    parse_part_verdict,
    parse_parts,
    part_request,
    shows_input,
)
from fi.experiments.evaluators._judge_spans import _end_criteria_span, _end_span, _start_span
from fi.experiments.results import EvalScore

OPENAI_KEY_ENV = "OPENAI_API_KEY"
DEFAULT_JUDGE_MODEL = "gpt-4.1-mini"  # the judge's model when none is named
OPENAI_DEFAULT_BASE_URL = "https://api.openai.com/v1"
_REASONING_MODEL = re.compile(r"^(o\d+|gpt-5)(?![a-z0-9])", re.IGNORECASE)
REASONING_MAX_COMPLETION_TOKENS = 4000  # reasoning tokens count against it


def is_reasoning_model(model: str) -> bool:
    """OpenAI reasoning models reject ``max_tokens`` and a non-default ``temperature``."""
    return bool(_REASONING_MODEL.match(model.rsplit("/", 1)[-1].strip()))


SPAN_NAME = "experiment.judge"
CRITERIA_SPAN_NAME = "experiment.judge.criteria"


def _render(value: Any, limit: Optional[int] = 20000) -> str:
    text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, default=repr)
    return text[:limit]


class Judge(Evaluator):
    kind = "judge"
    is_async = True

    def __init__(
        self,
        criteria: str,
        *,
        model: Optional[str] = None,
        api_key_env: str = "OPENAI_API_KEY",
        base_url: Optional[str] = None,
        name: Optional[str] = None,
        passing_score: Optional[float] = None,
        temperature: float = 0.0,
        max_tokens: Optional[int] = None,
        timeout_s: float = 60.0,
        transport: Optional[httpx.AsyncBaseTransport] = None,
    ) -> None:
        if model is None:
            if api_key_env != OPENAI_KEY_ENV:  # the default names an OpenAI model: another provider names its own
                raise UsageError(
                    f"judge(api_key_env={api_key_env!r}) needs model= (the default, {DEFAULT_JUDGE_MODEL}, is an "
                    "OpenAI model)."
                )
            model = DEFAULT_JUDGE_MODEL
        if not isinstance(model, str) or not model.strip():
            raise ValueError("judge(model=...) must be a non-empty model name")
        if not base_url and api_key_env != OPENAI_KEY_ENV:
            raise UsageError(
                f"judge(api_key_env={api_key_env!r}) needs base_url= (the provider's OpenAI-compatible "
                f"endpoint). Without it the ${api_key_env} key would be sent to OpenAI."
            )
        self.criteria = criteria
        self.model = model
        self.api_key_env = api_key_env
        self.base_url = base_url
        self.names: tuple[str, ...] = (name or "judge",)
        self.passing_score: Optional[float] = passing_score
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout_s = timeout_s
        self._transport = transport
        self.parts: Optional[tuple[Part, ...]] = None  # the criteria read's checklist, read once on the first row
        # invoked after reading the checklist so the run can journal it before judging any row on it
        self.on_checklist: Optional[Callable[[tuple[Part, ...]], None]] = None
        self._criteria_lock: Optional[tuple[Any, asyncio.Lock]] = None
        # Cache model retirement errors by (endpoint URL, model) so later rows skip that endpoint and model pair.
        # Without base_url=, a reused judge follows OPENAI_BASE_URL if the setting changes.
        self._retired: dict[tuple[str, str], ModelRetiredError] = {}
        # (endpoint URL, model) pairs that answered a call in this process. Without a response, calls go one row at a
        # time (a resumed run's journaled checklist skips the read), so a retired model gets one row's calls, not
        # concurrency x parts of them.
        self._served: set[tuple[str, str]] = set()

    @property
    def retired(self) -> Optional[ModelRetiredError]:
        """The provider's answer that this judge's model is retired at its current endpoint, or None."""
        return self._retired.get((self._url(), self.model))

    @property
    def asks_correctness(self) -> Optional[bool]:
        """Whether any part of the CRITERIA asks about correctness (EXPECTED is shown for it); None before the read."""
        return None if self.parts is None else any(p.needs_right_answer for p in self.parts)

    def describe(self) -> str:
        try:
            host = httpx.URL(self._base()).host or self._base()
        except Exception:  # a malformed base_url fails at request time, as an error score
            host = self._base()
        return f"{self.names[0]} (judge {self.model} via ${self.api_key_env} at {host})"

    def _base(self) -> str:
        if self.base_url:
            return self.base_url
        # only the OpenAI key reaches here (the constructor requires base_url= for any other key)
        return os.environ.get("OPENAI_BASE_URL") or OPENAI_DEFAULT_BASE_URL

    def _url(self) -> str:
        return self._base().rstrip("/") + "/chat/completions"

    def request_body(self, messages: list[dict[str, Any]]) -> dict[str, Any]:
        body: dict[str, Any] = {"model": self.model, "response_format": {"type": "json_object"}, "messages": messages}
        if is_reasoning_model(self.model):
            body["max_completion_tokens"] = self.max_tokens or REASONING_MAX_COMPLETION_TOKENS
        else:
            body["temperature"] = self.temperature
            body["max_tokens"] = self.max_tokens or 600  # the facts table comes before the verdict
        return body

    async def _chat(self, ec: EvalContext, key: str, system: str, user: str) -> tuple[Any, str]:
        """One chat call (a 429 or 5xx retried, ``_judge_http``), metered into the trial's usage; ``(response body,
        the answer's text)``."""
        body = self.request_body([{"role": "system", "content": system}, {"role": "user", "content": user}])
        # A client the judge builds reaches a plain ``http://`` base URL directly, whatever the proxy variables say.
        mounts = {"http://": SdkDirectAsyncTransport()} if self._transport is None else None
        async with httpx.AsyncClient(timeout=self.timeout_s, transport=self._transport, mounts=mounts) as http:
            resp, retries = await _judge_http.post(http, self._url(), body, key, direct=mounts is not None)
        if resp.status_code >= 400:
            try:
                answer: Any = resp.json()
            except ValueError:
                answer = resp.text
            found = _provider_errors.retirement(resp.status_code, answer, model=self.model)
            if found is not None:  # not a generic "judge HTTP 404"
                url = self._url()
                retired = ModelRetiredError(self.model, status=found.status, provider_code=found.code,
                                            provider_message=found.message, provider=httpx.URL(url).host or None)
                self._retired.setdefault((url, self.model), retired)
                raise retired
            again = f" (after {retries} retries)" if retries else ""
            raise RuntimeError(f"judge HTTP {resp.status_code}{again}: {resp.text[:300]}")
        data = resp.json()
        self._served.add((self._url(), self.model))
        used = data.get("usage") or {}
        ec.usage.append((self.model, int(used.get("prompt_tokens") or 0), int(used.get("completion_tokens") or 0)))
        return data, data["choices"][0]["message"]["content"]

    def _lock(self) -> asyncio.Lock:
        """The judge's lock on the running loop (a run drives its own loop): the criteria read, and the first calls."""
        loop = asyncio.get_running_loop()
        if self._criteria_lock is None or self._criteria_lock[0] is not loop:
            self._criteria_lock = (loop, asyncio.Lock())
        return self._criteria_lock[1]

    async def _ask(self, ec: EvalContext, key: str, requests: list[str]) -> list[Any]:
        """Finish the separate part requests before scoring. If this endpoint and model have not answered,
        one row's requests go at a time, and a row that waited makes none to a model found retired meanwhile."""
        def send() -> Any:
            return asyncio.gather(*(self._chat(ec, key, SYSTEM, r) for r in requests), return_exceptions=True)

        if not requests or (self._url(), self.model) in self._served:
            return list(await send())
        async with self._lock():
            if self.retired is not None:
                return [self.retired]
            if (self._url(), self.model) not in self._served:
                return list(await send())
        return list(await send())  # it answered while this row waited: no need to go alone

    async def checklist(self, ec: EvalContext, key: str) -> tuple[Part, ...]:
        """The criteria read's parts, the checklist every row is judged on: read once per judge, on its first row
        (concurrent first rows wait for one answer; a failed read is not cached, so the next row reads again)."""
        if self.parts is None:
            async with self._lock():
                if self.parts is None:
                    retired = self.retired  # rows waiting for the first read skip calls to a retired model
                    if retired is not None:
                        raise retired
                    span = _start_span(ec, CRITERIA_SPAN_NAME, self, kind="CHAIN")
                    started, data, error, parts = time.monotonic(), None, None, None
                    try:
                        data, text = await self._chat(ec, key, CRITERIA_SYSTEM, f"CRITERIA:\n{self.criteria}")
                        parts = parse_parts(text)
                    except Exception as exc:
                        error = exc
                    _end_criteria_span(span, ec, self.model, data, parts, error, (time.monotonic() - started) * 1000.0)
                    if isinstance(error, ModelRetiredError):  # said as itself: it names the model
                        raise error
                    if error is not None:
                        raise RuntimeError(f"the judge could not read its criteria: {error}") from error
                    if self.on_checklist is not None:  # journaled before any row is judged on it
                        self.on_checklist(parts)
                    self.parts = parts
        assert self.parts is not None
        return self.parts

    async def aevaluate(self, ec: EvalContext) -> dict[str, EvalScore]:
        name = self.names[0]
        key = os.environ.get(self.api_key_env)
        if not key:
            return {name: EvalScore(status="error", explanation=f"${self.api_key_env} is not set")}
        if self.retired is not None:  # the provider said the model is retired: no further calls to it
            return {name: error_score(self.retired)}
        try:
            parts = await self.checklist(ec, key)
        except Exception as exc:
            return {name: error_score(exc)}
        if self.retired is not None:  # retirement detected while the row waited: skip part requests
            return {name: error_score(self.retired)}
        texts = {"input_text": _render(ec.input), "output_text": _render(ec.output),
                 "expected_text": _render(ec.expected) if ec.expected is not None else None}
        span = _start_span(ec, SPAN_NAME, self)
        started = time.monotonic()
        asked = [p for p in parts if not p.counted_only]  # count-only parts require no model call
        answers = await self._ask(ec, key, [part_request(p, **texts) for p in asked])
        datas = [a[0] for a in answers if not isinstance(a, BaseException)]
        met: Optional[int] = None
        try:
            failed = next((a for a in answers if isinstance(a, BaseException)), None)
            if failed is not None:
                raise failed
            said = [parse_part_verdict(text) for _, text in answers]  # type: ignore[misc]
            verdicts = _verdicts(parts, said, ec.output)  # every character counted, not the prompt's cut
            met = sum(m for m, _ in verdicts)
            score, passed, reason = combine(parts, verdicts)
            if self.passing_score is not None:
                passed = score >= self.passing_score
            result = EvalScore(score, explanation=reason, passed=passed)
        except Exception as exc:
            result = error_score(exc)
        shown = {"uses_input": any(shows_input(p, ec.expected is not None) for p in parts),
                 "uses_expected": (any(p.needs_right_answer for p in parts) if ec.expected is not None else None)}
        _end_span(span, ec, self.model, datas, result, (time.monotonic() - started) * 1000.0,
                  parts=(len(parts), met), counted=(sum(p.count is not None for p in parts), len(asked)), **shown)
        return {name: result}


def _verdicts(parts: tuple[Part, ...], asked: list[tuple[bool, str]], output: Any) -> list[tuple[bool, str]]:
    """Each part's ``(met, reason)``: a count-only part by code alone; a part with a count beside something else is met
    when the count holds AND the model's verdict on the rest is met; any other part is the model's verdict. ``asked``
    holds the model's verdicts for the parts that are not count-only, in order. ``output`` is the row's OUTPUT: a dict
    or a list is counted by its text values, not its JSON text (``_judge_count.texts_of``)."""
    out, answers = [], iter(asked)
    for p in parts:
        if p.counted_only:
            out.append(decide(p.count, output))  # type: ignore[arg-type]
            continue
        met, reason = next(answers)
        if p.count is not None:
            holds, evidence = decide(p.count, output)
            met, reason = met and holds, f"{evidence} The rest of the part: {reason}".strip()
        out.append((met, reason))
    return out


def judge(
    criteria: str,
    *,
    model: Optional[str] = None,
    api_key_env: str = "OPENAI_API_KEY",
    base_url: Optional[str] = None,
    name: Optional[str] = None,
    passing_score: Optional[float] = None,
) -> Judge:
    """An LLM judge on any OpenAI-compatible endpoint (OpenAI, Groq, Together, xAI, your own).

    ``model`` defaults to ``gpt-4.1-mini`` (``DEFAULT_JUDGE_MODEL``). Another model is used only when you name it;
    cheaper ones miss some length and tone controls (see the module docstring). A model the provider has retired is
    an error score naming it (``ModelRetiredError``). A key other than ``OPENAI_API_KEY`` needs ``base_url=`` and
    ``model=``; its calls count toward ``max_cost_usd``.

    This helper uses the judge's default 60-second HTTP request timeout, independent of the
    runner's task-only ``timeout_s``. A request timeout produces an error score; the requests
    and retries together do not share or extend the task's timeout.
    """
    return Judge(criteria, model=model, api_key_env=api_key_env, base_url=base_url, name=name,
                 passing_score=passing_score)
