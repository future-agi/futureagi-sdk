import type { Context, Span, TracerProvider } from "@opentelemetry/api";
import type { Selector, SnapshotIdentity } from "../context/types";
import { activeContext, allowlisted, Attributes, carrierAttributes, CARRIER_KEY, mode, provider, recording, safe, SCOPE_KEY, setAttributes } from "./otel";
import { closure, errorType, identityAttrs, linkedSkill, selectorAttrs, SnapshotLike, validIdentity } from "./identity";
import { deliveryState, ScopeState } from "./registry";
import { logFirstLoad, recordLastLoad } from "./status";

export interface ReadTicket {
  readonly parent: Context;
  readonly current: Span;
  readonly provider?: TracerProvider;
  readonly started: number;
}
interface DeliveryTicket extends ReadTicket {
  readonly state: ScopeState;
  readonly mode: "on" | "load_only";
}
export function beginRead(enabled = true): ReadTicket | undefined {
  if (!enabled || mode() === "off") return undefined;
  return safe(() => {
    logFirstLoad();
    const parent = activeContext();
    const current = recording(parent);
    if (!parent || !current) return undefined;
    return { parent, current, provider: provider().value, started: Date.now() };
  });
}
// Capture parent/time before I/O, not the mode or a writable attribution state.
// Completion selects which evidence store can be mutated; off never records.
function atCompletion(ticket: ReadTicket): DeliveryTicket | undefined {
  const activeMode = mode();
  if (activeMode === "off") return undefined;
  const { current, parent } = ticket;
  const traceId = current.spanContext().traceId;
  const explicit = parent.getValue(SCOPE_KEY) as ScopeState | undefined;
  const state = deliveryState(traceId, activeMode, explicit);
  if (!explicit && Object.keys(state.attrs).length === 0) state.attrs = carrierAttributes(parent.getValue(CARRIER_KEY));
  const framework = (current as Span & { attributes?: Attributes }).attributes?.["gen_ai.agent.name"];
  if (!state.attrs["gen_ai.agent.name"] && typeof framework === "string") {
    state.attrs = allowlisted({ ...state.attrs, "gen_ai.agent.name": framework });
    state.agentSource = "framework";
  }
  return { ...ticket, state, mode: activeMode };
}
// Only overwrite an agent name which this hook itself put on this span.
const contextAgents = new WeakMap<Span, unknown>();
function scopeAttrs(ticket: DeliveryTicket): Attributes {
  const attrs = Object.fromEntries(Object.entries(ticket.state.attrs).filter(([key]) => /^(fi\.context\.(id|version_id|digest|name|version|requested_label|requested_version|binding_id|session_id)|gen_ai\.agent\.(name|id))$/.test(key)));
  const explicit = (ticket.current as Span & { attributes?: Attributes }).attributes;
  for (const key of ["gen_ai.agent.name", "gen_ai.agent.id"]) {
    if (explicit?.[key] !== undefined && !(key === "gen_ai.agent.name" && explicit[key] === contextAgents.get(ticket.current))) attrs[key] = explicit[key];
  }
  return allowlisted(attrs);
}
function emit(ticket: DeliveryTicket, name: string, attrs: Attributes, failed = false): boolean {
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
function enrich(ticket: DeliveryTicket, resetSkills = false): void {
  // An explicit scope may have been entered inside an ancestor span shared by
  // parallel agents. Never mutate that ancestor; its future children read the
  // scope carrier. Current-span enrichment is the automatic-mode contract.
  if (ticket.parent.getValue(SCOPE_KEY)) return;
  if (ticket.mode === "on" && mode() === "on") {
    const explicit = (ticket.current as Span & { attributes?: Attributes }).attributes;
    // OTel has setters, not a delete operation. On an already enriched span
    // replace its previous context's list with a truthful empty list/count.
    if (resetSkills && explicit?.["fi.skills.count"] !== undefined) {
      setAttributes(ticket.current, { "fi.skills.version_ids": [], "fi.skills.ids": [], "fi.skills.refs": [],
        "fi.skills.count": 0, ...(explicit["fi.skills.truncated"] === undefined ? {} : { "fi.skills.truncated": false }) });
    }
    const attrs = Object.fromEntries(Object.entries(ticket.state.attrs).filter(([key]) =>
      !key.startsWith("gen_ai.agent.") || explicit?.[key] === undefined ||
      (key === "gen_ai.agent.name" && explicit[key] === contextAgents.get(ticket.current))));
    setAttributes(ticket.current, attrs);
    if (ticket.state.agentSource === "context" && attrs["gen_ai.agent.name"]) contextAgents.set(ticket.current, attrs["gen_ai.agent.name"]);
  }
}
function loadContext(ticket: DeliveryTicket, snapshot: SnapshotLike, enrichCurrent = true): void {
  const attrs = identityAttrs(snapshot.identity, snapshot.manifest.requested);
  const version = snapshot.identity.versionId;
  if (!attrs["fi.context.version_id"]) return;
  const changed = ticket.state.attrs["fi.context.version_id"] !== version;
  ticket.state.selectContext(attrs, snapshot.identity.name);
  const links = closure(snapshot);
  // Do not assert an empty closure when lazy manifest metadata does not supply it.
  const linked: Attributes = links ? { "fi.context.linked_skill_version_ids": links.map(link => link.identity.versionId) } : {};
  if (!ticket.state.history.contexts.has(version) && emit(ticket, "context.load", { ...scopeAttrs(ticket), ...attrs, ...linked })) ticket.state.history.contexts.add(version);
  if (enrichCurrent) enrich(ticket, changed);
}
function loadSkill(ticket: DeliveryTicket, id: SnapshotIdentity, selector: Selector, via: string, evidence: string, root: boolean, extra: Attributes = {}): void {
  if (!validIdentity(id)) return;
  const key = `${id.versionId}:${evidence}`;
  const attrs: Attributes = { ...identityAttrs(id, selector), ...scopeAttrs(ticket),
    "fi.skill.load.via": via, "fi.skill.load.evidence": evidence,
    "fi.skill.load.cached": false, "fi.skill.load.root_file": root, ...extra };
  if (!ticket.state.history.loads.has(key) && emit(ticket, "skill.load", attrs)) {
    ticket.state.history.loads.add(key);
    recordLastLoad(id.name, id.version, evidence);
  }
  if (ticket.mode === "on") ticket.state.addSkill(attrs);
  enrich(ticket);
}
export function enterContext(snapshot: SnapshotLike): void {
  const read = beginRead();
  const delivery = read && atCompletion(read);
  if (delivery) loadContext(delivery, snapshot, false);
}
export function finishRead(read: ReadTicket | undefined, snapshot: SnapshotLike, path?: string): void {
  if (!read) return;
  safe(() => {
    const ticket = atCompletion(read);
    if (!ticket) return;
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
export function failRead(read: ReadTicket | undefined, snapshot: SnapshotLike, error: unknown, path?: string): void {
  if (!read) return;
  safe(() => {
    const ticket = atCompletion(read);
    if (!ticket) return;
    const link = path ? linkedSkill(snapshot, path) : undefined;
    // A context selector is not a child's selector. Until the consumption
    // interface supplies verified closure metadata, omit an unattributable
    // child failure rather than falsely matching a skill named like its context.
    if (snapshot.identity.kind === "agent_context" && path?.startsWith("skills/") && !link) return;
    const name = link?.identity.name ?? snapshot.identity.name;
    const selector = link?.requested ?? snapshot.manifest.requested;
    const type = errorType(error);
    const key = JSON.stringify([name, selector, type]);
    if (ticket.state.history.failures.has(key)) return;
    const via = snapshot.identity.kind === "agent_context" ? "context.read" : path === undefined ? "sdk.read_all" : "sdk.read_file";
    if (emit(ticket, "skill.load", { ...scopeAttrs(ticket), "fi.skill.name": name, ...selectorAttrs(selector), "fi.skill.load.via": via, "error.type": type }, true)) ticket.state.history.failures.add(key);
  });
}
export function declareIdentity(id: SnapshotIdentity, selector: Selector, via: "explicit" | "lock", cached: boolean): void {
  const read = beginRead();
  if (read) safe(() => {
    const ticket = atCompletion(read);
    if (ticket) loadSkill(ticket, id, selector, via, "declared", true, { "fi.skill.load.cached": cached });
  });
}
