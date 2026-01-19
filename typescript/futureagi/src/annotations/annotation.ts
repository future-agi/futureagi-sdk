import { APIKeyAuth } from '../api/auth';
import { HttpMethod, RequestConfig } from '../api/types';
import { Routes } from '../utils/routes';
import { SDKException, InvalidAuthError } from '../utils/errors';
import {
  AnnotationLabel,
  Project,
  BulkAnnotationResponse,
  AnnotationRecord,
  BackendAnnotationRecord,
  AnnotationOptions,
} from './types';

export class Annotation extends APIKeyAuth {
  /**
   * SDK client for logging human annotations using flat DataFrame-style format.
   * 
   */
  constructor(options: AnnotationOptions = {}) {
    super({
        fiApiKey: options.fiApiKey,
        fiSecretKey: options.fiSecretKey,
        fiBaseUrl: options.fiBaseUrl,
        timeout: options.timeout
    });
  }

  async logAnnotations(
    records: AnnotationRecord[],
    options: {
      projectName?: string;
      timeout?: number;
    } = {}
  ): Promise<BulkAnnotationResponse> {
    /**
     * Log annotations using flat DataFrame-style format.
     * 
     * Expected record format:
     * - context.span_id: Span ID for the annotation
     * - annotation.{name}.text: Text annotations
     * - annotation.{name}.label: Categorical annotations  
     * - annotation.{name}.score: Numeric annotations
     * - annotation.{name}.rating: Star ratings (1-5)
     * - annotation.{name}.thumbs: Thumbs up/down (true/false)
     * - annotation.notes: Optional notes text
     * 
     * @param records Array of annotation records
     * @param options.projectName Project name for label scoping
     * @param options.timeout Request timeout
     * 
     * @example
     * ```typescript
     * const records = [
     *   {
     *     'context.span_id': 'span123',
     *     'annotation.quality.text': 'good response',
     *     'annotation.rating.rating': 4,
     *     'annotation.helpful.thumbs': true,
     *     'annotation.notes': 'Great response!'
     *   }
     * ];
     * 
     * const response = await client.logAnnotations(records, {
     *   projectName: 'My Project'
     * });
     * ```
     */

    if (!Array.isArray(records)) {
      throw new Error('Records must be an array');
    }

    // Convert flat records to nested backend format
    const backendRecords = await this._convertRecordsToBackendFormat(
      records, 
      options.projectName
    );

    console.log(`Sending ${backendRecords.length} annotation records via bulk endpoint`);

    const config: RequestConfig = {
      method: HttpMethod.POST,
      url: `${this.baseUrl}/${Routes.BULK_ANNOTATION}`,
      data: { records: backendRecords },
      timeout: options.timeout,
    };

    try {
      const response = await this.request(config);
      return this._parseBulkAnnotationResponse(response.data);
    } catch (error: any) {
      if (error.response?.status === 403) {
        throw new InvalidAuthError();
      }
      throw new SDKException(
        error.response?.data?.message || 'Bulk annotation request failed'
      );
    }
  }

  async getLabels(options: {
    projectId?: string;
    timeout?: number;
  } = {}): Promise<AnnotationLabel[]> {
    /**
     * Fetch annotation labels available to the user.
     */
    const params: Record<string, string> = {};
    if (options.projectId) {
      params.project_id = options.projectId;
    }

    const config: RequestConfig = {
      method: HttpMethod.GET,
      url: `${this.baseUrl}/${Routes.GET_ANNOTATION_LABELS}`,
      params,
      timeout: options.timeout,
    };

    try {
      const response = await this.request(config);
      const data = response.data;
      
      // Handle wrapped response
      const labelsData = data.result || data;
      return labelsData.map((item: any) => ({
        id: item.id,
        name: item.name,
        type: item.type,
        description: item.description,
        settings: item.settings,
      }));
    } catch (error: any) {
      if (error.response?.status === 403) {
        throw new InvalidAuthError();
      }
      throw new SDKException('Failed to fetch annotation labels');
    }
  }

  async listProjects(options: {
    projectType?: string;
    name?: string;
    pageNumber?: number;
    pageSize?: number;
    timeout?: number;
  } = {}): Promise<Project[]> {
    /**
     * List available projects.
     */
    const params: Record<string, string | number> = {
      page_number: options.pageNumber || 0,
      page_size: options.pageSize || 20,
    };
    
    if (options.projectType) {
      params.project_type = options.projectType;
    }
    if (options.name) {
      params.name = options.name;
    }

    const config: RequestConfig = {
      method: HttpMethod.GET,
      url: `${this.baseUrl}/${Routes.LIST_PROJECTS}`,
      params,
      timeout: options.timeout,
    };

    try {
      const response = await this.request(config);
      const data = response.data;
      
      // Handle wrapped response with metadata
      let projectsData = data.result || data;
      if (projectsData.table) {
        projectsData = projectsData.table;
      }
      
      return projectsData.map((item: any) => ({
        id: item.id,
        name: item.name,
        project_type: item.project_type,
        created_at: item.created_at,
      }));
    } catch (error: any) {
      if (error.response?.status === 403) {
        throw new InvalidAuthError();
      }
      throw new SDKException('Failed to list projects');
    }
  }

  private async _convertRecordsToBackendFormat(
    records: AnnotationRecord[],
    projectName?: string
  ): Promise<BackendAnnotationRecord[]> {
    const backendRecords: BackendAnnotationRecord[] = [];

    for (const record of records) {
      const spanId = record['context.span_id'];
      if (!spanId) {
        continue;
      }

      const backendRecord: BackendAnnotationRecord = {
        observation_span_id: spanId,
        annotations: [],
        notes: [] as Array<{ text: string }>,
      };

      // Process annotation columns
      for (const [key, value] of Object.entries(record)) {
        if (key.startsWith('annotation.') && key !== 'annotation.notes' && value != null) {
          const annotation = await this._parseAnnotationColumn(key, value, projectName);
          if (annotation) {
            backendRecord.annotations.push(annotation);
          }
        }
      }

      // Process notes
      if (record['annotation.notes']) {
        backendRecord.notes.push({ text: String(record['annotation.notes']) });
      }

      if (backendRecord.annotations.length > 0 || backendRecord.notes.length > 0) {
        backendRecords.push(backendRecord);
      }
    }

    return backendRecords;
  }

  private async _parseAnnotationColumn(
    column: string,
    value: string | number | boolean,
    projectName?: string
  ): Promise<{
    annotation_label_id: string;
    value?: string;
    value_float?: number;
    value_bool?: boolean;
    value_str_list?: string[];
  } | null> {
    // Format: annotation.{name}.{type}
    const parts = column.split('.');
    if (parts.length !== 3) {
      return null;
    }

    const [, name, valueType] = parts;

    // Get project-specific label ID
    const labelId = await this._getLabelIdForNameAndType(name, valueType, projectName);
    if (!labelId) {
      throw new Error(
        `No annotation label found for name '${name}' and type '${valueType}' in project '${projectName}'`
      );
    }

    // Map column types to backend fields
    switch (valueType) {
      case 'text':
        return {
          annotation_label_id: labelId,
          value: String(value),
        };
      case 'label':
        return {
          annotation_label_id: labelId,
          value_str_list: Array.isArray(value) 
            ? value.map(String) 
            : [String(value)],
        };
      case 'score':
        return {
          annotation_label_id: labelId,
          value_float: Number(value),
        };
      case 'rating':
        return {
          annotation_label_id: labelId,
          value_float: Number(value),
        };
      case 'thumbs':
        return {
          annotation_label_id: labelId,
          value_bool: Boolean(value),
        };
      default:
        return null;
    }
  }

  private async _getProjectId(projectName: string): Promise<string> {
    const projects = await this.listProjects({ name: projectName });
    if (projects.length === 0) {
      throw new Error(`Project '${projectName}' not found`);
    }
    if (projects.length > 1) {
      const projectList = projects.map(p => `${p.name} (id: ${p.id})`).join(', ');
      throw new Error(`Multiple projects found for '${projectName}': ${projectList}`);
    }
    return projects[0].id;
  }

  private async _getLabelIdForNameAndType(
    name: string,
    columnType: string,
    projectName?: string
  ): Promise<string | null> {
    // Get project ID if project name provided
    let projectId: string | undefined;
    if (projectName) {
      projectId = await this._getProjectId(projectName);
    }

    // Get labels (filtered by project if specified)
    const labels = await this.getLabels({ projectId });

    // Map column types to backend label types
    const typeMapping: Record<string, string> = {
      text: 'text',
      label: 'categorical',
      score: 'numeric',
      rating: 'star',
      thumbs: 'thumbs_up_down',
    };

    const expectedLabelType = typeMapping[columnType];
    if (!expectedLabelType) {
      return null;
    }

    // Find matching label
    const matchingLabel = labels.find(
      label => label.name === name && label.type.toLowerCase() === expectedLabelType
    );

    return matchingLabel?.id || null;
  }

  private _parseBulkAnnotationResponse(data: any): BulkAnnotationResponse {
    // Handle wrapped response
    if (data.result) {
      data = data.result;
    }

    return {
      message: data.message || 'Bulk annotation completed',
      annotationsCreated: data.annotationsCreated || 0,
      annotationsUpdated: data.annotationsUpdated || 0,
      notesCreated: data.notesCreated || 0,
      succeededCount: data.succeededCount || 0,
      errorsCount: data.errorsCount || 0,
      warningsCount: data.warningsCount || 0,
      warnings: data.warnings,
      errors: data.errors,
    };
  }
}
