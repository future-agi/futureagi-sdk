import { activeContext, api, carrierAttributes, CARRIER_KEY, currentSpan, mode, PROCESSOR_KEY, provider, safe, SCOPE_KEY } from "./otel";
import { ScopeState, sharedRegistry } from "./registry";

export const LOAD_RULE = "A load is recorded on the first read of any file of a skill version inside a trace";
let lastLoad: { name: string; version: number; evidence: string; time: string } | null = null;
const logged = new Set<string>();
export function recordLastLoad(name: string, version: number, evidence: string): void {
  lastLoad = { name, version, evidence, time: new Date().toISOString() };
}
export function status() {
  return safe(() => {
    const selected = provider();
    const context = activeContext();
    const span = currentSpan(context);
    const traceId = span?.spanContext().traceId;
    const scope = context?.getValue(SCOPE_KEY) as ScopeState | undefined;
    const attrs = scope?.attrs ?? carrierAttributes(context?.getValue(CARRIER_KEY));
    const automatic = traceId ? sharedRegistry()?.get(traceId) : undefined;
    const readable = span as typeof span & { attributes?: Record<string, unknown>; resource?: { attributes?: Record<string, unknown> } };
    const framework = readable?.attributes?.["gen_ai.agent.name"];
    const service = readable?.resource?.attributes?.["service.name"];
    const agent = framework ?? attrs["gen_ai.agent.name"] ?? automatic?.["gen_ai.agent.name"];
    const seen = (globalThis as unknown as Record<symbol, unknown>)[PROCESSOR_KEY];
    const installed = !!traceId && seen === traceId;
    const activeMode = mode();
    return {
      otel_found: !!api(), provider: selected.source,
      processor_installed: activeMode === "on" && installed,
      mode: activeMode,
      truth_table_row: !selected.value ? "OTel absent / no provider" : "TS vanilla OTel JS provider",
      agent_name: typeof agent === "string" ? agent : typeof service === "string" && !service.startsWith("unknown_service") ? service : null,
      agent_name_source: agent && scope && agent === scope.attrs["gen_ai.agent.name"] ? scope.agentSource
        : framework ? (automatic?.["fi.context.name"] === framework ? "context" : "framework")
        : agent ? "context" : typeof service === "string" && !service.startsWith("unknown_service") ? "service.name" : "none",
      rule: LOAD_RULE, last_load: lastLoad ? { ...lastLoad } : null,
    };
  }) ?? { otel_found: false, provider: "none", processor_installed: false, mode: mode(), truth_table_row: "OTel absent / no provider", agent_name: null, agent_name_source: "none", rule: LOAD_RULE, last_load: null };
}
export function logFirstLoad(): void {
  if (mode() === "off") return;
  safe(() => {
    const facts = status();
    const reason = !facts.otel_found ? "no OpenTelemetry in this process"
      : facts.provider === "none" ? "no tracer provider found: pass one to configure({ tracerProvider })"
      : `recording skill loads (provider: ${facts.provider}; later spans: ${facts.processor_installed ? "stamped" : "not confirmed; list FutureAGISkillsSpanProcessor in the provider constructor"}; agent name: ${facts.agent_name ? "set" : "not set; set withAgentScope({ agent }) or OTEL_SERVICE_NAME"})`;
    if (logged.has(reason)) return;
    logged.add(reason);
    console.info(`futureagi.telemetry: ${reason}`);
  });
}
export function tracingHeader(tracing = true): string {
  if (!tracing || mode() === "off") return "off";
  return safe(() => provider().value ? mode() : "no_otel") ?? "no_otel";
}
export function doctorText(): string {
  const facts = status();
  // Identity values are deliberately redacted: diagnostic output must not leak
  // arbitrary app-supplied agent names, paths or credentials.
  return ["futureagi.telemetry", `OpenTelemetry found: ${facts.otel_found}`,
    `Provider: ${facts.provider}`, `Mode: ${facts.mode}`, `Later spans stamped in this trace: ${facts.processor_installed}`,
    `Setup: ${facts.truth_table_row}`, `Agent: ${facts.agent_name ? "set (redacted)" : "not set"} (${facts.agent_name_source})`,
    `Last load: ${facts.last_load ? `v${facts.last_load.version}, ${facts.last_load.evidence}, ${facts.last_load.time}` : "none"}`,
    facts.rule,
    facts.provider === "none" ? "Configure an OTel provider and pass it to configure({ tracerProvider })." : "For later spans, list new FutureAGISkillsSpanProcessor() in the provider constructor.",
    "Name the agent with withAgentScope({ agent }) or OTEL_SERVICE_NAME.",
  ].join("\n");
}
