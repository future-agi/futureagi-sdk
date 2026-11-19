import { allowlisted, Attributes, REGISTRY_KEY } from "./otel";

class History {
  readonly loads = new Set<string>();
  readonly failures = new Set<string>();
  readonly contexts = new Set<string>();
}

export class ScopeState {
  attrs: Attributes;
  agentSource = "none";
  visible = false;
  constructor(attrs: Attributes = {}, readonly history = new History()) { this.attrs = allowlisted(attrs); }
  // Scoped load-only dedup must not mutate the carrier revived by a later on.
  private evidence?: ScopeState;
  view(mode: "on" | "load_only"): ScopeState {
    if (mode === "on") return this;
    if (!this.evidence) {
      this.evidence = new ScopeState(this.attrs, this.history);
      this.evidence.agentSource = this.agentSource;
    }
    return this.evidence;
  }
  selectContext(attrs: Attributes, name: string): void {
    const changed = this.attrs["fi.context.version_id"] !== attrs["fi.context.version_id"];
    this.attrs = allowlisted({ ...Object.fromEntries(Object.entries(this.attrs).filter(([k]) =>
      !k.startsWith("fi.context.") && !(changed && k.startsWith("fi.skills.")))), ...attrs });
    if (!this.attrs["gen_ai.agent.name"] || this.agentSource === "context") {
      this.attrs = allowlisted({ ...this.attrs, "gen_ai.agent.name": name });
      this.agentSource = "context";
    }
    // Next load-only read starts from this verified context. Never retire history.
    this.evidence = undefined;
  }
  addSkill(attrs: Attributes): void {
    const versions = (this.attrs["fi.skills.version_ids"] ?? []) as readonly string[];
    const version = attrs["fi.skill.version_id"] as string;
    if (versions.includes(version)) return;
    if (versions.length >= 32) {
      this.attrs = allowlisted({ ...this.attrs, "fi.skills.truncated": true });
      return;
    }
    this.attrs = allowlisted({ ...this.attrs,
      "fi.skills.version_ids": [...versions, version],
      "fi.skills.ids": [...(this.attrs["fi.skills.ids"] as readonly string[] ?? []), attrs["fi.skill.id"]],
      "fi.skills.refs": [...(this.attrs["fi.skills.refs"] as readonly string[] ?? []), `${attrs["fi.skill.name"]}@v${attrs["fi.skill.version"]}`],
      "fi.skills.count": versions.length + 1,
    });
  }
}

/** Shared ABI: v=1, get(traceId) returns allowlisted attributes or undefined.
 * No spans, content, providers or timers are retained. TTL is absolute. */
export class TraceRegistry {
  readonly v = 1;
  private readonly entries = new Map<string, { born: number; state: ScopeState }>();
  constructor(readonly capacity = 4096, readonly ttl = 3600000, private readonly clock = Date.now) {}
  state(traceId: string, create = false, publish = create): ScopeState | undefined {
    const now = this.clock();
    let entry = this.entries.get(traceId);
    if (entry && now - entry.born >= this.ttl) { this.entries.delete(traceId); entry = undefined; }
    if (!entry && create) entry = { born: now, state: new ScopeState() };
    if (entry) {
      if (publish) entry.state.visible = true;
      this.entries.delete(traceId);
      this.entries.set(traceId, entry);
      while (this.entries.size > this.capacity) this.entries.delete(this.entries.keys().next().value!);
    }
    return entry?.state;
  }
  get(traceId: string): Attributes | undefined {
    const state = this.state(traceId);
    return state?.visible ? state.attrs : undefined;
  }
  get size(): number { return this.entries.size; }
}
export function sharedRegistry(create = false): TraceRegistry | undefined {
  const globals = globalThis as unknown as Record<symbol, TraceRegistry>;
  if (!globals[REGISTRY_KEY] && create) globals[REGISTRY_KEY] = localRegistry();
  return globals[REGISTRY_KEY];
}

// One bounded store for both formats and modes. Only publish its reader to
// processors after an on-mode read; get() never exposes evidence-only views.
const LOCAL = Symbol.for("futureagi.runtime.skills.delivery.v1");
function localRegistry(): TraceRegistry {
  const globals = globalThis as unknown as Record<symbol, TraceRegistry>;
  return globals[LOCAL] ??= new TraceRegistry();
}
export function deliveryState(traceId: string, mode: "on" | "load_only", explicit?: ScopeState): ScopeState {
  const owner = explicit ?? (sharedRegistry(mode === "on") ?? localRegistry()).state(traceId, true, mode === "on")!;
  return owner.view(mode);
}
