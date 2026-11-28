/**
 * Typed stream events for StreamManager.
 *
 * @module
 */

import type { Usage } from "./types/shared";
import type { ChatCompletion } from "./types/chat/chat-completion";
import type { ToolCallDelta } from "./types/chat/chat-completion-chunk";

export type StreamEvent =
  | { type: "content"; text: string }
  | { type: "tool_call"; index: number; id?: string; name?: string; arguments?: string }
  | { type: "usage"; usage: Usage }
  | { type: "done"; completion: ChatCompletion }
  | { type: "error"; error: Error };
