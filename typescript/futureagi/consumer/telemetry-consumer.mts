// The telemetry public subpath also compiles when its optional OTel peer is absent.
import {
  configure,
  FutureAGISkillsSpanProcessor,
  status,
  withAgentScope,
} from "@future-agi/sdk/telemetry";

configure({skillsTracing: "off"});
const processor = new FutureAGISkillsSpanProcessor();
const result = status();
const agent: string | null = result.agent_name;
withAgentScope({agent: "worker"}, () => undefined);
void [processor, agent];
