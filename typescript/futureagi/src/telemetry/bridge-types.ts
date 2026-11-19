/** Structural OpenTelemetry surface so platform-only TypeScript consumers do not need the optional peer's declarations. */
export type Attributes = Readonly<Record<string, string | number | boolean | readonly string[]>>;
export type Mode = "on" | "off" | "load_only";

export interface Context {
  getValue(key: symbol): unknown;
  setValue(key: symbol, value: unknown): Context;
  deleteValue(key: symbol): Context;
}

/** Only the operations used on the child span emitted by the bridge. */
interface EmittedSpan<MutationResult = void> {
  isRecording(): boolean;
  setAttribute(key: string, value: string | number | boolean | string[]): MutationResult;
  setStatus(status: { code: number; message?: string }): MutationResult;
  end(): void;
}

export interface Span extends EmittedSpan<Span> {
  spanContext(): { traceId: string };
}

interface Tracer {
  startSpan(name: string, options: { kind: 0; startTime: number }, parent: Context): EmittedSpan;
}

/** Runtime-compatible configuration shape; provider implementation stays optional. */
export interface TracerProvider {
  getTracer(name: string): Tracer;
}
