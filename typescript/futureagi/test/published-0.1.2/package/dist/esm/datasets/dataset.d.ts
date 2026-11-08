// Generated public declarations from @future-agi/sdk 0.1.2; do not edit.
import { AxiosResponse } from 'axios';
import { APIKeyAuth, APIKeyAuthConfig, ResponseHandler } from '../api/auth.js';
import { DatasetConfig, DatasetTable, HuggingfaceDatasetConfig, Column, Row } from './types.js';
/**
 * Response handler for dataset operations
 */
export declare class DatasetResponseHandler extends ResponseHandler {
    static _parseSuccess(response: AxiosResponse): DatasetConfig | DatasetTable;
    static _handleError(response: AxiosResponse): never;
}
/**
 * Dataset manager class for handling dataset operations
 */
export declare class Dataset extends APIKeyAuth {
    constructor(config?: APIKeyAuthConfig & {
        datasetConfig?: DatasetConfig;
    });
    create(source?: string | HuggingfaceDatasetConfig): Promise<Dataset>;
    download(filePath?: string, loadToMemory?: boolean): Promise<Dataset | string | object>;
    delete(): Promise<void>;
    getConfig(): DatasetConfig;
    addColumns(columns: Array<Column | Partial<Column>>): Promise<Dataset>;
    addRows(rows: Array<Row | Partial<Row>>): Promise<Dataset>;
    getColumnId(columnName: string): Promise<string | null>;
    addRunPrompt(options: {
        name: string;
        model: string;
        messages: Array<{
            role: string;
            content: string;
        }>;
        outputFormat?: string;
        concurrency?: number;
        maxTokens?: number;
        temperature?: number;
        presencePenalty?: number;
        frequencyPenalty?: number;
        topP?: number;
        tools?: Array<Record<string, any>>;
        toolChoice?: any;
        responseFormat?: Record<string, any>;
    }): Promise<Dataset>;
    addEvaluation(options: {
        name: string;
        evalTemplate: string;
        requiredKeysToColumnNames: Record<string, string>;
        saveAsTemplate?: boolean;
        run?: boolean;
        reasonColumn?: boolean;
        config?: Record<string, any>;
        model: string;
        errorLocalizer?: boolean;
        kbId?: string;
    }): Promise<Dataset>;
    getEvalStats(): Promise<Record<string, any>>;
    addOptimization(options: {
        optimizationName: string;
        promptColumnName: string;
        optimizeType?: string;
        modelConfig?: Record<string, any>;
    }): Promise<Dataset>;
    static createDataset(datasetConfig: DatasetConfig, source?: string | HuggingfaceDatasetConfig, options?: APIKeyAuthConfig): Promise<Dataset>;
    static downloadDataset(datasetName: string, filePath?: string, loadToMemory?: boolean, options?: APIKeyAuthConfig): Promise<string | object>;
    static deleteDataset(datasetName: string, options?: APIKeyAuthConfig): Promise<void>;
    static getDatasetConfig(datasetName: string, options?: APIKeyAuthConfig): Promise<DatasetConfig>;
    static addDatasetColumns(datasetName: string, columns: Array<Column | Partial<Column>>, options?: APIKeyAuthConfig): Promise<void>;
    static addDatasetRows(datasetName: string, rows: Array<Row | Partial<Row>>, options?: APIKeyAuthConfig): Promise<void>;
    /**
     * Unified helper that always returns a ready-to-use Dataset instance.
     * If the dataset already exists it is fetched; otherwise it is created (unless createIfMissing === false).
     */
    static open(datasetName: string, opts?: {
        createIfMissing?: boolean;
    } & APIKeyAuthConfig): Promise<Dataset>;
}
export type PublishedCall792 = (source?: string | HuggingfaceDatasetConfig) => Promise<Dataset>;
export type PublishedCall866 = (filePath?: string, loadToMemory?: boolean) => Promise<Dataset | string | object>;
export type PublishedCall959 = () => Promise<void>;
export type PublishedCall988 = () => DatasetConfig;
export type PublishedCall1020 = (columns: Array<Column | Partial<Column>>) => Promise<Dataset>;
export type PublishedCall1096 = (rows: Array<Row | Partial<Row>>) => Promise<Dataset>;
export type PublishedCall1160 = (columnName: string) => Promise<string | null>;
export type PublishedCall1221 = (options: {
    name: string;
    model: string;
    messages: Array<{
        role: string;
        content: string;
    }>;
    outputFormat?: string;
    concurrency?: number;
    maxTokens?: number;
    temperature?: number;
    presencePenalty?: number;
    frequencyPenalty?: number;
    topP?: number;
    tools?: Array<Record<string, any>>;
    toolChoice?: any;
    responseFormat?: Record<string, any>;
}) => Promise<Dataset>;
export type PublishedCall1740 = (options: {
    name: string;
    evalTemplate: string;
    requiredKeysToColumnNames: Record<string, string>;
    saveAsTemplate?: boolean;
    run?: boolean;
    reasonColumn?: boolean;
    config?: Record<string, any>;
    model: string;
    errorLocalizer?: boolean;
    kbId?: string;
}) => Promise<Dataset>;
export type PublishedCall2113 = () => Promise<Record<string, any>>;
export type PublishedCall2163 = (options: {
    optimizationName: string;
    promptColumnName: string;
    optimizeType?: string;
    modelConfig?: Record<string, any>;
}) => Promise<Dataset>;
export type PublishedCall2626 = (datasetConfig: DatasetConfig, source?: string | HuggingfaceDatasetConfig, options?: APIKeyAuthConfig) => Promise<Dataset>;
export type PublishedCall2772 = (datasetName: string, filePath?: string, loadToMemory?: boolean, options?: APIKeyAuthConfig) => Promise<string | object>;
export type PublishedCall2918 = (datasetName: string, options?: APIKeyAuthConfig) => Promise<void>;
export type PublishedCall3008 = (datasetName: string, options?: APIKeyAuthConfig) => Promise<DatasetConfig>;
export type PublishedCall3110 = (datasetName: string, columns: Array<Column | Partial<Column>>, options?: APIKeyAuthConfig) => Promise<void>;
export type PublishedCall3246 = (datasetName: string, rows: Array<Row | Partial<Row>>, options?: APIKeyAuthConfig) => Promise<void>;
export type PublishedCall3370 = (datasetName: string, opts?: {
    createIfMissing?: boolean;
} & APIKeyAuthConfig) => Promise<Dataset>;
export type PublishedCall336 = (response: AxiosResponse) => DatasetConfig | DatasetTable;
export type PublishedCall417 = (response: AxiosResponse) => never;
