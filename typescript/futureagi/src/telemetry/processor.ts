import type { Attributes, Context, Span } from "./bridge-types";
import { AGENT_NAME, markPublishedName } from "./agent-name";
import { allowlisted, carrierSource, CARRIER_KEY, mode, PROCESSOR_KEY, REGISTRY_KEY, safe } from "./otel";

interface StartSpan extends Span { readonly attributes?: Record<string, unknown>; }
interface RegistryReader { v: number; get(traceId: string): Attributes | undefined; }

/** List in the provider constructor. Never calls addSpanProcessor (OTel JS 2.x). */
export class FutureAGISkillsSpanProcessor {
  onStart(span: StartSpan, parentContext: Context): void {
    if (mode() !== "on") return;
    safe(() => {
      const globals = globalThis as unknown as Record<symbol, unknown>;
      // Conservative diagnostic: only the most recently observed trace. A
      // primitive marker allocates no registry and never retains span objects.
      const traceId = span.spanContext().traceId;
      globals[PROCESSOR_KEY] = traceId;
      const carrier = parentContext.getValue(CARRIER_KEY);
      const registry = globals[REGISTRY_KEY] as RegistryReader | undefined;
      const source = carrier != null
        ? carrierSource(carrier)
        : registry?.v === 1 ? registry.get(traceId) : undefined;
      const attrs = allowlisted(source);
      for (const [key, value] of Object.entries(attrs)) {
        if (Object.prototype.hasOwnProperty.call(span.attributes ?? {}, key)) continue;
        span.setAttribute(key, Array.isArray(value) ? [...value] : value as string | number | boolean);
        if (key === AGENT_NAME) markPublishedName(span, source);
      }
    });
  }
  onEnd(): void { /* No I/O or span retention. */ }
  forceFlush(): Promise<void> { return Promise.resolve(); }
  shutdown(): Promise<void> { return Promise.resolve(); }
}
