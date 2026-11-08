// Generated public declarations from @future-agi/sdk 0.1.2; do not edit.
/**
 * AnnotationQueue – SDK client for managing annotation queues, items, scores, and analytics.
 *
 * @example
 * ```ts
 * import { AnnotationQueue } from '@future-agi/sdk';
 *
 * const client = new AnnotationQueue({ fiApiKey: '...', fiSecretKey: '...' });
 *
 * const queue = await client.create({ name: 'Review Queue' });
 * await client.activate(queue.id);
 * await client.addItems(queue.id, [{ sourceType: 'trace', sourceId: 'abc' }]);
 * const progress = await client.getProgress(queue.id);
 * ```
 */
import { APIKeyAuth } from '../api/auth.js';
import type { AddItemsResponse, AnnotationPayload, AssignmentStrategy, ExportToDatasetResponse, ImportAnnotationsResponse, QueueAgreement, QueueAnalytics, QueueConfig, QueueDetail, QueueItem, QueueItemSource, QueueProgress, Score, ScoreInput, ScoreValue } from './types.js';
declare const CLEAR: typeof import("../../../../../../src/index").CLEAR;
type Clearable<T> = T | typeof CLEAR;
export { CLEAR };
export declare class AnnotationQueue extends APIKeyAuth {
    create(config: QueueConfig): Promise<QueueDetail>;
    list(options?: {
        status?: string;
        search?: string;
        includeCounts?: boolean;
        page?: number;
        pageSize?: number;
        timeout?: number;
    }): Promise<QueueDetail[]>;
    get(queueId: string, options?: {
        timeout?: number;
    }): Promise<QueueDetail>;
    update(queueId: string, updates: {
        name?: Clearable<string>;
        description?: Clearable<string>;
        instructions?: Clearable<string>;
        assignmentStrategy?: AssignmentStrategy;
        annotationsRequired?: Clearable<number>;
        reservationTimeoutMinutes?: Clearable<number>;
        requiresReview?: Clearable<boolean>;
    }, options?: {
        timeout?: number;
    }): Promise<QueueDetail>;
    delete(queueId: string, options?: {
        timeout?: number;
    }): Promise<Record<string, any>>;
    activate(queueId: string, options?: {
        timeout?: number;
    }): Promise<QueueDetail>;
    completeQueue(queueId: string, options?: {
        timeout?: number;
    }): Promise<QueueDetail>;
    addLabel(queueId: string, labelId: string, options?: {
        timeout?: number;
    }): Promise<Record<string, any>>;
    removeLabel(queueId: string, labelId: string, options?: {
        timeout?: number;
    }): Promise<Record<string, any>>;
    addItems(queueId: string, items: QueueItemSource[], options?: {
        timeout?: number;
    }): Promise<AddItemsResponse>;
    listItems(queueId: string, options?: {
        status?: string;
        assignedTo?: string;
        page?: number;
        pageSize?: number;
        timeout?: number;
    }): Promise<QueueItem[]>;
    removeItems(queueId: string, itemIds: string[], options?: {
        timeout?: number;
    }): Promise<Record<string, any>>;
    assignItems(queueId: string, itemIds: string[], userId?: string | null, options?: {
        timeout?: number;
    }): Promise<Record<string, any>>;
    importAnnotations(queueId: string, itemId: string, annotations: AnnotationPayload[], options?: {
        annotatorId?: string;
        timeout?: number;
    }): Promise<ImportAnnotationsResponse>;
    submitAnnotations(queueId: string, itemId: string, annotations: AnnotationPayload[], options?: {
        notes?: string;
        timeout?: number;
    }): Promise<Record<string, any>>;
    getAnnotations(queueId: string, itemId: string, options?: {
        timeout?: number;
    }): Promise<Score[]>;
    completeItem(queueId: string, itemId: string, options?: {
        timeout?: number;
    }): Promise<Record<string, any>>;
    skipItem(queueId: string, itemId: string, options?: {
        timeout?: number;
    }): Promise<Record<string, any>>;
    createScore(options: {
        sourceType: string;
        sourceId: string;
        labelId: string;
        value: ScoreValue;
        scoreSource?: string;
        notes?: string;
        timeout?: number;
    }): Promise<Score>;
    createScores(options: {
        sourceType: string;
        sourceId: string;
        scores: ScoreInput[];
        notes?: string;
        timeout?: number;
    }): Promise<Record<string, any>>;
    getScores(sourceType: string, sourceId: string, options?: {
        timeout?: number;
    }): Promise<Score[]>;
    getProgress(queueId: string, options?: {
        timeout?: number;
    }): Promise<QueueProgress>;
    getAnalytics(queueId: string, options?: {
        timeout?: number;
    }): Promise<QueueAnalytics>;
    getAgreement(queueId: string, options?: {
        timeout?: number;
    }): Promise<QueueAgreement>;
    export(queueId: string, options: {
        format: 'csv';
        status?: string;
        timeout?: number;
    }): Promise<string>;
    export(queueId: string, options?: {
        format?: 'json';
        status?: string;
        timeout?: number;
    }): Promise<Record<string, any>[]>;
    exportToDataset(queueId: string, options: {
        datasetName?: string;
        datasetId?: string;
        statusFilter?: string;
        timeout?: number;
    }): Promise<ExportToDatasetResponse>;
}
export type PublishedCall978 = (config: QueueConfig) => Promise<QueueDetail>;
export type PublishedCall1033 = (options?: {
    status?: string;
    search?: string;
    includeCounts?: boolean;
    page?: number;
    pageSize?: number;
    timeout?: number;
}) => Promise<QueueDetail[]>;
export type PublishedCall1245 = (queueId: string, options?: {
    timeout?: number;
}) => Promise<QueueDetail>;
export type PublishedCall1338 = (queueId: string, updates: {
    name?: Clearable<string>;
    description?: Clearable<string>;
    instructions?: Clearable<string>;
    assignmentStrategy?: AssignmentStrategy;
    annotationsRequired?: Clearable<number>;
    reservationTimeoutMinutes?: Clearable<number>;
    requiresReview?: Clearable<boolean>;
}, options?: {
    timeout?: number;
}) => Promise<QueueDetail>;
export type PublishedCall1767 = (queueId: string, options?: {
    timeout?: number;
}) => Promise<Record<string, any>>;
export type PublishedCall1871 = (queueId: string, options?: {
    timeout?: number;
}) => Promise<QueueDetail>;
export type PublishedCall1969 = (queueId: string, options?: {
    timeout?: number;
}) => Promise<QueueDetail>;
export type PublishedCall2099 = (queueId: string, labelId: string, options?: {
    timeout?: number;
}) => Promise<Record<string, any>>;
export type PublishedCall2222 = (queueId: string, labelId: string, options?: {
    timeout?: number;
}) => Promise<Record<string, any>>;
export type PublishedCall2348 = (queueId: string, items: QueueItemSource[], options?: {
    timeout?: number;
}) => Promise<AddItemsResponse>;
export type PublishedCall2477 = (queueId: string, options?: {
    status?: string;
    assignedTo?: string;
    page?: number;
    pageSize?: number;
    timeout?: number;
}) => Promise<QueueItem[]>;
export type PublishedCall2680 = (queueId: string, itemIds: string[], options?: {
    timeout?: number;
}) => Promise<Record<string, any>>;
export type PublishedCall2808 = (queueId: string, itemIds: string[], userId?: string | null, options?: {
    timeout?: number;
}) => Promise<Record<string, any>>;
export type PublishedCall2960 = (queueId: string, itemId: string, annotations: AnnotationPayload[], options?: {
    annotatorId?: string;
    timeout?: number;
}) => Promise<ImportAnnotationsResponse>;
export type PublishedCall3161 = (queueId: string, itemId: string, annotations: AnnotationPayload[], options?: {
    notes?: string;
    timeout?: number;
}) => Promise<Record<string, any>>;
export type PublishedCall3350 = (queueId: string, itemId: string, options?: {
    timeout?: number;
}) => Promise<Score[]>;
export type PublishedCall3466 = (queueId: string, itemId: string, options?: {
    timeout?: number;
}) => Promise<Record<string, any>>;
export type PublishedCall3592 = (queueId: string, itemId: string, options?: {
    timeout?: number;
}) => Promise<Record<string, any>>;
export type PublishedCall3714 = (options: {
    sourceType: string;
    sourceId: string;
    labelId: string;
    value: ScoreValue;
    scoreSource?: string;
    notes?: string;
    timeout?: number;
}) => Promise<Score>;
export type PublishedCall3951 = (options: {
    sourceType: string;
    sourceId: string;
    scores: ScoreInput[];
    notes?: string;
    timeout?: number;
}) => Promise<Record<string, any>>;
export type PublishedCall4151 = (sourceType: string, sourceId: string, options?: {
    timeout?: number;
}) => Promise<Score[]>;
export type PublishedCall4267 = (queueId: string, options?: {
    timeout?: number;
}) => Promise<QueueProgress>;
export type PublishedCall4370 = (queueId: string, options?: {
    timeout?: number;
}) => Promise<QueueAnalytics>;
export type PublishedCall4475 = (queueId: string, options?: {
    timeout?: number;
}) => Promise<QueueAgreement>;
export type PublishedCall4580 = (queueId: string, options: {
    format: 'csv';
    status?: string;
    timeout?: number;
}) => Promise<string>;
export type PublishedCall4718 = (queueId: string, options?: {
    format?: 'json';
    status?: string;
    timeout?: number;
}) => Promise<Record<string, any>[]>;
export type PublishedCall4874 = (queueId: string, options: {
    datasetName?: string;
    datasetId?: string;
    statusFilter?: string;
    timeout?: number;
}) => Promise<ExportToDatasetResponse>;
