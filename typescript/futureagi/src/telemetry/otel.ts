/** Optional OTel bridge. No runtime import, provider installation or exporter. */
import type { Context, Span, TracerProvider } from "@opentelemetry/api";

export type Attributes = Readonly<Record<string, string | number | boolean | readonly string[]>>;
export type Mode = "on" | "off" | "load_only";
export const CARRIER_KEY = Symbol.for("futureagi.runtime.span_attributes.v1");
export const SCOPE_KEY = Symbol.for("futureagi.runtime.scope.v1");
const SPAN_KEY = Symbol.for("OpenTelemetry Context Key SPAN");
export const REGISTRY_KEY = Symbol.for("futureagi.runtime.skills.v1");
export const PROCESSOR_KEY = Symbol.for("futureagi.runtime.skills.processor.v1");

interface ApiGlobal {
  version?: string;
  trace?: TracerProvider;
  context?: {
    active(): Context;
    with<T>(context: Context, callback: () => T): T;
  };
}
const CONFIG_KEY = Symbol.for("futureagi.runtime.skills.config.v1");
interface ModeReader { readonly v: 1; mode(): Mode }
const globals = globalThis as unknown as Record<symbol, ModeReader | undefined>;
let configuredMode: Mode | undefined;
let configuredProvider: TracerProvider | undefined;
let debugged = false;

export function configure(options: { skillsTracing?: Mode; tracerProvider?: TracerProvider } = {}): void {
  configuredMode = options.skillsTracing;
  configuredProvider = options.tracerProvider;
  // Share only the mode reader with traceAI and other ESM/CJS SDK instances.
  // Do not publish the provider, install an exporter or require OTel on import.
  try { globals[CONFIG_KEY] = modeReader; } catch { /* locked host global: keep local behavior */ }
}
function localMode(): Mode {
  const value = configuredMode ?? (typeof process !== "undefined" ? process.env.FI_SKILLS_TRACING : undefined);
  return value === "off" || value === "load_only" ? value : "on";
}
const modeReader: ModeReader = Object.freeze({ v: 1, mode: localMode });
export function mode(): Mode {
  try {
    const reader = globals[CONFIG_KEY];
    if (reader?.v === 1 && reader !== modeReader && typeof reader.mode === "function") {
      const value = reader.mode();
      if (value === "on" || value === "off" || value === "load_only") return value;
    }
  } catch { /* An optional bridge must not interrupt consumption. */ }
  return localMode();
}
export function api(): ApiGlobal | undefined {
  return (globalThis as unknown as Record<symbol, ApiGlobal>)[Symbol.for("opentelemetry.js.api.1")];
}
export function provider(): { value?: TracerProvider; source: "configured" | "global" | "none" } {
  if (configuredProvider) return { value: configuredProvider, source: "configured" };
  const value = api()?.trace;
  // The global trace registration is a ProxyTracerProvider in OTel API 1.x.
  const proxy = value as TracerProvider & { getDelegate?: () => TracerProvider };
  const delegate = proxy?.getDelegate?.();
  if (!value || delegate?.constructor?.name === "NoopTracerProvider") return { source: "none" };
  return { value, source: "global" };
}
export function activeContext(): Context | undefined { return api()?.context?.active(); }
export function currentSpan(context = activeContext()): Span | undefined {
  return context?.getValue(SPAN_KEY) as Span | undefined;
}
export function debugFailure(): void {
  if (!debugged && mode() !== "off") {
    debugged = true;
    // Never print caught errors: they can contain credentials or file content.
    if (typeof process !== "undefined" && process.env.FI_TELEMETRY_DEBUG === "1")
      console.debug("futureagi.telemetry: telemetry bridge unavailable; consumption unchanged");
  }
}
export function safe<T>(callback: () => T): T | undefined {
  try { return callback(); } catch { debugFailure(); return undefined; }
}
export function allowlisted(input: unknown): Attributes {
  if (!input || typeof input !== "object" || Array.isArray(input)) return Object.freeze({});
  const result: Record<string, string | number | boolean | readonly string[]> = {};
  for (const [key, value] of Object.entries(input)) {
    if (Object.keys(result).length >= 64) break;
    if (Buffer.byteLength(key, "utf8") > 256 || !/^(fi\.skills\.|fi\.context\.|gen_ai\.agent\.)/.test(key)) continue;
    if (typeof value === "string" && Buffer.byteLength(value, "utf8") <= 256) result[key] = value;
    else if (typeof value === "boolean" || (typeof value === "number" && Number.isFinite(value))) result[key] = value;
    else if (Array.isArray(value) && value.every(v => typeof v === "string" && Buffer.byteLength(v, "utf8") <= 256))
      result[key] = Object.freeze(value.slice(0, 32));
  }
  return Object.freeze(result);
}
export function carrierSource(value: unknown): unknown {
  if (!value || typeof value !== "object" || !("v" in value) || value.v !== 1 || !("attrs" in value)) return undefined;
  return value.attrs;
}
export function carrierAttributes(value: unknown): Attributes {
  return allowlisted(carrierSource(value));
}
export function recording(context = activeContext()): Span | undefined {
  const span = currentSpan(context);
  return span?.isRecording() ? span : undefined;
}
export function setAttributes(span: Span, attrs: Attributes): void {
  for (const [key, value] of Object.entries(attrs)) span.setAttribute(key, Array.isArray(value) ? [...value] : value as string | number | boolean);
}
