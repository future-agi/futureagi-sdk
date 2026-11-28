/** Runtime views for published response spellings. Unknown server fields survive. */
const seen = new Set<string>();
const normalized = new WeakMap<object, ReadonlySet<string>>();
type Aliases = Readonly<Record<string, string>>;

function warn(old: string, modern: string): void {
  const key = `${old}:${modern}`;
  if (seen.has(key)) return;
  seen.add(key);
  process.emitWarning(`${old} is deprecated; use ${modern} instead.`, 'DeprecationWarning');
}

/** Accept either spelling, prefer canonical data, and expose synchronized legacy getters.
 * Reading or assigning an old property, or supplying it as input, warns once per
 * alias per process. Canonical inputs are silent, including repeated SDK parsing.
 * Legacy views are non-enumerable so canonical wire payloads do not acquire duplicate
 * keys. Input objects and unrelated fields are not changed.
 */
export function legacyFields<T extends object>(data: T, aliases: Aliases): T {
  if (data === null || typeof data !== 'object') return data;
  const known = normalized.get(data);
  const result: Record<string, any> = { ...data };
  for (const [old, modern] of Object.entries(aliases)) {
    if (!known?.has(old) && Object.prototype.hasOwnProperty.call(data, old)) {
      warn(old, modern);
      if (!Object.prototype.hasOwnProperty.call(data, modern)) result[modern] = (data as Record<string, any>)[old];
    }
    Object.defineProperty(result, old, {
      configurable: true,
      enumerable: false,
      get() { warn(old, modern); return this[modern]; },
      set(value) { warn(old, modern); this[modern] = value; },
    });
  }
  normalized.set(result, new Set([...(known || []), ...Object.keys(aliases)]));
  return result as T;
}

function spellings(names: readonly string[]): Aliases {
  return Object.fromEntries(names.map(name => [name, name.replace(/[A-Z]/g, letter => `_${letter.toLowerCase()}`)]));
}

export const bulkFields = spellings([
  'annotationsCreated', 'annotationsUpdated', 'notesCreated', 'succeededCount', 'errorsCount', 'warningsCount',
]);
export const queueFields = spellings([
  'assignmentStrategy', 'annotationsRequired', 'reservationTimeoutMinutes', 'requiresReview',
  'createdAt', 'updatedAt', 'itemCount', 'completedCount',
]);
export const itemFields = spellings(['sourceType', 'sourceId', 'assignedTo', 'createdAt']);
export const progressFields = spellings(['inProgress', 'progressPct', 'annotatorStats']);
export const analyticsFields = spellings(['annotatorPerformance', 'labelDistribution', 'statusBreakdown']);
export const agreementFields = spellings(['overallAgreement', 'perLabel', 'annotatorPairs']);
export const scoreFields = spellings([
  'labelId', 'labelName', 'scoreSource', 'annotatorId', 'annotatorName', 'sourceType', 'sourceId', 'createdAt',
]);
export const exportFields = spellings(['datasetId', 'datasetName', 'rowsCreated']);
export const columnFields = spellings(['dataType', 'sourceId', 'isFrozen', 'isVisible', 'evalTags', 'averageScore', 'orderIndex']);
export const cellFields = spellings(['columnId', 'rowId', 'columnName', 'valueInfos', 'failureReason']);
export const datasetConfigFields = spellings(['modelType', 'columnOrder']);
export const datasetTableFields = spellings(['datasetConfig']);
export const huggingfaceFields = spellings(['numRows']);
export const kbConfigFields = spellings(['lastError']);
export const kbCreateFields = spellings(['kbId', 'kbName', 'fileIds', 'notUploaded']);
export const kbUpdateFields = spellings(['notUploaded']);
export const kbListFields = spellings(['tableData']);
