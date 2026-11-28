import { legacyFields, columnFields, cellFields, datasetConfigFields, datasetTableFields } from '../_compat-fields';
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
    getJavaScriptType(data_type: DataTypeChoices): string {
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
        return typeMapping[data_type] || 'string';
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

/** Dataset column. Legacy camelCase fields remain readable; prefer snake_case.
 * Helpers and SDK responses warn once per alias when legacy spellings are used.
 */
export interface Column {
    id: string;
    name: string;
    /** @deprecated Use data_type. SDK runtime paths warn once per alias per process. */
    dataType?: DataTypeChoices;
    data_type: DataTypeChoices;
    source?: SourceChoices;
    /** @deprecated Use source_id. SDK runtime paths warn once per alias per process. */
    sourceId?: string;
    source_id?: string;
    metadata?: Record<string, any>;
    /** @deprecated Use is_frozen. SDK runtime paths warn once per alias per process. */
    isFrozen?: boolean;
    is_frozen?: boolean;
    /** @deprecated Use is_visible. SDK runtime paths warn once per alias per process. */
    isVisible?: boolean;
    is_visible?: boolean;
    /** @deprecated Use eval_tags. SDK runtime paths warn once per alias per process. */
    evalTags?: string[];
    eval_tags?: string[];
    /** @deprecated Use average_score. SDK runtime paths warn once per alias per process. */
    averageScore?: number;
    average_score?: number;
    /** @deprecated Use order_index. SDK runtime paths warn once per alias per process. */
    orderIndex?: number;
    order_index?: number;
}

// Cell interface for dataset tables
export interface Cell {
    /** @deprecated Use column_id. SDK runtime paths warn once per alias per process. */
    columnId?: string;
    column_id?: string;
    /** @deprecated Use row_id. SDK runtime paths warn once per alias per process. */
    rowId?: string;
    row_id?: string;
    /** @deprecated Use column_name. SDK runtime paths warn once per alias per process. */
    columnName?: string;
    column_name?: string;
    value?: any;
    /** @deprecated Use value_infos. SDK runtime paths warn once per alias per process. */
    valueInfos?: Array<Record<string, any>>;
    value_infos?: Array<Record<string, any>>;
    metadata?: Record<string, any>;
    status?: string;
    /** @deprecated Use failure_reason. SDK runtime paths warn once per alias per process. */
    failureReason?: string;
    failure_reason?: string;
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
    /** @deprecated Use model_type. SDK runtime paths warn once per alias per process. */
    modelType?: ModelTypes.GENERATIVE_LLM;
    model_type?: ModelTypes;
    /** @deprecated Use column_order. SDK runtime paths warn once per alias per process. */
    columnOrder?: string[];
    column_order?: string[];
}

// Hugging Face dataset configuration
export interface HuggingfaceDatasetConfig {
    name: string;
    subset?: string;
    split?: string;
    /** @deprecated Use num_rows. SDK runtime paths warn once per alias per process. */
    numRows?: number;
    num_rows?: number;
}

// Dataset table interface
export interface DatasetTable {
    id: string;
    columns: Column[];
    rows: Row[];
    metadata?: Record<string, any>;
    /** @deprecated Use dataset_config. SDK runtime paths warn once per alias per process. */
    datasetConfig?: DatasetConfig;
    dataset_config?: DatasetConfig;
}

/** Canonical 0.2.0 column, retained under its additional descriptive name. */
export type CanonicalColumn = Column;
/** Older camelCase column input; normalized results expose both spellings. */
export type LegacyColumn = Omit<Column, 'dataType' | 'data_type'> & {
    dataType: DataTypeChoices;
    data_type?: DataTypeChoices;
};
export type LegacyDatasetTable = Omit<DatasetTable, 'columns'> & {
    columns: LegacyColumn[];
};
/** Utilities accept canonical wire tables as well as older camelCase tables. */
export type DatasetTableInput = Omit<DatasetTable, 'columns'> & {
    columns: Array<Column | LegacyColumn>;
};

/** Inputs accept the published or canonical required data-type spelling. */
export type ColumnInput = Omit<Column, 'id' | 'dataType' | 'data_type'> & (
    { dataType: DataTypeChoices; data_type?: DataTypeChoices } |
    { data_type: DataTypeChoices; dataType?: DataTypeChoices }
);
/** SDK column results expose both required data-type spellings. */
export type ColumnResult = Column & LegacyColumn;
/** Normalized SDK tables have both required column spellings. */
export type DatasetTableResult = Omit<DatasetTable, 'columns'> & { columns: ColumnResult[] };

/** Create a column from either spelling. Legacy inputs/access warn once per alias. */
export function createColumn(input: ColumnInput): ColumnResult {
    const options = legacyFields(input, columnFields);
    if (!options.name?.trim()) {
        throw new Error("Column name cannot be empty");
    }
    if (options.name.length > 255) {
        throw new Error("Column name too long (max 255 characters)");
    }

    return legacyFields({
        id: uuidv4(),
        name: options.name.trim(),
        data_type: options.data_type,
        source: options.source || SourceChoices.OTHERS,
        source_id: options.source_id,
        metadata: options.metadata || {},
        is_frozen: options.is_frozen || false,
        is_visible: options.is_visible !== false,
        eval_tags: options.eval_tags || [],
        average_score: options.average_score,
        order_index: options.order_index || 0,
    }, columnFields) as ColumnResult;
}

/** Create a cell from either spelling. Legacy inputs/access warn once per alias. */
export function createCell(input: Cell): Cell {
    const options = legacyFields(input, cellFields);
    if (options.value != null && String(options.value).length > 65535) {
        throw new Error("Cell value too long (max 65535 characters)");
    }

    return legacyFields({
        column_id: options.column_id,
        row_id: options.row_id,
        column_name: options.column_name,
        value: options.value,
        value_infos: options.value_infos || [],
        metadata: options.metadata || {},
        status: options.status,
        failure_reason: options.failure_reason,
    }, cellFields);
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
    // Ensure each cell has row_id; generate column_id if missing
    const updatedCells = options.cells.map(input => {
        const cell = legacyFields(input, cellFields);
        return legacyFields({
            ...cell,
            row_id: cell.row_id || rowId,
            column_id: cell.column_id || uuidv4(),
        }, cellFields);
    });

    return {
        id: rowId,
        order: options.order || 0,
        cells: updatedCells,
    };
}

function canonicalTable(input: DatasetTableInput): DatasetTableInput {
    const table = legacyFields(input, datasetTableFields);
    return {
        ...table,
        columns: table.columns.map(column => legacyFields(column, columnFields)),
        rows: table.rows.map(row => ({ ...row, cells: row.cells.map(cell => legacyFields(cell, cellFields)) })),
        ...(table.dataset_config ? { dataset_config: legacyFields(table.dataset_config, datasetConfigFields) } : {}),
    };
}

/** Dataset utilities accept either spelling and warn once for each legacy input alias. */
export const DatasetTableUtils = {
    /**
     * Convert dataset table to JSON format
     */
    toJson(table: DatasetTableInput): string {
        return JSON.stringify(canonicalTable(table), null, 2);
    },

    /**
     * Convert dataset table to CSV format
     */
    toCsv(input: DatasetTableInput): string {
        const table = canonicalTable(input);
        if (!table.columns.length || !table.rows.length) {
            return '';
        }

        // Create header
        const headers = table.columns.map(col => col.name);
        const csvLines = [headers.join(',')];

        // Add data rows
        for (const row of table.rows) {
            const rowData = table.columns.map(col => {
                const cell = row.cells.find(c => c.column_id === col.id);
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
