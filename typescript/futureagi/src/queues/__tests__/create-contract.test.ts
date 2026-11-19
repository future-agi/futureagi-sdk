/**
 * Contract: both queue create() methods against the backend's AnnotationQueueSerializer, read
 * from the checked-in snapshot tests/fixtures/server-contracts/annotation-queue-create.json.
 * Refresh it with scripts/snapshot-annotation-queue-contract.py (see the snapshot's "refresh").
 */
import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
import { join } from 'node:path';

import { AnnotationQueue } from '../client';
import {
    DEFAULT_QUEUE_SCOPE_IDS,
    IGNORED_ON_CREATE,
    QUEUE_CONFIG_REQUIRED_KEYS,
    QUEUE_CREATE_FIELDS,
    QUEUE_CREATE_IGNORED_KEYS,
    QUEUE_DEFAULT_SCOPE_KEYS,
    REQUIRED_ON_CREATE,
} from '../create-body';
import type { DefaultQueue, DefaultQueueScope, QueueConfig, QueueDetail } from '../types';
import { FutureAGIClient } from '../../futureagi-client';
import type {
    AnnotationQueueDefaultScope,
    CreateAnnotationQueueBody,
} from '../../futureagi-client';
import type {
    QueueDefaultQueue,
    QueueDefaultRequest,
    QueueDefaultResult,
    QueueLabelResult,
} from '../../generated/openapi/types.gen';

jest.mock('../../api/auth');

type Snapshot = {
    source: { sha256: string; files: { path: string; sha256: string }[] };
    refresh: string;
    serializer: {
        class: string;
        bases: string[];
        read_only_fields: string[];
        scope_ids_read: Record<string, string[]>;
    };
    create: { writable: string[]; required: string[]; read_only: string[] };
    view: {
        serializer_class: string;
        perform_create_saves: string[];
        scope_ids_read: Record<string, string[]>;
    };
    get_or_create_default: {
        methods: string[];
        path: string;
        request_serializer: {
            declared_fields: Record<string, { required?: boolean }>;
            exactly_one_of: string[] | null;
        };
    };
};

const snapshot: Snapshot = JSON.parse(
    readFileSync(
        join(__dirname, '../../../../../tests/fixtures/server-contracts/annotation-queue-create.json'),
        'utf8',
    ),
);
const sorted = (values: readonly string[]) => [...values].sort();
const toWire = (key: string) => key.replace(/[A-Z]/g, (c) => `_${c.toLowerCase()}`);

// Type-level checks: tsc (ts-jest) fails this file when the required keys of the types and the
// runtime lists (REQUIRED_ON_CREATE, which both create() methods check) differ. The tests below
// compare the runtime lists with the snapshot.
type RequiredKeys<T> = { [K in keyof T]-?: {} extends Pick<T, K> ? never : K }[keyof T];
type Equal<A, B> =
    (<G>() => G extends A ? 1 : 2) extends <G>() => G extends B ? 1 : 2 ? true : false;
const assertType = <T extends true>(): T | undefined => undefined;

const QUEUE_CONFIG_REQUIRED = ['name', 'labelIds'] as const;
assertType<Equal<RequiredKeys<QueueConfig>, 'name'>>();
assertType<Equal<RequiredKeys<CreateAnnotationQueueBody>, 'name'>>();

// get-or-create-default: the facade scope covers exactly the generated request's keys, and the
// queue client's camelCase keys map onto the same fields.
type ScopeIds = (typeof DEFAULT_QUEUE_SCOPE_IDS)[keyof typeof DEFAULT_QUEUE_SCOPE_IDS];
assertType<Equal<keyof QueueDefaultRequest, ScopeIds>>();
assertType<Equal<AnnotationQueueDefaultScope extends infer S ? keyof S : never, ScopeIds>>();
assertType<
    Equal<
        (typeof QUEUE_DEFAULT_SCOPE_KEYS)[keyof typeof QUEUE_DEFAULT_SCOPE_KEYS],
        ScopeIds
    >
>();
assertType<
    Equal<DefaultQueueScope extends infer S ? keyof S : never, keyof typeof QUEUE_DEFAULT_SCOPE_KEYS>
>();

// The hand-written DefaultQueue (what AnnotationQueue.getOrCreateDefault resolves to) against the
// generated QueueDefaultResult, which follows the server's response serializer: the same keys, the
// same action values, every generated queue field a QueueDetail field, and each label carrying the
// 8 fields DefaultQueue.labels lists.
assertType<Equal<keyof DefaultQueue, keyof QueueDefaultResult>>();
assertType<Equal<DefaultQueue['action'], QueueDefaultResult['action']>>();
assertType<Equal<DefaultQueue['created'], QueueDefaultResult['created']>>();
assertType<Equal<Exclude<keyof QueueDefaultQueue, keyof QueueDetail>, never>>();
assertType<
    Equal<
        keyof QueueLabelResult,
        'id' | 'name' | 'type' | 'settings' | 'description' | 'allow_notes' | 'required' | 'order'
    >
>();

// A get-or-create-default answer in the shape the view returns, one label included.
const DEFAULT_QUEUE_ANSWER: QueueDefaultResult = {
    queue: {
        id: '33333333-3333-4333-8333-333333333333',
        name: 'Default - P',
        description: '',
        instructions: '',
        status: 'active',
        is_default: true,
    },
    labels: [
        {
            id: '11111111-1111-4111-8111-111111111111',
            name: 'Helpful',
            type: 'categorical',
            settings: { options: [{ label: 'Yes' }, { label: 'No' }], multi_choice: false },
            description: 'Was the answer helpful?',
            allow_notes: true,
            required: true,
            order: 0,
        },
    ],
    created: true,
    action: 'created',
};

// Every key the facade body type allows, deprecated ones aside: a new key in the generated type
// is a compile error here until it is listed, and then the runtime check compares it with the server.
const FULL_FACADE_BODY: Required<
    Omit<CreateAnnotationQueueBody, (typeof IGNORED_ON_CREATE)[number]>
> = {
    name: 'Q',
    description: 'd',
    instructions: 'i',
    assignment_strategy: 'manual',
    annotations_required: 1,
    reservation_timeout_minutes: 60,
    requires_review: false,
    auto_assign: false,
    label_ids: ['11111111-1111-4111-8111-111111111111'],
    annotator_ids: ['22222222-2222-4222-8222-222222222222'],
    annotator_roles: { '22222222-2222-4222-8222-222222222222': ['reviewer', 'annotator'] },
};

function facadeWithCapture() {
    const sent: unknown[] = [];
    const fetchMock = jest.fn(async (input: Request | string, init?: RequestInit) => {
        const request = input instanceof Request ? input : new Request(input, init);
        sent.push(JSON.parse(await request.text()));
        return new Response(JSON.stringify({ id: 'q1', name: 'Q' }), {
            status: 201,
            headers: { 'Content-Type': 'application/json' },
        });
    });
    const client = new FutureAGIClient({
        apiKey: 'api-key',
        secretKey: 'secret-key',
        baseUrl: 'http://api.test',
        fetch: fetchMock as unknown as typeof fetch,
    });
    return { client, fetchMock, sent };
}

describe('annotation queue create() contract with the server serializer', () => {
    it('reads a snapshot pinned to backend content and how to refresh it', () => {
        expect(snapshot.source.sha256).toMatch(/^[0-9a-f]{64}$/);
        expect(snapshot.source).not.toHaveProperty('commit');
        expect(snapshot.source).not.toHaveProperty('ref');
        for (const file of snapshot.source.files) expect(file.sha256).toMatch(/^[0-9a-f]{64}$/);
        const files = snapshot.source.files.map(({ path, sha256 }) => ({ path, sha256 }));
        expect(createHash('sha256').update(JSON.stringify(files)).digest('hex')).toBe(snapshot.source.sha256);
        const paths = snapshot.source.files.map((f) => f.path);
        expect(paths).toContain('futureagi/model_hub/serializers/annotation_queues.py');
        expect(paths).toContain('futureagi/model_hub/views/annotation_queues.py');
        expect(snapshot.refresh).toContain('scripts/snapshot-annotation-queue-contract.py');
    });

    it('the view saves none of the deprecated fields on create', () => {
        expect(snapshot.view.serializer_class).toBe(snapshot.serializer.class);
        for (const field of IGNORED_ON_CREATE) {
            expect(snapshot.view.perform_create_saves).not.toContain(field);
        }
    });

    it('both create() methods check exactly the fields the server requires', () => {
        expect(sorted(REQUIRED_ON_CREATE)).toEqual(sorted(snapshot.create.required));
        expect(sorted(QUEUE_CONFIG_REQUIRED_KEYS)).toEqual(sorted(QUEUE_CONFIG_REQUIRED));
    });

    it.each(snapshot.create.required.flatMap((field) => [[field, 'absent'], [field, 'null']]))(
        'annotationQueues.create refuses a body without %s (%s) before any request',
        async (field, how) => {
            const { client, fetchMock } = facadeWithCapture();
            const body: Record<string, unknown> = { ...FULL_FACADE_BODY };
            if (how === 'absent') delete body[field];
            else body[field] = null;
            await expect(
                client.annotationQueues.create(body as unknown as CreateAnnotationQueueBody),
            ).rejects.toThrow(field === 'label_ids' && how === 'absent'
                ? 'needs label_ids or exactly one'
                : `annotationQueues.create(): ${field} is required`);
            expect(fetchMock).not.toHaveBeenCalled();
        },
    );

    it.each(snapshot.create.required)(
        'AnnotationQueue.create refuses a config without the key of %s before any request',
        async (field) => {
            const client = new AnnotationQueue({ fiApiKey: 'k', fiSecretKey: 's' });
            const request = jest.fn();
            (client as any).request = request;
            const key = (Object.keys(QUEUE_CREATE_FIELDS) as (keyof typeof QUEUE_CREATE_FIELDS)[])
                .find((k) => QUEUE_CREATE_FIELDS[k] === field)!;
            const config: Record<string, unknown> = { name: 'Q', labelIds: ['l1'] };
            delete config[key];
            await expect(client.create(config as unknown as QueueConfig)).rejects.toThrow(
                key === 'labelIds' ? 'needs labelIds or exactly one' : `AnnotationQueue.create(): ${key} is required`,
            );
            expect(request).not.toHaveBeenCalled();
        },
    );

    it('AnnotationQueue.create sends exactly the fields the server accepts', () => {
        expect(sorted(Object.values(QUEUE_CREATE_FIELDS))).toEqual(sorted(snapshot.create.writable));
        expect(sorted(QUEUE_CONFIG_REQUIRED.map((key) => QUEUE_CREATE_FIELDS[key]))).toEqual(
            sorted(snapshot.create.required),
        );
    });

    it('the deprecated keys are the ones the server treats as read-only', () => {
        expect(QUEUE_CREATE_IGNORED_KEYS.map(toWire)).toEqual([...IGNORED_ON_CREATE]);
        for (const field of IGNORED_ON_CREATE) {
            expect(snapshot.serializer.read_only_fields).toContain(field);
            expect(snapshot.create.writable).not.toContain(field);
        }
    });

    it('AnnotationQueue.create puts every server field on the wire', async () => {
        const client = new AnnotationQueue({ fiApiKey: 'k', fiSecretKey: 's' });
        const request = jest.fn().mockResolvedValue({ id: 'q1', name: 'Q' });
        (client as any).request = request;
        (client as any)._baseUrl = 'http://api.test';
        const full: Required<Omit<QueueConfig, (typeof QUEUE_CREATE_IGNORED_KEYS)[number]>> = {
            name: 'Q',
            labelIds: ['l1'],
            description: 'd',
            instructions: 'i',
            assignmentStrategy: 'manual',
            annotationsRequired: 1,
            reservationTimeoutMinutes: 60,
            requiresReview: false,
            autoAssign: false,
            annotatorIds: ['u1'],
            annotatorRoles: { u1: 'annotator' },
        };
        await client.create(full);
        expect(sorted(Object.keys(request.mock.calls[0][0].json))).toEqual(
            sorted(snapshot.create.writable),
        );
    });

    it('annotationQueues.create puts every server field on the wire', async () => {
        const { client, sent } = facadeWithCapture();
        expect(sorted(Object.keys(FULL_FACADE_BODY))).toEqual(sorted(snapshot.create.writable));
        await client.annotationQueues.create(FULL_FACADE_BODY);
        expect(sorted(Object.keys(sent[0] as object))).toEqual(sorted(snapshot.create.writable));
    });

    it('annotationQueues.create refuses a body without labels before any request', async () => {
        const { client, fetchMock } = facadeWithCapture();
        await expect(
            client.annotationQueues.create({ name: 'Q' } as unknown as CreateAnnotationQueueBody),
        ).rejects.toThrow('needs label_ids or exactly one');
        await expect(client.annotationQueues.create({ name: 'Q', label_ids: [] })).rejects.toThrow(
            'label_ids needs at least one annotation label id',
        );
        expect(fetchMock).not.toHaveBeenCalled();
    });

    it('annotationQueues.create drops project/dataset/agent_definition with one warning', async () => {
        const emitWarning = jest.spyOn(process, 'emitWarning').mockImplementation(() => {});
        try {
            const { client, sent } = facadeWithCapture();
            const labels = ['11111111-1111-4111-8111-111111111111'];
            await client.annotationQueues.create({
                name: 'Q',
                label_ids: labels,
                project: '33333333-3333-4333-8333-333333333333',
                dataset: null,
                agent_definition: '44444444-4444-4444-8444-444444444444',
            });
            await client.annotationQueues.create({ name: 'Q2', label_ids: labels, dataset: 'd' });
            expect(sent).toEqual([
                { name: 'Q', label_ids: labels },
                { name: 'Q2', label_ids: labels },
            ]);
            expect(emitWarning).toHaveBeenCalledTimes(1);
            const [message, options] = emitWarning.mock.calls[0] as unknown as [string, any];
            expect(message).toContain('annotationQueues.create()');
            expect(message).toContain('ignored by the server');
            expect(message).toContain('remain accepted for compatibility');
            // The hint is a call on this client, not a raw endpoint.
            expect(message).toContain('annotationQueues.getOrCreateDefault({ project_id })');
            expect(message).not.toContain('/model-hub/');
            expect(options).toMatchObject({ type: 'DeprecationWarning' });
        } finally {
            emitWarning.mockRestore();
        }
    });
});

describe('get-or-create-default contract with the server', () => {
    const defaultQueue = snapshot.get_or_create_default;
    const scopeFields = sorted(Object.keys(defaultQueue.request_serializer.declared_fields));

    it('both clients take exactly the request fields, one per deprecated create field', () => {
        expect(defaultQueue.methods).toEqual(['POST']);
        expect(sorted(defaultQueue.request_serializer.exactly_one_of ?? [])).toEqual(scopeFields);
        expect(sorted(Object.values(DEFAULT_QUEUE_SCOPE_IDS))).toEqual(scopeFields);
        expect(Object.keys(DEFAULT_QUEUE_SCOPE_IDS)).toEqual([...IGNORED_ON_CREATE]);
        expect(sorted(Object.values(QUEUE_DEFAULT_SCOPE_KEYS))).toEqual(scopeFields);
        expect(sorted(Object.keys(QUEUE_DEFAULT_SCOPE_KEYS).map(toWire))).toEqual(scopeFields);
    });

    it.each(Object.keys(snapshot.get_or_create_default.request_serializer.declared_fields))(
        'annotationQueues.getOrCreateDefault sends only %s',
        async (field) => {
            const requests: { method: string; path: string; body: unknown }[] = [];
            const fetchMock = jest.fn(async (input: Request | string, init?: RequestInit) => {
                const request = input instanceof Request ? input : new Request(input, init);
                requests.push({
                    method: request.method,
                    path: new URL(request.url).pathname,
                    body: JSON.parse(await request.text()),
                });
                return new Response(JSON.stringify({ status: true, result: DEFAULT_QUEUE_ANSWER }), {
                    status: 200,
                    headers: { 'Content-Type': 'application/json' },
                });
            });
            const client = new FutureAGIClient({
                apiKey: 'api-key',
                secretKey: 'secret-key',
                baseUrl: 'http://api.test',
                fetch: fetchMock as unknown as typeof fetch,
            });
            const id = '22222222-2222-4222-8222-222222222222';
            const answer = await client.annotationQueues.getOrCreateDefault({
                [field]: id,
            } as unknown as AnnotationQueueDefaultScope);
            expect(requests).toEqual([
                { method: defaultQueue.methods[0], path: defaultQueue.path, body: { [field]: id } },
            ]);
            // The body as the server sent it, the label included (as Python's facade returns it).
            expect(answer).toEqual({ status: true, result: DEFAULT_QUEUE_ANSWER });
            expect(answer.result.labels[0].type).toBe('categorical');
            expect(answer.result.action).toBe('created');
        },
    );

    it('the create serializer accepts the scope ids without an error, so both clients refuse them', () => {
        expect(snapshot.serializer.bases.some((base) => base.startsWith('Strict'))).toBe(false);
        for (const field of scopeFields) {
            expect(snapshot.create.writable).not.toContain(field);
            expect(snapshot.create.read_only).not.toContain(field);
        }
    });

    it('the server uses the scope ids on create only for its duplicate-name check', () => {
        // What the refusal says: the serializer reads them only in validate_name, the view's
        // create() and perform_create() use none, and perform_create saves none.
        expect(snapshot.serializer.scope_ids_read).toEqual({ validate_name: scopeFields });
        expect(snapshot.view.scope_ids_read).toEqual({});
        for (const field of scopeFields) {
            expect(snapshot.view.perform_create_saves).not.toContain(field);
        }
    });

    it.each(Object.keys(snapshot.get_or_create_default.request_serializer.declared_fields))(
        'annotationQueues.create refuses %s before any request, naming the call',
        async (field) => {
            const { client, fetchMock } = facadeWithCapture();
            const id = '22222222-2222-4222-8222-222222222222';
            const body = { name: 'Q', label_ids: ['l1'], [field]: id };
            await expect(
                client.annotationQueues.create(body as unknown as CreateAnnotationQueueBody),
            ).rejects.toThrow(
                `annotationQueues.create(): ${field} cannot be set on a new queue`,
            );
            await expect(
                client.annotationQueues.create(body as unknown as CreateAnnotationQueueBody),
            ).rejects.toThrow(`call annotationQueues.getOrCreateDefault({ ${field}: "${id}" })`);
            await expect(
                client.annotationQueues.create(body as unknown as CreateAnnotationQueueBody),
            ).rejects.toThrow(
                'the server never applies it to the queue (it only uses it to scope its ' +
                    'duplicate-name check)',
            );
            expect(fetchMock).not.toHaveBeenCalled();
        },
    );

    it('annotationQueues.create refuses several scope ids and does not send null ones', async () => {
        const { client, fetchMock, sent } = facadeWithCapture();
        await expect(
            client.annotationQueues.create({
                name: 'Q',
                label_ids: ['l1'],
                project_id: 'p',
                dataset_id: 'd',
            } as unknown as CreateAnnotationQueueBody),
        ).rejects.toThrow('project_id and dataset_id cannot be set');
        expect(fetchMock).not.toHaveBeenCalled();
        await client.annotationQueues.create({
            name: 'Q',
            label_ids: ['l1'],
            agent_definition_id: null,
        } as unknown as CreateAnnotationQueueBody);
        expect(sent).toEqual([{ name: 'Q', label_ids: ['l1'] }]);
    });

    it('annotationQueues.getOrCreateDefault needs exactly one id, before any request', async () => {
        const { client, fetchMock } = facadeWithCapture();
        await expect(
            client.annotationQueues.getOrCreateDefault({} as AnnotationQueueDefaultScope),
        ).rejects.toThrow('give exactly one of project_id, dataset_id, agent_definition_id');
        await expect(
            client.annotationQueues.getOrCreateDefault({
                project_id: 'p',
                dataset_id: 'd',
            } as unknown as AnnotationQueueDefaultScope),
        ).rejects.toThrow('(got project_id, dataset_id)');
        expect(fetchMock).not.toHaveBeenCalled();
    });
});
