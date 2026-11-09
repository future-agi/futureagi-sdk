import type { Client } from "../platform/client";
import * as operations from "../platform/_operations";
import type { RequestOptions } from "../platform/transport";
import {
  CHUNK_BYTES,
  PAGE_SIZE,
  SnapshotIntegrityError,
  requireLive,
} from "./snapshot";
import type {
  ResolutionLease,
  Selector,
  SnapshotIdentity,
  SnapshotKind,
  SnapshotSource,
} from "./types";

/** Generated URLs/envelopes on the shared transport. No cache or lease renewal. */
export class ConsumptionSource implements SnapshotSource {
  private readonly operations;
  constructor(
    private readonly client: Client,
    private readonly kind: SnapshotKind,
  ) {
    this.operations =
      kind === "agent_context"
        ? [
            operations.OP_CONTEXTS_RESOLVE,
            operations.OP_CONTEXTS_MANIFEST,
            operations.OP_CONTEXTS_READ_FILE,
            operations.OP_CONTEXTS_CHECK_ACCESS,
          ]
        : [
            operations.OP_SKILL_CONSUMPTION_RESOLVE,
            operations.OP_SKILL_CONSUMPTION_MANIFEST,
            operations.OP_SKILL_CONSUMPTION_READ_FILE,
            operations.OP_SKILL_CONSUMPTION_CHECK_ACCESS,
          ];
  }
  private path(identity: SnapshotIdentity) {
    if (identity.kind !== this.kind)
      throw new SnapshotIntegrityError("Consumption resource kind mismatch");
    return { resource_id: identity.resourceId, number: identity.version };
  }
  resolve(name: string, selector: Selector): Promise<unknown> {
    return this.client.transport.call(this.operations[0], {
      query: { name, ...selector },
    });
  }
  manifest(
    identity: SnapshotIdentity,
    offset: number,
    options: RequestOptions,
  ): Promise<unknown> {
    return this.client.transport.call(
      this.operations[1],
      {
        path: this.path(identity),
        query: { file_offset: offset, file_limit: PAGE_SIZE },
      },
      options,
    );
  }
  chunk(
    identity: SnapshotIdentity,
    path: string,
    offset: number,
    options: RequestOptions,
  ): Promise<unknown> {
    return this.client.transport.call(
      this.operations[2],
      {
        path: this.path(identity),
        query: { path, offset, max_bytes: CHUNK_BYTES },
      },
      options,
    );
  }
  async checkAccess(
    identity: SnapshotIdentity,
    lease: ResolutionLease,
  ): Promise<void> {
    requireLive(lease);
    const result = await this.client.transport.call<unknown>(
      this.operations[3],
      {
        path: this.path(identity),
        body: {},
      },
      { resolutionId: lease.resolutionId },
    );
    if (
      !result ||
      typeof result !== "object" ||
      !("allowed" in result) ||
      result.allowed !== true ||
      !("version_id" in result) ||
      result.version_id !== identity.versionId ||
      !("digest" in result) ||
      result.digest !== identity.digest
    ) {
      throw new SnapshotIntegrityError(
        "Access check did not authorize this snapshot",
      );
    }
    requireLive(lease);
  }
}
