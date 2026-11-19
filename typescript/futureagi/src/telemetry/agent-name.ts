// Keep the observer structural: either package may be installed without the
// optional SDK/OTel declarations. Standard recording spans expose both APIs.
import type { Attributes } from './otel';
const VIEW = Symbol.for('futureagi.runtime.agent-identity.v1');
interface View { name?: string; id?: string; automatic: boolean }
interface Writers {
  [VIEW]?(mark?: true): View;
  setAttribute(key: string, value: unknown): unknown;
  setAttributes?(attributes: Readonly<Record<string, unknown>>): unknown;
}

export const AGENT_NAME = 'gen_ai.agent.name';
// The optional fi-core processor looks up the exact SDK-published attributes
// object it just copied. Foreign carriers and equal strings prove no origin.
const SOURCES = Symbol.for('futureagi.runtime.context-agent.sources.v1');
const ORIGIN = Symbol.for('futureagi.runtime.context-agent.writer.v1');
type Origin = { automatic: boolean };
type ObservedSetter = Writers['setAttribute'] & { [ORIGIN]?: Origin };
type Source = 'context' | 'agent_scope';
// Keep the callback ABI read by the optional runtime processor. Older callbacks
// represented context alone; absence is never evidence of an SDK writer.
interface Observer { (span: Writers): void; source?: Source }
type Observers = WeakMap<object, Observer>;
const globals = globalThis as unknown as { [SOURCES]?: Observers };

export function agentIdentity(span: Writers): View {
  if (span[VIEW]) return span[VIEW]();
  const attrs = (span as Writers & { attributes?: Attributes }).attributes;
  const name = attrs?.[AGENT_NAME], id = attrs?.['gen_ai.agent.id'];
  return {name: typeof name === 'string' ? name : undefined, id: typeof id === 'string' ? id : undefined,
    automatic: (span.setAttribute as ObservedSetter)[ORIGIN]?.automatic === true};
}

// A framework may intentionally write even the same name later. OTel has no
// attribute-change listener; observe only the two public setters of spans on
// which we actually wrote a derived name. Nothing is added to exported data.
export function markInheritedName(span: Writers): void {
  if (span[VIEW]) { span[VIEW](true); return; }
  const single = span.setAttribute as ObservedSetter;
  let origin = single[ORIGIN];
  if (!origin) {
    const tracked = { automatic: false };
    const bulk = span.setAttributes;
    if (typeof bulk !== "function") return;
    const observed: ObservedSetter = function(this: Writers, key, value) {
      if (key === AGENT_NAME) tracked.automatic = false;
      return single.call(this, key, value);
    };
    observed[ORIGIN] = tracked;
    try {
      span.setAttributes = function(attributes) {
        if (Object.prototype.hasOwnProperty.call(attributes, AGENT_NAME)) tracked.automatic = false;
        return bulk.call(this, attributes);
      };
      span.setAttribute = observed;
    } catch { return; } // Non-standard read-only spans: preserve unknown writers.
    origin = tracked;
  }
  origin.automatic = true;
}

const markScope = Object.assign((span: Writers) => markInheritedName(span), {source: 'agent_scope' as const});
export function publishedSource<T extends object>(attrs: T, source: string): T {
  if (source === 'context' || source === 'agent_scope')
    (globals[SOURCES] ??= new WeakMap()).set(attrs, source === 'context' ? markInheritedName : markScope);
  return attrs;
}

export function inheritedSource(attrs: unknown): Source | 'none' {
  const observer = typeof attrs === 'object' && attrs !== null ? globals[SOURCES]?.get(attrs) : undefined;
  return observer ? observer.source ?? 'context' : 'none';
}

export function markPublishedName(span: Writers, attrs: unknown): void {
  if (typeof attrs === 'object' && attrs !== null) globals[SOURCES]?.get(attrs)?.(span);
}
