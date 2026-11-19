import type { Context, Span, TracerProvider } from "@opentelemetry/api";
import type { Selector, SnapshotIdentity } from "../context/types";
import { activeContext, allowlisted, Attributes, carrierAttributes, CARRIER_KEY, mode, provider, recording, safe, SCOPE_KEY, setAttributes } from "./otel";
import { closure, errorType, identityAttrs, linkedSkill, selectorAttrs, SnapshotLike, validIdentity } from "./identity";
import { evidenceState, ScopeState, sharedRegistry } from "./registry";
import { logFirstLoad, recordLastLoad } from "./status";

export interface ReadTicket {
  readonly parent: Context;
  readonly current: Span;
  readonly provider?: TracerProvider;
  readonly state: ScopeState;
  readonly started: number;
  readonly mode: "on" | "load_only";
}
export function beginRead(enabled = true): ReadTicket | undefined {
  if (!enabled || mode() === "off") return undefined;
  return safe(() => {
    logFirstLoad();
    const parent = activeContext();
    const current = recording(parent);
    if (!parent || !current) return undefined;
    const selected = provider();
    const activeMode = mode() as "on" | "load_only";
    const traceId = current.spanContext().traceId;
    const explicit = parent.getValue(SCOPE_KEY) as ScopeState | undefined;
    const state = explicit ?? (activeMode === "on" ? sharedRegistry(true)!.state(traceId, true)! : evidenceState(traceId));
    if (!explicit && Object.keys(state.attrs).length === 0) state.attrs = carrierAttributes(parent.getValue(CARRIER_KEY));
    const framework = (current as Span & { attributes?: Attributes }).attributes?.["gen_ai.agent.name"];
    if (!state.attrs["gen_ai.agent.name"] && typeof framework === "string") {
      state.attrs = allowlisted({ ...state.attrs, "gen_ai.agent.name": framework });
      state.agentSource = "framework";
    }
    return { parent, current, provider: selected.value, state, started: Date.now(), mode: activeMode };
  });
}
function scopeAttrs(ticket: ReadTicket): Attributes {
  const attrs = Object.fromEntries(Object.entries(ticket.state.attrs).filter(([key]) => /^(fi\.context\.(id|version_id|digest|name|version|requested_label|requested_version|binding_id|session_id)|gen_ai\.agent\.(name|id))$/.test(key)));
  const explicit = (ticket.current as Span & { attributes?: Attributes }).attributes;
  for (const key of ["gen_ai.agent.name", "gen_ai.agent.id"]) {
    if (explicit?.[key] !== undefined) attrs[key] = explicit[key];
  }
  return allowlisted(attrs);
}
function emit(ticket: ReadTicket, name: string, attrs: Attributes, failed = false): boolean {
  if (!ticket.provider) return false;
  const span = ticket.provider.getTracer(name === "context.load" ? "futureagi.context" : "futureagi.skills")
    .startSpan(name, { kind: 0, startTime: ticket.started }, ticket.parent);
  const recorded = span.isRecording();
  try {
    if (recorded) {
      setAttributes(span, Object.fromEntries(Object.entries(attrs).slice(0, 64)));
      if (failed) span.setStatus({ code: 2 }); // ERROR; never record exception messages/content.
    }
  } finally { span.end(); }
  return recorded;
}
function enrich(ticket: ReadTicket): void {
  // An explicit scope may have been entered inside an ancestor span shared by
  // parallel agents. Never mutate that ancestor; its future children read the
  // scope carrier. Current-span enrichment is the automatic-mode contract.
  if (ticket.parent.getValue(SCOPE_KEY)) return;
  if (ticket.mode === "on" && mode() === "on") {
    const explicit = (ticket.current as Span & { attributes?: Attributes }).attributes;
    const attrs = Object.fromEntries(Object.entries(ticket.state.attrs).filter(([key]) => !key.startsWith("gen_ai.agent.") || explicit?.[key] === undefined));
    setAttributes(ticket.current, attrs);
  }
}
export function loadContext(ticket: ReadTicket, snapshot: SnapshotLike, enrichCurrent = true): void {
  const attrs = identityAttrs(snapshot.identity, snapshot.manifest.requested);
  const version = snapshot.identity.versionId;
  if (!attrs["fi.context.version_id"] || ticket.state.contexts.has(version)) return;
  if (ticket.state.attrs["fi.context.version_id"] !== version) {
    ticket.state.attrs = allowlisted({ ...Object.fromEntries(Object.entries(ticket.state.attrs).filter(([key]) => !key.startsWith("fi.context.") && !key.startsWith("fi.skills."))), ...attrs });
  }
  if (!ticket.state.attrs["gen_ai.agent.name"]) {
    ticket.state.attrs = allowlisted({ ...ticket.state.attrs, "gen_ai.agent.name": snapshot.identity.name });
    ticket.state.agentSource = "context";
  }
  const links = closure(snapshot);
  // Do not assert an empty closure when lazy manifest metadata does not supply it.
  const linked: Attributes = links ? { "fi.context.linked_skill_version_ids": links.map(link => link.identity.versionId) } : {};
  if (emit(ticket, "context.load", { ...scopeAttrs(ticket), ...attrs, ...linked })) ticket.state.contexts.add(version);
  if (enrichCurrent) enrich(ticket);
}
function loadSkill(ticket: ReadTicket, id: SnapshotIdentity, selector: Selector, via: string, evidence: string, root: boolean, extra: Attributes = {}): void {
  if (!validIdentity(id)) return;
  const key = `${id.versionId}:${evidence}`;
  if (ticket.state.loads.has(key)) return;
  const attrs: Attributes = { ...identityAttrs(id, selector), ...scopeAttrs(ticket),
    "fi.skill.load.via": via, "fi.skill.load.evidence": evidence,
    "fi.skill.load.cached": false, "fi.skill.load.root_file": root, ...extra };
  if (emit(ticket, "skill.load", attrs)) {
    ticket.state.loads.add(key);
    recordLastLoad(id.name, id.version, evidence);
  }
  if (ticket.mode === "on") ticket.state.addSkill(attrs);
  enrich(ticket);
}
export function finishRead(ticket: ReadTicket | undefined, snapshot: SnapshotLike, path?: string): void {
  if (!ticket || mode() === "off") return;
  safe(() => {
    if (snapshot.identity.kind === "skill") {
      loadSkill(ticket, snapshot.identity, snapshot.manifest.requested, path === undefined ? "sdk.read_all" : "sdk.read_file", "delivered", path === undefined || path === "SKILL.md", {
        "fi.skill.files": snapshot.manifest.files.length,
        "fi.skill.bytes": snapshot.manifest.files.reduce((total, file) => total + file.sizeBytes, 0),
      });
    } else if (path === undefined || path === "AGENTS.md") loadContext(ticket, snapshot);
    else {
      const link = linkedSkill(snapshot, path);
      if (link) {
        loadContext(ticket, snapshot);
        loadSkill(ticket, link.identity, link.requested, "context.read", "delivered", path === `${link.mount}SKILL.md`, { "fi.skill.via_context.version_id": snapshot.identity.versionId });
      }
    }
  });
}
export function failRead(ticket: ReadTicket | undefined, snapshot: SnapshotLike, error: unknown, path?: string): void {
  if (!ticket || mode() === "off") return;
  safe(() => {
    const link = path ? linkedSkill(snapshot, path) : undefined;
    // A context selector is not a child's selector. Until the consumption
    // interface supplies verified closure metadata, omit an unattributable
    // child failure rather than falsely matching a skill named like its context.
    if (snapshot.identity.kind === "agent_context" && path?.startsWith("skills/") && !link) return;
    const name = link?.identity.name ?? snapshot.identity.name;
    const selector = link?.requested ?? snapshot.manifest.requested;
    const type = errorType(error);
    const key = JSON.stringify([name, selector, type]);
    if (ticket.state.failures.has(key)) return;
    const via = snapshot.identity.kind === "agent_context" ? "context.read" : path === undefined ? "sdk.read_all" : "sdk.read_file";
    if (emit(ticket, "skill.load", { ...scopeAttrs(ticket), "fi.skill.name": name, ...selectorAttrs(selector), "fi.skill.load.via": via, "error.type": type }, true)) ticket.state.failures.add(key);
  });
}
export function declareIdentity(id: SnapshotIdentity, selector: Selector, via: "explicit" | "lock", cached: boolean): void {
  const ticket = beginRead();
  if (ticket) safe(() => loadSkill(ticket, id, selector, via, "declared", true, { "fi.skill.load.cached": cached }));
}
