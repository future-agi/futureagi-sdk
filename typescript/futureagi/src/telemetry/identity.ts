import type { Selector, SnapshotIdentity, SnapshotManifest } from "../context/types";
import type { Attributes } from "./otel";

export interface SnapshotLike { readonly identity: SnapshotIdentity; readonly manifest: SnapshotManifest; }
export interface LockedSkill {
  readonly kind: "skill";
  readonly resourceId: string;
  readonly versionId: string;
  readonly name: string;
  readonly version: number;
  readonly digest: string;
  readonly requested: Selector;
}
export interface LinkedSkill { readonly mount: string; readonly identity: SnapshotIdentity; readonly requested: Selector; }
const closures = new WeakMap<object, readonly LinkedSkill[]>();
const uuid = /^[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}$/;
export function validIdentity(id: SnapshotIdentity): boolean {
  return (id.kind === "skill" || id.kind === "agent_context") && uuid.test(id.resourceId) && uuid.test(id.versionId)
    && /^sha256:[0-9a-f]{64}$/.test(id.digest) && Number.isSafeInteger(id.version) && id.version > 0
    && typeof id.name === "string" && id.name.length <= 64 && /^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(id.name);
}
export function selectorAttrs(selector: Selector, prefix = "fi.skill"): Attributes {
  if ("version" in selector && Number.isSafeInteger(selector.version) && selector.version! > 0) return { [`${prefix}.requested_version`]: selector.version! };
  if (typeof selector.label === "string" && /^[a-z0-9][a-z0-9-]{0,39}$/.test(selector.label)) return { [`${prefix}.requested_label`]: selector.label };
  return {};
}
export function identityAttrs(id: SnapshotIdentity, selector: Selector): Attributes {
  if (!validIdentity(id)) return {};
  const prefix = id.kind === "skill" ? "fi.skill" : "fi.context";
  return { [`${prefix}.id`]: id.resourceId, [`${prefix}.name`]: id.name,
    [`${prefix}.version_id`]: id.versionId, [`${prefix}.version`]: id.version,
    [`${prefix}.digest`]: id.digest, ...selectorAttrs(selector, prefix) };
}

/** Called only AFTER VerifiedSnapshot has validated the complete descriptor and
 * every child digest. Never resolves or downloads additional files for telemetry. */
export function rememberClosure(snapshot: SnapshotLike, files: Readonly<Record<string, string>>): void {
  if (snapshot.identity.kind !== "agent_context") return;
  const descriptor = JSON.parse(files[".futureagi/context.json"]) as { links: Array<{
    mount: string; skill_id: string; version_id: string; version: number; digest: string; requested: Selector;
  }> };
  const links = descriptor.links.map(link => Object.freeze({ mount: link.mount, requested: Object.freeze({ ...link.requested }),
    identity: Object.freeze({ kind: "skill" as const, resourceId: link.skill_id, versionId: link.version_id,
      version: link.version, digest: link.digest, name: link.mount.split("/")[1] }) }));
  if (links.every(link => validIdentity(link.identity))) closures.set(snapshot, Object.freeze(links));
}
export function copyClosure(from: object, to: object): void {
  const links = closures.get(from);
  if (links) closures.set(to, links);
}
export function closure(snapshot: object): readonly LinkedSkill[] | undefined { return closures.get(snapshot); }
export function linkedSkill(snapshot: object, path: string): LinkedSkill | undefined {
  return closure(snapshot)?.find(link => path.startsWith(link.mount));
}
export function errorType(error: unknown): string {
  const value = error as { constructor?: { name?: string }; status?: number } | null;
  if (value?.constructor?.name === "SnapshotIntegrityError") return "integrity";
  if (value?.constructor?.name === "ResolutionExpiredError") return "lease";
  if (value?.status === 401 || value?.status === 403) return "authorization";
  if (value?.status === 404) return "not_found";
  return "other";
}
