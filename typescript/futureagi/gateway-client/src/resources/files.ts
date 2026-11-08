import type { BaseClient } from "../base-client.js";
import type { FileObject, FileList, FileUploadParams } from "../types/files.js";

export class Files {
  constructor(private _client: BaseClient) {}

  async create(params: FileUploadParams): Promise<FileObject> {
    const form = new FormData();
    form.append("file", params.file as Blob);
    form.append("purpose", params.purpose);

    return (this._client as any).request({
      method: "POST",
      path: "/v1/files",
      body: form,
      headers: params.extra_headers,
    });
  }

  async list(): Promise<FileList> {
    return (this._client as any).request({
      method: "GET",
      path: "/v1/files",
    });
  }

  async retrieve(fileId: string): Promise<FileObject> {
    return (this._client as any).request({
      method: "GET",
      path: `/v1/files/${encodeURIComponent(fileId)}`,
    });
  }

  /** Retrieve file content as raw Response. */
  async content(fileId: string): Promise<Response> {
    return (this._client as any).requestRaw({
      method: "GET",
      path: `/v1/files/${encodeURIComponent(fileId)}/content`,
    });
  }

  async delete(fileId: string): Promise<{ id: string; deleted: boolean }> {
    return (this._client as any).request({
      method: "DELETE",
      path: `/v1/files/${encodeURIComponent(fileId)}`,
    });
  }
}
