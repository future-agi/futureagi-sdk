import { AnnotationQueue } from '../client';
import { SDKException } from '../../utils/errors';

// Mock the auth module so APIKeyAuth constructor doesn't actually validate
jest.mock('../../api/auth');

describe('AnnotationQueue', () => {
    let client: AnnotationQueue;
    let mockRequest: jest.Mock;

    beforeEach(() => {
        jest.clearAllMocks();

        client = new AnnotationQueue({
            fiApiKey: 'test-api-key',
            fiSecretKey: 'test-secret-key',
            fiBaseUrl: 'http://localhost:8000',
        });

        mockRequest = jest.fn();
        (client as any).request = mockRequest;
        (client as any)._baseUrl = 'http://localhost:8000';
    });

    // ======================================================================
    // Queue CRUD
    // ======================================================================

    describe('create', () => {
        it('should create a queue with full config', async () => {
            const queue = { id: 'q1', name: 'Test Queue', status: 'draft' };
            mockRequest.mockResolvedValueOnce(queue);

            const result = await client.create({
                name: 'Test Queue',
                description: 'A test queue',
                instructions: 'Rate quality',
                assignmentStrategy: 'round_robin',
                annotationsRequired: 2,
            });

            expect(result).toEqual(queue);
            expect(mockRequest).toHaveBeenCalledTimes(1);

            const config = mockRequest.mock.calls[0][0];
            expect(config.method).toBe('POST');
            expect(config.url).toContain('annotation-queues/');
            expect(config.json.name).toBe('Test Queue');
            expect(config.json.description).toBe('A test queue');
            expect(config.json.assignment_strategy).toBe('round_robin');
            expect(config.json.annotations_required).toBe(2);
        });

        it('should create a queue with minimal config', async () => {
            mockRequest.mockResolvedValueOnce({ id: 'q2', name: 'Min' });

            await client.create({ name: 'Min' });

            const config = mockRequest.mock.calls[0][0];
            expect(config.json).toEqual({ name: 'Min' });
        });
    });

    describe('list', () => {
        it('should list queues with filters', async () => {
            mockRequest.mockResolvedValueOnce([{ id: 'q1', name: 'A' }]);

            const result = await client.list({ status: 'active', search: 'test' });

            const config = mockRequest.mock.calls[0][0];
            expect(config.method).toBe('GET');
            expect(config.params.status).toBe('active');
            expect(config.params.search).toBe('test');
            expect(config.params.include_counts).toBe('true');
            expect(result).toHaveLength(1);
        });
    });

    describe('get', () => {
        it('should get a queue by ID', async () => {
            mockRequest.mockResolvedValueOnce({ id: 'q1', name: 'A' });

            const result = await client.get('q1');

            const config = mockRequest.mock.calls[0][0];
            expect(config.method).toBe('GET');
            expect(config.url).toContain('annotation-queues/q1/');
            expect(result.id).toBe('q1');
        });
    });

    describe('update', () => {
        it('should update queue fields', async () => {
            mockRequest.mockResolvedValueOnce({ id: 'q1', name: 'Updated' });

            await client.update('q1', { name: 'Updated', instructions: 'New' });

            const config = mockRequest.mock.calls[0][0];
            expect(config.method).toBe('PATCH');
            expect(config.json.name).toBe('Updated');
            expect(config.json.instructions).toBe('New');
        });

        it('should omit undefined fields', async () => {
            mockRequest.mockResolvedValueOnce({ id: 'q1', name: 'Same' });

            await client.update('q1', { name: 'Same' });

            const config = mockRequest.mock.calls[0][0];
            expect(config.json).toEqual({ name: 'Same' });
        });
    });

    describe('delete', () => {
        it('should delete a queue', async () => {
            mockRequest.mockResolvedValueOnce({ deleted: true });

            await client.delete('q1');

            const config = mockRequest.mock.calls[0][0];
            expect(config.method).toBe('DELETE');
            expect(config.url).toContain('q1');
        });
    });

    // ======================================================================
    // Queue Lifecycle
    // ======================================================================

    describe('activate', () => {
        it('should activate a queue', async () => {
            mockRequest.mockResolvedValueOnce({ id: 'q1', status: 'active' });

            const result = await client.activate('q1');

            const config = mockRequest.mock.calls[0][0];
            expect(config.method).toBe('POST');
            expect(config.url).toContain('update-status');
            expect(config.json).toEqual({ status: 'active' });
        });
    });

    describe('completeQueue', () => {
        it('should complete a queue', async () => {
            mockRequest.mockResolvedValueOnce({ id: 'q1', status: 'completed' });

            await client.completeQueue('q1');

            const config = mockRequest.mock.calls[0][0];
            expect(config.json).toEqual({ status: 'completed' });
        });
    });

    // ======================================================================
    // Labels
    // ======================================================================

    describe('addLabel', () => {
        it('should add a label to a queue', async () => {
            mockRequest.mockResolvedValueOnce({ label: { id: 'lbl1' }, created: true });

            await client.addLabel('q1', 'lbl1');

            const config = mockRequest.mock.calls[0][0];
            expect(config.method).toBe('POST');
            expect(config.url).toContain('add-label');
            expect(config.json).toEqual({ label_id: 'lbl1' });
        });
    });

    describe('removeLabel', () => {
        it('should remove a label from a queue', async () => {
            mockRequest.mockResolvedValueOnce({ removed: true });

            await client.removeLabel('q1', 'lbl1');

            const config = mockRequest.mock.calls[0][0];
            expect(config.url).toContain('remove-label');
            expect(config.json).toEqual({ label_id: 'lbl1' });
        });
    });

    // ======================================================================
    // Items
    // ======================================================================

    describe('addItems', () => {
        it('should add items to a queue', async () => {
            mockRequest.mockResolvedValueOnce({ added: 3, duplicates: 0 });

            const result = await client.addItems('q1', [
                { sourceType: 'trace', sourceId: 't1' },
                { sourceType: 'trace', sourceId: 't2' },
                { sourceType: 'dataset_row', sourceId: 'r1' },
            ]);

            const config = mockRequest.mock.calls[0][0];
            expect(config.method).toBe('POST');
            expect(config.url).toContain('add-items');
            expect(config.json.items).toHaveLength(3);
            expect(result.added).toBe(3);
        });

        it('should throw on empty items', async () => {
            await expect(client.addItems('q1', [])).rejects.toThrow('non-empty');
        });
    });

    describe('listItems', () => {
        it('should list items with filters', async () => {
            mockRequest.mockResolvedValueOnce([{ id: 'i1', status: 'pending' }]);

            const result = await client.listItems('q1', { status: 'pending', page: 2, pageSize: 10 });

            const config = mockRequest.mock.calls[0][0];
            expect(config.method).toBe('GET');
            expect(config.params.status).toBe('pending');
            expect(config.params.page).toBe(2);
            expect(config.params.page_size).toBe(10);
        });
    });

    describe('removeItems', () => {
        it('should bulk-remove items', async () => {
            mockRequest.mockResolvedValueOnce({ removed: 2 });

            await client.removeItems('q1', ['i1', 'i2']);

            const config = mockRequest.mock.calls[0][0];
            expect(config.method).toBe('POST');
            expect(config.url).toContain('bulk-remove');
            expect(config.json).toEqual({ item_ids: ['i1', 'i2'] });
        });

        it('should throw on empty itemIds', async () => {
            await expect(client.removeItems('q1', [])).rejects.toThrow('non-empty');
        });
    });

    describe('assignItems', () => {
        it('should assign items to a user', async () => {
            mockRequest.mockResolvedValueOnce({ assigned: 2 });

            await client.assignItems('q1', ['i1', 'i2'], 'u1');

            const config = mockRequest.mock.calls[0][0];
            expect(config.method).toBe('POST');
            expect(config.url).toContain('assign');
            expect(config.json.user_id).toBe('u1');
        });

        it('should unassign items with null userId', async () => {
            mockRequest.mockResolvedValueOnce({ assigned: 1 });

            await client.assignItems('q1', ['i1'], null);

            const config = mockRequest.mock.calls[0][0];
            expect(config.json.user_id).toBeNull();
        });
    });

    // ======================================================================
    // Annotation Submission
    // ======================================================================

    describe('importAnnotations', () => {
        it('should import annotations for an item', async () => {
            mockRequest.mockResolvedValueOnce({ imported: 2 });

            const result = await client.importAnnotations('q1', 'item1', [
                { labelId: 'lbl1', value: 'positive' },
                { labelId: 'lbl2', value: 4.5 },
            ]);

            const config = mockRequest.mock.calls[0][0];
            expect(config.method).toBe('POST');
            expect(config.url).toContain('q1/items/item1/annotations/import/');
            expect(config.json.annotations).toHaveLength(2);
            expect(result.imported).toBe(2);
        });

        it('should pass annotatorId when provided', async () => {
            mockRequest.mockResolvedValueOnce({ imported: 1 });

            await client.importAnnotations(
                'q1',
                'item1',
                [{ labelId: 'lbl1', value: 'good' }],
                { annotatorId: 'user123' },
            );

            const config = mockRequest.mock.calls[0][0];
            expect(config.json.annotator_id).toBe('user123');
        });

        it('should throw on empty annotations', async () => {
            await expect(
                client.importAnnotations('q1', 'item1', []),
            ).rejects.toThrow('non-empty');
        });
    });

    describe('submitAnnotations', () => {
        it('should submit annotations with notes', async () => {
            mockRequest.mockResolvedValueOnce({ submitted: 1 });

            await client.submitAnnotations(
                'q1',
                'item1',
                [{ labelId: 'lbl1', value: 'good' }],
                { notes: 'Looks fine' },
            );

            const config = mockRequest.mock.calls[0][0];
            expect(config.method).toBe('POST');
            expect(config.url).toContain('submit');
            expect(config.json.notes).toBe('Looks fine');
        });

        it('should throw on empty annotations', async () => {
            await expect(
                client.submitAnnotations('q1', 'item1', []),
            ).rejects.toThrow('non-empty');
        });
    });

    describe('getAnnotations', () => {
        it('should get annotations for an item', async () => {
            mockRequest.mockResolvedValueOnce([
                { id: 's1', labelName: 'Q', value: 'good' },
            ]);

            const result = await client.getAnnotations('q1', 'item1');

            const config = mockRequest.mock.calls[0][0];
            expect(config.method).toBe('GET');
            expect(config.url).toContain('annotations/');
            expect(result).toHaveLength(1);
        });
    });

    describe('completeItem', () => {
        it('should complete an item', async () => {
            mockRequest.mockResolvedValueOnce({ completed_item_id: 'item1' });

            await client.completeItem('q1', 'item1');

            const config = mockRequest.mock.calls[0][0];
            expect(config.method).toBe('POST');
            expect(config.url).toContain('complete');
        });
    });

    describe('skipItem', () => {
        it('should skip an item', async () => {
            mockRequest.mockResolvedValueOnce({ skipped_item_id: 'item1' });

            await client.skipItem('q1', 'item1');

            const config = mockRequest.mock.calls[0][0];
            expect(config.url).toContain('skip');
        });
    });

    // ======================================================================
    // Scores
    // ======================================================================

    describe('createScore', () => {
        it('should create a score with all fields', async () => {
            mockRequest.mockResolvedValueOnce({ id: 's1', value: 'positive' });

            const result = await client.createScore({
                sourceType: 'trace',
                sourceId: 't1',
                labelId: 'lbl1',
                value: 'positive',
                notes: 'API generated',
            });

            const config = mockRequest.mock.calls[0][0];
            expect(config.method).toBe('POST');
            expect(config.url).toContain('scores/');
            expect(config.json.source_type).toBe('trace');
            expect(config.json.source_id).toBe('t1');
            expect(config.json.label_id).toBe('lbl1');
            expect(config.json.value).toBe('positive');
            expect(config.json.score_source).toBe('api');
            expect(config.json.notes).toBe('API generated');
        });

        it('should default score_source to "api"', async () => {
            mockRequest.mockResolvedValueOnce({ id: 's1' });

            await client.createScore({
                sourceType: 'trace',
                sourceId: 't1',
                labelId: 'lbl1',
                value: true,
            });

            const config = mockRequest.mock.calls[0][0];
            expect(config.json.score_source).toBe('api');
        });
    });

    describe('createScores', () => {
        it('should create bulk scores', async () => {
            mockRequest.mockResolvedValueOnce({ scores: [{ id: 's1' }, { id: 's2' }] });

            await client.createScores({
                sourceType: 'observation_span',
                sourceId: 'os1',
                scores: [
                    { labelId: 'lbl1', value: 'good' },
                    { labelId: 'lbl2', value: 4.0 },
                ],
                notes: 'Batch import',
            });

            const config = mockRequest.mock.calls[0][0];
            expect(config.method).toBe('POST');
            expect(config.url).toContain('scores/bulk/');
            expect(config.json.scores).toHaveLength(2);
            expect(config.json.notes).toBe('Batch import');
        });

        it('should throw on empty scores', async () => {
            await expect(
                client.createScores({ sourceType: 'trace', sourceId: 't1', scores: [] }),
            ).rejects.toThrow('non-empty');
        });
    });

    describe('getScores', () => {
        it('should get scores for a source', async () => {
            mockRequest.mockResolvedValueOnce([
                { id: 's1', labelName: 'Sentiment', value: 'positive' },
            ]);

            const result = await client.getScores('trace', 't1');

            const config = mockRequest.mock.calls[0][0];
            expect(config.method).toBe('GET');
            expect(config.url).toContain('for-source');
            expect(config.params.source_type).toBe('trace');
            expect(config.params.source_id).toBe('t1');
            expect(result).toHaveLength(1);
        });
    });

    // ======================================================================
    // Progress & Analytics
    // ======================================================================

    describe('getProgress', () => {
        it('should get queue progress', async () => {
            const progress = {
                total: 100, pending: 30, inProgress: 20,
                completed: 45, skipped: 5, progressPct: 45.0,
            };
            mockRequest.mockResolvedValueOnce(progress);

            const result = await client.getProgress('q1');

            const config = mockRequest.mock.calls[0][0];
            expect(config.method).toBe('GET');
            expect(config.url).toContain('progress');
            expect(result.total).toBe(100);
            expect(result.completed).toBe(45);
        });
    });

    describe('getAnalytics', () => {
        it('should get queue analytics', async () => {
            const analytics = {
                throughput: [{ date: '2025-01-01', count: 10 }],
                annotatorPerformance: [{ annotatorName: 'Alice', completed: 50 }],
                labelDistribution: { positive: 30, negative: 20 },
                total: 100,
            };
            mockRequest.mockResolvedValueOnce(analytics);

            const result = await client.getAnalytics('q1');

            expect(result.total).toBe(100);
            expect(result.throughput).toHaveLength(1);
        });
    });

    describe('getAgreement', () => {
        it('should get agreement metrics', async () => {
            mockRequest.mockResolvedValueOnce({
                overallAgreement: 85.5,
                perLabel: [{ labelName: 'Sentiment', agreementPct: 90.0 }],
                annotatorPairs: [],
            });

            const result = await client.getAgreement('q1');

            expect(result.overallAgreement).toBe(85.5);
            expect(result.perLabel).toHaveLength(1);
        });
    });

    // ======================================================================
    // Export
    // ======================================================================

    describe('export', () => {
        it('should export as JSON with status filter', async () => {
            mockRequest.mockResolvedValueOnce([{ item_id: 'i1' }]);

            await client.export('q1', { format: 'json', status: 'completed' });

            const config = mockRequest.mock.calls[0][0];
            expect(config.method).toBe('GET');
            expect(config.url).toContain('export');
            expect(config.params.format).toBe('json');
            expect(config.params.status).toBe('completed');
        });

        it('should default format to json', async () => {
            mockRequest.mockResolvedValueOnce([]);

            await client.export('q1');

            const config = mockRequest.mock.calls[0][0];
            expect(config.params.format).toBe('json');
        });
    });

    describe('exportToDataset', () => {
        it('should export to a new dataset by name', async () => {
            mockRequest.mockResolvedValueOnce({
                datasetId: 'd1', datasetName: 'Curated', rowsCreated: 42,
            });

            const result = await client.exportToDataset('q1', { datasetName: 'Curated' });

            const config = mockRequest.mock.calls[0][0];
            expect(config.method).toBe('POST');
            expect(config.url).toContain('export-to-dataset');
            expect(config.json.dataset_name).toBe('Curated');
            expect(result.rowsCreated).toBe(42);
        });

        it('should export to existing dataset by ID', async () => {
            mockRequest.mockResolvedValueOnce({ datasetId: 'd1', rowsCreated: 10 });

            await client.exportToDataset('q1', {
                datasetId: 'd1',
                statusFilter: 'completed',
            });

            const config = mockRequest.mock.calls[0][0];
            expect(config.json.dataset_id).toBe('d1');
            expect(config.json.status_filter).toBe('completed');
        });

        it('should throw when neither name nor ID provided', async () => {
            await expect(
                client.exportToDataset('q1', {}),
            ).rejects.toThrow('datasetName or datasetId');
        });
    });

    // ======================================================================
    // URL Construction
    // ======================================================================

    describe('URL construction', () => {
        it('should interpolate queue_id in detail URL', async () => {
            mockRequest.mockResolvedValueOnce({ id: 'abc-123', name: 'A' });
            await client.get('abc-123');
            expect(mockRequest.mock.calls[0][0].url).toContain('annotation-queues/abc-123/');
        });

        it('should interpolate queue_id and item_id in annotations URL', async () => {
            mockRequest.mockResolvedValueOnce([]);
            await client.getAnnotations('q-id', 'item-id');
            expect(mockRequest.mock.calls[0][0].url).toContain('q-id/items/item-id/annotations/');
        });

        it('should interpolate in import URL', async () => {
            mockRequest.mockResolvedValueOnce({ imported: 0 });
            await client.importAnnotations('q-id', 'item-id', [{ labelId: 'l1', value: 'x' }]);
            expect(mockRequest.mock.calls[0][0].url).toContain('q-id/items/item-id/annotations/import/');
        });

        it('should interpolate in complete URL', async () => {
            mockRequest.mockResolvedValueOnce({});
            await client.completeItem('q-id', 'item-id');
            expect(mockRequest.mock.calls[0][0].url).toContain('q-id/items/item-id/complete/');
        });

        it('should interpolate in progress URL', async () => {
            mockRequest.mockResolvedValueOnce({ total: 0 });
            await client.getProgress('q-id');
            expect(mockRequest.mock.calls[0][0].url).toContain('annotation-queues/q-id/progress/');
        });

        it('should use scores/for-source URL', async () => {
            mockRequest.mockResolvedValueOnce([]);
            await client.getScores('trace', 't1');
            expect(mockRequest.mock.calls[0][0].url).toContain('scores/for-source/');
        });
    });
});
