/**
 * Typed stream events for StreamManager.events().
 *
 * Only what is emitted: a gateway error frame raises StreamError from
 * the iterator instead of arriving as an event, and `done` comes once, after
 * the body ends. @agentcc/client 1.0.1 declared an `error` variant that
 * nothing ever emitted.
 *
 * @module
 */

import type { Usage } from "./types/shared.js";
import type { ChatCompletion } from "./types/chat/chat-completion.js";
import type { ToolCallDelta } from "./types/chat/chat-completion-chunk.js";

export type StreamEvent =
  | { type: "content"; text: string }
  | { type: "tool_call"; index: number; id?: string; name?: string; arguments?: string }
  | { type: "usage"; usage: Usage }
  | { type: "done"; completion: ChatCompletion };
