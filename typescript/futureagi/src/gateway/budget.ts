/**
 * Per-user and global budget management.
 *
 * @module
 */

import { AgentCCError } from "./errors";

// ---------------------------------------------------------------------------
// Window parsing
// ---------------------------------------------------------------------------

const WINDOW_PATTERN = /^(\d+)([mhdwM])$/;

const WINDOW_UNIT_SECONDS: Record<string, number> = {
  m: 60,
  h: 3600,
  d: 86400,
  w: 604800,
  M: 2592000, // 30 days
};

function parseWindow(window: string): number {
  const match = WINDOW_PATTERN.exec(window);
  if (!match) {
    throw new Error(
      `Invalid window format: "${window}". ` +
        "Expected format like '1m', '5m', '1h', '1d', '1w', '1M'.",
    );
  }
  return parseInt(match[1], 10) * WINDOW_UNIT_SECONDS[match[2]];
}

// ---------------------------------------------------------------------------
// BudgetManager
// ---------------------------------------------------------------------------

export interface BudgetManagerOptions {
  maxBudget?: number;
  /** Rolling window duration, e.g. `"1h"`, `"1d"`, `"1M"`. */
  window?: string;
}

/**
 * Per-user and global budget management.
 *
 * Tracks cumulative spend and enforces budget limits at both global and
 * per-user levels.
 *
 * @example
 * ```typescript
 * const budget = new BudgetManager({ maxBudget: 10.0 }); // $10 total
 * budget.checkBudget(0.05);  // throws AgentCCError if over
 * budget.updateCost(0.05);
 *
 * // With rolling window:
 * const hourly = new BudgetManager({ maxBudget: 10.0, window: "1h" });
 * ```
 */
export class BudgetManager {
  readonly maxBudget: number | null;
  readonly window: string | null;

  private _currentSpend = 0;
  private _userBudgets: Record<string, number> = {};
  private _userSpend: Record<string, number> = {};
  private _windowStart: number;

  constructor(opts: BudgetManagerOptions = {}) {
    this.maxBudget = opts.maxBudget ?? null;
    this.window = opts.window ?? null;
    this._windowStart = Date.now() / 1000;
  }

  private _maybeResetWindow(): void {
    if (!this.window) return;
    const windowSeconds = parseWindow(this.window);
    const now = Date.now() / 1000;
    if (now - this._windowStart >= windowSeconds) {
      this._currentSpend = 0;
      this._userSpend = {};
      this._windowStart = now;
    }
  }

  /** Throws `AgentCCError` if adding `estimatedCost` would exceed budget. */
  checkBudget(estimatedCost: number = 0, user?: string): void {
    this._maybeResetWindow();
    if (
      this.maxBudget != null &&
      this._currentSpend + estimatedCost > this.maxBudget
    ) {
      throw new AgentCCError(
        `Budget exceeded: current spend $${this._currentSpend.toFixed(4)} + ` +
          `estimated $${estimatedCost.toFixed(4)} > max $${this.maxBudget.toFixed(4)}`,
      );
    }
    if (user && user in this._userBudgets) {
      const userSpend = this._userSpend[user] ?? 0;
      if (userSpend + estimatedCost > this._userBudgets[user]) {
        throw new AgentCCError(
          `User budget exceeded for '${user}': $${userSpend.toFixed(4)} + ` +
            `$${estimatedCost.toFixed(4)} > $${this._userBudgets[user].toFixed(4)}`,
        );
      }
    }
  }

  /** Record cost from a completed request. */
  updateCost(cost: number, user?: string): void {
    this._maybeResetWindow();
    this._currentSpend += cost;
    if (user) {
      this._userSpend[user] = (this._userSpend[user] ?? 0) + cost;
    }
  }

  /** Set budget limit for a specific user. */
  setUserBudget(user: string, budget: number): void {
    this._userBudgets[user] = budget;
  }

  /** Get current cumulative spend. */
  getCurrentSpend(user?: string): number {
    this._maybeResetWindow();
    if (user) return this._userSpend[user] ?? 0;
    return this._currentSpend;
  }

  /** Get remaining budget. Returns `null` if no budget is set. */
  getRemainingBudget(user?: string): number | null {
    this._maybeResetWindow();
    if (user && user in this._userBudgets) {
      return this._userBudgets[user] - (this._userSpend[user] ?? 0);
    }
    if (this.maxBudget != null) {
      return this.maxBudget - this._currentSpend;
    }
    return null;
  }

  /** Reset spend counters. */
  reset(user?: string): void {
    if (user) {
      this._userSpend[user] = 0;
    } else {
      this._currentSpend = 0;
      this._userSpend = {};
      this._windowStart = Date.now() / 1000;
    }
  }

  /**
   * Estimate future spend based on current rate.
   * @param hours - Number of hours to project (default 24).
   */
  projectedCost(hours: number = 24, user?: string): number {
    this._maybeResetWindow();
    const now = Date.now() / 1000;
    const elapsedHours = (now - this._windowStart) / 3600;
    if (elapsedHours <= 0) return 0;

    const current = user
      ? this._userSpend[user] ?? 0
      : this._currentSpend;
    return (current / elapsedHours) * hours;
  }

  /**
   * Check if a user has a budget set and hasn't exceeded it.
   */
  isValidUser(user: string): boolean {
    this._maybeResetWindow();
    if (!(user in this._userBudgets)) return false;
    const spend = this._userSpend[user] ?? 0;
    return spend <= this._userBudgets[user];
  }
}
