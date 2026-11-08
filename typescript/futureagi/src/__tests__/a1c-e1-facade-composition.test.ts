/** Real composed facade + generated serializer, with local fetch only.
 * These controls do not prove backend acceptance or installed-package readiness.
 */
import { FutureAGIClient, type AnnotationQueuesClient, type CreateAnnotationQueueBody } from '../futureagi-client';
import type { CatalogPageResult, SuccessEnvelope } from '../catalog-response-types';
import type { AnnotationQueue, QueueDefaultResponse } from '../generated/openapi/types.gen';
import { DefaultQueueLabelError, SDKException } from '../index';

// Compile-time equality, not assignability to any or a metadata-wrapper union.
type Equal<A, B> = (<T>() => T extends A ? 1 : 2) extends
    (<T>() => T extends B ? 1 : 2) ? true : false;
type Assert<T extends true> = T;
type CreateBodyReturn = Assert<Equal<Awaited<ReturnType<AnnotationQueuesClient['create']>>, AnnotationQueue>>;
type DefaultEnvelope = Assert<Equal<Awaited<ReturnType<AnnotationQueuesClient['getOrCreateDefault']>>, QueueDefaultResponse>>;
type QueuePage = Assert<Equal<Awaited<ReturnType<AnnotationQueuesClient['list']>>, CatalogPageResult<AnnotationQueue>>>;
type ArchiveEnvelope = Assert<Equal<Awaited<ReturnType<AnnotationQueuesClient['archive']>>,
    SuccessEnvelope<{ deleted: boolean; archived: boolean; queue_id: string }>>>;
type CreateInput = Assert<Equal<Parameters<AnnotationQueuesClient['create']>, [body: CreateAnnotationQueueBody]>>;

const BASE = 'http://composition.test';
const SCOPE = '22222222-2222-4222-8222-222222222222';
const LABEL = '11111111-1111-4111-8111-111111111111';
const QUEUE = '33333333-3333-4333-8333-333333333333';
const USER = '44444444-4444-4444-8444-444444444444';
const CREATE_PATH = '/model-hub/annotation-queues/';
const DEFAULT_PATH = `${CREATE_PATH}get-or-create-default/`;
const actions = ['created', 'restored', 'fetched'] as const;
const scopes = ['project', 'dataset', 'agent_definition'] as const;

function defaultResponse(action: typeof actions[number], labels = true): QueueDefaultResponse {
    return { status: true, result: {
        queue: { id: QUEUE, name: 'Default', status: 'active', is_default: true },
        labels: labels ? [{ id: LABEL, name: 'Helpful', type: 'thumbs_up_down', settings: {},
            allow_notes: false, required: false, order: 0 }] : [],
        created: action === 'created', action,
    } };
}

function facade(responses: Array<[number, unknown]>) {
    const sent: Array<{ method: string; path: string; query: string; body: unknown }> = [];
    const root = new FutureAGIClient({ apiKey: 'test', secretKey: 'test', baseUrl: BASE, retries: 0,
        fetch: async (input) => {
            const request = input as Request;
            const url = new URL(request.url);
            const text = await request.text();
            sent.push({ method: request.method, path: url.pathname, query: url.search,
                body: text ? JSON.parse(text) : undefined });
            const reply = responses.shift();
            if (!reply) throw new Error('Unexpected composed-facade request');
            return new Response(JSON.stringify(reply[1]), {
                status: reply[0], headers: { 'Content-Type': 'application/json' },
            });
        },
    });
    return { root, sent };
}

let emit: jest.SpyInstance;
beforeEach(() => { emit = jest.spyOn(process, 'emitWarning').mockImplementation(() => undefined); });
afterEach(() => { emit.mockRestore(); });

it.each(actions.flatMap(action => scopes.map(scope => [action, scope] as const)))(
    'composed %s default lookup for %s retains data-only create and one warning', async (action, scope) => {
        const created: AnnotationQueue = { id: QUEUE, name: 'Named', auto_assign: false };
        const { root, sent } = facade([[200, defaultResponse(action)], [201, created]]);
        const body: CreateAnnotationQueueBody = { name: 'Named', [scope]: SCOPE, auto_assign: false,
            annotator_ids: [USER], annotator_roles: { [USER]: ['reviewer'] } };
        const original = JSON.stringify(body);
        const result = await root.annotationQueues.create(body);
        expect(result).toEqual(created);
        expect(JSON.stringify(body)).toBe(original);
        expect(emit).toHaveBeenCalledTimes(1);
        expect(emit.mock.calls[0][0]).toContain('label_ids will be required');
        expect(emit.mock.calls[0][0]).toContain('not scoped');
        expect(emit.mock.calls[0][1]).toMatchObject({ type: 'DeprecationWarning', code: 'FUTUREAGI_QUEUE_CREATE_DEFAULT_LABELS' });
        expect(sent).toEqual([
            { method: 'POST', path: DEFAULT_PATH, query: '', body: { [`${scope}_id`]: SCOPE } },
            { method: 'POST', path: CREATE_PATH, query: '', body: { name: 'Named', label_ids: [LABEL],
                auto_assign: false, annotator_ids: [USER], annotator_roles: { [USER]: ['reviewer'] } } },
        ]);
    },
);

it.each(actions)('composed direct %s default retains QueueDefaultResponse envelope', async (action) => {
    const response = defaultResponse(action);
    const { root, sent } = facade([[200, response]]);
    expect(await root.annotationQueues.getOrCreateDefault({ project_id: SCOPE })).toEqual(response);
    expect(sent).toEqual([{ method: 'POST', path: DEFAULT_PATH, query: '', body: { project_id: SCOPE } }]);
    expect(emit).not.toHaveBeenCalled();
});

it.each(actions)('composed empty %s default keeps lookup side effect but never creates', async (action) => {
    const { root, sent } = facade([[200, defaultResponse(action, false)]]);
    const result = root.annotationQueues.create({ name: 'Named', project: SCOPE });
    await expect(result).rejects.toBeInstanceOf(DefaultQueueLabelError);
    await expect(result).rejects.toThrow('no labels');
    expect(emit).toHaveBeenCalledTimes(1);
    expect(sent).toEqual([{ method: 'POST', path: DEFAULT_PATH, query: '', body: { project_id: SCOPE } }]);
});

it.each([
    [{ name: 'Named', label_ids: null, project: SCOPE }, false],
    [{ name: 'Named', label_ids: [], project: SCOPE }, false],
    [{ label_ids: [LABEL], project: SCOPE }, false],
    [{ project: SCOPE }, false],
    [{ name: 'Named' }, true],
    [{ name: 'Named', project: null }, true],
    [{ name: 'Named', project: '' }, true],
    [{ name: 'Named', project: SCOPE, dataset: SCOPE }, true],
] as const)('composed invalid create %j never requests', async (body, warning) => {
    const { root, sent } = facade([]);
    // Invalid JS callers exercise runtime refusal, not a relaxation of the public type.
    await expect(root.annotationQueues.create(body as unknown as CreateAnnotationQueueBody)).rejects.toBeInstanceOf(SDKException);
    expect(sent).toEqual([]);
    expect(emit).toHaveBeenCalledTimes(Number(warning));
});

it.each(['project_id', 'dataset_id', 'agent_definition_id'].flatMap(key => [false, true].map(explicit => [key, explicit] as const)))(
    'composed scope-id %s with explicit=%s is refused before lookup or warning', async (key, explicit) => {
        const { root, sent } = facade([]);
        const body = { name: 'Named', project: SCOPE, [key]: SCOPE, ...(explicit ? { label_ids: [LABEL] } : {}) };
        await expect(root.annotationQueues.create(body)).rejects.toThrow('getOrCreateDefault');
        expect(sent).toEqual([]);
        expect(emit).not.toHaveBeenCalled();
    },
);

it('composed explicit labels skip lookup and strip null scope ids', async () => {
    const created = { id: QUEUE, name: 'Named' };
    const { root, sent } = facade([[201, created]]);
    const body = { name: 'Named', label_ids: [LABEL], project_id: null, dataset_id: null, agent_definition_id: null };
    expect(await root.annotationQueues.create(body)).toEqual(created);
    expect(emit).not.toHaveBeenCalled();
    expect(sent).toEqual([{ method: 'POST', path: CREATE_PATH, query: '', body: { name: 'Named', label_ids: [LABEL] } }]);
});

it('composed explicit scope warns once per caller without lookup', async () => {
    const { root, sent } = facade([[201, { name: 'Named' }], [201, { name: 'Named' }]]);
    for (let i = 0; i < 2; i++) await root.annotationQueues.create({ name: 'Named', label_ids: [LABEL], project: SCOPE });
    expect(emit).toHaveBeenCalledTimes(1);
    expect(emit.mock.calls[0][1]).toMatchObject({ code: 'FUTUREAGI_QUEUE_CREATE_IGNORED_FIELDS' });
    expect(sent).toEqual(Array.from({ length: 2 }, () => ({ method: 'POST', path: CREATE_PATH,
        query: '', body: { name: 'Named', label_ids: [LABEL] } })));
});

it('composed facade retains A1 page queries A2 envelopes and E1 withdrawal', async () => {
    const page = { count: 0, next: null, previous: null, results: [], total_pages: 0, current_page: 2 };
    const archive = { status: true, result: { deleted: false, archived: true, queue_id: QUEUE } };
    const { root, sent } = facade([[200, page], [200, archive]]);
    expect(await root.annotationQueues.list({ page: 2, page_size: 7, limit: 5 })).toEqual(page);
    expect(await root.annotationQueues.archive(QUEUE)).toEqual(archive);
    expect(Object.fromEntries(new URLSearchParams(sent[0].query))).toEqual({ page: '2', page_size: '7', limit: '5' });
    expect(sent[0].method).toBe('GET');
    expect(sent[0].path).toBe(CREATE_PATH);
    expect(root).not.toHaveProperty('simulations');
    expect(root.environments).toBeDefined();
});
