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

/** Published 0.2.0 contract; camelCase aliases are optional on caller-owned objects. */
export interface BulkAnnotationResponse {
  message: string;
  /** @deprecated Use annotations_created. SDK response access warns once per alias per process. */
  annotationsCreated?: number;
  annotations_created: number;
  /** @deprecated Use annotations_updated. SDK response access warns once per alias per process. */
  annotationsUpdated?: number;
  annotations_updated: number;
  /** @deprecated Use notes_created. SDK response access warns once per alias per process. */
  notesCreated?: number;
  notes_created: number;
  /** @deprecated Use succeeded_count. SDK response access warns once per alias per process. */
  succeededCount?: number;
  succeeded_count: number;
  /** @deprecated Use errors_count. SDK response access warns once per alias per process. */
  errorsCount?: number;
  errors_count: number;
  /** @deprecated Use warnings_count. SDK response access warns once per alias per process. */
  warningsCount?: number;
  warnings_count: number;
  warnings?: Array<Record<string, any>>;
  errors?: Array<Record<string, any>>;
}

/** Older camelCase input shape, separate from the 0.2.0 canonical interface. */
export interface LegacyBulkAnnotationResponse {
  message: string;
  annotationsCreated: number;
  annotationsUpdated: number;
  notesCreated: number;
  succeededCount: number;
  errorsCount: number;
  warningsCount: number;
  annotations_created?: number;
  annotations_updated?: number;
  notes_created?: number;
  succeeded_count?: number;
  errors_count?: number;
  warnings_count?: number;
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

/** Canonical server payload; retained as an alias of the published contract. */
export type BulkAnnotationCanonicalResponse = BulkAnnotationResponse;

/** SDK responses expose both spellings; legacy getters warn once per alias. */
export type BulkAnnotationResult = BulkAnnotationResponse & LegacyBulkAnnotationResponse;
