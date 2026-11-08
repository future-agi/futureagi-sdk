import { SnapshotClient } from "../context/client";
import type { SnapshotSource } from "../context/types";

/** Requires the frozen generated leaf consumption facade's operation adapter.
 * Never falls back to broad legacy Skills routes for a Context credential.
 */
export class SkillsClient extends SnapshotClient {
  constructor(source: SnapshotSource) {
    super(source, "skill");
  }
}
