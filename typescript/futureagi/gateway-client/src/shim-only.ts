// ---------------------------------------------------------------------------
// What @agentcc/client 1.x accepted that @future-agi/sdk/gateway does not
// ---------------------------------------------------------------------------
//
// The client-side options below changed or checked a request before it was
// sent, from tables and rules the SDK held itself. They are not part of this
// client; the @agentcc/client 2.x compatibility package keeps them. A
// defined value raises here instead of being dropped without a word.

const SHIM_ONLY_OPTIONS: Record<string, string> = {
  dropParams: "a client-side model table that removed tools and response_format for models it listed",
  modifyParams: "a client-side transform of every request's params; change the params before the call instead",
  preCallRules: "client-side rules checked before every request; check them before the call instead",
};

/** Raise a TypeError for any 1.x-only option given a value (null and undefined mean "not given"). */
export function assertNoShimOnlyOptions(opts: object): void {
  for (const [name, what] of Object.entries(SHIM_ONLY_OPTIONS)) {
    const value = (opts as Record<string, unknown>)[name];
    if (value !== undefined && value !== null) {
      throw new TypeError(
        `AgentCC option ${name} is not part of @future-agi/sdk/gateway: it was ${what}. ` +
          "Remove it, or keep @agentcc/client 1.x for it.",
      );
    }
  }
}
