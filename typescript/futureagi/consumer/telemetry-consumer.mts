// The telemetry public subpath also compiles when its optional OTel peer is absent.
import {
  configure,
  FutureAGISkillsSpanProcessor,
  status,
  withAgentScope,
} from "@future-agi/sdk/telemetry";

configure({skillsTracing: "off"});
// @ts-expect-error The provider must return a tracer that can start spans.
configure({tracerProvider: {getTracer: () => null}});
// @ts-expect-error An emitted span must support recording, attributes, status and end.
configure({tracerProvider: {getTracer: () => ({startSpan: () => ({end() {}})})}});
const processor = new FutureAGISkillsSpanProcessor();
const result = status();
const agent: string | null = result.agent_name;
withAgentScope({agent: "worker"}, () => undefined);
void [processor, agent];
