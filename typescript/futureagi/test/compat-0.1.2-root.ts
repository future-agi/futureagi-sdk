// Older input shapes remain available under explicit legacy names. The actual
// root's canonical required fields are pinned independently against 0.2.0.
export * from '../src/index';
export type {
  LegacyBulkAnnotationResponse as BulkAnnotationResponse,
  LegacyColumn as Column,
  LegacyColumn as ColumnType,
  LegacyDatasetTable as DatasetTable,
  LegacyDatasetTable as DatasetTableType,
  LegacyQueueProgress as QueueProgress,
  LegacyKnowledgeBaseCreateResponse as KnowledgeBaseCreateResponse,
  LegacyKnowledgeBaseListResponse as KnowledgeBaseListResponse,
} from '../src/index';
