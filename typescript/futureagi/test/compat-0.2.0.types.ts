// Required fields and reads from the published 0.2.0 root declarations.
import {
  BulkAnnotationResponse, Column, ColumnType, DataTypeChoices,
  DatasetTable, KnowledgeBaseCreateResponse, KnowledgeBaseListResponse,
  QueueProgress, Routes,
} from '../src/index';

const bulk: BulkAnnotationResponse = {
  message: 'ok', annotations_created: 1, annotations_updated: 2,
  notes_created: 3, succeeded_count: 4, errors_count: 0, warnings_count: 0,
};
const column: Column = { id: 'column', name: 'text', data_type: DataTypeChoices.TEXT };
const columnType: ColumnType = column;
const table: DatasetTable = { id: 'table', columns: [columnType], rows: [] };
const progress: QueueProgress = { total: 1, pending: 0, in_progress: 1, completed: 0, skipped: 0 };
const created: KnowledgeBaseCreateResponse = { kb_id: 'kb', kb_name: 'Knowledge' };
const listed: KnowledgeBaseListResponse = { result: { table_data: [{ id: 'kb', name: 'Knowledge' }] } };

// Read from arbitrary declared instances, not narrowed construction literals.
function publishedReads(
  b: BulkAnnotationResponse, c: Column, ct: ColumnType,
  p: QueueProgress, k: KnowledgeBaseCreateResponse, l: KnowledgeBaseListResponse,
): void {
  const counts: number[] = [b.annotations_created, b.annotations_updated, b.notes_created,
    b.succeeded_count, b.errors_count, b.warnings_count, p.in_progress];
  const dataTypes: DataTypeChoices[] = [c.data_type, ct.data_type];
  const names: string[] = [k.kb_id, k.kb_name];
  const rows: Array<{ id: string; name: string }> = l.result.table_data;
  void [counts, dataTypes, names, rows];
}
publishedReads(bulk, column, columnType, progress, created, listed);
void table;
const retiredRoute: 'sdk/api/v1/log/model/' = Routes.log_model;
void retiredRoute;
