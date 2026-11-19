/**
 * What creating an annotation queue (POST /model-hub/annotation-queues/) needs, and what getting
 * a default queue (POST /model-hub/annotation-queues/get-or-create-default/) needs.
 *
 * Shared by `AnnotationQueue` and `FutureAGIClient.annotationQueues`. The backend facts
 * (`AnnotationQueueSerializer`, `AnnotationQueueViewSet` and the get-or-create-default request)
 * are pinned in `tests/fixtures/server-contracts/annotation-queue-create.json`; the contract tests
 * fail when either client drifts from that snapshot.
 */

import { SDKException } from '../utils/errors';
import type { QueueConfig } from './types';

/**
 * The fields the server requires on create (the snapshot's `create.required`; the contract tests
 * fail when the two differ). Both create() methods require them on the final POST.
 */
export const REQUIRED_ON_CREATE = ['name', 'label_ids'] as const;

/** Request fields the server ignores on create (read-only). They are not sent. */
export const IGNORED_ON_CREATE = ['project', 'dataset', 'agent_definition'] as const;

/** `QueueConfig` keys that `AnnotationQueue.create()` accepts but does not send. */
export const QUEUE_CREATE_IGNORED_KEYS = [
    'project',
    'dataset',
    'agentDefinition',
] as const satisfies readonly (keyof QueueConfig)[];

/** The request field `AnnotationQueue.create()` sends for each other `QueueConfig` key. */
export const QUEUE_CREATE_FIELDS = {
    name: 'name',
    labelIds: 'label_ids',
    description: 'description',
    instructions: 'instructions',
    assignmentStrategy: 'assignment_strategy',
    annotationsRequired: 'annotations_required',
    reservationTimeoutMinutes: 'reservation_timeout_minutes',
    requiresReview: 'requires_review',
    autoAssign: 'auto_assign',
    annotatorIds: 'annotator_ids',
    annotatorRoles: 'annotator_roles',
} as const satisfies {
    readonly [K in Exclude<keyof QueueConfig, (typeof QUEUE_CREATE_IGNORED_KEYS)[number]>]-?: string;
};

/** The get-or-create-default field for each ignored create field. Exactly one is given per call. */
export const DEFAULT_QUEUE_SCOPE_IDS = {
    project: 'project_id',
    dataset: 'dataset_id',
    agent_definition: 'agent_definition_id',
} as const satisfies { readonly [K in (typeof IGNORED_ON_CREATE)[number]]: string };

/** The `AnnotationQueue.getOrCreateDefault()` key for each get-or-create-default field. */
export const QUEUE_DEFAULT_SCOPE_KEYS = {
    projectId: 'project_id',
    datasetId: 'dataset_id',
    agentDefinitionId: 'agent_definition_id',
} as const;

/** The get-or-create-default method of each client, as a scope-id refusal names it. */
export const FACADE_DEFAULT_QUEUE_METHOD = 'annotationQueues.getOrCreateDefault';
export const QUEUE_CLIENT_DEFAULT_QUEUE_METHOD = 'AnnotationQueue.getOrCreateDefault';

/**
 * The facade's get-or-create-default keys: the request fields, each mapped to itself. A facade
 * create body may not carry them (it is the wire format).
 */
export const FACADE_DEFAULT_SCOPE_KEYS: Readonly<Record<string, string>> = Object.fromEntries(
    Object.values(DEFAULT_QUEUE_SCOPE_IDS).map((field) => [field, field]),
);
/**
 * Keys an `AnnotationQueue.create()` config may not carry, mapped to the `getOrCreateDefault` key
 * to use instead: the camelCase keys, and the wire spelling, which would be dropped silently.
 */
export const QUEUE_CLIENT_REFUSED_SCOPE_KEYS: Readonly<Record<string, string>> = {
    ...Object.fromEntries(Object.keys(QUEUE_DEFAULT_SCOPE_KEYS).map((key) => [key, key])),
    ...Object.fromEntries(
        Object.entries(QUEUE_DEFAULT_SCOPE_KEYS).map(([key, field]) => [field, key]),
    ),
};

/** What each client's create() points at instead of the ignored fields. */
export const FACADE_DEFAULT_QUEUE_CALL =
    'annotationQueues.getOrCreateDefault({ project_id }), or dataset_id or agent_definition_id';
export const QUEUE_CLIENT_DEFAULT_QUEUE_CALL =
    'AnnotationQueue.getOrCreateDefault({ projectId }), or datasetId or agentDefinitionId';

/** No truthful default: missing/ambiguous scope or no labels on its default queue. */
export class DefaultQueueLabelError extends SDKException {
    constructor(message: string) {
        super(message);
        this.name = 'DefaultQueueLabelError';
    }
}

/** Reuse the client's getOrCreateDefault method; never manufacture or guess a label. */
export async function withDefaultLabels<T extends object>(
    body: T,
    labelKey: string,
    scopeKeys: Readonly<Record<string, string>>,
    getDefault: (scope: Record<string, string>) => Promise<unknown>,
    caller: string,
): Promise<T> {
    const out: Record<string, any> = { ...body };
    if (out[labelKey] !== undefined || out.name == null) return out as T;
    const message = `${caller}: ${labelKey} will be required; pass them explicitly. For ` +
        "compatibility, the given scope is used only to obtain its default queue's labels; " +
        'the new queue is not scoped to that entity.';
    const proc = (globalThis as { process?: { emitWarning?: (...args: unknown[]) => void } }).process;
    if (proc && typeof proc.emitWarning === 'function') {
        proc.emitWarning(message, { type: 'DeprecationWarning', code: 'FUTUREAGI_QUEUE_CREATE_DEFAULT_LABELS' });
    } else if (typeof console !== 'undefined') {
        console.warn(`DeprecationWarning: ${message}`);
    }
    const given = Object.keys(scopeKeys).filter((key) => out[key] != null);
    if (given.length !== 1) {
        throw new DefaultQueueLabelError(
            `${caller}: needs ${labelKey} or exactly one of ${Object.keys(scopeKeys).join(', ')} ` +
            "to resolve a default queue's labels",
        );
    }
    const result: any = await getDefault({ [scopeKeys[given[0]]]: out[given[0]] });
    const labels = (result?.result ?? result)?.labels;
    if (!Array.isArray(labels) || labels.length === 0) {
        throw new DefaultQueueLabelError(`${caller}: the default queue has no labels; pass ${labelKey} explicitly`);
    }
    if (labels.some((label: any) => !label || typeof label.id !== 'string' || !label.id)) {
        throw new DefaultQueueLabelError(`${caller}: the default queue returned invalid label ids; pass ${labelKey} explicitly`);
    }
    out[labelKey] = labels.map((label: any) => label.id);
    // This call's single warning also explains why the scope keys are not sent.
    for (const key of Object.keys(scopeKeys)) delete out[key];
    return out as T;
}

const DEPRECATION_CODE = 'FUTUREAGI_QUEUE_CREATE_IGNORED_FIELDS';
const warnedCallers = new Set<string>();

export function ignoredOnCreateMessage(caller: string, names: string, instead: string): string {
    return (
        `${caller}: ${names} are ignored by the server (they are read-only when a queue is ` +
        'created), so they are not sent. They remain accepted for compatibility. A ' +
        'create never scopes a queue; for the default queue of a project, dataset or agent ' +
        `definition, call ${instead}.`
    );
}

/** One deprecation warning per caller per process (Node's `DeprecationWarning`, else console). */
export function warnIgnoredOnCreate(caller: string, names: string, instead: string): void {
    if (warnedCallers.has(caller)) return;
    warnedCallers.add(caller);
    const message = ignoredOnCreateMessage(caller, names, instead);
    const proc = (globalThis as { process?: { emitWarning?: (...args: unknown[]) => void } })
        .process;
    if (proc && typeof proc.emitWarning === 'function') {
        proc.emitWarning(message, { type: 'DeprecationWarning', code: DEPRECATION_CODE });
    } else if (typeof console !== 'undefined') {
        console.warn(`DeprecationWarning: ${message}`);
    }
}

/** `value` as a list of id strings; throws `SDKException` otherwise. */
export function idList(value: unknown, caller: string, argument: string): string[] {
    if (!Array.isArray(value) || value.some((id) => typeof id !== 'string' || id === '')) {
        throw new SDKException(`${caller}: ${argument} must be an array of non-empty id strings`);
    }
    return [...value];
}

/**
 * Throws `SDKException` naming every key of `keys` whose value is missing (`null` / `undefined`).
 * The label ids get their own rule afterwards (`labelIdList`).
 */
export function requireKeys(values: object, keys: readonly string[], caller: string): void {
    const record = values as Record<string, unknown>;
    const missing = keys.filter((key) => record[key] == null);
    if (missing.length === 0) return;
    const one = missing.length === 1;
    throw new SDKException(
        `${caller}: ${missing.join(' and ')} ${one ? 'is' : 'are'} required; the server ` +
            `refuses a queue without ${one ? 'it' : 'them'}`,
    );
}

/** The `AnnotationQueue.create()` config keys of the required request fields. */
export const QUEUE_CONFIG_REQUIRED_KEYS = (
    Object.keys(QUEUE_CREATE_FIELDS) as (keyof typeof QUEUE_CREATE_FIELDS)[]
).filter((key) => (REQUIRED_ON_CREATE as readonly string[]).includes(QUEUE_CREATE_FIELDS[key]));

/** `idList` for the label ids, which need at least one id. */
export function labelIdList(value: unknown, caller: string, argument: string): string[] {
    if (value == null) {
        throw new SDKException(
            `${caller}: ${argument} is required: at least one annotation label id; the server ` +
                'refuses a queue without labels',
        );
    }
    const ids = idList(value, caller, argument);
    if (ids.length === 0) {
        throw new SDKException(
            `${caller}: ${argument} needs at least one annotation label id; the server refuses ` +
                'a queue without labels',
        );
    }
    return ids;
}

/**
 * Refuses a project, dataset or agent definition id in a create body or config: a create has no
 * such field, and the server never applies it to the queue it creates (its serializer reads it
 * only to scope the duplicate-name check, `validate_name`, and the view saves none of them; the
 * snapshot pins both). So the queue would belong to nothing while the caller believes it is
 * scoped. `keys` maps each refused key to the key `defaultCall` takes. Keys holding `null` /
 * `undefined` are allowed (and never sent).
 */
export function refuseScopeIds(
    body: object,
    caller: string,
    keys: Readonly<Record<string, string>>,
    defaultCall: string,
): void {
    const values = body as Record<string, unknown>;
    const passed = Object.keys(keys).filter((key) => values[key] != null);
    if (passed.length === 0) return;
    const call =
        passed.length === 1
            ? `${defaultCall}({ ${keys[passed[0]]}: ${JSON.stringify(values[passed[0]])} })`
            : `${defaultCall}() with one of them`;
    const it = passed.length === 1 ? 'it' : 'them';
    throw new SDKException(
        `${caller}: ${passed.join(' and ')} cannot be set on a new queue: a create has no such ` +
            `field, and the server never applies ${it} to the queue (it only uses ${it} to ` +
            'scope its duplicate-name check), so the queue would belong to no project, dataset ' +
            'or agent definition. For the default queue of a project, dataset or agent ' +
            `definition, call ${call}.`,
    );
}

/**
 * A request body for the queue create: scope ids refused, required fields present, label ids
 * checked, ignored fields dropped.
 */
export function createBody<T extends object>(
    body: T,
    caller: string,
    instead: string,
    defaultCall: string,
): Omit<T, (typeof IGNORED_ON_CREATE)[number]> {
    const out: Record<string, unknown> = { ...(body as Record<string, unknown>) };
    refuseScopeIds(out, caller, FACADE_DEFAULT_SCOPE_KEYS, defaultCall);
    for (const key of Object.keys(FACADE_DEFAULT_SCOPE_KEYS)) delete out[key];
    requireKeys(out, REQUIRED_ON_CREATE, caller);
    out.label_ids = labelIdList(out.label_ids, caller, 'label_ids');
    let passed = false;
    for (const key of IGNORED_ON_CREATE) {
        if (out[key] != null) passed = true;
        delete out[key];
    }
    if (passed) warnIgnoredOnCreate(caller, 'project, dataset and agent_definition', instead);
    return out as Omit<T, (typeof IGNORED_ON_CREATE)[number]>;
}

/**
 * The get-or-create-default request body: exactly one id from `scope`. `keys` maps each key
 * the caller accepts to its request field. Throws `SDKException` before any request otherwise.
 */
export function defaultQueueBody(
    scope: object,
    caller: string,
    keys: Readonly<Record<string, string>>,
): Record<string, string> {
    const values = (scope ?? {}) as Record<string, unknown>;
    const given = Object.keys(keys).filter((key) => values[key] != null);
    if (given.length !== 1) {
        throw new SDKException(
            `${caller}: give exactly one of ${Object.keys(keys).join(', ')} ` +
                `(got ${given.length ? given.join(', ') : 'none'})`,
        );
    }
    const key = given[0];
    const value = values[key];
    if (typeof value !== 'string' || value === '') {
        throw new SDKException(`${caller}: ${key} must be a non-empty id string`);
    }
    return { [keys[key]]: value };
}
