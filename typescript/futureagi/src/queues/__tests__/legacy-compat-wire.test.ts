/** 0.1.2 compatibility; actual Axios/fetch serialization with local transports only.
 * Paging audit: see python/tests/test_legacy_compat_wire.py for the FA file:line table.
 * TS twins: AnnotationQueue.list(page=1,pageSize=20), listItems(page=1,pageSize=50)
 * translate only pageSize -> limit. Annotation.listProjects(pageNumber=0,pageSize=20),
 * Dataset.getColumnId/downloadDataset(page_size,current_page_index=0) retain their names.
 * KnowledgeBase.listKbs and Prompt.listTemplates/listTemplateVersions have no paging inputs.
 * No EvalTemplateManager surface exists under src/ in the published TS 0.1.2 package.
 */
import axios from 'axios';
import { AnnotationQueue } from '../client';
import type { QueueConfig } from '../types';
import { Annotation } from '../../annotations/annotation';
import { Dataset } from '../../datasets/dataset';
import { FutureAGIClient, type CreateAnnotationQueueBody } from '../../futureagi-client';
// Consumer-facing import: ts-jest/typecheck must reject a missing root export.
import { DefaultQueueLabelError, SDKException } from '../../index';
import { DefaultQueueLabelError as InternalDefaultQueueLabelError } from '../create-body';

it('exports the same default-label error constructor from the package root', () => {
    expect(DefaultQueueLabelError).toBe(InternalDefaultQueueLabelError);
    const error: DefaultQueueLabelError = new DefaultQueueLabelError('No usable labels');
    expect(error).toBeInstanceOf(SDKException);
    expect(error.name).toBe('DefaultQueueLabelError');
});

const BASE = 'http://compat.test';
const SCOPE = '22222222-2222-4222-8222-222222222222';
const LABEL = '11111111-1111-4111-8111-111111111111';
const QUEUE = '33333333-3333-4333-8333-333333333333';
const auth = { fiApiKey: 'test', fiSecretKey: 'test', fiBaseUrl: BASE };
const defaultResult = (labels: object[]) => ({ status: true, result: {
    queue: { id: QUEUE, name: 'Default', status: 'active', is_default: true },
    labels, created: false, action: 'fetched',
} });

function legacy(responses: unknown[], annotation = false) {
    return capture((annotation ? new Annotation(auth) : new AnnotationQueue(auth)) as AnnotationQueue, responses);
}

function capture<T>(client: T, responses: unknown[]) {
    const sent: { url: string; body: any }[] = [];
    (client as any)._axiosInstance.defaults.adapter = async (config: any) => {
        sent.push({ url: axios.getUri(config), body: config.data ? JSON.parse(config.data) : undefined });
        return { data: responses.shift(), status: 200, statusText: 'OK', headers: {}, config };
    };
    return { client, sent };
}

function facade(responses: unknown[]) {
    const sent: { url: string; body: any }[] = [];
    const client = new FutureAGIClient({ apiKey: 'test', secretKey: 'test', baseUrl: BASE,
        fetch: async (input: any) => {
            const request = input as Request;
            sent.push({ url: request.url, body: await request.json() });
            return new Response(JSON.stringify(responses.shift()), { status: 200, headers: { 'Content-Type': 'application/json' } });
        },
    });
    return { client: client.annotationQueues, sent };
}

it.each([
    ['list', {}, '?page=1&limit=20&include_counts=true'],
    ['list', { page: 2, pageSize: 7 }, '?page=2&limit=7&include_counts=true'],
    ['listItems', {}, '?page=1&limit=50'],
    ['listItems', { page: 2, pageSize: 7, status: 'pending' }, '?page=2&limit=7&status=pending'],
])('published %s sends accepted query %j', async (method, options, expected) => {
    const { client, sent } = legacy([{ results: [] }]);
    if (method === 'list') await client.list(options as Parameters<AnnotationQueue['list']>[0]);
    else await client.listItems(QUEUE, options as Parameters<AnnotationQueue['listItems']>[1]);
    expect(new URL(sent[0].url).search).toBe(expected);
});

it('projects keep zero-based page_number and page_size', async () => {
    const { client, sent } = legacy([{ result: [] }], true);
    await (client as unknown as Annotation).listProjects({ pageNumber: 2, pageSize: 7 });
    expect(new URL(sent[0].url).search).toBe('?page_number=2&page_size=7');
});

it.each(['getColumnId', 'download'] as const)('dataset %s retains zero-based wire parameters', async (method) => {
    const { client, sent } = capture(new Dataset({ ...auth, datasetConfig: { id: SCOPE, name: 'Legacy' } }),
        [{ result: { column_config: [], table: [], metadata: { total_pages: 1 } } }]);
    if (method === 'getColumnId') await client.getColumnId('missing');
    else await client.download(undefined, true);
    expect(new URL(sent[0].url).search).toBe(method === 'getColumnId'
        ? '?page_size=1&current_page_index=0' : '?page_size=1000&current_page_index=0');
});

it.each(['project', 'dataset', 'agentDefinition'] as const)(
    'published create derives labels using the default queue for %s', async (scope) => {
        const { client, sent } = legacy([defaultResult([{ id: LABEL }]), { id: QUEUE, name: 'Legacy' }]);
        const emit = jest.spyOn(process, 'emitWarning').mockImplementation(() => undefined);
        try {
            await client.create({ name: 'Legacy', [scope]: SCOPE, description: 'kept' } as unknown as QueueConfig);
            expect(emit).toHaveBeenCalledTimes(1);
            expect(emit.mock.calls[0][0]).toContain('labelIds will be required');
            expect(emit.mock.calls[0][1]).toMatchObject({ type: 'DeprecationWarning' });
            const key = scope === 'agentDefinition' ? 'agent_definition' : scope;
            expect(sent).toEqual([
                { url: `${BASE}/model-hub/annotation-queues/get-or-create-default/`, body: { [`${key}_id`]: SCOPE } },
                { url: `${BASE}/model-hub/annotation-queues/`, body: { name: 'Legacy', description: 'kept', label_ids: [LABEL] } },
            ]);
        } finally { emit.mockRestore(); }
    },
);

it.each(['project', 'dataset', 'agent_definition'] as const)(
    'facade create derives labels using the default queue for %s', async (scope) => {
        const { client, sent } = facade([defaultResult([{ id: LABEL }]), { id: QUEUE, name: 'Legacy' }]);
        const emit = jest.spyOn(process, 'emitWarning').mockImplementation(() => undefined);
        try {
            await client.create({ name: 'Legacy', [scope]: SCOPE, description: 'kept' } as unknown as CreateAnnotationQueueBody);
            expect(emit).toHaveBeenCalledTimes(1);
            expect(emit.mock.calls[0][0]).toContain('label_ids will be required');
            expect(emit.mock.calls[0][1]).toMatchObject({ type: 'DeprecationWarning' });
            expect(sent).toEqual([
                { url: `${BASE}/model-hub/annotation-queues/get-or-create-default/`, body: { [`${scope}_id`]: SCOPE } },
                { url: `${BASE}/model-hub/annotation-queues/`, body: { name: 'Legacy', description: 'kept', label_ids: [LABEL] } },
            ]);
        } finally { emit.mockRestore(); }
    },
);

it.each(['legacy', 'facade'])('%s refuses to invent a default label', async (surface) => {
    const emit = jest.spyOn(process, 'emitWarning').mockImplementation(() => undefined);
    try {
        for (const [scope, reason, requests] of [
            [{}, 'exactly one', 0],
            [{ project: SCOPE, dataset: SCOPE }, 'exactly one', 0],
            [{ project: SCOPE }, 'no labels', 1],
        ] as const) {
            emit.mockClear();
            const { client, sent } = surface === 'legacy' ? legacy([defaultResult([])]) : facade([defaultResult([])]);
            const result = client.create({ name: 'Legacy', ...scope } as any);
            await expect(result).rejects.toBeInstanceOf(DefaultQueueLabelError);
            await expect(result).rejects.toThrow(reason);
            expect(emit).toHaveBeenCalledTimes(1);
            expect(sent).toHaveLength(requests);
        }
    } finally { emit.mockRestore(); }
});

it.each(['legacy', 'facade'])('%s explicit labels neither look up nor warn', async (surface) => {
    const emit = jest.spyOn(process, 'emitWarning').mockImplementation(() => undefined);
    try {
        const { client, sent } = surface === 'legacy' ? legacy([{ id: QUEUE, name: 'Explicit' }]) : facade([{ id: QUEUE, name: 'Explicit' }]);
        await client.create({ name: 'Explicit', [surface === 'legacy' ? 'labelIds' : 'label_ids']: [LABEL] } as any);
        expect(sent).toHaveLength(1);
        expect(emit).not.toHaveBeenCalled();
    } finally { emit.mockRestore(); }
});
