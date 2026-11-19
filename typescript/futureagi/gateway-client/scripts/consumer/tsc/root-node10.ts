// moduleResolution node10 with the gateway's typesVersions: the root entry
// still resolves (no typesVersions key matches it).
import * as root from "@future-agi/sdk";
import { AgentCC } from "@future-agi/sdk/gateway";
export type Root = typeof root;
export const c = new AgentCC({ apiKey: "k" });
