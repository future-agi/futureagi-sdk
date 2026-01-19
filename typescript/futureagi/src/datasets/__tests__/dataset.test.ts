import { Dataset, DatasetResponseHandler } from '../dataset';
import { DatasetConfig, DatasetTable, HuggingfaceDatasetConfig, createColumn, createCell, createRow, DataTypeChoices, SourceChoices } from '../types';
import { DatasetError, DatasetNotFoundError, DatasetValidationError } from '../../utils/errors';
import { AxiosResponse } from 'axios';
import * as fs from 'fs';
import { Readable } from 'stream';

// Mock built-in modules
jest.mock('axios');
jest.mock('fs', () => ({
    ...jest.requireActual('fs'), // import and retain default behavior
    existsSync: jest.fn(),
    createReadStream: jest.fn(),
}));

// Mock the APIKeyAuth base class
jest.mock('../../api/auth', () => ({
    APIKeyAuth: class MockAPIKeyAuth {
        protected _baseUrl = 'https://api.futureagi.com';
        
        constructor(config: any) {
            // Mock constructor
        }
        
        async request(config: any, responseHandler?: any): Promise<any> {
            // Mock request method - will be overridden in tests
            return {};
        }
    },
    ResponseHandler: class MockResponseHandler {
        static parse(response: any, handlerClass: any) {
            return handlerClass._parseSuccess(response);
        }
        
        static _parseSuccess(response: any) {
            if (response.data) {
                return response.data;
            }
            throw new Error("Mock _parseSuccess error: response.data is undefined");
        }
        
        static _handleError(response: any) {
            throw new Error('Mock error');
        }
    },
}));

describe('DatasetResponseHandler', () => {
    describe('_parseSuccess', () => {
        test('should parse dataset names response', () => {
            const mockResponse: Partial<AxiosResponse> = {
                data: {
                    result: {
                        datasets: [
                            {
                                datasetId: 'dataset-123',
                                name: 'test-dataset',
                            },
                        ],
                    },
                },
                config: {
                    url: 'https://api.futureagi.com/model-hub/develops/get-datasets-names/',
                    headers: {} as any,
                } as any,
            };

            const result = DatasetResponseHandler._parseSuccess(mockResponse as AxiosResponse);
            expect(result).toEqual({
                id: 'dataset-123',
                name: 'test-dataset',
            });
        });

        test('should throw error for empty datasets list', () => {
            const mockResponse: Partial<AxiosResponse> = {
                data: {
                    result: {
                        datasets: [],
                    },
                },
                config: {
                    url: 'https://api.futureagi.com/model-hub/develops/get-datasets-names/',
                    headers: {} as any,
                } as any,
            };

            expect(() => {
                DatasetResponseHandler._parseSuccess(mockResponse as AxiosResponse);
            }).toThrow(DatasetNotFoundError);
        });

        test('should throw error for multiple datasets', () => {
            const mockResponse: Partial<AxiosResponse> = {
                data: {
                    result: {
                        datasets: [
                            { datasetId: '1', name: 'dataset1', },
                            { datasetId: '2', name: 'dataset2', },
                        ],
                    },
                },
                config: {
                    url: 'https://api.futureagi.com/model-hub/develops/get-datasets-names/',
                    headers: {} as any,
                } as any,
            };

            expect(() => {
                DatasetResponseHandler._parseSuccess(mockResponse as AxiosResponse);
            }).toThrow('Multiple datasets found');
        });

        test('should parse dataset table response', () => {
            const mockResponse: Partial<AxiosResponse> = {
                data: {
                    result: {
                        columnConfig: [
                            {
                                id: 'col-1',
                                name: 'name',
                                dataType: DataTypeChoices.TEXT,
                                originType: SourceChoices.OTHERS,
                                sourceId: null,
                                isFrozen: { isFrozen: false },
                                isVisible: true,
                                evalTag: [],
                                averageScore: null,
                                orderIndex: 0,
                            },
                        ],
                        table: [
                            {
                                rowId: 'row-1',
                                order: 0,
                                'col-1': {
                                    cellValue: 'John',
                                    valueInfos: null,
                                    metadata: null,
                                    status: 'completed',
                                    failureReason: null,
                                },
                            },
                        ],
                        metadata: {},
                    },
                },
                config: {
                    url: 'https://api.futureagi.com/model-hub/develops/dataset-123/get-dataset-table/',
                    headers: {} as any,
                } as any,
            };

            const result = DatasetResponseHandler._parseSuccess(mockResponse as AxiosResponse) as DatasetTable;
            expect(result.id).toBe('dataset-123');
            expect(result.columns).toHaveLength(1);
            expect(result.rows).toHaveLength(1);
            expect(result.columns[0].name).toBe('name');
            expect(result.rows[0].cells).toHaveLength(1);
        });

        test('should parse dataset creation response', () => {
            const mockResponse: Partial<AxiosResponse> = {
                data: {
                    result: {
                        datasetId: 'dataset-123',
                        datasetName: 'test-dataset',
                    },
                },
                config: {
                    url: 'https://api.futureagi.com/model-hub/develops/create-empty-dataset/',
                    headers: {} as any,
                } as any,
            };

            const result = DatasetResponseHandler._parseSuccess(mockResponse as AxiosResponse);
            expect(result).toEqual({
                id: 'dataset-123',
                name: 'test-dataset',
            });
        });
    });

    describe('_handleError', () => {
        test('should handle different error status codes', () => {
            const mockResponse: Partial<AxiosResponse> = {
                status: 404,
                data: { message: 'Dataset not found' },
                statusText: 'Not Found',
            };

            expect(() => {
                DatasetResponseHandler._handleError(mockResponse as AxiosResponse);
            }).toThrow(DatasetNotFoundError);
        });

        test('should handle server errors', () => {
            const mockResponse: Partial<AxiosResponse> = {
                status: 500,
                data: { message: 'Internal server error' },
                statusText: 'Internal Server Error',
            };

            expect(() => {
                DatasetResponseHandler._handleError(mockResponse as AxiosResponse);
            }).toThrow('Internal server error');
        });
    });
});

describe('Dataset', () => {
    let dataset: Dataset;
    let mockRequest: jest.Mock;

    beforeEach(() => {
        mockRequest = jest.fn();
        dataset = new Dataset({
            fiApiKey: 'test-key',
            fiSecretKey: 'test-secret',
        });
        (dataset as any).request = mockRequest;
    });

    describe('constructor', () => {
        test('should create dataset instance', () => {
            expect(dataset).toBeInstanceOf(Dataset);
        });

        test('should create dataset with config', () => {
            const config: DatasetConfig = {
                id: 'dataset-123',
                name: 'test-dataset',
            };

            const datasetWithConfig = new Dataset({
                fiApiKey: 'test-key',
                fiSecretKey: 'test-secret',
                datasetConfig: config,
            });

            expect(datasetWithConfig.getConfig()).toEqual(config);
        });
    });

    describe('getConfig', () => {
        test('should return dataset config', () => {
            const config: DatasetConfig = {
                id: 'dataset-123',
                name: 'test-dataset',
            };

            (dataset as any)._datasetConfig = config;
            expect(dataset.getConfig()).toEqual(config);
        });

        test('should throw error when no config is set', () => {
            expect(() => {
                dataset.getConfig();
            }).toThrow(DatasetError);
        });
    });

    describe('create', () => {
        test('should create empty dataset', async () => {
            const config: DatasetConfig = {
                name: 'test-dataset',
            };

            (dataset as any)._datasetConfig = config;
            mockRequest.mockResolvedValue({
                id: 'dataset-123',
                name: 'test-dataset',
            });

            const result = await dataset.create();
            expect(result).toBe(dataset);
            expect(mockRequest).toHaveBeenCalledWith(
                expect.objectContaining({
                    method: 'POST',
                    json: expect.objectContaining({
                        new_dataset_name: 'test-dataset',
                    }),
                }),
                DatasetResponseHandler
            );
        });

        test('should create dataset from file', async () => {
            const config: DatasetConfig = {
                name: 'test-dataset',
            };

            (dataset as any)._datasetConfig = config;
            mockRequest.mockResolvedValue({
                id: 'dataset-123',
                name: 'test-dataset',
            });

            // Mock fs.existsSync to avoid file system check
            (fs.existsSync as jest.Mock).mockReturnValue(true);
            (fs.createReadStream as jest.Mock).mockReturnValue(new Readable());

            const result = await dataset.create('path/to/file.csv');
            expect(result).toBe(dataset);
            expect(mockRequest).toHaveBeenCalledWith(
                expect.objectContaining({
                    method: 'POST',
                    // Data is now a FormData object, which is harder to inspect directly
                }),
                DatasetResponseHandler
            );
        });

        test('should create dataset from Hugging Face', async () => {
            const config: DatasetConfig = {
                name: 'test-dataset',
            };

            const hfConfig: HuggingfaceDatasetConfig = {
                name: 'squad',
                subset: 'plain_text',
                split: 'train',
                numRows: 1000,
            };

            (dataset as any)._datasetConfig = config;
            mockRequest.mockResolvedValue({
                id: 'dataset-123',
                name: 'test-dataset',
            });

            const result = await dataset.create(hfConfig);
            expect(result).toBe(dataset);
            expect(mockRequest).toHaveBeenCalledWith(
                expect.objectContaining({
                    method: 'POST',
                    json: expect.objectContaining({
                        new_dataset_name: 'test-dataset',
                        huggingface_dataset_name: 'squad',
                        huggingface_dataset_config: 'plain_text',
                        huggingface_dataset_split: 'train',
                        num_rows: 1000,
                    }),
                }),
                DatasetResponseHandler
            );
        });

        test('should throw error when dataset config is not set', async () => {
            await expect(dataset.create()).rejects.toThrow(DatasetError);
        });

        test('should throw error when dataset already exists', async () => {
            const config: DatasetConfig = {
                id: 'dataset-123',
                name: 'test-dataset',
            };

            (dataset as any)._datasetConfig = config;
            await expect(dataset.create()).rejects.toThrow(DatasetError);
        });
    });

    describe('download', () => {
        test('should download dataset', async () => {
            const config: DatasetConfig = {
                id: 'dataset-123',
                name: 'test-dataset',
            };

            (dataset as any)._datasetConfig = config;
            mockRequest.mockResolvedValue({
                id: 'dataset-123',
                columns: [],
                rows: [],
                metadata: {},
            });

            const result = await dataset.download();
            expect(result).toBe(dataset);
            expect(mockRequest).toHaveBeenCalled();
        });

        test('should download dataset to memory', async () => {
            const config: DatasetConfig = {
                id: 'dataset-123',
                name: 'test-dataset',
            };

            const mockTable: DatasetTable = {
                id: 'dataset-123',
                columns: [],
                rows: [],
                metadata: {},
            };

            (dataset as any)._datasetConfig = config;
            mockRequest.mockResolvedValue(mockTable);

            const result = await dataset.download(undefined, true);
            expect(result).toEqual(mockTable);
        });

        test('should throw error when dataset name is not set', async () => {
            await expect(dataset.download()).rejects.toThrow(DatasetError);
        });

        test('should throw error when dataset ID is not set', async () => {
            const config: DatasetConfig = {
                name: 'test-dataset',
            };

            (dataset as any)._datasetConfig = config;
            await expect(dataset.download()).rejects.toThrow(DatasetError);
        });
    });

    describe('delete', () => {
        test('should delete dataset', async () => {
            const config: DatasetConfig = {
                id: 'dataset-123',
                name: 'test-dataset',
            };

            (dataset as any)._datasetConfig = config;
            mockRequest.mockResolvedValue({});

            await dataset.delete();
            expect((dataset as any)._datasetConfig).toBeNull();
            expect(mockRequest).toHaveBeenCalledWith(
                expect.objectContaining({
                    method: 'DELETE',
                    json: { dataset_ids: ['dataset-123'] },
                }),
                DatasetResponseHandler
            );
        });

        test('should throw error when dataset ID is not set', async () => {
            await expect(dataset.delete()).rejects.toThrow(DatasetError);
        });
    });

    describe('addColumns', () => {
        test('should add columns to dataset', async () => {
            const config: DatasetConfig = {
                id: 'dataset-123',
                name: 'test-dataset',
            };

            const columns = [
                createColumn({ name: 'col1', dataType: DataTypeChoices.TEXT }),
                createColumn({ name: 'col2', dataType: DataTypeChoices.INTEGER }),
            ];

            (dataset as any)._datasetConfig = config;
            mockRequest.mockResolvedValue({});

            const result = await dataset.addColumns(columns);
            expect(result).toBe(dataset);
            expect(mockRequest).toHaveBeenCalledWith(
                expect.objectContaining({
                    method: 'POST',
                    json: { new_columns_data: expect.any(Array) },
                }),
                DatasetResponseHandler
            );
        });

        test('should throw error when dataset ID is not set', async () => {
            const columns = [
                createColumn({ name: 'col1', dataType: DataTypeChoices.TEXT }),
            ];

            await expect(dataset.addColumns(columns)).rejects.toThrow(DatasetError);
        });

        test('should throw error for empty columns array', async () => {
            const config: DatasetConfig = {
                id: 'dataset-123',
                name: 'test-dataset',
            };

            (dataset as any)._datasetConfig = config;
            await expect(dataset.addColumns([])).rejects.toThrow(DatasetValidationError);
        });
    });

    describe('addRows', () => {
        test('should add rows to dataset', async () => {
            const config: DatasetConfig = {
                id: 'dataset-123',
                name: 'test-dataset',
            };

            const rows = [
                createRow({
                    cells: [
                        createCell({ columnId: 'col-1', rowId: 'row-1', value: 'test' }),
                    ],
                }),
            ];

            (dataset as any)._datasetConfig = config;
            mockRequest.mockResolvedValue({});

            const result = await dataset.addRows(rows);
            expect(result).toBe(dataset);
            expect(mockRequest).toHaveBeenCalledWith(
                expect.objectContaining({
                    method: 'POST',
                    json: { rows: expect.any(Array) },
                }),
                DatasetResponseHandler
            );
        });

        test('should throw error when dataset ID is not set', async () => {
            const rows = [
                createRow({
                    cells: [
                        createCell({ columnId: 'col-1', rowId: 'row-1', value: 'test' }),
                    ],
                }),
            ];

            await expect(dataset.addRows(rows)).rejects.toThrow(DatasetError);
        });

        test('should throw error for empty rows array', async () => {
            const config: DatasetConfig = {
                id: 'dataset-123',
                name: 'test-dataset',
            };

            (dataset as any)._datasetConfig = config;
            await expect(dataset.addRows([])).rejects.toThrow(DatasetValidationError);
        });
    });

    describe('addRunPrompt', () => {
        test('should add a run prompt with correct payload', async () => {
            const config: DatasetConfig = {
                id: 'dataset-123',
                name: 'test-dataset',
            };

            (dataset as any)._datasetConfig = config;
            mockRequest.mockResolvedValue({});

            const options = {
                name: 'my_prompt',
                model: 'gpt-3.5-turbo',
                messages: [{ role: 'user', content: 'Hello' }],
            };

            const result = await dataset.addRunPrompt(options as any);
            expect(result).toBe(dataset);
            expect(mockRequest).toHaveBeenCalledWith(
                expect.objectContaining({
                    method: 'POST',
                    json: expect.objectContaining({
                        dataset_id: 'dataset-123',
                        name: 'my_prompt',
                        config: expect.objectContaining({
                            model: 'gpt-3.5-turbo',
                            messages: options.messages,
                        }),
                    }),
                }),
                DatasetResponseHandler
            );
        });

        test('should throw error when dataset ID is not set', async () => {
            const options = {
                name: 'my_prompt',
                model: 'gpt-3.5-turbo',
                messages: [{ role: 'user', content: 'Hello' }],
            };

            await expect(dataset.addRunPrompt(options as any)).rejects.toThrow(DatasetError);
        });
    });

    describe('getColumnId', () => {
        test('should get column ID by name', async () => {
            const config: DatasetConfig = {
                id: 'dataset-123',
                name: 'test-dataset',
            };

            const mockTable: DatasetTable = {
                id: 'dataset-123',
                columns: [
                    {
                        id: 'col-1',
                        name: 'test_column',
                        dataType: DataTypeChoices.TEXT,
                        source: SourceChoices.OTHERS,
                        metadata: {},
                        isFrozen: false,
                        isVisible: true,
                        evalTags: [],
                        orderIndex: 0,
                    },
                ],
                rows: [],
                metadata: {},
            };

            (dataset as any)._datasetConfig = config;
            mockRequest.mockResolvedValue(mockTable);

            const result = await dataset.getColumnId('test_column');
            expect(result).toBe('col-1');
        });

        test('should return null for non-existent column', async () => {
            const config: DatasetConfig = {
                id: 'dataset-123',
                name: 'test-dataset',
            };

            const mockTable: DatasetTable = {
                id: 'dataset-123',
                columns: [],
                rows: [],
                metadata: {},
            };

            (dataset as any)._datasetConfig = config;
            mockRequest.mockResolvedValue(mockTable);

            const result = await dataset.getColumnId('non_existent_column');
            expect(result).toBeNull();
        });

        test('should throw error when dataset ID is not set', async () => {
            await expect(dataset.getColumnId('test_column')).rejects.toThrow(DatasetError);
        });

        test('should throw error for empty column name', async () => {
            const config: DatasetConfig = {
                id: 'dataset-123',
                name: 'test-dataset',
            };

            (dataset as any)._datasetConfig = config;
            await expect(dataset.getColumnId('')).rejects.toThrow(DatasetValidationError);
        });
    });

    describe('static methods', () => {
        test('should create dataset using static method', async () => {
            const config: DatasetConfig = {
                name: 'test-dataset',
            };

            const mockDatasetInstance = new Dataset();
            const mockCreate = jest.fn().mockResolvedValue(mockDatasetInstance);
            jest.spyOn(Dataset.prototype, 'create').mockImplementation(mockCreate);
            
            const result = await Dataset.createDataset(config, undefined, {
                fiApiKey: 'test-key',
                fiSecretKey: 'test-secret',
            });

            expect(result).toBeInstanceOf(Dataset);
            // This assertion is tricky because create is called on a new instance
            // A better test would be to mock the constructor
        });

        test('should download dataset using static method', async () => {
            const mockDownload = jest.fn().mockResolvedValue('csv content');
            const mockFetchConfig = jest.fn().mockResolvedValue({
                id: 'dataset-123',
                name: 'test-dataset',
            });

            // Mock the internal methods on the prototype
            jest.spyOn(Dataset.prototype as any, '_fetchDatasetConfig').mockImplementation(mockFetchConfig);
            jest.spyOn(Dataset.prototype, 'download').mockImplementation(mockDownload);

            const result = await Dataset.downloadDataset('test-dataset');
            expect(result).toBe('csv content');
            expect(mockDownload).toHaveBeenCalled();
        });

        test('should delete dataset using static method', async () => {
            const mockDelete = jest.fn().mockResolvedValue(undefined);
            const mockFetchConfig = jest.fn().mockResolvedValue({
                id: 'dataset-123',
                name: 'test-dataset',
            });
            
            jest.spyOn(Dataset.prototype as any, '_fetchDatasetConfig').mockImplementation(mockFetchConfig);
            jest.spyOn(Dataset.prototype, 'delete').mockImplementation(mockDelete);

            await Dataset.deleteDataset('test-dataset');
            expect(mockDelete).toHaveBeenCalled();
        });
    });
}); 