// ---------------------------------------------------------------------------
// Batch Execution — Run multiple completions with concurrency control
// ---------------------------------------------------------------------------

import type { ChatCompletion } from "./types/chat/chat-completion";
import type { ChatCompletionMessageParam } from "./types/chat/completion-create-params";

// ---------------------------------------------------------------------------
// Semaphore — simple concurrency limiter
// ---------------------------------------------------------------------------

class Semaphore {
  private _count: number;
  private _waiting: Array<() => void> = [];

  constructor(max: number) {
    this._count = max;
  }

  async acquire(): Promise<void> {
    if (this._count > 0) {
      this._count--;
      return;
    }
    return new Promise<void>((resolve) => {
      this._waiting.push(resolve);
    });
  }

  release(): void {
    const next = this._waiting.shift();
    if (next) {
      next();
    } else {
      this._count++;
    }
  }
}

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface CompletionClient {
  chat: {
    completions: {
      create(params: {
        model: string;
        messages: ChatCompletionMessageParam[];
        [key: string]: unknown;
      }): Promise<ChatCompletion>;
    };
  };
}

export interface BatchCompletionParams {
  model: string;
  messages: ChatCompletionMessageParam[][];
  maxConcurrency?: number;
  returnExceptions?: boolean;
  temperature?: number;
  max_tokens?: number;
  [key: string]: unknown;
}

export interface BatchCompletionModelsParams {
  models: string[];
  messages: ChatCompletionMessageParam[];
  maxConcurrency?: number;
  temperature?: number;
  max_tokens?: number;
  [key: string]: unknown;
}

export interface ModelCompletionResult {
  model: string;
  completion: ChatCompletion | null;
  error: Error | null;
}

// ---------------------------------------------------------------------------
// batchCompletion — same model, multiple message arrays
// ---------------------------------------------------------------------------

export async function batchCompletion(
  client: CompletionClient,
  params: BatchCompletionParams,
): Promise<Array<ChatCompletion | Error>> {
  const {
    model,
    messages,
    maxConcurrency = 5,
    returnExceptions = false,
    temperature,
    max_tokens,
    ...restParams
  } = params;

  // Remove batch-specific params from pass-through
  delete restParams.messages;
  delete restParams.model;
  delete restParams.maxConcurrency;
  delete restParams.returnExceptions;

  const sem = new Semaphore(maxConcurrency);
  const results = new Array<ChatCompletion | Error>(messages.length);

  const createParams: Record<string, unknown> = { ...restParams };
  if (temperature !== undefined) createParams.temperature = temperature;
  if (max_tokens !== undefined) createParams.max_tokens = max_tokens;

  const tasks = messages.map(async (msgs, i) => {
    await sem.acquire();
    try {
      results[i] = await client.chat.completions.create({
        model,
        messages: msgs,
        ...createParams,
      });
    } catch (err) {
      if (returnExceptions) {
        results[i] = err instanceof Error ? err : new Error(String(err));
      } else {
        throw err;
      }
    } finally {
      sem.release();
    }
  });

  if (returnExceptions) {
    await Promise.allSettled(tasks);
  } else {
    await Promise.all(tasks);
  }

  return results;
}

// ---------------------------------------------------------------------------
// batchCompletionModels — same messages, different models
// ---------------------------------------------------------------------------

export async function batchCompletionModels(
  client: CompletionClient,
  params: BatchCompletionModelsParams,
): Promise<ModelCompletionResult[]> {
  const {
    models,
    messages,
    maxConcurrency = 5,
    temperature,
    max_tokens,
    ...restParams
  } = params;

  delete restParams.models;
  delete restParams.messages;
  delete restParams.maxConcurrency;

  const sem = new Semaphore(maxConcurrency);
  const results = new Array<ModelCompletionResult>(models.length);

  const createParams: Record<string, unknown> = { ...restParams };
  if (temperature !== undefined) createParams.temperature = temperature;
  if (max_tokens !== undefined) createParams.max_tokens = max_tokens;

  const tasks = models.map(async (model, i) => {
    await sem.acquire();
    try {
      const completion = await client.chat.completions.create({
        model,
        messages,
        ...createParams,
      });
      results[i] = { model, completion, error: null };
    } catch (err) {
      results[i] = {
        model,
        completion: null,
        error: err instanceof Error ? err : new Error(String(err)),
      };
    } finally {
      sem.release();
    }
  });

  await Promise.allSettled(tasks);
  return results;
}
