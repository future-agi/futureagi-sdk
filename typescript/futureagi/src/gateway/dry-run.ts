// ---------------------------------------------------------------------------
// Dry Run — request inspection types
// ---------------------------------------------------------------------------

export interface DryRunResult {
  /** The full URL that would be sent to. */
  url: string;
  /** HTTP method (e.g. "POST"). */
  method: string;
  /** All headers that would be sent. */
  headers: Record<string, string>;
  /** The request body (after modifyParams and dropParams). */
  body: Record<string, unknown> | null;
}
