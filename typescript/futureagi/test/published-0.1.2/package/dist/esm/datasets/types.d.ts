// Generated public declarations from @future-agi/sdk 0.1.2; do not edit.
export declare enum DataTypeChoices {
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
export declare enum SourceChoices {
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
export declare enum ModelTypes {
    GENERATIVE_LLM = "GenerativeLLM",
    GENERATIVE_IMAGE = "GenerativeImage"
}
export declare const DataTypeUtils: {
    getJavaScriptType(dataType: DataTypeChoices): string;
    getSourceChoices(): Array<{
        value: string;
        displayName: string;
    }>;
};
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
export interface Row {
    id: string;
    order?: number;
    cells: Cell[];
}
export interface DatasetConfig {
    id?: string;
    name: string;
    modelType?: ModelTypes.GENERATIVE_LLM;
    columnOrder?: string[];
}
export interface HuggingfaceDatasetConfig {
    name: string;
    subset?: string;
    split?: string;
    numRows?: number;
}
export interface DatasetTable {
    id: string;
    columns: Column[];
    rows: Row[];
    metadata?: Record<string, any>;
    datasetConfig?: DatasetConfig;
}
export declare function createColumn(options: {
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
}): Column;
export declare function createCell(options: {
    columnId?: string;
    rowId?: string;
    columnName?: string;
    value?: any;
    valueInfos?: Array<Record<string, any>>;
    metadata?: Record<string, any>;
    status?: string;
    failureReason?: string;
}): Cell;
export declare function createRow(options: {
    cells: Cell[];
    order?: number;
}): Row;
export declare const DatasetTableUtils: {
    /**
     * Convert dataset table to JSON format
     */
    toJson(table: DatasetTable): string;
    /**
     * Convert dataset table to CSV format
     */
    toCsv(table: DatasetTable): string;
    /**
     * Convert value based on data type
     */
    convertValue(value: any, dataType: DataTypeChoices): any;
};
export type { Column as ColumnType, Cell as CellType, Row as RowType, DatasetConfig as DatasetConfigType, HuggingfaceDatasetConfig as HuggingfaceDatasetConfigType, DatasetTable as DatasetTableType, };
export type PublishedCall1193 = (dataType: DataTypeChoices) => string;
export type PublishedCall1251 = () => Array<{
    value: string;
    displayName: string;
}>;
export type PublishedCall3130 = (table: DatasetTable) => string;
export type PublishedCall3231 = (table: DatasetTable) => string;
export type PublishedCall3330 = (value: any, dataType: DataTypeChoices) => any;
export type PublishedCall2724 = (options: {
    columnId?: string;
    rowId?: string;
    columnName?: string;
    value?: any;
    valueInfos?: Array<Record<string, any>>;
    metadata?: Record<string, any>;
    status?: string;
    failureReason?: string;
}) => Cell;
export type PublishedCall2402 = (options: {
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
}) => Column;
export type PublishedCall2995 = (options: {
    cells: Cell[];
    order?: number;
}) => Row;
