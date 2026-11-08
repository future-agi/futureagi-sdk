import type { RequestOptions } from "../platform/transport";

export type Selector = Readonly<
  { label: string; version?: never } | { version: number; label?: never }
>;
export type SnapshotKind = "agent_context" | "skill";
export interface SnapshotIdentity {
  readonly kind: SnapshotKind;
  readonly resourceId: string;
  readonly name: string;
  readonly version: number;
  readonly versionId: string;
  readonly digest: string;
}
export interface ResolutionLease {
  readonly resolutionId: string;
  readonly resolutionExpiresAt: string;
}
export interface FileMetadata {
  readonly path: string;
  readonly sha256: string;
  readonly sizeBytes: number;
}
export interface SnapshotManifest {
  readonly identity: SnapshotIdentity;
  readonly requested: Selector;
  readonly lease: ResolutionLease;
  readonly files: readonly FileMetadata[];
}
/** Adapter to generated operations, not a second HTTP client. Forward options
 * unchanged and address continuation by the supplied UUID/version, never a label.
 */
export interface SnapshotSource {
  resolve(name: string, selector: Selector): Promise<unknown>;
  manifest(
    identity: SnapshotIdentity,
    offset: number,
    options: RequestOptions,
  ): Promise<unknown>;
  chunk(
    identity: SnapshotIdentity,
    path: string,
    offset: number,
    options: RequestOptions,
  ): Promise<unknown>;
}
