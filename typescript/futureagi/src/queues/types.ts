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

export type AnnotatorRole = 'annotator' | 'reviewer' | 'manager';

export interface QueueConfig {
    name: string;
    /** Annotation label ids, at least one. If omitted, reuse the given scope's default queue
     * labels with one DeprecationWarning. Throws DefaultQueueLabelError if no single scope or
     * its default queue has no usable labels. Import the error from `@future-agi/sdk`.
     * The lookup can create or restore the default queue even if the label check then fails;
     * the server does not invent a default label. */
    labelIds?: string[];
    description?: string;
    instructions?: string;
    /** `'manual'` (server default), `'round_robin'` or `'load_balanced'`. */
    assignmentStrategy?: AssignmentStrategy;
    /** Annotations needed per item (server default 1). */
    annotationsRequired?: number;
    /** How long an annotator holds an item, in minutes (server default 60). */
    reservationTimeoutMinutes?: number;
    /** Completed items go to a reviewer first. The server checks that your plan includes the review workflow. */
    requiresReview?: boolean;
    /** Every member can annotate any item without an explicit assignment. */
    autoAssign?: boolean;
    /** User ids to add as members. The creator is always added as a manager, reviewer and annotator. */
    annotatorIds?: string[];
    /** Roles per user id in `annotatorIds`: a role or a list of them (default `'annotator'`). */
    annotatorRoles?: Record<string, AnnotatorRole | AnnotatorRole[]>;
    /**
     * Not sent (read-only on create). When labelIds is omitted, identifies the default queue
     * used to obtain labels; otherwise warns that this cannot scope the new queue.
     * To use the default queue itself, call `getOrCreateDefault({ projectId })`.
     */
    project?: string;
    /** Not sent on create; accepted for default-label lookup, as `project`.
     * To use the default queue itself, call `getOrCreateDefault({ datasetId })`. */
    dataset?: string;
    /** Not sent on create; accepted for default-label lookup, as `project`.
     * To use the default queue itself, call `getOrCreateDefault({ agentDefinitionId })`. */
    agentDefinition?: string;
}

export interface QueueDetail {
    id: string;
    name: string;
    description?: string;
    instructions?: string;
    status?: QueueStatus;
    /** @deprecated Use assignment_strategy. SDK response access warns once per alias per process. */
    assignmentStrategy?: string;
    assignment_strategy?: string;
    /** @deprecated Use annotations_required. SDK response access warns once per alias per process. */
    annotationsRequired?: number;
    annotations_required?: number;
    /** @deprecated Use reservation_timeout_minutes. SDK response access warns once per alias per process. */
    reservationTimeoutMinutes?: number;
    reservation_timeout_minutes?: number;
    /** @deprecated Use requires_review. SDK response access warns once per alias per process. */
    requiresReview?: boolean;
    requires_review?: boolean;
    is_default?: boolean;
    /** @deprecated Use created_at. SDK response access warns once per alias per process. */
    createdAt?: string;
    created_at?: string;
    /** @deprecated Use updated_at. SDK response access warns once per alias per process. */
    updatedAt?: string;
    updated_at?: string;
    /** @deprecated Use item_count. SDK response access warns once per alias per process. */
    itemCount?: number;
    item_count?: number;
    /** @deprecated Use completed_count. SDK response access warns once per alias per process. */
    completedCount?: number;
    completed_count?: number;
}

/** Exactly one of a project, dataset or agent definition id (`getOrCreateDefault`). */
export type DefaultQueueScope =
    | { projectId: string; datasetId?: never; agentDefinitionId?: never }
    | { projectId?: never; datasetId: string; agentDefinitionId?: never }
    | { projectId?: never; datasetId?: never; agentDefinitionId: string };

/** The default queue of a project, dataset or agent definition (`getOrCreateDefault`). */
export interface DefaultQueue {
    queue: QueueDetail;
    /** The queue's labels: id, name, type, settings, description, allow_notes, required, order. */
    labels: Record<string, any>[];
    /** True only when this call created the queue. */
    created: boolean;
    /** `'restored'` means an archived default queue came back. */
    action: 'created' | 'restored' | 'fetched';
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
    /** @deprecated Use source_type. SDK response access warns once per alias per process. */
    sourceType?: string;
    source_type?: string;
    /** @deprecated Use source_id. SDK response access warns once per alias per process. */
    sourceId?: string;
    source_id?: string;
    status?: QueueItemStatus;
    order?: number;
    /** @deprecated Use assigned_to. SDK response access warns once per alias per process. */
    assignedTo?: string;
    assigned_to?: string;
    /** @deprecated Use created_at. SDK response access warns once per alias per process. */
    createdAt?: string;
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
    /** @deprecated Use label_id. SDK response access warns once per alias per process. */
    labelId?: string;
    label_id?: string;
    /** @deprecated Use label_name. SDK response access warns once per alias per process. */
    labelName?: string;
    label_name?: string;
    value?: ScoreValue;
    /** @deprecated Use score_source. SDK response access warns once per alias per process. */
    scoreSource?: string;
    score_source?: string;
    notes?: string;
    /** @deprecated Use annotator_id. SDK response access warns once per alias per process. */
    annotatorId?: string;
    annotator_id?: string;
    /** @deprecated Use annotator_name. SDK response access warns once per alias per process. */
    annotatorName?: string;
    annotator_name?: string;
    /** @deprecated Use source_type. SDK response access warns once per alias per process. */
    sourceType?: string;
    source_type?: string;
    /** @deprecated Use source_id. SDK response access warns once per alias per process. */
    sourceId?: string;
    source_id?: string;
    /** @deprecated Use created_at. SDK response access warns once per alias per process. */
    createdAt?: string;
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
    /** @deprecated Use in_progress. SDK response access warns once per alias per process. */
    inProgress?: number;
    in_progress: number;
    completed: number;
    skipped: number;
    /** @deprecated Use progress_pct. SDK response access warns once per alias per process. */
    progressPct?: number;
    progress_pct?: number;
    /** @deprecated Use annotator_stats. SDK response access warns once per alias per process. */
    annotatorStats?: Array<Record<string, any>>;
    annotator_stats?: Array<Record<string, any>>;
}

export interface QueueAnalytics {
    throughput?: Record<string, any>;
    /** @deprecated Use annotator_performance. SDK response access warns once per alias per process. */
    annotatorPerformance?: Array<Record<string, any>>;
    annotator_performance?: Array<Record<string, any>>;
    /** @deprecated Use label_distribution. SDK response access warns once per alias per process. */
    labelDistribution?: Record<string, any>;
    label_distribution?: Record<string, any>;
    /** @deprecated Use status_breakdown. SDK response access warns once per alias per process. */
    statusBreakdown?: Record<string, number>;
    status_breakdown?: Record<string, number>;
    total?: number;
}

export interface QueueAgreement {
    /** @deprecated Use overall_agreement. SDK response access warns once per alias per process. */
    overallAgreement?: number;
    overall_agreement?: number;
    /** @deprecated Use per_label. SDK response access warns once per alias per process. */
    perLabel?: Array<Record<string, any>>;
    per_label?: Array<Record<string, any>>;
    /** @deprecated Use annotator_pairs. SDK response access warns once per alias per process. */
    annotatorPairs?: Array<Record<string, any>>;
    annotator_pairs?: Array<Record<string, any>>;
}

// ---------------------------------------------------------------------------
// Export
// ---------------------------------------------------------------------------

export interface ExportToDatasetResponse {
    /** @deprecated Use dataset_id. SDK response access warns once per alias per process. */
    datasetId?: string;
    dataset_id?: string;
    /** @deprecated Use dataset_name. SDK response access warns once per alias per process. */
    datasetName?: string;
    dataset_name?: string;
    /** @deprecated Use rows_created. SDK response access warns once per alias per process. */
    rowsCreated?: number;
    rows_created?: number;
}

/** Older camelCase input, separate from the published 0.2.0 interface. */
export type LegacyQueueProgress = Omit<QueueProgress, 'inProgress' | 'in_progress'> & {
    inProgress: number;
    in_progress?: number;
};
/** SDK progress responses expose both required counter spellings. */
export type QueueProgressResult = QueueProgress & LegacyQueueProgress;
