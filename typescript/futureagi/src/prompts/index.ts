import type { Client } from "../generated/openapi/client";
import * as sdk from "../generated/openapi/sdk.gen";
import type * as types from "../generated/openapi/types.gen";
import { coreOptions, coreResult, type CoreResponse } from "../_resources";
import type { CatalogPageResult } from "../catalog-response-types";
import { BadRequestError } from "../_core/errors";
import { compilePrompt, type CompilablePrompt, type PromptVariables } from "./compile";

/** One version's prompt configuration: its messages and model settings, stored as sent. */
export type PromptConfig = {
  /** Chat messages; `{{name}}` placeholders are filled by `compile`. */
  messages: Array<Record<string, unknown>>;
  /** Model settings (model, temperature, max_tokens ...). */
  configuration?: Record<string, unknown>;
  [key: string]: unknown;
};
/** The `create` body: template fields plus the first version's configuration. */
export type PromptCreateInput = {
  /** Template name, unique in the organization; `getByName` and `getByLabel` look it up. */
  name: string;
  /** Its first entry becomes version v1 (a draft until committed). */
  prompt_config: PromptConfig[];
  /** Template description. */
  description?: string;
  /** Variable names and sample values for the first version. */
  variable_names?: Record<string, unknown>;
  /** Free-form metadata stored on the first version. */
  metadata?: Record<string, unknown>;
  /** Folder id to file the template under. */
  prompt_folder?: string | null;
};
/** What `create` returns: the new template's `id` and `name`, and its first version (`created_version`). */
export type PromptCreated = Omit<types.PromptHistoryExecution, "id"> & {
  /** The template id (use it for versions and labels). */
  id: string;
  /** The template name. */
  name: string;
  /** The first version's name (`v1`), a draft until committed. */
  created_version: string;
  /** The template the version belongs to (the same id). */
  root_template: string;
  /** The template description. */
  description?: string;
};
/** Template fields `update` changes (prompt configurations change through versions). */
export type PromptUpdate = Partial<Pick<types.PromptTemplateWritable, "name" | "description" | "variable_names" | "prompt_folder" | "placeholders">>;
/** The `versions.create` body: one new draft version per entry. */
export type PromptDraftsInput = {
  /** Each entry becomes the next version, a draft until committed. */
  new_prompts: Array<{
    /** Its first entry is the version's configuration. */
    prompt_config: PromptConfig[];
    /** Variable names and sample values for this version. */
    variable_names?: Record<string, unknown>;
    /** Evaluation configurations for this version. */
    evaluation_configs?: Array<Record<string, unknown>>;
    /** Free-form metadata stored on this version. */
    metadata?: Record<string, unknown>;
  }>;
};
/** Filters and DRF page fields for `list`. */
export type PromptListQuery = NonNullable<types.ModelHubPromptTemplatesListData["query"]>;
/** Select exactly one non-empty version or label; omission never selects the default. */
export type PromptSelector = { version?: string; label?: string };
/** A retrieved template version, ready for `compile`. */
export type PromptRecord = types.PromptTemplate & CompilablePrompt & {
  version?: string;
  prompt_config?: PromptConfig[];
  is_draft?: boolean;
};
/** One page of a template's versions, including total_pages and current_page. */
export type PromptVersionPage = CatalogPageResult<types.PromptHistoryExecution>;
/** The result of assigning a label: the version that now holds it and the versions it left. */
export type PromptLabelAssignment = {
  template_id: string; version: string; label_id: string; label_name: string; moved_from_versions: string[];
};
/** The labels on one version of a template. */
export type PromptVersionLabels = { version: string; labels: string[]; is_default: boolean; is_draft: boolean };

// These action responses differ from the read-serializer schemas in older Swagger.
const promptResult = <T>(request: Promise<CoreResponse<unknown>>): Promise<T> => coreResult(request) as Promise<T>;

/** Manage labels separately from assigning them to a committed prompt version. */
export class PromptLabelsClient {
  constructor(private readonly client: Client) {}

  /** Return the organization's label page including total_pages and current_page.
   * List the organization's labels (DRF page). Pagination: limit (page size); page (1-based). */
  list(query?: types.ModelHubPromptLabelsListData["query"]) {
    // FA prompt_labels.py:67 inherits settings.py:644's ExtendedPageNumberPagination.
    return coreResult(sdk.modelHubPromptLabelsList(coreOptions(this.client, { query }))) as Promise<CatalogPageResult<types.PromptLabel>>;
  }
  /** Create a custom label. */
  create(body: types.PromptLabelWritable) {
    return coreResult(sdk.modelHubPromptLabelsCreate(coreOptions(this.client, { body })));
  }
  /** Fetch one label. */
  get(labelId: string) {
    return coreResult(sdk.modelHubPromptLabelsRead(coreOptions(this.client, { path: { id: labelId } })));
  }
  /** Rename a label or change its metadata. */
  update(labelId: string, body: Partial<types.PromptLabelWritable>) {
    return coreResult(sdk.modelHubPromptLabelsPartialUpdate(coreOptions(this.client, {
      path: { id: labelId }, body: body as types.PromptLabelWritable,
    })));
  }
  /** Delete a label. */
  delete(labelId: string) {
    return coreResult(sdk.modelHubPromptLabelsDelete(coreOptions(this.client, { path: { id: labelId } })));
  }
  /** Move an existing label to one version of a template; never creates a label. */
  assign(templateId: string, labelId: string, options: { version: string }) {
    // The generated action schema is the label read serializer, not this write payload.
    return promptResult<PromptLabelAssignment>(sdk.modelHubPromptLabelsAssignLabelById(coreOptions(this.client, {
      path: { template_id: templateId, label_id: labelId }, body: options as unknown as types.PromptLabelWritable,
    })));
  }
  /** Remove a label from a version (by the version's id). */
  remove(versionId: string, labelId: string) {
    return promptResult<{ detail: string }>(sdk.modelHubPromptLabelsRemoveLabelFromVersion(coreOptions(this.client, {
      body: { version_id: versionId, label_id: labelId } as unknown as types.PromptLabelWritable,
    })));
  }
  /** The labels on each version of a template. Pagination: no supported paging parameters. */
  forTemplate(templateId: string) {
    // The deployed query is omitted by the older generated Swagger schema.
    const query = { template_id: templateId } as types.ModelHubPromptLabelsTemplateLabelsData["query"];
    return promptResult<PromptVersionLabels[]>(sdk.modelHubPromptLabelsTemplateLabels(coreOptions(this.client, { query })));
  }
}

/** Draft creation, commit and default-version selection. */
export class PromptVersionsClient {
  constructor(private readonly client: Client) {}

  /** Return a version page including total_pages and current_page, even without page/limit.
   * A page of a template's versions. Pagination: page (1-based); limit (page size). */
  list(templateId: string, query?: { page?: number; limit?: number }) {
    // FA prompt_template.py:648,3245-3246,3270-3276 always paginates with a nonzero default size.
    return promptResult<PromptVersionPage>(sdk.modelHubPromptTemplatesVersions(coreOptions(this.client, { path: { id: templateId }, query: query as never })));
  }
  /** Add draft versions after the latest one; returns each new version. */
  create(templateId: string, body: PromptDraftsInput) {
    return promptResult<types.PromptHistoryExecution[]>(sdk.modelHubPromptTemplatesAddNewDraft(coreOptions(this.client, {
      path: { id: templateId }, body: body as unknown as types.PromptTemplateWritable,
    })));
  }
  /** Commit a draft version, optionally making it the default. */
  commit(templateId: string, version: string, options: { message?: string; setDefault?: boolean } = {}) {
    const body = { version_name: version, message: options.message ?? "", set_default: options.setDefault ?? false, is_draft: false };
    return promptResult<string>(sdk.modelHubPromptTemplatesCommit(coreOptions(this.client, {
      path: { id: templateId }, body: body as unknown as types.PromptTemplateWritable,
    })));
  }
  /** Make a version the template's default (looked up by template name). */
  setDefault(templateName: string, version: string) {
    return promptResult<{ template_id: string; version: string; is_default: boolean }>(sdk.modelHubPromptLabelsSetDefault(coreOptions(this.client, {
      body: { template_name: templateName, version } as unknown as types.PromptLabelWritable,
    })));
  }
}

/** Prompt templates with their versions and labels. Legacy Prompt objects remain independent and unchanged. */
export class PromptsClient {
  /** Labels and their assignment to versions. */
  readonly labels: PromptLabelsClient;
  /** Draft, commit and default versions. */
  readonly versions: PromptVersionsClient;

  constructor(private readonly client: Client) {
    this.labels = new PromptLabelsClient(client);
    this.versions = new PromptVersionsClient(client);
  }
  /** Return a template page including total_pages and current_page.
   * List templates (DRF page). Pagination: limit (page size); page (1-based). */
  list(query?: PromptListQuery) {
    // FA prompt_template.py:648,697-698 uses ExtendedPageNumberPagination.
    return coreResult(sdk.modelHubPromptTemplatesList(coreOptions(this.client, { query }))) as Promise<CatalogPageResult<types.PromptTemplate>>;
  }
  /**
   * Create a template and its first version (v1, a draft until committed) in one call.
   * Commit `created_version` next, then label it and fetch it by label.
   */
  async create(body: PromptCreateInput) {
    if (!Array.isArray(body.prompt_config) || body.prompt_config.length === 0) {
      throw new TypeError("prompt_config must be a non-empty list; its first entry (messages and model settings) becomes v1");
    }
    // The generated body schema is the template read serializer, not this create-with-version payload.
    return promptResult<PromptCreated>(sdk.modelHubPromptTemplatesCreateDraft(coreOptions(this.client, {
      body: body as unknown as types.PromptTemplateWritable,
    })));
  }
  /** Fetch a template. */
  get(templateId: string) {
    return promptResult<PromptRecord>(sdk.modelHubPromptTemplatesRead(coreOptions(this.client, { path: { id: templateId } })));
  }
  /**
   * Fetch by template name and exactly one non-empty version or label; there is no default fallback.
   * @throws {BadRequestError} Before any request if the selector is missing, empty or conflicting.
   Pagination: no supported paging parameters. */
  async getByName(name: string, selector: PromptSelector = {}) {
    const { version, label } = selector;
    const selected = version !== undefined ? version : label;
    if ((version === undefined) === (label === undefined) || typeof selected !== "string" || !selected.trim()) {
      const message = "provide exactly one of version or label as a non-empty string; no default version is selected";
      throw new BadRequestError(400, { detail: message }, { code: "invalid_prompt_selector", message });
    }
    // Older Swagger omits this action's name/version/label query parameters.
    const query = { name, [version !== undefined ? "version" : "label"]: selected } as unknown as types.ModelHubPromptLabelsGetByNameData["query"];
    return promptResult<PromptRecord>(sdk.modelHubPromptLabelsGetByName(coreOptions(this.client, { query })));
  }
  /** Fetch the version of a template that holds a label. */
  getByLabel(name: string, label: string) {
    return this.getByName(name, { label });
  }
  /** Change template fields; configurations change through `versions`. */
  update(templateId: string, body: PromptUpdate) {
    return coreResult(sdk.modelHubPromptTemplatesPartialUpdate(coreOptions(this.client, {
      path: { id: templateId }, body: body as types.PromptTemplateWritable,
    })));
  }
  /** Delete a template. */
  delete(templateId: string) {
    return coreResult(sdk.modelHubPromptTemplatesDelete(coreOptions(this.client, { path: { id: templateId } })));
  }
  /** Pure local rendering; no fetch, credential lookup or mutation. */
  compile(template: CompilablePrompt, variables?: PromptVariables) {
    return compilePrompt(template, variables);
  }
}

export { compilePrompt } from "./compile";
export type { CompilablePrompt, PromptMessage, PromptVariables } from "./compile";
