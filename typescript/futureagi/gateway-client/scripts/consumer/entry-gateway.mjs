import { AgentCC, openaiOptions } from "@future-agi/sdk/gateway";
export const client = new AgentCC({ apiKey: "k", baseUrl: "http://127.0.0.1:9", dangerouslyAllowBrowser: true });
export const opts = openaiOptions;
