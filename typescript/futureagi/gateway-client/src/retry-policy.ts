/**
 * Per-error-type retry configuration.
 *
 * @module
 */

export interface RetryPolicyOptions {
  rateLimitRetries?: number;
  timeoutRetries?: number;
  connectionErrorRetries?: number;
  internalServerErrorRetries?: number;
  badGatewayRetries?: number;
  serviceUnavailableRetries?: number;
  gatewayTimeoutRetries?: number;
}

const STATUS_FIELDS: Record<number, keyof RetryPolicyOptions> = {
  429: "rateLimitRetries",
  500: "internalServerErrorRetries",
  502: "badGatewayRetries",
  503: "serviceUnavailableRetries",
  504: "gatewayTimeoutRetries",
};

const DEFAULTS: Required<RetryPolicyOptions> = {
  rateLimitRetries: 3,
  timeoutRetries: 2,
  connectionErrorRetries: 2,
  internalServerErrorRetries: 2,
  badGatewayRetries: 1,
  serviceUnavailableRetries: 1,
  gatewayTimeoutRetries: 1,
};

export class RetryPolicy {
  private _opts: Required<RetryPolicyOptions>;

  constructor(opts: RetryPolicyOptions = {}) {
    this._opts = { ...DEFAULTS, ...opts };
  }

  getRetriesForStatus(statusCode: number): number {
    const field = STATUS_FIELDS[statusCode];
    if (field) return this._opts[field] as number;
    return 0;
  }

  getRetriesForConnectionError(): number {
    return this._opts.connectionErrorRetries;
  }

  getRetriesForTimeout(): number {
    return this._opts.timeoutRetries;
  }
}
