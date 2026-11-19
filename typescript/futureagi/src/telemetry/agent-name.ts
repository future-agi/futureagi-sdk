import type { Span } from '@opentelemetry/api';

export const AGENT_NAME = 'gen_ai.agent.name';
// The optional fi-core processor looks up the exact SDK-published attributes
// object it just copied. Foreign carriers and equal strings prove no origin.
const SOURCES = Symbol.for('futureagi.runtime.context-agent.sources.v1');
const ORIGIN = Symbol.for('futureagi.runtime.context-agent.writer.v1');
type Origin = { automatic: boolean };
type ObservedSetter = Span['setAttribute'] & { [ORIGIN]?: Origin };
type Observers = WeakMap<object, (span: Span) => void>;
const globals = globalThis as unknown as { [SOURCES]?: Observers };

export function automaticName(span: Span): boolean {
  return (span.setAttribute as ObservedSetter)[ORIGIN]?.automatic === true;
}

// A framework may intentionally write even the same name later. OTel has no
// attribute-change listener; observe only the two public setters of spans on
// which we actually wrote a derived name. Nothing is added to exported data.
export function markContextName(span: Span): void {
  const single = span.setAttribute as ObservedSetter;
  let origin = single[ORIGIN];
  if (!origin) {
    const tracked = { automatic: false };
    const bulk = span.setAttributes;
    const observed: ObservedSetter = function(this: Span, key, value) {
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

export function contextSource<T extends object>(attrs: T): T {
  (globals[SOURCES] ??= new WeakMap()).set(attrs, markContextName);
  return attrs;
}

export function markPublishedName(span: Span, attrs: unknown): void {
  if (typeof attrs === 'object' && attrs !== null) globals[SOURCES]?.get(attrs)?.(span);
}
