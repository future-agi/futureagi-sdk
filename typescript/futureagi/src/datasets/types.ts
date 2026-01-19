import { v4 as uuidv4 } from 'uuid';
import { ModelProvider } from '../api/types';

// Data type choices for dataset columns
export enum DataTypeChoices {
    TEXT = "text",
    BOOLEAN = "boolean",
    INTEGER = "integer",
    FLOAT = "float",
    JSON = "json",
    ARRAY = "array",
    IMAGE = "image",
    DATETIME = "datetime",
    AUDIO = "audio"
}

// Source choices for dataset columns
export enum SourceChoices {
    EVALUATION = "evaluation",
    EVALUATION_TAGS = "evaluation_tags",
    EVALUATION_REASON = "evaluation_reason",
    RUN_PROMPT = "run_prompt",
    EXPERIMENT = "experiment",
    OPTIMISATION = "optimisation",
    EXPERIMENT_EVALUATION = "experiment_evaluation",
    EXPERIMENT_EVALUATION_TAGS = "experiment_evaluation_tags",
    OPTIMISATION_EVALUATION = "optimisation_evaluation",
    ANNOTATION_LABEL = "annotation_label",
    OPTIMISATION_EVALUATION_TAGS = "optimisation_evaluation_tags",
    EXTRACTED_JSON = "extracted_json",
    CLASSIFICATION = "classification",
    EXTRACTED_ENTITIES = "extracted_entities",
    API_CALL = "api_call",
    PYTHON_CODE = "python_code",
    VECTOR_DB = "vector_db",
    CONDITIONAL = "conditional",
    OTHERS = "OTHERS"
}

export enum ModelTypes {
    GENERATIVE_LLM = "GenerativeLLM",
    GENERATIVE_IMAGE = "GenerativeImage"
}

// Utility functions for data types
export const DataTypeUtils = {
    getJavaScriptType(dataType: DataTypeChoices): string {
        const typeMapping = {
            [DataTypeChoices.TEXT]: 'string',
            [DataTypeChoices.BOOLEAN]: 'boolean',
            [DataTypeChoices.INTEGER]: 'number',
            [DataTypeChoices.FLOAT]: 'number',
            [DataTypeChoices.JSON]: 'object',
            [DataTypeChoices.ARRAY]: 'object',
            [DataTypeChoices.IMAGE]: 'string',
            [DataTypeChoices.AUDIO]: 'string',
            [DataTypeChoices.DATETIME]: 'string',
        };
        return typeMapping[dataType] || 'string';
    },

    getSourceChoices(): Array<{ value: string; displayName: string }> {
        return Object.values(SourceChoices).map(source => ({
            value: source,
            displayName: source.replace(/_/g, ' ').toLowerCase()
                .split(' ')
                .map(word => word.charAt(0).toUpperCase() + word.slice(1))
                .join(' ')
        }));
    }
};

// Column interface for dataset tables
export interface Column {
    id: string;
    name: string;
    dataType: DataTypeChoices;
    source?: SourceChoices;
    sourceId?: string;
    metadata?: Record<string, any>;
    isFrozen?: boolean;
    isVisible?: boolean;
    evalTags?: string[];
    averageScore?: number;
    orderIndex?: number;
}

// Cell interface for dataset tables
export interface Cell {
    columnId?: string;
    rowId?: string;
    columnName?: string;
    value?: any;
    valueInfos?: Array<Record<string, any>>;
    metadata?: Record<string, any>;
    status?: string;
    failureReason?: string;
}

// Row interface for dataset tables
export interface Row {
    id: string;
    order?: number;
    cells: Cell[];
}

// Dataset configuration interface
export interface DatasetConfig {
    id?: string;
    name: string;
    modelType?: ModelTypes.GENERATIVE_LLM;
    columnOrder?: string[];
}

// Hugging Face dataset configuration
export interface HuggingfaceDatasetConfig {
    name: string;
    subset?: string;
    split?: string;
    numRows?: number;
}

// Dataset table interface
export interface DatasetTable {
    id: string;
    columns: Column[];
    rows: Row[];
    metadata?: Record<string, any>;
    datasetConfig?: DatasetConfig;
}

// Column creation helper
export function createColumn(options: {
    name: string;
    dataType: DataTypeChoices;
    source?: SourceChoices;
    sourceId?: string;
    metadata?: Record<string, any>;
    isFrozen?: boolean;
    isVisible?: boolean;
    evalTags?: string[];
    averageScore?: number;
    orderIndex?: number;
}): Column {
    if (!options.name?.trim()) {
        throw new Error("Column name cannot be empty");
    }
    if (options.name.length > 255) {
        throw new Error("Column name too long (max 255 characters)");
    }

    return {
        id: uuidv4(),
        name: options.name.trim(),
        dataType: options.dataType,
        source: options.source || SourceChoices.OTHERS,
        sourceId: options.sourceId,
        metadata: options.metadata || {},
        isFrozen: options.isFrozen || false,
        isVisible: options.isVisible !== false,
        evalTags: options.evalTags || [],
        averageScore: options.averageScore,
        orderIndex: options.orderIndex || 0,
    };
}

// Cell creation helper
export function createCell(options: {
    columnId?: string;
    rowId?: string;
    columnName?: string;
    value?: any;
    valueInfos?: Array<Record<string, any>>;
    metadata?: Record<string, any>;
    status?: string;
    failureReason?: string;
}): Cell {
    if (options.value != null && String(options.value).length > 65535) {
        throw new Error("Cell value too long (max 65535 characters)");
    }

    return {
        columnId: options.columnId,
        rowId: options.rowId,
        columnName: options.columnName,
        value: options.value,
        valueInfos: options.valueInfos || [],
        metadata: options.metadata || {},
        status: options.status,
        failureReason: options.failureReason,
    };
}

// Row creation helper
export function createRow(options: {
    cells: Cell[];
    order?: number;
}): Row {
    if (!options.cells || options.cells.length === 0) {
        throw new Error("Row must have at least one cell");
    }
    if (options.order != null && options.order < 0) {
        throw new Error("Row order must be non-negative");
    }

    const rowId = uuidv4();
    // Ensure each cell has rowId; generate columnId if missing
    const updatedCells = options.cells.map(cell => ({
        ...cell,
        rowId: cell.rowId || rowId,
        columnId: cell.columnId || uuidv4(),
    }));

    return {
        id: rowId,
        order: options.order || 0,
        cells: updatedCells,
    };
}

// Dataset table utilities
export const DatasetTableUtils = {
    /**
     * Convert dataset table to JSON format
     */
    toJson(table: DatasetTable): string {
        return JSON.stringify(table, null, 2);
    },

    /**
     * Convert dataset table to CSV format
     */
    toCsv(table: DatasetTable): string {
        if (!table.columns.length || !table.rows.length) {
            return '';
        }

        // Create header
        const headers = table.columns.map(col => col.name);
        const csvLines = [headers.join(',')];

        // Add data rows
        for (const row of table.rows) {
            const rowData = table.columns.map(col => {
                const cell = row.cells.find(c => c.columnId === col.id);
                const value = cell?.value || '';
                // Escape CSV values
                const stringValue = String(value);
                return stringValue.includes(',') || stringValue.includes('"') || stringValue.includes('\n')
                    ? `"${stringValue.replace(/"/g, '""')}"`
                    : stringValue;
            });
            csvLines.push(rowData.join(','));
        }

        return csvLines.join('\n');
    },

    /**
     * Convert value based on data type
     */
    convertValue(value: any, dataType: DataTypeChoices): any {
        if (value == null) return null;

        try {
            switch (dataType) {
                case DataTypeChoices.BOOLEAN:
                    if (typeof value === 'boolean') return value;
                    return String(value).toLowerCase() === 'true';
                case DataTypeChoices.INTEGER:
                    return parseInt(String(value), 10);
                case DataTypeChoices.FLOAT:
                    return parseFloat(String(value));
                case DataTypeChoices.JSON:
                    return typeof value === 'string' ? JSON.parse(value) : value;
                case DataTypeChoices.ARRAY:
                    return Array.isArray(value) ? value : [value];
                case DataTypeChoices.DATETIME:
                    return new Date(String(value)).toISOString();
                case DataTypeChoices.TEXT:
                case DataTypeChoices.IMAGE:
                case DataTypeChoices.AUDIO:
                default:
                    return String(value);
            }
        } catch (error) {
            console.warn(`Failed to convert value "${value}" to ${dataType}:`, error);
            return String(value);
        }
    }
};

// Export all types
export type {
    Column as ColumnType,
    Cell as CellType,
    Row as RowType,
    DatasetConfig as DatasetConfigType,
    HuggingfaceDatasetConfig as HuggingfaceDatasetConfigType,
    DatasetTable as DatasetTableType,
}; 