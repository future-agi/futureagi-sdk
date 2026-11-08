import type { Client } from "../platform/client";
import type { RequestOptions } from "../platform/transport";
import {
  CHUNK_BYTES,
  ContextSnapshot,
  ManifestCollector,
  PAGE_SIZE,
  SnapshotIntegrityError,
  parseSelector,
  requireLive,
} from "./snapshot";
import type {
  Selector,
  SnapshotIdentity,
  SnapshotKind,
  SnapshotSource,
} from "./types";

const PREFIX = "/model-hub/skills/contexts/";
function versionPath(identity: SnapshotIdentity): string {
  return `${PREFIX}${identity.resourceId}/versions/${identity.version}/`;
}

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

class ContextSource implements SnapshotSource {
  constructor(private readonly client: Client) {}
  resolve(name: string, selector: Selector): Promise<unknown> {
    return this.client.request("GET", `${PREFIX}resolve/`, {
      query: { name, ...selector },
    });
  }
  manifest(
    identity: SnapshotIdentity,
    offset: number,
    options: RequestOptions,
  ): Promise<unknown> {
    return this.client.request(
      "GET",
      `${versionPath(identity)}manifest/`,
      { query: { file_offset: offset, file_limit: PAGE_SIZE } },
      options,
    );
  }
  chunk(
    identity: SnapshotIdentity,
    path: string,
    offset: number,
    options: RequestOptions,
  ): Promise<unknown> {
    return this.client.request(
      "GET",
      `${versionPath(identity)}files/`,
      { query: { path, offset, max_bytes: CHUNK_BYTES } },
      options,
    );
  }
}

/** Wrap the shared authenticated platform Client; no HTTP implementation or cache. */
export class ContextClient extends SnapshotClient {
  constructor(client: Client) {
    super(new ContextSource(client), "agent_context");
  }
}
