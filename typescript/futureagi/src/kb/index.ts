// Export runtime values
export {
    StatusType,
    SUPPORTED_FILE_TYPES,
    CONTENT_TYPE_MAP
} from './types';

// Export types (for TypeScript users)
export type {
    KnowledgeBaseConfig,
    KnowledgeBaseCreateResponse,
    LegacyKnowledgeBaseCreateResponse,
    LegacyKnowledgeBaseListResponse,
    KnowledgeBaseCreateResult,
    KnowledgeBaseListResult,
    KnowledgeBaseUpdateResponse,
    KnowledgeBaseListResponse,
    KnowledgeBaseOptions,
    SupportedFileType
} from './types';

export { KnowledgeBase } from './client'; 