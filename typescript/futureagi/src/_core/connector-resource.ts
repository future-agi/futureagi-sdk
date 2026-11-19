/** Connector namespaces retain the root so withOptions settings remain effective. */
import type { PlatformCore } from "./platform-base";
import { Page } from "./pagination";
import { FutureAGIAPIError } from "./errors";

export class Resource {
  constructor(protected readonly client: { readonly _platform: PlatformCore }) {}
}

/** Walk channel cursors on the declared operation, never on a provider URL. */
export async function cursorPage(
  call: (query: Record<string, unknown>) => Promise<any>,
  query: Record<string, unknown>,
): Promise<Page<Record<string, unknown>>> {
  const fetch = async (cursor?: string) => {
    const value = await call({ ...query, ...(cursor === undefined ? {} : { cursor }) });
    if (!value || !Array.isArray(value.channels)) {
      throw new FutureAGIAPIError(200, undefined, { code: "invalid_page", message: "The response is missing its channel items" });
    }
    return value;
  };
  return new Page(await fetch(), { style: "cursor", itemsField: "channels", cursorParam: "cursor", nextCursorField: "next_cursor" }, fetch, undefined);
}
