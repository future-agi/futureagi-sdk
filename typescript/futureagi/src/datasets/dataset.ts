import { AxiosResponse } from 'axios';
import { v4 as uuidv4 } from 'uuid';
import * as fs from 'fs';
import * as path from 'path';
import FormData from 'form-data';
import { APIKeyAuth, APIKeyAuthConfig, ResponseHandler } from '../api/auth';
import { HttpMethod, RequestConfig } from '../api/types';
import { Routes } from '../utils/routes';
import { DEFAULT_SETTINGS } from '../utils/constants';
import {
    DatasetError,
    DatasetNotFoundError,
    DatasetAuthError,
    DatasetValidationError,
    RateLimitError,
    ServerError,
    ServiceUnavailableError,
} from '../utils/errors';
import {
    DatasetConfig,
    DatasetTable,
    HuggingfaceDatasetConfig,
    Column,
    Row,
    Cell,
    createColumn,
    createRow,
    createCell,
    DatasetTableUtils,
    DataTypeChoices,
    SourceChoices,
    ModelTypes,
} from './types';

const DEFAULT_API_TIMEOUT = 30000; // 30 seconds in milliseconds

/**
 * Simple LRU Cache implementation
 */
class LRUCache<K, V> {
    private capacity: number;
    private cache: Map<K, V>;
    private accessOrder: K[];

    constructor(capacity: number = 100) {
        this.capacity = capacity;
        this.cache = new Map();
        this.accessOrder = [];
    }

    get(key: K): V | null {
        if (this.cache.has(key)) {
            const index = this.accessOrder.indexOf(key);
            if (index > -1) {
                this.accessOrder.splice(index, 1);
            }
            this.accessOrder.push(key);
            return this.cache.get(key) || null;
        }
        return null;
    }

    put(key: K, value: V): void {
        if (this.cache.has(key)) {
            const index = this.accessOrder.indexOf(key);
            if (index > -1) {
                this.accessOrder.splice(index, 1);
            }
        } else if (this.cache.size >= this.capacity) {
            if (this.accessOrder.length > 0) {
                const oldest = this.accessOrder.shift();
                if (oldest !== undefined) {
                    this.cache.delete(oldest);
                }
            }
        }
        
        this.cache.set(key, value);
        this.accessOrder.push(key);
    }

    clear(): void {
        this.cache.clear();
        this.accessOrder = [];
    }
}

/**
 * Response handler for dataset operations
 */
export class DatasetResponseHandler extends ResponseHandler {
    static _parseSuccess(response: AxiosResponse): DatasetConfig | DatasetTable {
        const data = response.data;
        const url = response.config.url || '';

        if (url.includes(Routes.dataset_names)) {
            const datasets = data.result?.datasets;
            if (!datasets || datasets.length === 0) {
                throw new DatasetNotFoundError("No dataset found matching the criteria.");
            }
            if (datasets.length > 1) {
                throw new Error("Multiple datasets found. Please specify a dataset name.");
            }
            
            return {
                id: datasets[0].datasetId,
                name: datasets[0].name,
                modelType: datasets[0].modelType,
            };
        }

        if (url.includes('/get-dataset-table/')) {
            const id = url.split('/').slice(-3, -2)[0];
            const result = data.result;
            
            const columns: Column[] = result.columnConfig.map((col: any) => ({
                id: col.id,
                name: col.name,
                dataType: col.dataType,
                source: col.originType,
                sourceId: col.sourceId,
                isFrozen: col.isFrozen?.isFrozen || false,
                isVisible: col.isVisible,
                evalTags: col.evalTag || [],
                averageScore: col.averageScore,
                orderIndex: col.orderIndex,
            }));

            const rows: Row[] = result.table.map((row: any) => {
                const cells: Cell[] = [];
                const rowId = row.rowId;
                const order = row.order;
                
                Object.entries(row).forEach(([columnId, value]: [string, any]) => {
                    if (columnId !== 'rowId' && columnId !== 'order') {
                        cells.push(createCell({
                            columnId,
                            rowId,
                            value: value?.cellValue,
                            valueInfos: value?.valueInfos ? [value.valueInfos] : [],
                            metadata: value?.metadata,
                            status: value?.status,
                            failureReason: value?.failureReason,
                        }));
                    }
                });

                return createRow({ cells, order });
            });

            return {
                id,
                columns,
                rows,
                metadata: result.metadata,
            };
        }

        if (url.includes(Routes.dataset_empty) || 
            url.includes(Routes.dataset_local) || 
            url.includes(Routes.dataset_huggingface)) {
            return {
                id: data.result.datasetId,
                name: data.result.datasetName,
                modelType: data.result.datasetModelType,
            };
        }

        return data;
    }

    static _handleError(response: AxiosResponse): never {
        const errorMap = {
            400: DatasetValidationError,
            401: DatasetAuthError,
            403: DatasetAuthError,
            404: DatasetNotFoundError,
            429: RateLimitError,
            500: ServerError,
            503: ServiceUnavailableError,
        };

        const ErrorClass = errorMap[response.status as keyof typeof errorMap] || DatasetError;
        
        if (response.status > 500 && response.status < 600 && ErrorClass === DatasetError) {
            throw new ServerError(response.data?.message || response.statusText);
        }

        let message: string;
        try {
            const errorData = response.data;
            message = errorData?.detail || errorData?.message || errorData?.error || 
                     JSON.stringify(errorData) || response.statusText;
        } catch {
            message = response.statusText || `HTTP error ${response.status} with no descriptive message.`;
        }

        throw new ErrorClass(message);
    }
}

/**
 * Dataset manager class for handling dataset operations
 */
export class Dataset extends APIKeyAuth {
    private static _datasetInstanceCache = new LRUCache<string, Dataset>(100);
    private _datasetConfig: DatasetConfig | null = null;

    constructor(config: APIKeyAuthConfig & { datasetConfig?: DatasetConfig } = {}) {
        super(config);
        
        if (config.datasetConfig) {
            // Directly assign; caller will decide whether to call create()
            this._datasetConfig = config.datasetConfig;
        }
    }

    private async _initializeDatasetConfig(datasetConfig: DatasetConfig): Promise<void> {
        try {
            const fetchedConfig = await this._fetchDatasetConfig(datasetConfig.name);
            this._datasetConfig = fetchedConfig;
        } catch (error) {
            if (error instanceof DatasetNotFoundError) {
                this._datasetConfig = datasetConfig;
            } else {
                throw new DatasetError(`Failed to initialize dataset configuration for ${datasetConfig.name}: ${error}`);
            }
        }
    }

    // Instance methods for chaining
    async create(source?: string | HuggingfaceDatasetConfig): Promise<Dataset> {
        if (!this._datasetConfig) {
            throw new DatasetError("dataset_config must be set before creating a dataset.");
        }

        if (this._datasetConfig.id) {
            throw new DatasetError(`Dataset '${this._datasetConfig.name}' appears to already exist with ID: ${this._datasetConfig.id}.`);
        }

        const responseConfig = await this._createDataset(this._datasetConfig, source);
        this._datasetConfig = {
            ...this._datasetConfig,
            id: responseConfig.id,
            name: responseConfig.name,
            modelType: responseConfig.modelType,
        };
        
        return this;
    }

    async download(filePath?: string, loadToMemory: boolean = false): Promise<Dataset | string | object> {
        if (!this._datasetConfig?.name) {
            throw new DatasetError("Dataset name must be configured to download.");
        }
        if (!this._datasetConfig.id) {
            throw new DatasetError(`Dataset '${this._datasetConfig.name}' must have an ID to be downloaded. Fetch config first if ID is missing.`);
        }

        const result = await this._downloadDataset(this._datasetConfig.name, filePath, loadToMemory);
        return loadToMemory ? result : this;
    }

    async delete(): Promise<void> {
        if (!this._datasetConfig?.id) {
            throw new DatasetError("Dataset ID must be configured to delete.");
        }
        
        await this._deleteDataset();
        this._datasetConfig = null;
    }

    getConfig(): DatasetConfig {
        if (!this._datasetConfig) {
            throw new DatasetError("No dataset configured for this instance.");
        }
        return this._datasetConfig;
    }

    async addColumns(columns: Array<Column | Partial<Column>>): Promise<Dataset> {
        if (!this._datasetConfig?.id) {
            throw new DatasetError("Dataset must be configured with an ID to add columns.");
        }

        if (!columns || columns.length === 0) {
            throw new DatasetValidationError("Columns list cannot be empty.");
        }

        const processedColumns: Column[] = columns.map(col => {
            if ('id' in col && col.id) {
                // Already a complete Column
                return col as Column;
            } else {
                // Create column from partial data
                return createColumn({
                    name: col.name || '',
                    dataType: col.dataType || DataTypeChoices.TEXT,
                    source: col.source,
                    sourceId: col.sourceId,
                    metadata: col.metadata,
                    isFrozen: col.isFrozen,
                    isVisible: col.isVisible,
                    evalTags: col.evalTags,
                    averageScore: col.averageScore,
                    orderIndex: col.orderIndex,
                });
            }
        });

        await this._addColumns(processedColumns);
        return this;
    }

    async addRows(rows: Array<Row | Partial<Row>>): Promise<Dataset> {
        if (!this._datasetConfig?.id) {
            throw new DatasetError("Dataset must be configured with an ID to add rows.");
        }

        if (!rows || rows.length === 0) {
            throw new DatasetValidationError("Rows list cannot be empty.");
        }

        const processedRows: Row[] = rows.map(row => {
            if ('id' in row && row.id) {
                // Already a complete Row
                return row as Row;
            } else {
                // Create row from partial data
                const cells = row.cells?.map(cell => 
                    'columnId' in cell && cell.columnId ? 
                    cell as Cell : 
                    createCell({
                        columnId: cell.columnId || '',
                        rowId: row.id || uuidv4(),
                        columnName: cell.columnName,
                        value: cell.value,
                        valueInfos: cell.valueInfos,
                        metadata: cell.metadata,
                        status: cell.status,
                        failureReason: cell.failureReason,
                    })
                ) || [];

                return createRow({ cells, order: row.order });
            }
        });

        await this._addRows(processedRows);
        return this;
    }

    async getColumnId(columnName: string): Promise<string | null> {
        if (!this._datasetConfig?.id) {
            throw new DatasetError("Dataset must be configured with an ID to get a column ID.");
        }
        if (!columnName) {
            throw new DatasetValidationError("Column name cannot be empty.");
        }

        const url = `${this._baseUrl}/${Routes.dataset_table.replace('{dataset_id}', this._datasetConfig.id)}`;
        const datasetTable = await this.request<DatasetTable>(
            {
                method: HttpMethod.GET,
                url,
                params: { page_size: 1, current_page_index: 0 },
                timeout: DEFAULT_API_TIMEOUT,
            },
            DatasetResponseHandler
        ) as DatasetTable;

        const column = datasetTable.columns.find(col => col.name === columnName);
        return column?.id || null;
    }

    async addRunPrompt(options: {
        name: string;
        model: string;
        messages: Array<{ role: string; content: string }>;
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
    }): Promise<Dataset> {
        if (!this._datasetConfig?.id) {
            throw new DatasetError("Dataset must be configured with an ID to add a run prompt column.");
        }

        const {
            name,
            model,
            messages,
            outputFormat = "string",
            concurrency = 5,
            maxTokens = 500,
            temperature = 0.5,
            presencePenalty = 1,
            frequencyPenalty = 1,
            topP = 1,
            tools,
            toolChoice,
            responseFormat,
        } = options;

        if (!name) {
            throw new DatasetValidationError("Run prompt column name cannot be empty.");
        }
        if (!model) {
            throw new DatasetValidationError("Model cannot be empty for run prompt.");
        }
        if (!messages || messages.length === 0) {
            throw new DatasetValidationError("Messages list cannot be empty for run prompt.");
        }

        // Process messages to handle column references and format conversion (parity with Python SDK)
        const processedMessages = [];
        const referencedColumns = new Set<string>();

        for (const msg of messages) {
            const processedMsg: any = { ...msg };
            
            // Set default role if not provided
            if (!processedMsg.role) {
                processedMsg.role = "user";
            }

            if (processedMsg.content) {
                let content = processedMsg.content;
                
                // Convert string content to the expected list format
                if (typeof content === "string") {
                    // Handle column references in string content
                    const columnRefs = content.match(/\{\{(.*?)\}\}/g) || [];
                    for (const ref of columnRefs) {
                        const colName = ref.slice(2, -2); // Remove {{ and }}
                        const colId = await this.getColumnId(colName);
                        if (!colId) {
                            throw new DatasetError(
                                `Referenced column '${ref}' not found in dataset '${this._datasetConfig.name}'`
                            );
                        }
                        referencedColumns.add(colName);
                        content = content.replace(ref, `{{${colId}}}`);
                    }
                    
                    // Convert to expected format: list of dictionaries
                    processedMsg.content = [{ type: "text", text: content }];
                    
                } else if (Array.isArray(content)) {
                    // Handle list content (already in expected format)
                    const processedContent = [];
                    for (const contentItem of content) {
                        if (typeof contentItem === "object" && contentItem !== null) {
                            const processedItem = { ...contentItem };
                            // Handle column references in dict content
                            if (processedItem.text) {
                                let textContent = processedItem.text;
                                const columnRefs = textContent.match(/\{\{(.*?)\}\}/g) || [];
                                for (const ref of columnRefs) {
                                    const colName = ref.slice(2, -2); // Remove {{ and }}
                                    const colId = await this.getColumnId(colName);
                                    if (!colId) {
                                        throw new DatasetError(
                                            `Referenced column '${ref}' not found in dataset '${this._datasetConfig.name}'`
                                        );
                                    }
                                    referencedColumns.add(colName);
                                    textContent = textContent.replace(ref, `{{${colId}}}`);
                                }
                                processedItem.text = textContent;
                            }
                            processedContent.push(processedItem);
                        } else {
                            // If list item is not a dict, treat as text
                            processedContent.push({ type: "text", text: String(contentItem) });
                        }
                    }
                    processedMsg.content = processedContent;
                }
            }

            processedMessages.push(processedMsg);
        }

        // Build payload in parity with Python SDK
        const payload: Record<string, any> = {
            dataset_id: this._datasetConfig.id,
            name,
            config: {
                model,
                output_format: outputFormat,
                concurrency,
                messages: processedMessages,
                max_tokens: maxTokens,
                temperature,
                presence_penalty: presencePenalty,
                frequency_penalty: frequencyPenalty,
                top_p: topP,
            },
        };

        if (tools) {
            payload.config.tools = tools;
        }
        if (typeof toolChoice !== "undefined") {
            payload.config.tool_choice = toolChoice;
        }
        if (responseFormat) {
            payload.config.response_format = responseFormat;
        }

        const url = `${this._baseUrl}/${Routes.dataset_add_run_prompt_column}`;
        await this.request(
            {
                method: HttpMethod.POST,
                url,
                json: payload,
                timeout: DEFAULT_API_TIMEOUT,
            },
            DatasetResponseHandler
        );

        return this;
    }

    async addEvaluation(options: {
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
    }): Promise<Dataset> {
        if (!this._datasetConfig?.id) {
            throw new DatasetError("Dataset must be configured with an ID to add evaluation.");
        }

        const {
            name,
            evalTemplate,
            requiredKeysToColumnNames,
            saveAsTemplate = false,
            run = true,
            reasonColumn = false,
            config,
            model,
            errorLocalizer = false,
            kbId,
        } = options;

        if (!name) {
            throw new DatasetValidationError("Evaluation name cannot be empty.");
        }
        if (!evalTemplate) {
            throw new DatasetValidationError("Evaluation template cannot be empty.");
        }
        if (!requiredKeysToColumnNames || Object.keys(requiredKeysToColumnNames).length === 0) {
            throw new DatasetValidationError("Required keys to column names mapping cannot be empty.");
        }
        if (!model) {
            throw new DatasetValidationError("Model cannot be empty for evaluation.");
        }

        // --- Fetch evaluation template details -------------------------------------------------
        // Define a lightweight response handler (avoids cross-package deps)
        class EvalInfoResponseHandler extends ResponseHandler {
            static _parseSuccess(response: AxiosResponse): any {
                const data = response.data;
                if (data && data.result) {
                    return data.result;
                }
                throw new DatasetError(`Failed to fetch evaluation info: ${JSON.stringify(data)}`);
            }
            static _handleError(response: AxiosResponse): never {
                if (response.status === 403 || response.status === 401) {
                    throw new DatasetAuthError("Authentication failed while fetching evaluation info.");
                }
                throw new DatasetError(`Failed to fetch evaluation info: ${response.status} ${response.statusText}`);
            }
        }

        // Fetch all templates once and filter locally (mirrors Python SDK logic)
        const allTemplates = await this.request<any>(
            {
                method: HttpMethod.GET,
                url: `${this._baseUrl}/${Routes.get_eval_templates}`,
                timeout: DEFAULT_API_TIMEOUT,
            },
            EvalInfoResponseHandler
        ) as Array<Record<string, any>>;

        const matchedListItem = allTemplates.find((tpl: any) => {
            const tplName: string = tpl.name || tpl.eval_name || tpl.template_name || "";
            return tplName.toLowerCase() === evalTemplate.toLowerCase();
        });

        if (!matchedListItem) {
            throw new DatasetValidationError(`Unknown or unsupported evaluation template: ${evalTemplate}`);
        }

        const evalId = matchedListItem.eval_id || matchedListItem.evalId || matchedListItem.id;
        if (!evalId) {
            throw new DatasetError(`Failed to determine eval_id for template '${evalTemplate}'.`);
        }

        // Now fetch detailed info for this template to obtain template_id & required_keys
        const templateDetail = await this.request<any>(
            {
                method: HttpMethod.GET,
                url: `${this._baseUrl}/${Routes.evaluate_template.replace('{eval_id}', evalId)}`,
                timeout: DEFAULT_API_TIMEOUT,
            },
            EvalInfoResponseHandler
        ) as Record<string, any>;

        const templateId = templateDetail.id;
        const requiredKeys: string[] = templateDetail.config?.required_keys || [];

        if (!templateId) {
            throw new DatasetError(`template_id not found for evaluation template '${evalTemplate}'.`);
        }

        // --- Build column mapping -------------------------------------------------------------
        const mapping: Record<string, string> = {};
        for (const key of requiredKeys) {
            if (!(key in requiredKeysToColumnNames)) {
                throw new DatasetValidationError(`Required key '${key}' not found in requiredKeysToColumnNames for template '${evalTemplate}'.`);
            }
            const columnName = requiredKeysToColumnNames[key];
            if (!columnName) {
                throw new DatasetValidationError(`Column name mapping for key '${key}' cannot be empty.`);
            }
            const columnId = await this.getColumnId(columnName);
            if (!columnId) {
                throw new DatasetError(`Column '${columnName}' (mapped from key '${key}') not found in dataset '${this._datasetConfig.name}'.`);
            }
            mapping[key] = columnId;
        }

        // --- Prepare payload ------------------------------------------------------------------
        const evalConfigPayload: Record<string, any> = {
            template_id: templateId,
            run,
            name,
            saveAsTemplate,
            config: {
                mapping,
                config: config || {},
                reasonColumn: reasonColumn,
            },
        };

        // Add optional fields to the top level payload
        if (model) {
            evalConfigPayload.model = model;
        }
        if (errorLocalizer) {
            evalConfigPayload.error_localizer = errorLocalizer;
        }
        if (kbId) {
            evalConfigPayload.kb_id = kbId;
        }

        const url = `${this._baseUrl}/${Routes.dataset_add_evaluation.replace('{dataset_id}', this._datasetConfig.id)}`;
        await this.request(
            {
                method: HttpMethod.POST,
                url,
                json: evalConfigPayload,
                timeout: DEFAULT_API_TIMEOUT,
            },
            DatasetResponseHandler
        );

        return this;
    }

    async getEvalStats(): Promise<Record<string, any>> {
        if (!this._datasetConfig?.id) {
            throw new DatasetError("Dataset must be configured with an ID to get evaluation stats.");
        }

        const url = `${this._baseUrl}/${Routes.dataset_eval_stats.replace('{dataset_id}', this._datasetConfig.id)}`;
        const response = await this.request<any>(
            {
                method: HttpMethod.GET,
                url,
                timeout: DEFAULT_API_TIMEOUT,
            },
            DatasetResponseHandler
        );

        return response.result || {};
    }

    async addOptimization(options: {
        optimizationName: string;
        promptColumnName: string;
        optimizeType?: string;
        modelConfig?: Record<string, any>;
    }): Promise<Dataset> {
        if (!this._datasetConfig?.id) {
            throw new DatasetError("Dataset must be configured with an ID to add optimization.");
        }

        const {
            optimizationName,
            promptColumnName,
            optimizeType = "PROMPT_TEMPLATE",
            modelConfig,
        } = options;

        if (!optimizationName) {
            throw new DatasetValidationError("Optimization name cannot be empty.");
        }
        if (!promptColumnName) {
            throw new DatasetValidationError("Prompt column name cannot be empty.");
        }

        const url = `${this._baseUrl}/${Routes.dataset_optimization_create}`;
        await this.request(
            {
                method: HttpMethod.POST,
                url,
                json: {
                    dataset_id: this._datasetConfig.id,
                    optimization_name: optimizationName,
                    prompt_column_name: promptColumnName,
                    optimize_type: optimizeType,
                    model_config: modelConfig,
                },
                timeout: DEFAULT_API_TIMEOUT,
            },
            DatasetResponseHandler
        );

        return this;
    }

    // Private methods
    private async _fetchDatasetConfig(datasetName: string): Promise<DatasetConfig> {
        const url = `${this._baseUrl}/${Routes.dataset_names}`;
        const response = await this.request<DatasetConfig>(
            {
                method: HttpMethod.GET,
                url,
                params: { search_text: datasetName },
                timeout: DEFAULT_API_TIMEOUT,
            },
            DatasetResponseHandler
        ) as DatasetConfig;

        return response;
    }

    private async _createDataset(
        config: DatasetConfig,
        source?: string | HuggingfaceDatasetConfig
    ): Promise<DatasetConfig> {
        if (!source) {
            return this._createEmptyDataset(config);
        }

        if (typeof source === 'string') {
            return this._createFromFile(config, source);
        }

        return this._createFromHuggingface(config, source);
    }

    private async _createEmptyDataset(config: DatasetConfig): Promise<DatasetConfig> {
        const url = `${this._baseUrl}/${Routes.dataset_empty}`;
        const response = await this.request<DatasetConfig>(
            {
                method: HttpMethod.POST,
                url,
                json: {
                    new_dataset_name: config.name,
                    model_type: config.modelType,
                },
                timeout: DEFAULT_API_TIMEOUT,
            },
            DatasetResponseHandler
        ) as DatasetConfig;

        return response;
    }

    private async _createFromFile(config: DatasetConfig, filePath: string): Promise<DatasetConfig> {
        const url = `${this._baseUrl}/${Routes.dataset_local}`;
        
        if (!fs.existsSync(filePath)) {
            throw new DatasetError(`File not found at path: ${filePath}`);
        }

        const formData = new FormData();
        formData.append('file', fs.createReadStream(filePath));
        formData.append('new_dataset_name', config.name);
        formData.append('model_type', config.modelType);

        const response = await this.request<DatasetConfig>(
            {
                method: HttpMethod.POST,
                url,
                data: formData,
                headers: formData.getHeaders(),
                timeout: DEFAULT_API_TIMEOUT,
            },
            DatasetResponseHandler
        ) as DatasetConfig;

        return response;
    }

    private async _createFromHuggingface(
        config: DatasetConfig,
        hfConfig: HuggingfaceDatasetConfig
    ): Promise<DatasetConfig> {
        const url = `${this._baseUrl}/${Routes.dataset_huggingface}`;
        const response = await this.request<DatasetConfig>(
            {
                method: HttpMethod.POST,
                url,
                json: {
                    new_dataset_name: config.name,
                    model_type: config.modelType,
                    huggingface_dataset_name: hfConfig.name,
                    huggingface_dataset_config: hfConfig.subset,
                    huggingface_dataset_split: hfConfig.split,
                    num_rows: hfConfig.numRows,
                },
                timeout: DEFAULT_API_TIMEOUT,
            },
            DatasetResponseHandler
        ) as DatasetConfig;

        return response;
    }

    private async _downloadDataset(
        name: string,
        filePath?: string,
        loadToMemory: boolean = false
    ): Promise<string | object> {
        if (!this._datasetConfig?.id) {
            throw new DatasetError("Dataset ID is required for download.");
        }

        const url = `${this._baseUrl}/${Routes.dataset_table.replace('{dataset_id}', this._datasetConfig.id)}`;
        const datasetTable = await this.request<DatasetTable>(
            {
                method: HttpMethod.GET,
                url,
                params: { page_size: 1000, current_page_index: 0 },
                timeout: DEFAULT_API_TIMEOUT,
            },
            DatasetResponseHandler
        ) as DatasetTable;

        if (loadToMemory) {
            return datasetTable;
        }

        const outputPath = filePath || `${name}.csv`;
        const csvContent = DatasetTableUtils.toCsv(datasetTable);
        
        try {
            fs.writeFileSync(outputPath, csvContent);
        } catch (error) {
            throw new DatasetError(`Failed to write dataset to file: ${error}`);
        }

        return outputPath;
    }

    private async _deleteDataset(): Promise<void> {
        if (!this._datasetConfig?.id) {
            throw new DatasetError("Dataset ID is required for deletion.");
        }

        const url = `${this._baseUrl}/${Routes.dataset_delete}`;
        await this.request(
            {
                method: HttpMethod.DELETE,
                url,
                json: { dataset_ids: [this._datasetConfig.id] },
                timeout: DEFAULT_API_TIMEOUT,
            },
            DatasetResponseHandler
        );
    }

    private async _addColumns(columns: Column[]): Promise<void> {
        if (!this._datasetConfig?.id) {
            throw new DatasetError("Dataset ID is required to add columns.");
        }

        const url = `${this._baseUrl}/${Routes.dataset_add_columns.replace('{dataset_id}', this._datasetConfig.id)}`;
        await this.request(
            {
                method: HttpMethod.POST,
                url,
                json: { new_columns_data: columns },
                timeout: DEFAULT_API_TIMEOUT,
            },
            DatasetResponseHandler
        );
    }

    private async _addRows(rows: Row[]): Promise<void> {
        if (!this._datasetConfig?.id) {
            throw new DatasetError("Dataset ID is required to add rows.");
        }

        const url = `${this._baseUrl}/${Routes.dataset_add_rows.replace('{dataset_id}', this._datasetConfig.id)}`;
        await this.request(
            {
                method: HttpMethod.POST,
                url,
                json: { rows },
                timeout: DEFAULT_API_TIMEOUT,
            },
            DatasetResponseHandler
        );
    }

    // Static methods
    static async createDataset(
        datasetConfig: DatasetConfig,
        source?: string | HuggingfaceDatasetConfig,
        options?: APIKeyAuthConfig
    ): Promise<Dataset> {
        const instance = new Dataset({ ...options, datasetConfig });
        return instance.create(source);
    }

    static async downloadDataset(
        datasetName: string,
        filePath?: string,
        loadToMemory: boolean = false,
        options?: APIKeyAuthConfig
    ): Promise<string | object> {
        const instance = new Dataset(options);
        const config = await instance._fetchDatasetConfig(datasetName);
        instance._datasetConfig = config;
        return instance.download(filePath, loadToMemory);
    }

    static async deleteDataset(datasetName: string, options?: APIKeyAuthConfig): Promise<void> {
        const instance = new Dataset(options);
        const config = await instance._fetchDatasetConfig(datasetName);
        instance._datasetConfig = config;
        await instance.delete();
    }

    static async getDatasetConfig(
        datasetName: string,
        options?: APIKeyAuthConfig
    ): Promise<DatasetConfig> {
        const instance = new Dataset(options);
        return instance._fetchDatasetConfig(datasetName);
    }

    static async addDatasetColumns(
        datasetName: string,
        columns: Array<Column | Partial<Column>>,
        options?: APIKeyAuthConfig
    ): Promise<void> {
        const instance = new Dataset(options);
        const config = await instance._fetchDatasetConfig(datasetName);
        instance._datasetConfig = config;
        await instance.addColumns(columns);
    }

    static async addDatasetRows(
        datasetName: string,
        rows: Array<Row | Partial<Row>>,
        options?: APIKeyAuthConfig
    ): Promise<void> {
        const instance = new Dataset(options);
        const config = await instance._fetchDatasetConfig(datasetName);
        instance._datasetConfig = config;
        await instance.addRows(rows);
    }

    /**
     * Unified helper that always returns a ready-to-use Dataset instance.
     * If the dataset already exists it is fetched; otherwise it is created (unless createIfMissing === false).
     */
    static async open(
        datasetName: string,
        opts: {
            createIfMissing?: boolean;
        } & APIKeyAuthConfig = {}
    ): Promise<Dataset> {

        const { createIfMissing = true, ...authOpts } = opts;

        try {
            // Try to fetch existing
            const cfg = await Dataset.getDatasetConfig(datasetName, authOpts);
            return new Dataset({ ...authOpts, datasetConfig: cfg });
        } catch (err) {
            if (err instanceof DatasetNotFoundError && createIfMissing) {
                // Create new dataset then return instance
                const dsConfig: DatasetConfig = {
                    name: datasetName,
                    modelType: ModelTypes.GENERATIVE_LLM,
                } as DatasetConfig;

                const instance = new Dataset({ ...authOpts, datasetConfig: dsConfig });
                await instance.create();
                return instance;
            }
            throw err;
        }
    }
} 