import type { Client } from "../platform/client";
import {
  ContextSnapshot,
  ManifestCollector,
  SnapshotIntegrityError,
  parseSelector,
  requireLive,
} from "./snapshot";
import type {
  ResolutionLease,
  Selector,
  SnapshotIdentity,
  SnapshotKind,
  SnapshotSource,
} from "./types";

import { ConsumptionSource } from "./source";

export class SnapshotClient {
  constructor(
    private readonly source: SnapshotSource,
    private readonly kind: SnapshotKind,
  ) {}
  async resolve(
    name: string,
    selector: Selector = { label: "production" },
  ): Promise<ContextSnapshot> {
    const requested = parseSelector(selector);
    const pages = new ManifestCollector(
      await this.source.resolve(name, requested),
      this.kind,
    );
    if (
      pages.identity.name !== name ||
      JSON.stringify(pages.requested) !== JSON.stringify(requested) ||
      ("version" in requested && pages.identity.version !== requested.version)
    )
      throw new SnapshotIntegrityError(
        "Resolve response does not match requested selector",
      );
    while (pages.nextOffset !== null) {
      requireLive(pages.lease);
      pages.add(
        await this.source.manifest(pages.identity, pages.nextOffset, {
          resolutionId: pages.lease.resolutionId,
        }),
      );
    }
    return new ContextSnapshot(pages.finish(), this.source);
  }
}

/** Wrap the shared authenticated platform Client; no HTTP implementation or cache. */
export class ContextClient extends SnapshotClient {
  private readonly consumption: ConsumptionSource;
  constructor(client: Client) {
    const source = new ConsumptionSource(client, "agent_context");
    super(source, "agent_context");
    this.consumption = source;
  }
  checkAccess(
    identity: SnapshotIdentity,
    lease: ResolutionLease,
  ): Promise<void> {
    return this.consumption.checkAccess(identity, lease);
  }
}
