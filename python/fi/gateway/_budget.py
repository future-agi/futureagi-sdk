"""Per-user and global budget management."""

from __future__ import annotations

import re
import threading
import time
from dataclasses import dataclass, field

_WINDOW_PATTERN = re.compile(r"^(\d+)([mhdwM])$")

_WINDOW_UNIT_SECONDS: dict[str, float] = {
    "m": 60.0,
    "h": 3600.0,
    "d": 86400.0,
    "w": 604800.0,
    "M": 2592000.0,  # 30 days
}


@dataclass
class BudgetManager:
    """Per-user and global budget management.

    Tracks cumulative spend and enforces budget limits at both global and
    per-user levels.  Thread-safe via an internal lock.

    Usage::

        from fi.gateway import BudgetManager

        budget = BudgetManager(max_budget=10.0)  # $10 total
        budget.check_budget(0.05)  # raises AgentCCError if over
        budget.update_cost(0.05)

        # With rolling window:
        budget = BudgetManager(max_budget=10.0, window="1h")  # $10 per hour
    """

    max_budget: float | None = None
    window: str | None = None
    _current_spend: float = field(default=0.0, init=False)
    _user_budgets: dict[str, float] = field(default_factory=dict, init=False)
    _user_spend: dict[str, float] = field(default_factory=dict, init=False)
    _lock: threading.Lock = field(default_factory=threading.Lock, init=False)
    _window_start: float = field(default=0.0, init=False)

    def __post_init__(self) -> None:
        self._window_start = time.time()

    @staticmethod
    def _parse_window(window: str) -> float:
        """Convert a duration string (e.g. '1m', '5m', '1h', '1d', '1w', '1M') to seconds."""
        match = _WINDOW_PATTERN.match(window)
        if not match:
            raise ValueError(
                f"Invalid window format: {window!r}. "
                "Expected format like '1m', '5m', '1h', '1d', '1w', '1M'."
            )
        count = int(match.group(1))
        unit = match.group(2)
        return count * _WINDOW_UNIT_SECONDS[unit]

    def _maybe_reset_window(self) -> None:
        """Reset spend if the current window has expired. Must be called under lock."""
        if self.window is None:
            return
        window_seconds = self._parse_window(self.window)
        now = time.time()
        if now - self._window_start >= window_seconds:
            self._current_spend = 0.0
            self._user_spend.clear()
            self._window_start = now

    def check_budget(self, estimated_cost: float = 0.0, user: str | None = None) -> None:
        """Raise ``AgentCCError`` if adding *estimated_cost* would exceed budget."""
        with self._lock:
            self._maybe_reset_window()
            if self.max_budget is not None and self._current_spend + estimated_cost > self.max_budget:
                from fi.gateway._exceptions import AgentCCError

                raise AgentCCError(
                    f"Budget exceeded: current spend ${self._current_spend:.4f} + "
                    f"estimated ${estimated_cost:.4f} > max ${self.max_budget:.4f}"
                )
            if user and user in self._user_budgets:
                user_spend = self._user_spend.get(user, 0.0)
                if user_spend + estimated_cost > self._user_budgets[user]:
                    from fi.gateway._exceptions import AgentCCError

                    raise AgentCCError(
                        f"User budget exceeded for '{user}': ${user_spend:.4f} + "
                        f"${estimated_cost:.4f} > ${self._user_budgets[user]:.4f}"
                    )

    def update_cost(self, cost: float, user: str | None = None) -> None:
        """Record cost from a completed request."""
        with self._lock:
            self._maybe_reset_window()
            self._current_spend += cost
            if user:
                self._user_spend[user] = self._user_spend.get(user, 0.0) + cost

    def set_user_budget(self, user: str, budget: float) -> None:
        """Set budget limit for a specific user."""
        with self._lock:
            self._user_budgets[user] = budget

    def get_current_spend(self, user: str | None = None) -> float:
        """Get current cumulative spend."""
        with self._lock:
            self._maybe_reset_window()
            if user:
                return self._user_spend.get(user, 0.0)
            return self._current_spend

    def get_remaining_budget(self, user: str | None = None) -> float | None:
        """Get remaining budget.  Returns ``None`` if no budget is set."""
        with self._lock:
            self._maybe_reset_window()
            if user and user in self._user_budgets:
                return self._user_budgets[user] - self._user_spend.get(user, 0.0)
            if self.max_budget is not None:
                return self.max_budget - self._current_spend
            return None

    def reset(self, user: str | None = None) -> None:
        """Reset spend counters."""
        with self._lock:
            if user:
                self._user_spend[user] = 0.0
            else:
                self._current_spend = 0.0
                self._user_spend.clear()
                self._window_start = time.time()

    def projected_cost(self, hours: float = 24.0, user: str | None = None) -> float:
        """Estimate future spend based on current rate.

        Args:
            hours: Number of hours to project into the future (default 24).
            user: If provided, project for a specific user.

        Returns:
            Projected cost in USD.
        """
        with self._lock:
            self._maybe_reset_window()
            now = time.time()
            elapsed_hours = (now - self._window_start) / 3600.0
            if elapsed_hours <= 0:
                return 0.0

            current = self._user_spend.get(user, 0.0) if user else self._current_spend

            rate = current / elapsed_hours
            return rate * hours

    def is_valid_user(self, user: str) -> bool:
        """Check if a user has a budget set and hasn't exceeded it.

        Returns ``True`` if the user has a budget and their current spend
        is within that budget, ``False`` otherwise.
        """
        with self._lock:
            self._maybe_reset_window()
            if user not in self._user_budgets:
                return False
            user_spend = self._user_spend.get(user, 0.0)
            return user_spend <= self._user_budgets[user]
