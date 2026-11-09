import { Client } from "../platform/client";
import { SnapshotClient } from "../context/client";
import { ConsumptionSource } from "../context/source";
import type {
  ResolutionLease,
  SnapshotIdentity,
  SnapshotSource,
} from "../context/types";

/** Isolated leaf consumption. A custom source retains responsibility for authorization. */
export class SkillsClient extends SnapshotClient {
  private readonly consumption?: ConsumptionSource;
  constructor(source: Client | SnapshotSource) {
    const consumption =
      source instanceof Client
        ? new ConsumptionSource(source, "skill")
        : undefined;
    super(consumption ?? (source as SnapshotSource), "skill");
    this.consumption = consumption;
  }
  checkAccess(
    identity: SnapshotIdentity,
    lease: ResolutionLease,
  ): Promise<void> {
    if (!this.consumption)
      throw new TypeError(
        "A custom SnapshotSource must supply its own live authorizer",
      );
    return this.consumption.checkAccess(identity, lease);
  }
}
