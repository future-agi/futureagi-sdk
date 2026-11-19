// Generated public declarations from @future-agi/sdk 0.1.2; do not edit.
/**
 * Status types for knowledge base operations
 */
export declare enum StatusType {
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
    lastError?: string;
    /** List of file IDs or names in the knowledge base */
    files?: string[];
}
/**
 * Response interface for knowledge base creation
 */
export interface KnowledgeBaseCreateResponse {
    kbId: string;
    kbName: string;
    fileIds?: string[];
    notUploaded?: string[];
}
/**
 * Response interface for knowledge base update
 */
export interface KnowledgeBaseUpdateResponse {
    id: string;
    name: string;
    files?: string[];
    notUploaded?: string[];
}
/**
 * Response interface for knowledge base list
 */
export interface KnowledgeBaseListResponse {
    result: {
        tableData: Array<{
            id: string;
            name: string;
            status?: string;
            files?: string[];
        }>;
    };
}
/**
 * Supported file types for knowledge base uploads
 */
export declare const SUPPORTED_FILE_TYPES: readonly [
    "pdf",
    "docx",
    "txt",
    "rtf"
];
export type SupportedFileType = typeof SUPPORTED_FILE_TYPES[number];
/**
 * Content type mapping for file uploads
 */
export declare const CONTENT_TYPE_MAP: Record<SupportedFileType, string>;
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
declare const _default: {
    StatusType: typeof StatusType;
    SUPPORTED_FILE_TYPES: readonly [
        "pdf",
        "docx",
        "txt",
        "rtf"
    ];
    CONTENT_TYPE_MAP: Record<"pdf" | "docx" | "txt" | "rtf", string>;
};
export default _default;
