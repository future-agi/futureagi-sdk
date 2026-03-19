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

import { APIKeyAuth, APIKeyAuthConfig, ResponseHandler } from '../api/auth';
import { HttpMethod, RequestConfig } from '../api/types';
import { SDKException } from '../utils/errors';
import { Routes } from '../utils/routes';
import type {
    AddItemsResponse,
    AnnotationPayload,
    AssignmentStrategy,
    ExportToDatasetResponse,
    ImportAnnotationsResponse,
    QueueAgreement,
    QueueAnalytics,
    QueueConfig,
    QueueDetail,
    QueueItem,
    QueueItemSource,
    QueueProgress,
    Score,
    ScoreInput,
    ScoreValue,
} from './types';
import { VALID_SOURCE_TYPES, VALID_ASSIGNMENT_STRATEGIES } from './types';

// ---------------------------------------------------------------------------
// Response type for handlers
// ---------------------------------------------------------------------------

interface ApiResponse {
    data: any;
    status: number;
}

// ---------------------------------------------------------------------------
// Response handlers
// ---------------------------------------------------------------------------

function unwrap(data: any): any {
    if (data && typeof data === 'object' && 'result' in data) {
        return data.result;
    }
    return data;
}

class QueueResponseHandler extends ResponseHandler<QueueDetail> {
    static _parseSuccess(response: ApiResponse): QueueDetail {
        return unwrap(response.data);
    }
}

class QueueListResponseHandler extends ResponseHandler<QueueDetail[]> {
    static _parseSuccess(response: ApiResponse): QueueDetail[] {
        const data = unwrap(response.data);
        if (Array.isArray(data)) return data;
        return data?.results ?? data?.table ?? [];
    }
}

class DictResponseHandler extends ResponseHandler<Record<string, any>> {
    static _parseSuccess(response: ApiResponse): Record<string, any> {
        return unwrap(response.data);
    }
}

class ItemListResponseHandler extends ResponseHandler<QueueItem[]> {
    static _parseSuccess(response: ApiResponse): QueueItem[] {
        const data = unwrap(response.data);
        if (Array.isArray(data)) return data;
        return data?.results ?? [];
    }
}

class ScoreListResponseHandler extends ResponseHandler<Score[]> {
    static _parseSuccess(response: ApiResponse): Score[] {
        const data = unwrap(response.data);
        if (Array.isArray(data)) return data;
        return data?.results ?? [];
    }
}

class ScoreResponseHandler extends ResponseHandler<Score> {
    static _parseSuccess(response: ApiResponse): Score {
        return unwrap(response.data);
    }
}

class AddItemsResponseHandler extends ResponseHandler<AddItemsResponse> {
    static _parseSuccess(response: ApiResponse): AddItemsResponse {
        return unwrap(response.data);
    }
}

class ImportAnnotationsResponseHandler extends ResponseHandler<ImportAnnotationsResponse> {
    static _parseSuccess(response: ApiResponse): ImportAnnotationsResponse {
        return unwrap(response.data);
    }
}

class QueueProgressResponseHandler extends ResponseHandler<QueueProgress> {
    static _parseSuccess(response: ApiResponse): QueueProgress {
        return unwrap(response.data);
    }
}

class QueueAnalyticsResponseHandler extends ResponseHandler<QueueAnalytics> {
    static _parseSuccess(response: ApiResponse): QueueAnalytics {
        return unwrap(response.data);
    }
}

class QueueAgreementResponseHandler extends ResponseHandler<QueueAgreement> {
    static _parseSuccess(response: ApiResponse): QueueAgreement {
        return unwrap(response.data);
    }
}

class ExportToDatasetResponseHandler extends ResponseHandler<ExportToDatasetResponse> {
    static _parseSuccess(response: ApiResponse): ExportToDatasetResponse {
        return unwrap(response.data);
    }
}

class ExportJsonResponseHandler extends ResponseHandler<Record<string, any>[]> {
    static _parseSuccess(response: ApiResponse): Record<string, any>[] {
        return unwrap(response.data);
    }
}

// ---------------------------------------------------------------------------
// URL helper
// ---------------------------------------------------------------------------

function buildUrl(base: string, route: string, params: Record<string, string> = {}): string {
    let url = `${base}/${route}`;
    for (const [key, val] of Object.entries(params)) {
        url = url.replace(`{${key}}`, encodeURIComponent(val));
    }
    return url;
}

// ---------------------------------------------------------------------------
// Source type validation helper
// ---------------------------------------------------------------------------

function validateSourceType(sourceType: string): void {
    if (!(VALID_SOURCE_TYPES as readonly string[]).includes(sourceType)) {
        throw new SDKException(
            `Invalid sourceType '${sourceType}'. Must be one of: ${VALID_SOURCE_TYPES.join(', ')}`,
        );
    }
}

// ---------------------------------------------------------------------------
// Client
// ---------------------------------------------------------------------------

// Sentinel for explicitly clearing a field via PATCH
const CLEAR = Symbol('CLEAR');
type Clearable<T> = T | typeof CLEAR;

export { CLEAR };

export class AnnotationQueue extends APIKeyAuth {
    // ------------------------------------------------------------------
    // Queue CRUD
    // ------------------------------------------------------------------

    async create(config: QueueConfig): Promise<QueueDetail> {
        if (config.assignmentStrategy != null &&
            !(VALID_ASSIGNMENT_STRATEGIES as readonly string[]).includes(config.assignmentStrategy)) {
            throw new SDKException(
                `Invalid assignmentStrategy '${config.assignmentStrategy}'. Must be one of: ${VALID_ASSIGNMENT_STRATEGIES.join(', ')}`,
            );
        }

        const body: Record<string, any> = { name: config.name };
        if (config.description != null) body.description = config.description;
        if (config.instructions != null) body.instructions = config.instructions;
        if (config.assignmentStrategy != null) body.assignment_strategy = config.assignmentStrategy;
        if (config.annotationsRequired != null) body.annotations_required = config.annotationsRequired;
        if (config.reservationTimeoutMinutes != null) body.reservation_timeout_minutes = config.reservationTimeoutMinutes;
        if (config.requiresReview != null) body.requires_review = config.requiresReview;
        if (config.project != null) body.project = config.project;
        if (config.dataset != null) body.dataset = config.dataset;
        if (config.agentDefinition != null) body.agent_definition = config.agentDefinition;

        return this.request(
            {
                method: HttpMethod.POST,
                url: buildUrl(this._baseUrl, Routes.ANNOTATION_QUEUES),
                json: body,
            },
            QueueResponseHandler,
        ) as Promise<QueueDetail>;
    }

    async list(options?: {
        status?: string;
        search?: string;
        includeCounts?: boolean;
        page?: number;
        pageSize?: number;
        timeout?: number;
    }): Promise<QueueDetail[]> {
        const params: Record<string, any> = {
            page: options?.page ?? 1,
            page_size: options?.pageSize ?? 20,
        };
        if (options?.status) params.status = options.status;
        if (options?.search) params.search = options.search;
        if (options?.includeCounts !== false) params.include_counts = 'true';

        return this.request(
            {
                method: HttpMethod.GET,
                url: buildUrl(this._baseUrl, Routes.ANNOTATION_QUEUES),
                params,
                timeout: options?.timeout,
            },
            QueueListResponseHandler,
        ) as Promise<QueueDetail[]>;
    }

    async get(queueId: string, options?: { timeout?: number }): Promise<QueueDetail> {
        return this.request(
            {
                method: HttpMethod.GET,
                url: buildUrl(this._baseUrl, Routes.ANNOTATION_QUEUE_DETAIL, { queue_id: queueId }),
                timeout: options?.timeout,
            },
            QueueResponseHandler,
        ) as Promise<QueueDetail>;
    }

    async update(
        queueId: string,
        updates: {
            name?: Clearable<string>;
            description?: Clearable<string>;
            instructions?: Clearable<string>;
            assignmentStrategy?: AssignmentStrategy;
            annotationsRequired?: Clearable<number>;
            reservationTimeoutMinutes?: Clearable<number>;
            requiresReview?: Clearable<boolean>;
        },
        options?: { timeout?: number },
    ): Promise<QueueDetail> {
        const body: Record<string, any> = {};

        const set = (wireKey: string, val: any) => {
            if (val === CLEAR) {
                body[wireKey] = null;
            } else if (val !== undefined) {
                body[wireKey] = val;
            }
        };

        set('name', updates.name);
        set('description', updates.description);
        set('instructions', updates.instructions);
        set('assignment_strategy', updates.assignmentStrategy);
        set('annotations_required', updates.annotationsRequired);
        set('reservation_timeout_minutes', updates.reservationTimeoutMinutes);
        set('requires_review', updates.requiresReview);

        return this.request(
            {
                method: HttpMethod.PATCH,
                url: buildUrl(this._baseUrl, Routes.ANNOTATION_QUEUE_DETAIL, { queue_id: queueId }),
                json: body,
                timeout: options?.timeout,
            },
            QueueResponseHandler,
        ) as Promise<QueueDetail>;
    }

    async delete(queueId: string, options?: { timeout?: number }): Promise<Record<string, any>> {
        return this.request(
            {
                method: HttpMethod.DELETE,
                url: buildUrl(this._baseUrl, Routes.ANNOTATION_QUEUE_DETAIL, { queue_id: queueId }),
                timeout: options?.timeout,
            },
            DictResponseHandler,
        ) as Promise<Record<string, any>>;
    }

    // ------------------------------------------------------------------
    // Queue lifecycle
    // ------------------------------------------------------------------

    async activate(queueId: string, options?: { timeout?: number }): Promise<QueueDetail> {
        return this._updateStatus(queueId, 'active', options?.timeout);
    }

    async completeQueue(queueId: string, options?: { timeout?: number }): Promise<QueueDetail> {
        return this._updateStatus(queueId, 'completed', options?.timeout);
    }

    private async _updateStatus(queueId: string, status: 'active' | 'completed' | 'paused', timeout?: number): Promise<QueueDetail> {
        return this.request(
            {
                method: HttpMethod.POST,
                url: buildUrl(this._baseUrl, Routes.ANNOTATION_QUEUE_STATUS, { queue_id: queueId }),
                json: { status },
                timeout,
            },
            QueueResponseHandler,
        ) as Promise<QueueDetail>;
    }

    // ------------------------------------------------------------------
    // Labels
    // ------------------------------------------------------------------

    async addLabel(queueId: string, labelId: string, options?: { timeout?: number }): Promise<Record<string, any>> {
        return this.request(
            {
                method: HttpMethod.POST,
                url: buildUrl(this._baseUrl, Routes.ANNOTATION_QUEUE_ADD_LABEL, { queue_id: queueId }),
                json: { label_id: labelId },
                timeout: options?.timeout,
            },
            DictResponseHandler,
        ) as Promise<Record<string, any>>;
    }

    async removeLabel(queueId: string, labelId: string, options?: { timeout?: number }): Promise<Record<string, any>> {
        return this.request(
            {
                method: HttpMethod.POST,
                url: buildUrl(this._baseUrl, Routes.ANNOTATION_QUEUE_REMOVE_LABEL, { queue_id: queueId }),
                json: { label_id: labelId },
                timeout: options?.timeout,
            },
            DictResponseHandler,
        ) as Promise<Record<string, any>>;
    }

    // ------------------------------------------------------------------
    // Items
    // ------------------------------------------------------------------

    async addItems(
        queueId: string,
        items: QueueItemSource[],
        options?: { timeout?: number },
    ): Promise<AddItemsResponse> {
        if (!items || items.length === 0) {
            throw new SDKException('items must be a non-empty array');
        }

        for (const item of items) {
            if (!(VALID_SOURCE_TYPES as readonly string[]).includes(item.sourceType)) {
                throw new SDKException(
                    `Invalid sourceType '${item.sourceType}'. Must be one of: ${VALID_SOURCE_TYPES.join(', ')}`,
                );
            }
        }

        const wireItems = items.map((item) => ({
            source_type: item.sourceType,
            source_id: item.sourceId,
        }));

        return this.request(
            {
                method: HttpMethod.POST,
                url: buildUrl(this._baseUrl, Routes.QUEUE_ITEMS_ADD, { queue_id: queueId }),
                json: { items: wireItems },
                timeout: options?.timeout,
            },
            AddItemsResponseHandler,
        ) as Promise<AddItemsResponse>;
    }

    async listItems(
        queueId: string,
        options?: {
            status?: string;
            assignedTo?: string;
            page?: number;
            pageSize?: number;
            timeout?: number;
        },
    ): Promise<QueueItem[]> {
        const params: Record<string, any> = {
            page: options?.page ?? 1,
            page_size: options?.pageSize ?? 50,
        };
        if (options?.status) params.status = options.status;
        if (options?.assignedTo) params.assigned_to = options.assignedTo;

        return this.request(
            {
                method: HttpMethod.GET,
                url: buildUrl(this._baseUrl, Routes.QUEUE_ITEMS, { queue_id: queueId }),
                params,
                timeout: options?.timeout,
            },
            ItemListResponseHandler,
        ) as Promise<QueueItem[]>;
    }

    async removeItems(
        queueId: string,
        itemIds: string[],
        options?: { timeout?: number },
    ): Promise<Record<string, any>> {
        if (!itemIds || itemIds.length === 0) {
            throw new SDKException('itemIds must be a non-empty array');
        }

        return this.request(
            {
                method: HttpMethod.POST,
                url: buildUrl(this._baseUrl, Routes.QUEUE_ITEMS_BULK_REMOVE, { queue_id: queueId }),
                json: { item_ids: itemIds },
                timeout: options?.timeout,
            },
            DictResponseHandler,
        ) as Promise<Record<string, any>>;
    }

    async assignItems(
        queueId: string,
        itemIds: string[],
        userId: string | null = null,
        options?: { timeout?: number },
    ): Promise<Record<string, any>> {
        if (!itemIds || itemIds.length === 0) {
            throw new SDKException('itemIds must be a non-empty array');
        }

        return this.request(
            {
                method: HttpMethod.POST,
                url: buildUrl(this._baseUrl, Routes.QUEUE_ITEMS_ASSIGN, { queue_id: queueId }),
                json: { item_ids: itemIds, user_id: userId },
                timeout: options?.timeout,
            },
            DictResponseHandler,
        ) as Promise<Record<string, any>>;
    }

    // ------------------------------------------------------------------
    // Annotation submission
    // ------------------------------------------------------------------

    async importAnnotations(
        queueId: string,
        itemId: string,
        annotations: AnnotationPayload[],
        options?: { annotatorId?: string; timeout?: number },
    ): Promise<ImportAnnotationsResponse> {
        if (!annotations || annotations.length === 0) {
            throw new SDKException('annotations must be a non-empty array');
        }

        const wireAnnotations = annotations.map((a) => ({
            label_id: a.labelId,
            value: a.value,
            ...(a.scoreSource != null ? { score_source: a.scoreSource } : {}),
        }));
        const body: Record<string, any> = { annotations: wireAnnotations };
        if (options?.annotatorId != null) body.annotator_id = options.annotatorId;

        return this.request(
            {
                method: HttpMethod.POST,
                url: buildUrl(this._baseUrl, Routes.QUEUE_ITEM_ANNOTATIONS_IMPORT, {
                    queue_id: queueId,
                    item_id: itemId,
                }),
                json: body,
                timeout: options?.timeout,
            },
            ImportAnnotationsResponseHandler,
        ) as Promise<ImportAnnotationsResponse>;
    }

    async submitAnnotations(
        queueId: string,
        itemId: string,
        annotations: AnnotationPayload[],
        options?: { notes?: string; timeout?: number },
    ): Promise<Record<string, any>> {
        if (!annotations || annotations.length === 0) {
            throw new SDKException('annotations must be a non-empty array');
        }

        const wireAnnotations = annotations.map((a) => ({
            label_id: a.labelId,
            value: a.value,
            ...(a.scoreSource != null ? { score_source: a.scoreSource } : {}),
        }));
        const body: Record<string, any> = { annotations: wireAnnotations };
        if (options?.notes != null) body.notes = options.notes;

        return this.request(
            {
                method: HttpMethod.POST,
                url: buildUrl(this._baseUrl, Routes.QUEUE_ITEM_ANNOTATIONS_SUBMIT, {
                    queue_id: queueId,
                    item_id: itemId,
                }),
                json: body,
                timeout: options?.timeout,
            },
            DictResponseHandler,
        ) as Promise<Record<string, any>>;
    }

    async getAnnotations(
        queueId: string,
        itemId: string,
        options?: { timeout?: number },
    ): Promise<Score[]> {
        return this.request(
            {
                method: HttpMethod.GET,
                url: buildUrl(this._baseUrl, Routes.QUEUE_ITEM_ANNOTATIONS_LIST, {
                    queue_id: queueId,
                    item_id: itemId,
                }),
                timeout: options?.timeout,
            },
            ScoreListResponseHandler,
        ) as Promise<Score[]>;
    }

    async completeItem(
        queueId: string,
        itemId: string,
        options?: { timeout?: number },
    ): Promise<Record<string, any>> {
        return this.request(
            {
                method: HttpMethod.POST,
                url: buildUrl(this._baseUrl, Routes.QUEUE_ITEM_COMPLETE, {
                    queue_id: queueId,
                    item_id: itemId,
                }),
                timeout: options?.timeout,
            },
            DictResponseHandler,
        ) as Promise<Record<string, any>>;
    }

    async skipItem(
        queueId: string,
        itemId: string,
        options?: { timeout?: number },
    ): Promise<Record<string, any>> {
        return this.request(
            {
                method: HttpMethod.POST,
                url: buildUrl(this._baseUrl, Routes.QUEUE_ITEM_SKIP, {
                    queue_id: queueId,
                    item_id: itemId,
                }),
                timeout: options?.timeout,
            },
            DictResponseHandler,
        ) as Promise<Record<string, any>>;
    }

    // ------------------------------------------------------------------
    // Scores (unified annotation model)
    // ------------------------------------------------------------------

    async createScore(options: {
        sourceType: string;
        sourceId: string;
        labelId: string;
        value: ScoreValue;
        scoreSource?: string;
        notes?: string;
        timeout?: number;
    }): Promise<Score> {
        validateSourceType(options.sourceType);

        const body: Record<string, any> = {
            source_type: options.sourceType,
            source_id: options.sourceId,
            label_id: options.labelId,
            value: options.value,
            score_source: options.scoreSource ?? 'api',
        };
        if (options.notes != null) body.notes = options.notes;

        return this.request(
            {
                method: HttpMethod.POST,
                url: buildUrl(this._baseUrl, Routes.SCORES),
                json: body,
                timeout: options.timeout,
            },
            ScoreResponseHandler,
        ) as Promise<Score>;
    }

    async createScores(options: {
        sourceType: string;
        sourceId: string;
        scores: ScoreInput[];
        notes?: string;
        timeout?: number;
    }): Promise<Record<string, any>> {
        validateSourceType(options.sourceType);

        if (!options.scores || options.scores.length === 0) {
            throw new SDKException('scores must be a non-empty array');
        }

        const wireScores = options.scores.map((s) => ({
            label_id: s.labelId,
            value: s.value,
            ...(s.scoreSource != null ? { score_source: s.scoreSource } : {}),
        }));

        const body: Record<string, any> = {
            source_type: options.sourceType,
            source_id: options.sourceId,
            scores: wireScores,
        };
        if (options.notes != null) body.notes = options.notes;

        return this.request(
            {
                method: HttpMethod.POST,
                url: buildUrl(this._baseUrl, Routes.SCORES_BULK),
                json: body,
                timeout: options.timeout,
            },
            DictResponseHandler,
        ) as Promise<Record<string, any>>;
    }

    async getScores(
        sourceType: string,
        sourceId: string,
        options?: { timeout?: number },
    ): Promise<Score[]> {
        validateSourceType(sourceType);

        return this.request(
            {
                method: HttpMethod.GET,
                url: buildUrl(this._baseUrl, Routes.SCORES_FOR_SOURCE),
                params: { source_type: sourceType, source_id: sourceId },
                timeout: options?.timeout,
            },
            ScoreListResponseHandler,
        ) as Promise<Score[]>;
    }

    // ------------------------------------------------------------------
    // Progress & Analytics
    // ------------------------------------------------------------------

    async getProgress(queueId: string, options?: { timeout?: number }): Promise<QueueProgress> {
        return this.request(
            {
                method: HttpMethod.GET,
                url: buildUrl(this._baseUrl, Routes.ANNOTATION_QUEUE_PROGRESS, { queue_id: queueId }),
                timeout: options?.timeout,
            },
            QueueProgressResponseHandler,
        ) as Promise<QueueProgress>;
    }

    async getAnalytics(queueId: string, options?: { timeout?: number }): Promise<QueueAnalytics> {
        return this.request(
            {
                method: HttpMethod.GET,
                url: buildUrl(this._baseUrl, Routes.ANNOTATION_QUEUE_ANALYTICS, { queue_id: queueId }),
                timeout: options?.timeout,
            },
            QueueAnalyticsResponseHandler,
        ) as Promise<QueueAnalytics>;
    }

    async getAgreement(queueId: string, options?: { timeout?: number }): Promise<QueueAgreement> {
        return this.request(
            {
                method: HttpMethod.GET,
                url: buildUrl(this._baseUrl, Routes.ANNOTATION_QUEUE_AGREEMENT, { queue_id: queueId }),
                timeout: options?.timeout,
            },
            QueueAgreementResponseHandler,
        ) as Promise<QueueAgreement>;
    }

    // ------------------------------------------------------------------
    // Export
    // ------------------------------------------------------------------

    async export(queueId: string, options: { format: 'csv'; status?: string; timeout?: number }): Promise<string>;
    async export(queueId: string, options?: { format?: 'json'; status?: string; timeout?: number }): Promise<Record<string, any>[]>;
    async export(
        queueId: string,
        options?: { format?: 'json' | 'csv'; status?: string; timeout?: number },
    ): Promise<string | Record<string, any>[]> {
        const fmt = options?.format ?? 'json';
        const params: Record<string, any> = { export_format: fmt };
        if (options?.status) params.status = options.status;

        const requestConfig: RequestConfig = {
            method: HttpMethod.GET,
            url: buildUrl(this._baseUrl, Routes.ANNOTATION_QUEUE_EXPORT, { queue_id: queueId }),
            params,
            timeout: options?.timeout,
        };

        if (fmt === 'csv') {
            requestConfig.responseType = 'text';
            const response = await this.request(requestConfig);
            const axiosResponse = response as { data: string };
            return axiosResponse.data;
        }

        return this.request(requestConfig, ExportJsonResponseHandler) as Promise<Record<string, any>[]>;
    }

    async exportToDataset(
        queueId: string,
        options: {
            datasetName?: string;
            datasetId?: string;
            statusFilter?: string;
            timeout?: number;
        },
    ): Promise<ExportToDatasetResponse> {
        if (options.datasetName == null && options.datasetId == null) {
            throw new SDKException('Provide either datasetName or datasetId');
        }
        if (options.datasetName != null && options.datasetId != null) {
            throw new SDKException('Provide either datasetName or datasetId, not both');
        }

        const body: Record<string, any> = {};
        if (options.datasetName != null) body.dataset_name = options.datasetName;
        if (options.datasetId != null) body.dataset_id = options.datasetId;
        if (options.statusFilter != null) body.status_filter = options.statusFilter;

        return this.request(
            {
                method: HttpMethod.POST,
                url: buildUrl(this._baseUrl, Routes.ANNOTATION_QUEUE_EXPORT_TO_DATASET, { queue_id: queueId }),
                json: body,
                timeout: options.timeout,
            },
            ExportToDatasetResponseHandler,
        ) as Promise<ExportToDatasetResponse>;
    }
}
