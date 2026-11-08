// Generated public declarations from @future-agi/sdk 0.1.2; do not edit.
/**
 * Types for the Annotation Queue SDK module.
 */
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
    assignmentStrategy?: string;
    annotationsRequired?: number;
    reservationTimeoutMinutes?: number;
    requiresReview?: boolean;
    createdAt?: string;
    updatedAt?: string;
    itemCount?: number;
    completedCount?: number;
}
export declare const VALID_SOURCE_TYPES: readonly [
    "trace",
    "observation_span",
    "trace_session",
    "call_execution",
    "prototype_run",
    "dataset_row"
];
export type SourceType = (typeof VALID_SOURCE_TYPES)[number];
export declare const VALID_ASSIGNMENT_STRATEGIES: readonly [
    "manual",
    "round_robin",
    "load_balanced"
];
export type AssignmentStrategy = (typeof VALID_ASSIGNMENT_STRATEGIES)[number];
export interface QueueItemSource {
    sourceType: SourceType;
    sourceId: string;
}
export interface QueueItem {
    id: string;
    sourceType?: string;
    sourceId?: string;
    status?: QueueItemStatus;
    order?: number;
    assignedTo?: string;
    createdAt?: string;
}
export interface AddItemsResponse {
    added: number;
    duplicates: number;
    errors?: Array<Record<string, any>>;
}
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
    throughput?: Record<string, any>;
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
export interface ExportToDatasetResponse {
    datasetId?: string;
    datasetName?: string;
    rowsCreated?: number;
}
