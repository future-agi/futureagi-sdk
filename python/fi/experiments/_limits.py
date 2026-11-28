"""``Limits``. Only the this release fields exist in this build."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Optional


@dataclass(frozen=True)
class Limits:
    """Retries, fail-fast and prices for a run.

    - ``retries``: re-run a trial that raised a user exception up to N times.
    - ``transient_retries``: 429 / 5xx / connection errors / provider ``RateLimitError`` classes
      retry with backoff 2-4-8 s (``Retry-After`` honoured); concurrency halves on a 429 and
      recovers by one every 30 s.
    - ``fail_fast``: stop when the first N trials all fail with one exception class (0 = off).
    - ``prices``: USD per 1M input/output tokens by model name, for ``max_cost_usd``.
    """

    retries: int = 0
    transient_retries: int = 3
    fail_fast: int = 5
    prices: Optional[Mapping[str, tuple[float, float]]] = None

    def __post_init__(self) -> None:
        for name in ("retries", "transient_retries", "fail_fast"):
            if int(getattr(self, name)) < 0:
                raise ValueError(f"Limits.{name} must be >= 0")
