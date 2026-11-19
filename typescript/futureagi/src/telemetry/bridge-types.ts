/** Structural OpenTelemetry surface so platform-only TypeScript consumers do not need the optional peer's declarations. */
export type Attributes = Readonly<Record<string, string | number | boolean | readonly string[]>>;
export type Mode = "on" | "off" | "load_only";

export interface Context {
  getValue(key: symbol): unknown;
  setValue(key: symbol, value: unknown): Context;
  deleteValue(key: symbol): Context;
}

export interface Span {
  isRecording(): boolean;
  spanContext(): { traceId: string };
  setAttribute(key: string, value: string | number | boolean | string[]): Span;
  setStatus(status: { code: number; message?: string }): Span;
  end(): void;
}

/** Runtime-compatible configuration shape; provider implementation stays optional. */
export interface TracerProvider {
  getTracer(name: string): unknown;
}
