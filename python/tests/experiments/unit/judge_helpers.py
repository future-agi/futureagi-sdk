"""A mock judge endpoint that also answers the judge's one criteria read (``CRITERIA_SYSTEM``, regression coverage).

``with_criteria(handler, needs_right_answer=True)`` answers the criteria read and passes every other request (one per
part of the checklist, wave 2d) to ``handler``; ``reads`` (a list) collects the criteria-read request bodies.
``part_verdict(met)`` is the body of one part's answer, in the shape ``SYSTEM`` asks for."""

import json
from typing import Any, Callable, Optional

import httpx

from fi.experiments.evaluators.judge import CRITERIA_SYSTEM


def criteria_answer(needs_right_answer: bool, needs_input: bool = True, parts: Optional[list] = None) -> dict[str, Any]:
    parts = parts or [{"part": "the criteria", "look_at": "the output", "needs_right_answer": needs_right_answer,
                       "needs_input": needs_input, "required": True}]
    return {"model": "m", "usage": {"prompt_tokens": 3, "completion_tokens": 2},
            "choices": [{"message": {"content": json.dumps({"parts": parts})}}]}


def part_verdict(met: bool, reason: str = "ok", model: str = "m", tokens: tuple = (5, 4)) -> dict[str, Any]:
    content = json.dumps({"facts": [], "reason": reason, "met": met})
    return {"model": model, "usage": {"prompt_tokens": tokens[0], "completion_tokens": tokens[1]},
            "choices": [{"message": {"content": content}}]}


def is_criteria_read(request: httpx.Request) -> bool:
    return json.loads(request.content)["messages"][0]["content"] == CRITERIA_SYSTEM


def with_criteria(handler: Callable[[httpx.Request], httpx.Response], needs_right_answer: bool = True,
                  reads: Optional[list] = None, needs_input: bool = True,
                  parts: Optional[list] = None) -> Callable[[httpx.Request], httpx.Response]:
    def answer(request: httpx.Request) -> httpx.Response:
        if is_criteria_read(request):
            if reads is not None:
                reads.append(json.loads(request.content))
            return httpx.Response(200, json=criteria_answer(needs_right_answer, needs_input, parts))
        return handler(request)

    return answer
