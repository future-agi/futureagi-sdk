/**
 * Types for the Annotation Queue SDK module.
 */

// ---------------------------------------------------------------------------
// Queue
// ---------------------------------------------------------------------------

export interface QueueConfig {
    name: string;
    description?: string;
    instructions?: string;
    assignmentStrategy?: 'manual' | 'round_robin' | 'load_balanced';
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
    status?: string;
    assignmentStrategy?: string;
    annotationsRequired?: number;
    reservationTimeoutMinutes?: number;
    requiresReview?: boolean;
    createdAt?: string;
    updatedAt?: string;
    itemCount?: number;
    completedCount?: number;
}

// ---------------------------------------------------------------------------
// Items
// ---------------------------------------------------------------------------

export type SourceType = 'trace' | 'observation_span' | 'trace_session' | 'call_execution' | 'prototype_run' | 'dataset_row';

export interface QueueItemSource {
    sourceType: SourceType;
    sourceId: string;
}

export interface QueueItem {
    id: string;
    sourceType?: string;
    sourceId?: string;
    status?: string;
    order?: number;
    assignedTo?: string;
    createdAt?: string;
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
    labelId?: string;
    labelName?: string;
    value?: ScoreValue;
    scoreSource?: string;
    notes?: string;
    annotatorId?: string;
    annotatorName?: string;
    sourceType?: string;
    sourceId?: string;
    createdAt?: string;
}

export interface AnnotationPayload {
    labelId: string;
    value?: ScoreValue;
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
    inProgress: number;
    completed: number;
    skipped: number;
    progressPct?: number;
    annotatorStats?: Array<Record<string, any>>;
}

export interface QueueAnalytics {
    throughput?: Array<Record<string, any>>;
    annotatorPerformance?: Array<Record<string, any>>;
    labelDistribution?: Record<string, any>;
    statusBreakdown?: Record<string, number>;
    total?: number;
}

export interface QueueAgreement {
    overallAgreement?: number;
    perLabel?: Array<Record<string, any>>;
    annotatorPairs?: Array<Record<string, any>>;
}

// ---------------------------------------------------------------------------
// Export
// ---------------------------------------------------------------------------

export interface ExportToDatasetResponse {
    datasetId?: string;
    datasetName?: string;
    rowsCreated?: number;
}
