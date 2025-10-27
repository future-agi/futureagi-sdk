import { AxiosResponse } from 'axios';
import {
  APIKeyAuth,
  APIKeyAuthConfig,
  ResponseHandler,
} from '../api/auth';
import { HttpMethod, RequestConfig } from '../api/types';
import { Routes } from '../utils/routes';
import { ModelConfig, PromptTemplate, MessageBase, Variables } from './types';
import { PromptLabels, setDefaultVersion as labelsSetDefaultVersion, getTemplateLabels as labelsGetTemplateLabels, assignLabelToTemplateVersion as labelsAssign, removeLabelFromTemplateVersion as labelsRemove } from './labels';
import {
  InvalidAuthError,
  SDKException,
  TemplateAlreadyExists,
  TemplateNotFound,
} from '../utils/errors';

/**
 * Simple JSON handler – returns parsed JSON on success, handles common auth/not-found errors.
 */
class SimpleJsonResponseHandler extends ResponseHandler<Record<string, any>, Record<string, any>> {
  public static _parseSuccess(response: AxiosResponse): Record<string, any> {
    return response.data;
  }

  public static _handleError(response: AxiosResponse): never {
    if (response.status === 403) {
      throw new InvalidAuthError();
    }
    if (response.status === 404) {
      throw new TemplateNotFound('unknown');
    }
    // Fallback – use generic logic from base class
    return super._handleError(response);
  }
}

/**
 * Response handler for prompt-template related endpoints. Converts backend payloads into
 * strongly-typed `PromptTemplate` instances where appropriate.
 */
class PromptResponseHandler extends ResponseHandler<
  Record<string, any>,
  PromptTemplate | string | Record<string, any>
> {
  private static _buildModelConfig(cfgSrc: Record<string, any> | undefined): ModelConfig {
    if (!cfgSrc) return new ModelConfig();

    return new ModelConfig({
      model_name: cfgSrc.modelName ?? cfgSrc.model,
      temperature: cfgSrc.temperature ?? 0,
      frequency_penalty: cfgSrc.frequencyPenalty ?? cfgSrc.frequency_penalty ?? 0,
      presence_penalty: cfgSrc.presencePenalty ?? cfgSrc.presence_penalty ?? 0,
      max_tokens: cfgSrc.maxTokens ?? cfgSrc.max_tokens,
      top_p: cfgSrc.topP ?? cfgSrc.top_p ?? 0,
      response_format: cfgSrc.responseFormat ?? cfgSrc.response_format,
      tool_choice: cfgSrc.toolChoice ?? cfgSrc.tool_choice,
      tools: cfgSrc.tools ?? null,
    });
  }

  private static _toPromptTemplate(data: Record<string, any>): PromptTemplate {
    const promptConfigRaw = data.promptConfig || data.prompt_config;
    let modelConfiguration: ModelConfig | undefined;
    let messages: MessageBase[] = [];

    if (promptConfigRaw && Array.isArray(promptConfigRaw) && promptConfigRaw.length > 0) {
      const pc = promptConfigRaw[0];
      modelConfiguration = this._buildModelConfig(pc.configuration || {});
      messages = pc.messages || [];
    }

    return new PromptTemplate({
      id: data.id,
      name: data.name,
      description: data.description ?? '',
      messages,
      model_configuration: modelConfiguration,
      variable_names: data.variableNames ?? data.variable_names ?? {},
      version: data.version,
      is_default: data.isDefault ?? true,
      evaluation_configs: data.evaluationConfigs ?? [],
      status: data.status,
      error_message: data.errorMessage,
      // include labels metadata if provided by get-by-name endpoint
      ...(Array.isArray(data.labels) ? { labels: data.labels } : {}),
      placeholders: data.placeholders ?? {},
    });
  }

  public static _parseSuccess(response: AxiosResponse): any {
    const { data } = response;
    const url = response.config.url ?? '';
    const method = response.config.method?.toUpperCase() ?? 'GET';

    // Search endpoint: /prompt-templates/?search=<name>
    if (url.includes('search=')) {
      const results = data.results ?? [];
      const name = url.split('search=')[1];
      const found = results.find((it: any) => it.name === name);
      if (found) return found.id;
      throw new SDKException(`No template found with the given name: ${name}`);
    }

    // GET template by ID endpoint 
    if (method === HttpMethod.GET && !url.endsWith('/')) {
      // Heuristic: treat as single-template retrieval by ID
      return this._toPromptTemplate(data);
    }

    // GET template by name endpoint – keep parity with Python SDK behaviour
    if (method === HttpMethod.GET && url.includes(Routes.get_template_by_name)) {
      return this._toPromptTemplate(data);
    }

    // POST create template endpoint returns { result: {...} }
    if (method === HttpMethod.POST && url.endsWith(Routes.create_template)) {
      return data.result ?? data;
    }

    // Fallback to raw payload
    return data;
  }

  public static _handleError(response: AxiosResponse): never {
    // Optional debug output
    if (process.env.FI_SDK_DEBUG === '1' || process.env.FI_SDK_DEBUG === 'true') {
      /* eslint-disable no-console */
      console.error('[PromptResponseHandler] HTTP', response.status, 'payload:', response.data);
      /* eslint-enable no-console */
    }

    if (response.status === 403) {
      throw new InvalidAuthError();
    }
    if (response.status === 404) {
      // Attempt to parse the template name from query string if present
      const url = response.config.url ?? '';
      const match = url.match(/name=([^&]+)/);
      const name = match ? decodeURIComponent(match[1]) : 'unknown';
      throw new TemplateNotFound(name);
    }
    if (response.status === 400) {
      const detail = response.data ?? {};
      const errorCode = detail.errorCode;
      // Map "template not found" phrasing used by backend to our TemplateNotFound exception
      if (detail?.result && typeof detail.result === 'string') {
        const lowercase = detail.result.toLowerCase();
        if (lowercase.includes('no prompttemplate matches') || lowercase.includes('failed to retrieve template')) {
          throw new TemplateNotFound('unknown');
        }
      }

      if (errorCode === 'TEMPLATE_ALREADY_EXIST') {
        throw new TemplateAlreadyExists(detail.name ?? '<unknown>');
      }

      const msg =
        detail.result ||
        detail.message ||
        detail.error ||
        (() => {
          try {
            return JSON.stringify(detail);
          } catch {
            return undefined;
          }
        })() ||
        'Bad request – please verify request body.';
      throw new SDKException(msg);
    }

    return super._handleError(response);
  }
}

/**
 * Main Prompt client – allows programmatic CRUD and execution of prompt templates.
 */
export class Prompt extends APIKeyAuth {
  public template?: PromptTemplate;
  private _pendingLabel?: string;

  // ---------- Static helpers ----------

  /**
   * List all prompt templates (raw JSON payload).
   */
  public static async listTemplates(options: APIKeyAuthConfig = {}): Promise<Record<string, any>> {
    const client = new APIKeyAuth(options);
    try {
      const res = (await client.request({
        method: HttpMethod.GET,
        url: `${client.baseUrl}/${Routes.list_templates}`,
      } as RequestConfig)) as AxiosResponse;
      return (res as any).data ?? res;
    } finally {
      await client.close();
    }
  }

  /**
   * Convenience: fetch template by exact name.
   */
  public static async getTemplateByName(
    name: string,
    { label, version, ...options }: APIKeyAuthConfig & { label?: string; version?: string } = {},
  ): Promise<PromptTemplate> {
    const client = new APIKeyAuth(options);
    try {
      // If a specific version or label is provided, use the direct endpoint. No fallback.
      if (version || label) {
        const params: Record<string, any> = { name };
        if (version) params.version = version;
        if (label) params.label = label;

        return (await client.request(
          {
            method: HttpMethod.GET,
            url: `${client.baseUrl}/${Routes.prompt_label_get_by_name}`,
            params,
          } as RequestConfig,
          PromptResponseHandler,
        )) as PromptTemplate;
      }

      // No version or label, so try 'production' with fallback.
      try {
        return (await client.request(
          {
            method: HttpMethod.GET,
            url: `${client.baseUrl}/${Routes.prompt_label_get_by_name}`,
            params: { name, label: 'production' },
          } as RequestConfig,
          PromptResponseHandler,
        )) as PromptTemplate;
      } catch (err) {
        if (err instanceof TemplateNotFound || (err instanceof SDKException && err.message.includes('No version found'))) {
          // Fallback to the default template resolution endpoint
          return (await client.request(
            {
              method: HttpMethod.GET,
              url: `${client.baseUrl}/${Routes.get_template_by_name}`,
              params: { name },
            } as RequestConfig,
            PromptResponseHandler,
          )) as PromptTemplate;
        }
        // Re-throw other errors
        throw err;
      }
    } finally {
      await client.close();
    }
  }

  /**
   * Delete template by name (helper).
   */
  public static async deleteTemplateByName(name: string, options: APIKeyAuthConfig = {}): Promise<boolean> {
    const client = new APIKeyAuth(options);
    try {
      const tmpl = (await client.request(
        {
          method: HttpMethod.GET,
          url: `${client.baseUrl}/${Routes.prompt_label_get_by_name}`,
          params: { name },
        } as RequestConfig,
        PromptResponseHandler,
      )) as PromptTemplate;

      await client.request(
        {
          method: HttpMethod.DELETE,
          url: `${client.baseUrl}/${Routes.delete_template.replace('{template_id}', tmpl.id ?? '')}`,
        } as RequestConfig,
      );
      return true;
    } finally {
      await client.close();
    }
  }

  /** Set default version for a template by name (class helper). */
  public static async setDefaultVersion(
    templateName: string,
    version: string,
    options: APIKeyAuthConfig = {},
  ): Promise<Record<string, any>> {
    return labelsSetDefaultVersion(templateName, version, options);
  }

  /** List versions and labels for a template by name or id. */
  public static async getTemplateLabels(
    args: APIKeyAuthConfig & { template_name?: string; template_id?: string } = {},
  ): Promise<Record<string, any>> {
    return labelsGetTemplateLabels(args);
  }

  /** Assign label to template/version using only names. */
  public static async assignLabelToTemplateVersion(
    templateName: string,
    version: string,
    label: string,
    options: APIKeyAuthConfig = {},
  ): Promise<Record<string, any>> {
    return labelsAssign(templateName, version, label, options);
  }

  /** Remove label by name from template/version using only names. */
  public static async removeLabelFromTemplateVersion(
    templateName: string,
    version: string,
    label: string,
    options: APIKeyAuthConfig = {},
  ): Promise<Record<string, any>> {
    return labelsRemove(templateName, version, label, options);
  }

  // ---------- Instance ----------

  constructor(
    template?: PromptTemplate,
    options: APIKeyAuthConfig = {},
  ) {
    super(options);

    if (template) {
      this.template = template;
    }
  }

  /**
   * Create a new draft prompt template.
   */
  async open(): Promise<Prompt> {
    if (!this.template) {
      throw new SDKException('template must be set');
    }

    // If template already has an ID it's already created – just return the client.
    if (this.template.id) {
      return this;
    }

    // Attempt to fetch existing template by name; propagate any errors.
    if (this.template.name) {
      try {
        const remote = await Prompt.getTemplateByName(this.template.name, {
          fiApiKey: this.fiApiKey,
          fiSecretKey: this.fiSecretKey,
          fiBaseUrl: this.baseUrl,
        });

        // Found existing template – adopt it and return immediately
        this.template = remote;
        return this;
      } catch (err) {
        // In production, treat any error during lookup as "not found" and proceed to create
        // This handles cases where the lookup endpoint is unstable but create works
        // Template truly does not exist – proceed to create below
      }
    }

    // Transform messages into backend-friendly format
    const { messages, placeholders } = this._prepareMessagesAndPlaceholders();

    const jsonPayload = {
      name: this.template.name,
      prompt_config: [
        {
          messages,
          configuration: {
            model: this.template.model_configuration?.model_name ?? 'gpt-4o-mini',
            temperature: this.template.model_configuration?.temperature,
            max_tokens: this.template.model_configuration?.max_tokens,
            top_p: this.template.model_configuration?.top_p,
            frequency_penalty: this.template.model_configuration?.frequency_penalty,
            presence_penalty: this.template.model_configuration?.presence_penalty,
          },
          placeholders: Object.keys(placeholders),
        },
      ],
      variable_names: this.template.variable_names,
      evaluation_configs: this.template.evaluation_configs ?? [],
      placeholders: placeholders,
    };

    let response: any;
    try {
      response = await this.request(
        {
          method: HttpMethod.POST,
          url: `${this.baseUrl}/${Routes.create_template}`,
          json: jsonPayload,
          timeout: 60000, // 60 second timeout for create operations
        } as RequestConfig,
        PromptResponseHandler,
      );
    } catch (error) {
      throw error;
    }

    // Update template with returned info
    this.template.id = response.id;
    this.template.name = response.name;
    this.template.version = response.templateVersion ?? response.createdVersion ?? 'v1';

    return this;
  }

  private async _createNewDraft(): Promise<void> {
    if (!this.template || !this.template.id) {
      throw new SDKException('Template must be created before creating a new version.');
    }

    const { messages, placeholders } = this._prepareMessagesAndPlaceholders();

    const modelConfig = {
      model: this.template.model_configuration?.model_name ?? 'gpt-4o-mini',
      temperature: this.template.model_configuration?.temperature,
      max_tokens: this.template.model_configuration?.max_tokens,
      top_p: this.template.model_configuration?.top_p,
      frequency_penalty: this.template.model_configuration?.frequency_penalty,
      presence_penalty: this.template.model_configuration?.presence_penalty,
    };

    const body = {
      new_prompts: [
        {
          prompt_config: [
            {
              messages,
              configuration: modelConfig,
              placeholders: Object.keys(placeholders),
            },
          ],
          variable_names: this.template.variable_names,
          evaluation_configs: this.template.evaluation_configs ?? [],
          placeholders: placeholders,
        },
      ],
    };

    const url = `${this.baseUrl}/${Routes.add_new_draft.replace('{template_id}', this.template.id)}`;

    const resp: any = await this.request(
      {
        method: HttpMethod.POST,
        url,
        json: body,
        timeout: 60000, // 60 second timeout for create operations
      } as RequestConfig,
      PromptResponseHandler,
    );

    // The backend typically returns { result: [ { templateVersion: 'vX', ... } ] }
    if (resp && typeof resp === 'object' && resp.result && Array.isArray(resp.result) && resp.result.length > 0) {
      const newVersion = resp.result[0]?.templateVersion;
      if (newVersion && this.template) {
        this.template.version = newVersion;
      }
    }
  }

  /* ------------------------------------------------------------------
   * Version-history helpers (parity with Python SDK)
   * ------------------------------------------------------------------ */

  /** Fetch raw version history (array of objects) */
  private async _fetchTemplateVersionHistory(): Promise<any[]> {
    if (!this.template || !this.template.id) {
      throw new SDKException('Template must be created before fetching history.');
    }
    const res = (await this.request(
      {
        method: HttpMethod.GET,
        url: `${this.baseUrl}/${Routes.get_template_version_history}`,
        params: { template_id: this.template.id },
        timeout: 60000, // 60 second timeout for history operations
      } as RequestConfig,
    )) as AxiosResponse;

    return (res.data ?? res).results ?? [];
  }

  /** Public: list full version history */
  public async listTemplateVersions(): Promise<any[]> {
    return this._fetchTemplateVersionHistory();
  }

  /** Internal draft-status helper */
  private async _currentVersionIsDraft(): Promise<boolean> {
    const history = await this._fetchTemplateVersionHistory();
    return history.some((e) => e.templateVersion === this.template?.version && e.isDraft === true);
  }

  /** Apply selected fields from another PromptTemplate to current */
  private _applyTemplateUpdates(tpl: PromptTemplate): void {
    if (!this.template) return;
    const mutable: (keyof PromptTemplate)[] = [
      'messages',
      'description',
      'variable_names',
      'model_configuration',
      'evaluation_configs',
      'placeholders',
    ];
    for (const field of mutable) {
      const val = (tpl as any)[field];
      if (val !== undefined) (this.template as any)[field] = val;
    }
  }

  /** Save current draft state to backend */
  public async saveCurrentDraft(): Promise<boolean> {
    if (!this.template || !this.template.id) {
      throw new SDKException('Template must be created before it can be updated.');
    }
    if (!(await this._currentVersionIsDraft())) {
      throw new SDKException('Current version is already committed; create a new draft version first.');
    }

    const { messages, placeholders } = this._prepareMessagesAndPlaceholders();
    const modelCfg = {
      model: this.template.model_configuration?.model_name ?? 'gpt-4o-mini',
      temperature: this.template.model_configuration?.temperature,
      max_tokens: this.template.model_configuration?.max_tokens,
      top_p: this.template.model_configuration?.top_p,
      frequency_penalty: this.template.model_configuration?.frequency_penalty,
      presence_penalty: this.template.model_configuration?.presence_penalty,
    };

    const body = {
      is_run: 'draft',
      is_sdk: true,
      version: this.template.version,
      prompt_config: [
        {
          messages,
          configuration: modelCfg,
          placeholders: Object.keys(placeholders),
        },
      ],
      variable_names: this.template.variable_names,
      evaluation_configs: this.template.evaluation_configs ?? [],
      placeholders: placeholders,
    };

    await this.request(
      {
        method: HttpMethod.POST,
        url: `${this.baseUrl}/${Routes.run_template.replace('{template_id}', this.template.id)}`,
        json: body,
        timeout: 60000, // 60 second timeout for save operations
      } as RequestConfig,
      SimpleJsonResponseHandler,
    );

    return true;
  }

  /** Commit current draft version */
  public async commitCurrentVersion(message = '', set_default = false, label: string | undefined = undefined): Promise<boolean> {
    if (!this.template || !this.template.id || !this.template.version) {
      throw new SDKException('Template and version must be set before commit.');
    }

    const body = {
      version_name: this.template.version,
      message,
      set_default,
      is_draft: false,
    };

    await this.request(
      {
        method: HttpMethod.POST,
        url: `${this.baseUrl}/${Routes.commit_template.replace('{template_id}', this.template.id)}`,
        json: body,
        timeout: 60000, // 60 second timeout for commit operations
      } as RequestConfig,
      SimpleJsonResponseHandler,
    );

    // If a label was queued during draft, assign it now post-commit
    const labelToAssign = label || this._pendingLabel;
    if (labelToAssign && this.template?.id && this.template.version) {
      try {
        await this.labels().assign(labelToAssign);
      } catch (err: any) {
        // eslint-disable-next-line no-console
        console.error(`Failed to assign label '${labelToAssign}' after commit: ${err.message}`);
      } finally {
        this._pendingLabel = undefined;
      }
    }

    return true;
  }

  /** Commit current draft if needed then open a new draft version */
  public async createNewVersion({
    template,
    commit_message = 'Auto-commit via SDK',
    set_default = false,
  }: {
    template?: PromptTemplate;
    commit_message?: string;
    set_default?: boolean;
  } = {}): Promise<Prompt> {
    if (!this.template) throw new SDKException('Client.template must be set');

    if (template) this._applyTemplateUpdates(template);

    if (await this._currentVersionIsDraft()) {
      await this.commitCurrentVersion(commit_message, set_default);
    }

    await this._createNewDraft();
    return this;
  }

  /** Accessor: label service for instance operations */
  public labels(): PromptLabels {
    return new PromptLabels(this as any);
  }

  /* ------------------------------------------------------------------
   * Deprecated execution method
   * ------------------------------------------------------------------ */

  /**
   * Execution support removed – this SDK variant focuses solely on template management.
   */
  // eslint-disable-next-line @typescript-eslint/no-unused-vars


  /**
   * Delete the current template.
   */
  async delete(): Promise<boolean> {
    if (!this.template || !this.template.id) {
      throw new SDKException('Template ID missing; cannot delete.');
    }

    await this.request(
      {
        method: HttpMethod.DELETE,
        url: `${this.baseUrl}/${Routes.delete_template.replace('{template_id}', this.template.id)}`,
        timeout: 60000, // 60 second timeout for delete operations
      } as RequestConfig,
    );

    // Clear local ref
    this.template = undefined;
    return true;
  }

  // Helper to transform messages into backend format (adds variable_names if missing for user role)
  private _prepareMessages(): any[] {
    if (!this.template) return [];
    const varNames = Object.keys(this.template.variable_names ?? {});

    const messages: any[] = [];
    
    // Check if there's a system message in the template messages
    const hasSystemMessage = (this.template.messages || []).some(
      (msg: any) => msg.role === 'system'
    );
    
    // Add a default empty system prompt if none exists
    if (!hasSystemMessage) {
      messages.push({
        role: 'system',
        content: [{ type: 'text', text: '' }]
      });
    }

    // Process existing messages
    const processedMessages = this.template.messages.map((msg) => {
      const obj: any = { ...msg };
      if (typeof obj.content === 'string') {
        obj.content = [{ type: 'text', text: obj.content }];
      }
      if (obj.role === 'user') {
        // Ensure variable_names field exists for user messages
        if (!obj.variable_names || obj.variable_names.length === 0) {
          obj.variable_names = varNames;
        }
      }
      return obj;
    });
    
    return [...messages, ...processedMessages];
  }

  private _prepareMessagesAndPlaceholders(): { messages: any[]; placeholders: Record<string, any[]> } {
    if (!this.template) return { messages: [], placeholders: {} };
    const varNames = Object.keys(this.template.variable_names ?? {});
    const messages: any[] = [];
    const placeholders: Record<string, any[]> = {};

    // Ensure a system message exists
    const hasSystemMessage = (this.template.messages || []).some((m: any) => m.role === 'system');
    if (!hasSystemMessage) {
      messages.push({ role: 'system', content: [{ type: 'text', text: '' }] });
    }

    for (const msg of this.template.messages) {
      const obj: any = { ...msg };

      // Placeholder entries get moved to placeholders map
      if (obj.type === 'placeholder') {
        const name = obj.name;
        if (name) placeholders[name] = placeholders[name] ?? [];
        continue;
      }

      if (typeof obj.content === 'string') {
        obj.content = [{ type: 'text', text: obj.content }];
      }
      if (obj.role === 'user') {
        if (!obj.variable_names || obj.variable_names.length === 0) {
          obj.variable_names = varNames;
        }
      }
      messages.push(obj);
    }

    return { messages, placeholders };
  }

  /** Compile the template messages with provided variables.
   * Replaces {{var}} occurrences in string contents; preserves structured contents.
   */
  public compile(variables: Variables = {}): Array<{ role: string; content: string | any[] }> {
    if (!this.template || !this.template.messages) {
      throw new SDKException('Template must be loaded before compilation.');
    }

    const substitute = (text: string): string =>
      text.replace(/\{\{\s*(\w+)\s*\}\}/g, (_m, name: string) =>
        Object.prototype.hasOwnProperty.call(variables, name) ? String((variables as any)[name]) : `{{${name}}}`,
      );

    const compiled: Array<{ role: string; content: string | any[] }> = [];
    for (const msg of this.template.messages) {
      // Placeholder message support: { type: 'placeholder', name: 'messagesVar' }
      if ((msg as any).type === 'placeholder') {
        const ph = msg as any;
        const arr = (variables as any)?.[ph.name];
        if (Array.isArray(arr)) {
          for (const it of arr) {
            const r = it.role;
            const c = it.content;
            if (Array.isArray(c)) {
              const parts = c.map((part: any) =>
                typeof part?.text === 'string' ? { ...part, text: substitute(part.text) } : part,
              );
              compiled.push({ role: r, content: parts });
            } else {
              compiled.push({ role: r, content: substitute(String(c)) });
            }
          }
          continue;
        }
        // if not provided, keep placeholder as-is
        compiled.push({ role: 'placeholder', content: [{ type: 'text', text: ph.name }] });
        continue;
      }

      const role: string = (msg as any).role;
      const content: any = (msg as any).content;
      if (Array.isArray(content)) {
        // structured content – substitute only text fields
        const newParts = content.map((part) =>
          typeof part?.text === 'string' ? { ...part, text: substitute(part.text) } : part,
        );
        compiled.push({ role, content: newParts });
      } else {
        compiled.push({ role, content: substitute(String(content)) });
      }
    }
    return compiled;
  }
}

export default { Prompt };
