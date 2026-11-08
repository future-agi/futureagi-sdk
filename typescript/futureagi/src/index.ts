export * from './api';
export * from './datasets';
export * from './kb';
export * from './prompt';
export * from './annotations';
export * from './queues';
export * from './utils';
export * from './futureagi-client';
export * from './knowledge-bases';
export * from './prompts';
export * from './scores';
// FutureAGIClient errors and response shapes stay at the root. The released
// Client's distinct error/page tree stays under platform, never star-exported here.
export * from './_core';
export {
  APIConnectionError, AuthenticationError, BadRequestError, ConflictError,
  NotFoundError, PaymentRequiredError, PermissionDeniedError, CoreRateLimitError,
  UnprocessableEntityError, Page, ConsoleUnavailableError, CoreServerError,
} from './_core';
// Released root identities; Dataset* names are aliases of these same constructors.
export { RateLimitError, ServerError, RateLimitError as DatasetRateLimitError, ServerError as DatasetServerError } from './utils/errors';
export * from './webhooks';
// The released Client is not an alias for FutureAGIClient.
export { Client } from './platform';
export type { ClientConfig, RequestOptions } from './platform';
export * as platform from './platform';
