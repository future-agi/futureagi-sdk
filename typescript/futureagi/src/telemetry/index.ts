import type { Context } from "@opentelemetry/api";
import { activeContext, allowlisted, api, carrierAttributes, CARRIER_KEY, configure, debugFailure, mode, recording, safe, SCOPE_KEY } from "./otel";
import { identityAttrs, LockedSkill, SnapshotLike } from "./identity";
import { declareIdentity, enterContext } from "./hooks";
import { ScopeState, sharedRegistry } from "./registry";

export { configure };
export { status } from "./status";
export { FutureAGISkillsSpanProcessor } from "./processor";
export type { LockedSkill } from "./identity";
export type { Mode } from "./otel";

/** The carrier returned by getValue is an immutable value, never a mutable
 * shared attributes map. The context view publishes a fresh value after reads,
 * including across await, without installing/replacing a context manager. */
class ScopeContext implements Context {
  constructor(private readonly base: Context, private readonly state: ScopeState, private readonly reset: boolean) {}
  getValue(key: symbol): unknown {
    if (key === SCOPE_KEY) return this.state;
    if (key === CARRIER_KEY) return Object.freeze({ v: 1, attrs: mode() === "on" ? this.state.propagationAttrs : Object.freeze({}), reset_skills: this.reset });
    return this.base.getValue(key);
  }
  setValue(key: symbol, value: unknown): Context {
    if (key === CARRIER_KEY || key === SCOPE_KEY) return this.base.setValue(key, value);
    return new ScopeContext(this.base.setValue(key, value), this.state, this.reset);
  }
  deleteValue(key: symbol): Context {
    if (key === CARRIER_KEY || key === SCOPE_KEY) return this.base.deleteValue(key);
    return new ScopeContext(this.base.deleteValue(key), this.state, this.reset);
  }
}

export function withAgentScope<T>(options: { agent?: string; context?: SnapshotLike }, callback: () => T): T {
  const entryMode = mode();
  if (entryMode === "off") return callback();
  const setup = safe(() => {
    const manager = api()?.context;
    const parent = activeContext();
    if (!manager || !parent) return undefined;
    const previous = parent.getValue(SCOPE_KEY) as ScopeState | undefined;
    const span = recording(parent);
    const carrier = parent.getValue(CARRIER_KEY);
    const inherited = previous?.attrs ?? (carrier !== undefined ? carrierAttributes(carrier) : span ? sharedRegistry()?.get(span.spanContext().traceId) : undefined) ?? {};
    let attrs = { ...inherited };
    if (options.context) {
      attrs = Object.fromEntries(Object.entries(attrs).filter(([key]) => !/^(fi\.context\.|fi\.skills\.|gen_ai\.agent\.)/.test(key)));
    }
    if (options.agent !== undefined) attrs["gen_ai.agent.name"] = options.agent;
    const state = new ScopeState(allowlisted(attrs));
    state.agentSource = options.agent !== undefined ? "agent_scope" : options.context ? "none" : previous?.agentSource ?? "none";
    if (options.context) state.view(entryMode).selectContext(identityAttrs(options.context.identity, options.context.manifest.requested), options.context.identity.name);
    return { manager, context: new ScopeContext(parent, state, !!options.context) };
  });
  if (!setup) return callback();
  // Never retry application callbacks, including synchronous exceptions and
  // asynchronous rejection. Only a bridge failure before invocation falls back.
  let invoked = false;
  try {
    return setup.manager.with(setup.context, () => {
      invoked = true;
      if (options.context) safe(() => enterContext(options.context!));
      return callback();
    });
  } catch (error) {
    if (invoked) throw error;
    debugFailure();
    return callback();
  }
}

/** An application assertion, not proof that a model followed a skill. */
export function declareSkill(snapshotOrLock: SnapshotLike | LockedSkill): void {
  if (mode() === "off") return;
  safe(() => {
    if ("manifest" in snapshotOrLock) {
      if (snapshotOrLock.identity.kind === "skill") declareIdentity(snapshotOrLock.identity, snapshotOrLock.manifest.requested, "explicit", "files" in snapshotOrLock);
    } else if (snapshotOrLock.kind === "skill") declareIdentity(snapshotOrLock, snapshotOrLock.requested, "lock", false);
  });
}
