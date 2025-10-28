import { Dataset, DatasetConfig, DataTypeChoices, createColumn, createRow, createCell } from '../';
import * as fs from 'fs';
import * as path from 'path';
import { v4 as uuidv4 } from 'uuid';
import { ModelTypes } from '../types';

// Integration tests for the Dataset module
// These tests make real API calls and require a running FutureAGI backend
// and valid API keys set in the environment variables.

const describeIf = (condition: boolean) => (condition ? describe : describe.skip);

const areEnvVarsSet = !!(process.env.FI_API_KEY && process.env.FI_SECRET_KEY && process.env.FI_BASE_URL);

describeIf(areEnvVarsSet)('Dataset Integration Tests', () => {
    let dataset: Dataset;
    const datasetName = `test-dataset-${uuidv4()}`;
    const datasetConfig: DatasetConfig = {
        name: datasetName,
    };

    beforeAll(() => {
        // Increase timeout for integration tests
        jest.setTimeout(30000); // 30 seconds

        dataset = new Dataset({
            fiApiKey: process.env.FI_API_KEY,
            fiSecretKey: process.env.FI_SECRET_KEY,
            fiBaseUrl: process.env.FI_BASE_URL,
            datasetConfig,
        });
    });

    afterAll(async () => {
        // Clean up the created dataset
        try {
            await dataset.delete();
            console.log(`✅ Cleaned up dataset: ${datasetName}`);
        } catch (error) {
            console.error(`❌ Failed to clean up dataset: ${datasetName}`, error);
        }
    });

    test('should create an empty dataset', async () => {
        await dataset.create();
        const config = dataset.getConfig();
        
        expect(config.id).toBeDefined();
        expect(config.name).toBe(datasetName);
    });

    test('should add columns to the dataset', async () => {
        const columns = [
            createColumn({ name: 'question', dataType: DataTypeChoices.TEXT }),
            createColumn({ name: 'answer', dataType: DataTypeChoices.TEXT }),
        ];

        await dataset.addColumns(columns);

        // To verify, we'll try to get the column ID
        const columnId = await dataset.getColumnId('question');
        expect(columnId).toBeDefined();
    });

    test('should add rows to the dataset', async () => {
        const questionColId = await dataset.getColumnId('question');
        const answerColId = await dataset.getColumnId('answer');

        if (!questionColId || !answerColId) {
            throw new Error('Could not get column IDs for testing');
        }
        
        const rows = [
            createRow({
                cells: [
                    createCell({ columnId: questionColId, rowId: 'row-1', value: 'What is FutureAGI?' }),
                    createCell({ columnId: answerColId, rowId: 'row-1', value: 'An AI evaluation platform.' }),
                ],
            }),
        ];

        await dataset.addRows(rows);
    });

    test('should download the dataset to a file', async () => {
        const filePath = path.join(__dirname, `${datasetName}.csv`);
        const resultPath = await dataset.download(filePath, false);

        expect(resultPath).toBe(filePath);
        expect(fs.existsSync(filePath)).toBe(true);

        // Verify content
        const content = fs.readFileSync(filePath, 'utf-8');
        expect(content).toContain('question,answer');
        expect(content).toContain('What is FutureAGI?,An AI evaluation platform.');

        // Clean up the downloaded file
        fs.unlinkSync(filePath);
    });

    test('should create dataset from a file, download, and delete', async () => {
        const newDatasetName = `test-from-file-${uuidv4()}`;
        const newDatasetConfig: DatasetConfig = {
            name: newDatasetName,
        };

        const fileDataset = new Dataset({
            fiApiKey: process.env.FI_API_KEY,
            fiSecretKey: process.env.FI_SECRET_KEY,
            fiBaseUrl: process.env.FI_BASE_URL,
            datasetConfig: newDatasetConfig,
        });

        // Create a dummy CSV file
        const tempFilePath = path.join(__dirname, 'temp-upload.csv');
        fs.writeFileSync(tempFilePath, 'header1,header2\nvalue1,value2');

        try {
            // Create dataset from file
            await fileDataset.create(tempFilePath);
            const createdConfig = fileDataset.getConfig();
            expect(createdConfig.id).toBeDefined();

            // Download to verify
            const downloadedContent = await fileDataset.download(undefined, true) as any;
            expect(downloadedContent.columns).toHaveLength(2);
            expect(downloadedContent.rows).toHaveLength(1);
            
        } finally {
            // Clean up
            await fileDataset.delete();
            fs.unlinkSync(tempFilePath);
        }
    });
}); 