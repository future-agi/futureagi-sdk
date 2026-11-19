/**
 * Status types for knowledge base operations
 */
export enum StatusType {
    PROCESSING = "Processing",
    COMPLETED = "Completed",
    PARTIAL_COMPLETED = "PartialCompleted",
    FAILED = "Failed"
}

/**
 * Configuration interface for Knowledge Base
 */
export interface KnowledgeBaseConfig {
    /** Unique identifier for the knowledge base */
    id?: string;
    /** Name of the knowledge base */
    name: string;
    /** Current status of the knowledge base */
    status?: string;
    /** Last error message if any */
    /** @deprecated Use last_error. SDK runtime paths warn once per alias per process. */
    lastError?: string;
    last_error?: string;
    /** List of file IDs or names in the knowledge base */
    files?: string[];
}

/**
 * Response interface for knowledge base creation
 */
export interface KnowledgeBaseCreateResponse {
    /** @deprecated Use kb_id. SDK runtime paths warn once per alias per process. */
    kbId?: string;
    kb_id: string;
    /** @deprecated Use kb_name. SDK runtime paths warn once per alias per process. */
    kbName?: string;
    kb_name: string;
    /** @deprecated Use file_ids. SDK runtime paths warn once per alias per process. */
    fileIds?: string[];
    file_ids?: string[];
    /** @deprecated Use not_uploaded. SDK runtime paths warn once per alias per process. */
    notUploaded?: string[];
    not_uploaded?: string[];
}

/**
 * Response interface for knowledge base update
 */
export interface KnowledgeBaseUpdateResponse {
    id: string;
    name: string;
    files?: string[];
    /** @deprecated Use not_uploaded. SDK runtime paths warn once per alias per process. */
    notUploaded?: string[];
    not_uploaded?: string[];
}

/**
 * Response interface for knowledge base list
 */
export interface KnowledgeBaseListResponse {
    result: {
        /** @deprecated Use table_data. SDK response access warns once per process. */
        tableData?: Array<KnowledgeBaseConfig & { id: string }>;
        table_data: Array<KnowledgeBaseConfig & { id: string }>;
    };
}

/** Older camelCase creation input, separate from the 0.2.0 canonical interface. */
export type LegacyKnowledgeBaseCreateResponse = Omit<KnowledgeBaseCreateResponse, 'kbId' | 'kbName' | 'kb_id' | 'kb_name'> & {
    kbId: string;
    kbName: string;
    kb_id?: string;
    kb_name?: string;
};
/** Older camelCase list input. */
export interface LegacyKnowledgeBaseListResponse {
    result: {
        tableData: Array<KnowledgeBaseConfig & { id: string }>;
        table_data?: Array<KnowledgeBaseConfig & { id: string }>;
    };
}
export type KnowledgeBaseCreateResult = KnowledgeBaseCreateResponse & LegacyKnowledgeBaseCreateResponse;
export type KnowledgeBaseListResult = KnowledgeBaseListResponse & LegacyKnowledgeBaseListResponse;

/**
 * Supported file types for knowledge base uploads
 */
export const SUPPORTED_FILE_TYPES = ['pdf', 'docx', 'txt', 'rtf'] as const;
export type SupportedFileType = typeof SUPPORTED_FILE_TYPES[number];

/**
 * Content type mapping for file uploads
 */
export const CONTENT_TYPE_MAP: Record<SupportedFileType, string> = {
    pdf: 'application/pdf',
    rtf: 'application/rtf',
    txt: 'text/plain',
    docx: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
};

/**
 * Options for knowledge base operations
 */
export interface KnowledgeBaseOptions {
    /** FutureAGI API key */
    fiApiKey?: string;
    /** FutureAGI secret key */
    fiSecretKey?: string;
    /** FutureAGI base URL */
    fiBaseUrl?: string;
    /** Request timeout in milliseconds */
    timeout?: number;
}

export default {
    StatusType,
    SUPPORTED_FILE_TYPES,
    CONTENT_TYPE_MAP
}; 