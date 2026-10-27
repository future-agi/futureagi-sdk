/**
 * Types for the Annotation Queue SDK module.
 */

// ---------------------------------------------------------------------------
// Queue
// ---------------------------------------------------------------------------

export const VALID_LABEL_TYPES = ['categorical', 'text', 'numeric', 'star', 'thumbs_up_down'] as const;
export type LabelType = (typeof VALID_LABEL_TYPES)[number];

export type QueueStatus = 'draft' | 'active' | 'paused' | 'completed';
export type QueueItemStatus = 'pending' | 'assigned' | 'in_progress' | 'completed' | 'skipped';

export interface QueueConfig {
    name: string;
    description?: string;
    instructions?: string;
    assignmentStrategy?: AssignmentStrategy;
    annotationsRequired?: number;
    reservationTimeoutMinutes?: number;
    requiresReview?: boolean;
    project?: string;
    dataset?: string;
    agentDefinition?: string;
}

export interface QueueDetail {
    id: string;
    name: string;
    description?: string;
    instructions?: string;
    status?: QueueStatus;
    assignment_strategy?: string;
    annotations_required?: number;
    reservation_timeout_minutes?: number;
    requires_review?: boolean;
    created_at?: string;
    updated_at?: string;
    item_count?: number;
    completed_count?: number;
}

// ---------------------------------------------------------------------------
// Items
// ---------------------------------------------------------------------------

export const VALID_SOURCE_TYPES = ['trace', 'observation_span', 'trace_session', 'call_execution', 'prototype_run', 'dataset_row'] as const;
export type SourceType = (typeof VALID_SOURCE_TYPES)[number];

export const VALID_ASSIGNMENT_STRATEGIES = ['manual', 'round_robin', 'load_balanced'] as const;
export type AssignmentStrategy = (typeof VALID_ASSIGNMENT_STRATEGIES)[number];

export interface QueueItemSource {
    sourceType: SourceType;
    sourceId: string;
}

export interface QueueItem {
    id: string;
    source_type?: string;
    source_id?: string;
    status?: QueueItemStatus;
    order?: number;
    assigned_to?: string;
    created_at?: string;
}

export interface AddItemsResponse {
    added: number;
    duplicates: number;
    errors?: Array<Record<string, any>>;
}

// ---------------------------------------------------------------------------
// Scores / Annotations
// ---------------------------------------------------------------------------

export type ScoreValue = string | number | boolean | string[];

export interface Score {
    id?: string;
    label_id?: string;
    label_name?: string;
    value?: ScoreValue;
    score_source?: string;
    notes?: string;
    annotator_id?: string;
    annotator_name?: string;
    source_type?: string;
    source_id?: string;
    created_at?: string;
}

export interface ScoreInput {
    labelId: string;
    value: ScoreValue;
    scoreSource?: string;
}

export interface AnnotationPayload {
    labelId: string;
    value: ScoreValue;
    scoreSource?: string;
}

export interface ImportAnnotationsResponse {
    imported: number;
}

// ---------------------------------------------------------------------------
// Progress & Analytics
// ---------------------------------------------------------------------------

export interface QueueProgress {
    total: number;
    pending: number;
    in_progress: number;
    completed: number;
    skipped: number;
    progress_pct?: number;
    annotator_stats?: Array<Record<string, any>>;
}

export interface QueueAnalytics {
    throughput?: Record<string, any>;
    annotator_performance?: Array<Record<string, any>>;
    label_distribution?: Record<string, any>;
    status_breakdown?: Record<string, number>;
    total?: number;
}

export interface QueueAgreement {
    overall_agreement?: number;
    per_label?: Array<Record<string, any>>;
    annotator_pairs?: Array<Record<string, any>>;
}

// ---------------------------------------------------------------------------
// Export
// ---------------------------------------------------------------------------

export interface ExportToDatasetResponse {
    dataset_id?: string;
    dataset_name?: string;
    rows_created?: number;
}
