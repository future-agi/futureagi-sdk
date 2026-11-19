// Capability declarations must accept every released-part name in the customer contract.
// These are server-advertised switches, not a claim that any offering is enabled.
import type { GetWorkspaceCapabilitiesResponse } from "../src/generated/platform/types.gen.js";

type Features = GetWorkspaceCapabilitiesResponse["features"];
type ReleasedPart = NonNullable<Features["releasedParts"]>[number];

// Preserve the original values while accepting the subsequently declared switches.
const usage: ReleasedPart = "usage_spend";
const unchecked: ReleasedPart = "unchecked_mark";
const ownership: ReleasedPart = "agent_ownership";
const otlp: ReleasedPart = "console_otlp";
const emergencyStop: ReleasedPart = "console_emergency_stop";
const signedTriggers: ReleasedPart = "console_signed_triggers";
const programmaticRuns: ReleasedPart = "console_programmatic_runs";

// releasedParts remains optional; omission and an empty list mean no switch is on.
const absent: Pick<Features, "releasedParts"> = {};
const disabled: Pick<Features, "releasedParts"> = { releasedParts: [] };
const advertised: Pick<Features, "releasedParts"> = {
  releasedParts: [usage, unchecked, ownership, otlp, emergencyStop, signedTriggers, programmaticRuns],
};

// A wider known enum must not silently turn into an unconstrained string array.
// @ts-expect-error Misspelled release parts are not part of the declared contract.
const misspelled: ReleasedPart = "console_programmatic_run";
// @ts-expect-error Release switch names are strings, never numbers.
const numeric: ReleasedPart = 1;
void [absent, disabled, advertised, misspelled, numeric];
