/**
 * Delta reconciliation (ported from the Omega runtime). Every `message_delta.delta` and
 * `activity_output.chunk` the SDK yields is a new increment that never repeats.
 *
 * On a new connection the server re-seeds each still-open message or running step once with its
 * cumulative text, then streams suffixes. The reconciler keeps what it has
 * yielded per key and diffs that first frame:
 * - it starts with the delivered text: only the remainder is yielded, as a normal delta;
 * - a message whose snapshot does not (the server regenerated it): `message_reset {messageId, text}`
 *   carries the full replacement, and later deltas continue from it;
 * - activity output whose head was dropped (a rolling tail): the overlap of delivered suffix and
 *   snapshot prefix is skipped; with no overlap the whole snapshot is yielded with `truncated: true`.
 * A completed message (`message_complete`) closes its key.
 */

/** The event the reconciler synthesises when the server regenerated a message. */
export interface MessageResetEvent {
  /** Discriminator for a regenerated message's replacement text. */
  readonly type: "message_reset";
  /** Identifier of the message whose accumulated text must be replaced. */
  readonly messageId: string;
  /** The full replacement text; later deltas continue from it. */
  readonly text: string;
}

interface Keyed {
  readonly key: string;
  readonly text: string;
}

function keyOf(event: Readonly<Record<string, unknown>>): Keyed | undefined {
  if (event.type === "message_delta" && typeof event.messageId === "string" && typeof event.delta === "string") {
    return { key: `m:${event.messageId}`, text: event.delta };
  }
  if (event.type === "activity_output" && typeof event.stepId === "string" && typeof event.chunk === "string") {
    return { key: `a:${event.stepId}:${String(event.stream)}`, text: event.chunk };
  }
  return undefined;
}

/** Longest suffix of `delivered` that is a prefix of `snapshot`. */
function overlap(delivered: string, snapshot: string): number {
  const max = Math.min(delivered.length, snapshot.length);
  for (let n = max; n > 0; n -= 1) {
    if (delivered.endsWith(snapshot.slice(0, n))) return n;
  }
  return 0;
}

/** Tracks delivered text per open message and output stream, across reconnects. */
export class DeltaReconciler {
  private readonly delivered = new Map<string, string>();
  private seeded = new Set<string>();

  /** Call when a new connection opens: the next frame per key may be a cumulative snapshot. */
  newConnection(): void {
    this.seeded = new Set();
  }

  /** Reconcile one event. Returns the events to yield (zero, one, or a reset). */
  push<E extends Readonly<Record<string, unknown>>>(event: E): (E | MessageResetEvent)[] {
    if (event.type === "message_complete") {
      const message = event.message as { id?: unknown } | undefined;
      if (typeof message?.id === "string") this.delivered.delete(`m:${message.id}`);
      return [event];
    }
    const keyed = keyOf(event);
    if (keyed === undefined) return [event];
    const { key, text } = keyed;
    const before = this.delivered.get(key) ?? "";
    const firstOnConnection = !this.seeded.has(key);
    this.seeded.add(key);
    if (!firstOnConnection || before === "") {
      this.delivered.set(key, before + text);
      return text === "" ? [] : [event];
    }
    if (text.startsWith(before)) {
      const rest = text.slice(before.length);
      this.delivered.set(key, text);
      return rest === "" ? [] : [this.withText(event, rest)];
    }
    if (event.type === "message_delta") {
      this.delivered.set(key, text);
      return [{ type: "message_reset", messageId: event.messageId as string, text }];
    }
    const shared = overlap(before, text);
    const rest = text.slice(shared);
    this.delivered.set(key, before + rest);
    if (rest === "") return [];
    const out = this.withText(event, rest);
    return [shared === 0 ? ({ ...out, truncated: true } as E) : out];
  }

  private withText<E extends Readonly<Record<string, unknown>>>(event: E, text: string): E {
    return (event.type === "message_delta" ? { ...event, delta: text } : { ...event, chunk: text }) as E;
  }
}
