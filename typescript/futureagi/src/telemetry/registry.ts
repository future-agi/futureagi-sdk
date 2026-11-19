import { allowlisted, Attributes, REGISTRY_KEY } from "./otel";

export class ScopeState {
  attrs: Attributes;
  readonly loads = new Set<string>();
  readonly failures = new Set<string>();
  readonly contexts = new Set<string>();
  agentSource = "none";
  constructor(attrs: Attributes = {}) { this.attrs = allowlisted(attrs); }
  // Scoped load-only dedup must not mutate the carrier revived by a later on.
  private evidence?: ScopeState;
  evidenceOnly(): ScopeState { return this.evidence ??= new ScopeState(this.attrs); }
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
  state(traceId: string, create = false): ScopeState | undefined {
    const now = this.clock();
    let entry = this.entries.get(traceId);
    if (entry && now - entry.born >= this.ttl) { this.entries.delete(traceId); entry = undefined; }
    if (!entry && create) entry = { born: now, state: new ScopeState() };
    if (entry) {
      this.entries.delete(traceId);
      this.entries.set(traceId, entry);
      while (this.entries.size > this.capacity) this.entries.delete(this.entries.keys().next().value!);
    }
    return entry?.state;
  }
  get(traceId: string): Attributes | undefined { return this.state(traceId)?.attrs; }
  get size(): number { return this.entries.size; }
}
export function sharedRegistry(create = false): TraceRegistry | undefined {
  const globals = globalThis as unknown as Record<symbol, TraceRegistry>;
  if (!globals[REGISTRY_KEY] && create) globals[REGISTRY_KEY] = new TraceRegistry();
  return globals[REGISTRY_KEY];
}

// load_only keeps only bounded evidence, never exposes attribution to a processor.
let evidence: TraceRegistry | undefined;
export function evidenceState(traceId: string): ScopeState {
  evidence ??= new TraceRegistry();
  return evidence.state(traceId, true)!;
}
