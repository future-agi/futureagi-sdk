import type { AxiosResponse } from 'axios';
import type { Prompt } from './client';
import { APIKeyAuth, APIKeyAuthConfig } from '../api/auth';
import { HttpMethod, RequestConfig } from '../api/types';
import { Routes } from '../utils/routes';
import { SDKException } from '../utils/errors';

export class PromptLabels {
  constructor(private prompt: Prompt) {}

  async list(): Promise<Record<string, any>> {
    const res = (await this.prompt.request({
      method: HttpMethod.GET,
      url: `${this.prompt.baseUrl}/${Routes.prompt_labels}`,
    } as RequestConfig)) as AxiosResponse;
    return (res.data ?? res) as any;
  }

  async getByName(name: string): Promise<Record<string, any> | undefined> {
    const data = await this.list();
    const items = (data as any).results ?? data;
    if (!Array.isArray(items)) return undefined;
    return items.find((it: any) => String(it?.name ?? '').toLowerCase() === name.toLowerCase());
  }

  async create(name: string): Promise<Record<string, any>> {
    const res = (await this.prompt.request({
      method: HttpMethod.POST,
      url: `${this.prompt.baseUrl}/${Routes.prompt_labels}`,
      json: { name, type: 'custom' },
    } as RequestConfig)) as AxiosResponse;
    return (res.data ?? res) as any;
  }

  async assign(name: string, version?: string): Promise<Record<string, any>> {
    // Prevent assignment to drafts
    if (!version && (await (this.prompt as any)._currentVersionIsDraft?.())) {
      (this.prompt as any)._pendingLabel = name;
      return { detail: 'Label will be assigned after commit', queued: true } as any;
    }
    if (version && version === this.prompt.template?.version && (await (this.prompt as any)._currentVersionIsDraft?.())) {
      (this.prompt as any)._pendingLabel = name;
      return { detail: 'Label will be assigned after commit', queued: true } as any;
    }

    const labelObj = await this.getByName(name);
    if (!labelObj?.id) throw new SDKException(`Label '${name}' not found. Create it first, then assign.`);
    const tplId = this.prompt.template?.id;
    const ver = version ?? this.prompt.template?.version;
    if (!tplId || !ver) throw new SDKException('template_id and version are required');
    const res = (await this.prompt.request({
      method: HttpMethod.POST,
      url: `${this.prompt.baseUrl}/${Routes.prompt_label_assign_by_id
        .replace('{template_id}', tplId)
        .replace('{label_id}', String(labelObj.id))}`,
      json: { version: ver },
    } as RequestConfig)) as AxiosResponse;
    return (res.data ?? res) as any;
  }

  async remove(name: string, version?: string): Promise<Record<string, any>> {
    if (!this.prompt.template?.id) throw new SDKException('Template must be loaded');
    const ver = version ?? this.prompt.template?.version;
    if (!ver) throw new SDKException('Version must be specified or available on the client');
    return this.removeFromVersion(name, ver);
  }

  async removeFromCurrentVersion(name: string): Promise<Record<string, any>> {
    if (!this.prompt.template?.id || !this.prompt.template.version) {
      throw new SDKException('Template and current version must be loaded');
    }
    return this.removeFromVersion(name, this.prompt.template.version);
  }

  private async removeFromVersion(name: string, version: string): Promise<Record<string, any>> {
    const versionId = await this._getVersionIdByName(version);
    if (!versionId) throw new SDKException(`Could not resolve version_id for version '${version}'`);
    const item = await this.getByName(name);
    if (!item?.id) throw new SDKException(`Label '${name}' not found`);
    const res = (await this.prompt.request({
      method: HttpMethod.POST,
      url: `${this.prompt.baseUrl}/${Routes.prompt_label_remove}`,
      json: { label_id: String(item.id), version_id: versionId },
    } as RequestConfig)) as AxiosResponse;
    return (res.data ?? res) as any;
  }

  private async _getVersionIdByName(versionName: string): Promise<string | undefined> {
    const res = (await this.prompt.request({
      method: HttpMethod.GET,
      url: `${this.prompt.baseUrl}/${Routes.get_template_version_history}`,
      params: { template_id: this.prompt.template?.id },
    } as RequestConfig)) as AxiosResponse;
    const history = (res.data ?? res).results ?? [];
    for (const e of history) {
      if (String(e.templateVersion) === versionName) {
        for (const key of ['id', 'versionId', 'executionId']) {
          if (e[key]) return String(e[key]);
        }
      }
    }
    return undefined;
  }
}

export async function setDefaultVersion(
  templateName: string,
  version: string,
  options: APIKeyAuthConfig = {},
): Promise<Record<string, any>> {
  const client = new APIKeyAuth(options);
  try {
    const res = (await client.request({
      method: HttpMethod.POST,
      url: `${client.baseUrl}/${Routes.prompt_label_set_default}`,
      json: { template_name: templateName, version },
    } as RequestConfig)) as AxiosResponse;
    return (res.data ?? res) as any;
  } finally {
    await client.close();
  }
}

export async function getTemplateLabels(
  {
    template_name,
    template_id,
    ...options
  }: APIKeyAuthConfig & { template_name?: string; template_id?: string } = {},
): Promise<Record<string, any>> {
  if (!template_name && !template_id) throw new SDKException('template_name or template_id is required');
  const client = new APIKeyAuth(options);
  try {
    const params: Record<string, any> = template_name ? { template_name } : { template_id };
    const res = (await client.request({
      method: HttpMethod.GET,
      url: `${client.baseUrl}/${Routes.prompt_label_template_labels}`,
      params,
    } as RequestConfig)) as AxiosResponse;
    return (res.data ?? res) as any;
  } finally {
    await client.close();
  }
}

export async function assignLabelToTemplateVersion(
  templateName: string,
  version: string,
  label: string,
  options: APIKeyAuthConfig = {},
): Promise<Record<string, any>> {
  const client = new APIKeyAuth(options);
  try {
    // Resolve template_id via search
    const search = (await client.request({
      method: HttpMethod.GET,
      url: `${client.baseUrl}/${Routes.get_template_id_by_name}`,
      params: { search: templateName },
    } as RequestConfig)) as AxiosResponse;
    const results = (search.data ?? search).results ?? [];
    const found = results.find((it: any) => it?.name === templateName);
    if (!found?.id) throw new SDKException(`No template found with name: ${templateName}`);
    const templateId = String(found.id);

    // Verify version exists and is not draft
    const hist = (await client.request({
      method: HttpMethod.GET,
      url: `${client.baseUrl}/${Routes.get_template_version_history}`,
      params: { template_id: templateId },
    } as RequestConfig)) as AxiosResponse;
    const history = (hist.data ?? hist).results ?? [];
    const entry = history.find((e: any) => String(e.templateVersion) === version);
    if (!entry) throw new SDKException(`No version '${version}' found for template '${templateName}'`);
    if (entry.isDraft === true) throw new SDKException('Cannot assign label to a draft version. Commit first.');

    // Resolve label id by name
    const labelsResp = (await client.request({
      method: HttpMethod.GET,
      url: `${client.baseUrl}/${Routes.prompt_labels}`,
    } as RequestConfig)) as AxiosResponse;
    const items = (labelsResp.data ?? labelsResp).results ?? (labelsResp.data ?? labelsResp);
    const labelObj = Array.isArray(items)
      ? items.find((it: any) => String(it?.name ?? '').toLowerCase() === label.toLowerCase())
      : undefined;
    if (!labelObj?.id) throw new SDKException(`Label '${label}' not found. Create it first, then assign.`);

    // Assign
    const res = (await client.request({
      method: HttpMethod.POST,
      url: `${client.baseUrl}/${Routes.prompt_label_assign_by_id
        .replace('{template_id}', templateId)
        .replace('{label_id}', String(labelObj.id))}`,
      json: { version },
    } as RequestConfig)) as AxiosResponse;
    return (res.data ?? res) as any;
  } finally {
    await client.close();
  }
}

export async function removeLabelFromTemplateVersion(
  templateName: string,
  version: string,
  label: string,
  options: APIKeyAuthConfig = {},
): Promise<Record<string, any>> {
  const client = new APIKeyAuth(options);
  try {
    // Resolve template_id via search
    const search = (await client.request({
      method: HttpMethod.GET,
      url: `${client.baseUrl}/${Routes.get_template_id_by_name}`,
      params: { search: templateName },
    } as RequestConfig)) as AxiosResponse;
    const results = (search.data ?? search).results ?? [];
    const found = results.find((it: any) => it?.name === templateName);
    if (!found?.id) throw new SDKException(`No template found with name: ${templateName}`);
    const templateId = String(found.id);

    // Resolve version_id via history
    const hist = (await client.request({
      method: HttpMethod.GET,
      url: `${client.baseUrl}/${Routes.get_template_version_history}`,
      params: { template_id: templateId },
    } as RequestConfig)) as AxiosResponse;
    const history = (hist.data ?? hist).results ?? [];
    let versionId: string | undefined;
    for (const e of history) {
      if (String(e.templateVersion) === version) {
        for (const key of ['id', 'versionId', 'executionId']) {
          if (e[key]) { versionId = String(e[key]); break; }
        }
        break;
      }
    }
    if (!versionId) throw new SDKException(`No version '${version}' found for template '${templateName}'`);

    // Resolve label id by name
    const labelsResp = (await client.request({
      method: HttpMethod.GET,
      url: `${client.baseUrl}/${Routes.prompt_labels}`,
    } as RequestConfig)) as AxiosResponse;
    const items = (labelsResp.data ?? labelsResp).results ?? (labelsResp.data ?? labelsResp);
    const labelObj = Array.isArray(items)
      ? items.find((it: any) => String(it?.name ?? '').toLowerCase() === label.toLowerCase())
      : undefined;
    if (!labelObj?.id) throw new SDKException(`Label '${label}' not found`);

    // Remove
    const res = (await client.request({
      method: HttpMethod.POST,
      url: `${client.baseUrl}/${Routes.prompt_label_remove}`,
      json: { label_id: String(labelObj.id), version_id: versionId },
    } as RequestConfig)) as AxiosResponse;
    return (res.data ?? res) as any;
  } finally {
    await client.close();
  }
}


