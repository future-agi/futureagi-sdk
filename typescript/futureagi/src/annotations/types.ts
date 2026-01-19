/**
 * Type definitions for the Annotation module
 */

export interface AnnotationLabel {
  id: string;
  name: string;
  type: string;
  description?: string;
  settings?: Record<string, any>;
}

export interface Project {
  id: string;
  name: string;
  project_type?: string;
  created_at?: string;
}

export interface BulkAnnotationResponse {
  message: string;
  annotationsCreated: number;
  annotationsUpdated: number;
  notesCreated: number;
  succeededCount: number;
  errorsCount: number;
  warningsCount: number;
  warnings?: Array<Record<string, any>>;
  errors?: Array<Record<string, any>>;
}

export interface AnnotationRecord {
  'context.span_id': string;
  'annotation.notes'?: string;
  [key: string]: string | number | boolean | undefined;
}

export interface BackendAnnotationRecord {
  observation_span_id: string;
  annotations: Array<{
    annotation_label_id: string;
    value?: string;
    value_float?: number;
    value_bool?: boolean;
    value_str_list?: string[];
  }>;
  notes: Array<{ text: string }>;
}

export interface AnnotationOptions {
  fiApiKey?: string;
  fiSecretKey?: string;
  fiBaseUrl?: string;
  timeout?: number;
}