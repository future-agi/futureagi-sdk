import { legacyFields, queueFields, itemFields, scoreFields, progressFields, analyticsFields, agreementFields, exportFields } from '../_compat-fields';
/**
 * AnnotationQueue – SDK client for managing annotation queues, items, scores, and analytics.
 *
 * @example
 * ```ts
 * import { AnnotationQueue } from '@future-agi/sdk';
 *
 * const client = new AnnotationQueue({ fiApiKey: '...', fiSecretKey: '...' });
 *
 * const label = await client.createLabel({ name: 'Helpful', type: 'thumbs_up_down' });
 * const queue = await client.create({ name: 'Review Queue', labelIds: [label.id] });
 * await client.activate(queue.id);
 * await client.addItems(queue.id, [{ sourceType: 'trace', sourceId: 'abc' }]);
 * const progress = await client.getProgress(queue.id);
 * ```
 */

import { APIKeyAuth, ResponseHandler } from '../api/auth';
import type { APIKeyAuthConfig } from '../api/auth';
import { HttpMethod } from '../api/types';
import type { RequestConfig } from '../api/types';
import { SDKException } from '../utils/errors';
import { Routes } from '../utils/routes';
import type { AnnotationLabel } from '../annotations/types';
import type {
    AddItemsResponse,
    AnnotationPayload,
    AssignmentStrategy,
    DefaultQueue,
    DefaultQueueScope,
    ExportToDatasetResponse,
    ImportAnnotationsResponse,
    LabelType,
    QueueAgreement,
    QueueAnalytics,
    QueueConfig,
    QueueDetail,
    QueueItem,
    QueueItemSource,
    QueueProgressResult,
    Score,
    ScoreInput,
    ScoreValue,
} from './types';
import { VALID_SOURCE_TYPES, VALID_ASSIGNMENT_STRATEGIES, VALID_LABEL_TYPES } from './types';
import {
    QUEUE_CLIENT_DEFAULT_QUEUE_CALL,
    QUEUE_CLIENT_DEFAULT_QUEUE_METHOD,
    QUEUE_CLIENT_REFUSED_SCOPE_KEYS,
    QUEUE_CREATE_FIELDS,
    QUEUE_CONFIG_REQUIRED_KEYS,
    QUEUE_CREATE_IGNORED_KEYS,
    QUEUE_DEFAULT_SCOPE_KEYS,
    defaultQueueBody,
    idList,
    labelIdList,
    refuseScopeIds,
    requireKeys,
    warnIgnoredOnCreate,
    withDefaultLabels,
} from './create-body';

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
        return legacyFields(unwrap(response.data), queueFields);
    }
}

class DefaultQueueResponseHandler extends ResponseHandler<DefaultQueue> {
    static _parseSuccess(response: ApiResponse): DefaultQueue {
        const data = unwrap(response.data);
        return { ...data, queue: legacyFields(data.queue, queueFields) };
    }
}

class QueueListResponseHandler extends ResponseHandler<QueueDetail[]> {
    static _parseSuccess(response: ApiResponse): QueueDetail[] {
        const data = unwrap(response.data);
        const items = Array.isArray(data) ? data : (data?.results ?? data?.table ?? []);
        return items.map((item: any) => legacyFields(item, queueFields));
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
        const items = Array.isArray(data) ? data : (data?.results ?? []);
        return items.map((item: any) => legacyFields(item, itemFields));
    }
}

class ScoreListResponseHandler extends ResponseHandler<Score[]> {
    static _parseSuccess(response: ApiResponse): Score[] {
        const data = unwrap(response.data);
        const items = Array.isArray(data) ? data : (data?.results ?? []);
        return items.map((item: any) => legacyFields(item, scoreFields));
    }
}

class ScoreResponseHandler extends ResponseHandler<Score> {
    static _parseSuccess(response: ApiResponse): Score {
        return legacyFields(unwrap(response.data), scoreFields);
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

class QueueProgressResponseHandler extends ResponseHandler<QueueProgressResult> {
    static _parseSuccess(response: ApiResponse): QueueProgressResult {
        return legacyFields(unwrap(response.data), progressFields);
    }
}

class QueueAnalyticsResponseHandler extends ResponseHandler<QueueAnalytics> {
    static _parseSuccess(response: ApiResponse): QueueAnalytics {
        return legacyFields(unwrap(response.data), analyticsFields);
    }
}

class QueueAgreementResponseHandler extends ResponseHandler<QueueAgreement> {
    static _parseSuccess(response: ApiResponse): QueueAgreement {
        return legacyFields(unwrap(response.data), agreementFields);
    }
}

class ExportToDatasetResponseHandler extends ResponseHandler<ExportToDatasetResponse> {
    static _parseSuccess(response: ApiResponse): ExportToDatasetResponse {
        return legacyFields(unwrap(response.data), exportFields);
    }
}

class ExportJsonResponseHandler extends ResponseHandler<Record<string, any>[]> {
    static _parseSuccess(response: ApiResponse): Record<string, any>[] {
        return unwrap(response.data);
    }
}

class LabelResponseHandler extends ResponseHandler<AnnotationLabel> {
    static _parseSuccess(response: ApiResponse): AnnotationLabel {
        const data = unwrap(response.data);
        return data?.data ?? data;
    }
}

class LabelListResponseHandler extends ResponseHandler<AnnotationLabel[]> {
    static _parseSuccess(response: ApiResponse): AnnotationLabel[] {
        const data = unwrap(response.data);
        if (Array.isArray(data)) return data;
        return data?.results ?? data?.data ?? [];
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

    /**
     * Create a queue. Omitting labelIds reuses getOrCreateDefault for exactly one of project,
     * dataset or agentDefinition, with one DeprecationWarning saying labelIds will be required.
     * The lookup can create or restore the default queue even if the label check then fails;
     * the new queue remains unscoped. Throws DefaultQueueLabelError (an SDKException, importable
     * from `@future-agi/sdk`) if no single scope or no usable labels exist on its default queue.
     * Explicit labelIds avoids the lookup and warning.
     */
    async create(config: QueueConfig): Promise<QueueDetail> {
        if (config.assignmentStrategy != null &&
            !(VALID_ASSIGNMENT_STRATEGIES as readonly string[]).includes(config.assignmentStrategy)) {
            throw new SDKException(
                `Invalid assignmentStrategy '${config.assignmentStrategy}'. Must be one of: ${VALID_ASSIGNMENT_STRATEGIES.join(', ')}`,
            );
        }

        const caller = 'AnnotationQueue.create()';
        refuseScopeIds(
            config,
            caller,
            QUEUE_CLIENT_REFUSED_SCOPE_KEYS,
            QUEUE_CLIENT_DEFAULT_QUEUE_METHOD,
        );
        config = await withDefaultLabels(
            config, 'labelIds',
            { project: 'projectId', dataset: 'datasetId', agentDefinition: 'agentDefinitionId' },
            (scope) => this.getOrCreateDefault(scope as unknown as DefaultQueueScope), caller,
        );
        requireKeys(config, QUEUE_CONFIG_REQUIRED_KEYS, caller);
        const body: Record<string, any> = {};
        for (const key of Object.keys(QUEUE_CREATE_FIELDS) as (keyof typeof QUEUE_CREATE_FIELDS)[]) {
            if (config[key] != null) body[QUEUE_CREATE_FIELDS[key]] = config[key];
        }
        body.label_ids = labelIdList(config.labelIds, caller, 'labelIds');
        if (config.annotatorIds != null) {
            body.annotator_ids = idList(config.annotatorIds, caller, 'annotatorIds');
        }
        if (QUEUE_CREATE_IGNORED_KEYS.some((key) => config[key] != null)) {
            warnIgnoredOnCreate(
                caller,
                'project, dataset and agentDefinition',
                QUEUE_CLIENT_DEFAULT_QUEUE_CALL,
            );
        }

        return this.request(
            {
                method: HttpMethod.POST,
                url: buildUrl(this._baseUrl, Routes.ANNOTATION_QUEUES),
                json: body,
            },
            QueueResponseHandler,
        ) as Promise<QueueDetail>;
    }

    /**
     * Get the default queue of a project, dataset or agent definition: give exactly one id.
     *
     * The server returns the active default queue, restores an archived one, or creates it
     * (`action` is `'fetched'`, `'restored'` or `'created'`), with its labels. Default queues are
     * open to every member of the organization. This is how a queue belongs to a project, dataset
     * or agent definition: `create` never scopes one. Throws `SDKException` before any request
     * when not exactly one id is given.
     */
    async getOrCreateDefault(
        scope: DefaultQueueScope,
        options?: { timeout?: number },
    ): Promise<DefaultQueue> {
        const body = defaultQueueBody(
            scope,
            'AnnotationQueue.getOrCreateDefault()',
            QUEUE_DEFAULT_SCOPE_KEYS,
        );
        return this.request(
            {
                method: HttpMethod.POST,
                url: buildUrl(this._baseUrl, Routes.ANNOTATION_QUEUE_GET_OR_CREATE_DEFAULT),
                json: body,
                timeout: options?.timeout,
            },
            DefaultQueueResponseHandler,
        ) as Promise<DefaultQueue>;
    }

    /** List queues with a 1-based page; published pageSize (default 20) is sent as limit. */
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
            limit: options?.pageSize ?? 20,
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
    // Name → ID resolvers
    // ------------------------------------------------------------------

    private async _getQueueIdFromName(queueName: string): Promise<string> {
        const queues = await this.list({ search: queueName });
        const matches = queues.filter((q) => q.name.toLowerCase() === queueName.toLowerCase());
        if (matches.length === 0) {
            throw new SDKException(`Queue with name '${queueName}' not found.`);
        }
        if (matches.length > 1) {
            throw new SDKException(
                `Multiple queues found with name '${queueName}': ${matches.map((q) => q.id).join(', ')}. Use queueId instead.`,
            );
        }
        return matches[0].id;
    }

    private async _getLabelIdFromName(labelName: string): Promise<string> {
        const labels = await this.listLabels();
        const matches = labels.filter((l) => l.name.toLowerCase() === labelName.toLowerCase());
        if (matches.length === 0) {
            throw new SDKException(`Label with name '${labelName}' not found.`);
        }
        if (matches.length > 1) {
            throw new SDKException(
                `Multiple labels found with name '${labelName}': ${matches.map((l) => `${l.id} (${l.type})`).join(', ')}. Use labelId instead.`,
            );
        }
        return matches[0].id;
    }

    // ------------------------------------------------------------------
    // Labels (CRUD)
    // ------------------------------------------------------------------

    async createLabel(options: {
        name: string;
        type: LabelType;
        settings?: Record<string, any>;
        description?: string;
        project?: string;
        timeout?: number;
    }): Promise<AnnotationLabel> {
        if (!(VALID_LABEL_TYPES as readonly string[]).includes(options.type)) {
            throw new SDKException(
                `Invalid label type '${options.type}'. Must be one of: ${VALID_LABEL_TYPES.join(', ')}`,
            );
        }

        const body: Record<string, any> = { name: options.name, type: options.type };
        if (options.settings != null) body.settings = options.settings;
        if (options.description != null) body.description = options.description;
        if (options.project != null) body.project = options.project;

        return this.request(
            {
                method: HttpMethod.POST,
                url: buildUrl(this._baseUrl, Routes.ANNOTATIONS_LABELS),
                json: body,
                timeout: options.timeout,
            },
            LabelResponseHandler,
        ) as Promise<AnnotationLabel>;
    }

    async listLabels(options?: {
        projectId?: string;
        timeout?: number;
    }): Promise<AnnotationLabel[]> {
        const params: Record<string, any> = {};
        if (options?.projectId != null) params.project_id = options.projectId;

        return this.request(
            {
                method: HttpMethod.GET,
                url: buildUrl(this._baseUrl, Routes.ANNOTATIONS_LABELS),
                params,
                timeout: options?.timeout,
            },
            LabelListResponseHandler,
        ) as Promise<AnnotationLabel[]>;
    }

    async getLabel(options: {
        labelId?: string;
        labelName?: string;
        timeout?: number;
    }): Promise<AnnotationLabel> {
        if (!options.labelId && !options.labelName) {
            throw new SDKException('Provide either labelId or labelName');
        }
        const resolvedId = options.labelId ?? await this._getLabelIdFromName(options.labelName!);

        return this.request(
            {
                method: HttpMethod.GET,
                url: buildUrl(this._baseUrl, Routes.ANNOTATIONS_LABELS_DETAIL, { label_id: resolvedId }),
                timeout: options.timeout,
            },
            LabelResponseHandler,
        ) as Promise<AnnotationLabel>;
    }

    async deleteLabel(options: {
        labelId?: string;
        labelName?: string;
        timeout?: number;
    }): Promise<Record<string, any>> {
        if (!options.labelId && !options.labelName) {
            throw new SDKException('Provide either labelId or labelName');
        }
        const resolvedId = options.labelId ?? await this._getLabelIdFromName(options.labelName!);

        return this.request(
            {
                method: HttpMethod.DELETE,
                url: buildUrl(this._baseUrl, Routes.ANNOTATIONS_LABELS_DETAIL, { label_id: resolvedId }),
                timeout: options.timeout,
            },
            DictResponseHandler,
        ) as Promise<Record<string, any>>;
    }

    // ------------------------------------------------------------------
    // Labels (queue attachment)
    // ------------------------------------------------------------------

    /** Attach a label using published positional ids or the additive named-options form. */
    async addLabel(queueId: string, labelId: string, options?: { timeout?: number }): Promise<Record<string, any>>;
    async addLabel(options: { queueId?: string; labelId?: string; queueName?: string; labelName?: string; timeout?: number }): Promise<Record<string, any>>;
    async addLabel(input: string | { queueId?: string; labelId?: string; queueName?: string; labelName?: string; timeout?: number }, labelId?: string, legacyOptions?: { timeout?: number }): Promise<Record<string, any>> {
        const options = typeof input === 'string' ? { queueId: input, labelId, timeout: legacyOptions?.timeout } : input;
        if (!options.queueId && !options.queueName) {
            throw new SDKException('Provide either queueId or queueName');
        }
        if (!options.labelId && !options.labelName) {
            throw new SDKException('Provide either labelId or labelName');
        }
        const resolvedQueueId = options.queueId ?? await this._getQueueIdFromName(options.queueName!);
        const resolvedLabelId = options.labelId ?? await this._getLabelIdFromName(options.labelName!);

        return this.request(
            {
                method: HttpMethod.POST,
                url: buildUrl(this._baseUrl, Routes.ANNOTATION_QUEUE_ADD_LABEL, { queue_id: resolvedQueueId }),
                json: { label_id: resolvedLabelId },
                timeout: options.timeout,
            },
            DictResponseHandler,
        ) as Promise<Record<string, any>>;
    }

    /** Detach a label using published positional ids or the additive named-options form. */
    async removeLabel(queueId: string, labelId: string, options?: { timeout?: number }): Promise<Record<string, any>>;
    async removeLabel(options: { queueId?: string; labelId?: string; queueName?: string; labelName?: string; timeout?: number }): Promise<Record<string, any>>;
    async removeLabel(input: string | { queueId?: string; labelId?: string; queueName?: string; labelName?: string; timeout?: number }, labelId?: string, legacyOptions?: { timeout?: number }): Promise<Record<string, any>> {
        const options = typeof input === 'string' ? { queueId: input, labelId, timeout: legacyOptions?.timeout } : input;
        if (!options.queueId && !options.queueName) {
            throw new SDKException('Provide either queueId or queueName');
        }
        if (!options.labelId && !options.labelName) {
            throw new SDKException('Provide either labelId or labelName');
        }
        const resolvedQueueId = options.queueId ?? await this._getQueueIdFromName(options.queueName!);
        const resolvedLabelId = options.labelId ?? await this._getLabelIdFromName(options.labelName!);

        return this.request(
            {
                method: HttpMethod.POST,
                url: buildUrl(this._baseUrl, Routes.ANNOTATION_QUEUE_REMOVE_LABEL, { queue_id: resolvedQueueId }),
                json: { label_id: resolvedLabelId },
                timeout: options.timeout,
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

    /** List items with a 1-based page; published pageSize (default 50) is sent as limit. */
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
            limit: options?.pageSize ?? 50,
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

    /** Progress includes both in_progress and deprecated inProgress (warning once on use). */
    async getProgress(queueId: string, options?: { timeout?: number }): Promise<QueueProgressResult> {
        return this.request(
            {
                method: HttpMethod.GET,
                url: buildUrl(this._baseUrl, Routes.ANNOTATION_QUEUE_PROGRESS, { queue_id: queueId }),
                timeout: options?.timeout,
            },
            QueueProgressResponseHandler,
        ) as Promise<QueueProgressResult>;
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
