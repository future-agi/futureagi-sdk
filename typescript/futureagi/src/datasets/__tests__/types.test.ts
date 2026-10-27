import {
    DataTypeChoices,
    SourceChoices,
    DataTypeUtils,
    createColumn,
    createRow,
    createCell,
    DatasetTableUtils,
    type Column,
    type Cell,
    type Row,
    type DatasetTable,
} from '../types';
import { ModelProvider } from '../../api/types';

describe('DataTypeChoices', () => {
    test('should have all expected values', () => {
        expect(DataTypeChoices.TEXT).toBe('text');
        expect(DataTypeChoices.BOOLEAN).toBe('boolean');
        expect(DataTypeChoices.INTEGER).toBe('integer');
        expect(DataTypeChoices.FLOAT).toBe('float');
        expect(DataTypeChoices.JSON).toBe('json');
        expect(DataTypeChoices.ARRAY).toBe('array');
        expect(DataTypeChoices.IMAGE).toBe('image');
        expect(DataTypeChoices.DATETIME).toBe('datetime');
        expect(DataTypeChoices.AUDIO).toBe('audio');
    });
});

describe('SourceChoices', () => {
    test('should have all expected values', () => {
        expect(SourceChoices.EVALUATION).toBe('evaluation');
        expect(SourceChoices.RUN_PROMPT).toBe('run_prompt');
        expect(SourceChoices.EXPERIMENT).toBe('experiment');
        expect(SourceChoices.OTHERS).toBe('OTHERS');
    });
});

describe('DataTypeUtils', () => {
    describe('getJavaScriptType', () => {
        test('should return correct JavaScript types', () => {
            expect(DataTypeUtils.getJavaScriptType(DataTypeChoices.TEXT)).toBe('string');
            expect(DataTypeUtils.getJavaScriptType(DataTypeChoices.BOOLEAN)).toBe('boolean');
            expect(DataTypeUtils.getJavaScriptType(DataTypeChoices.INTEGER)).toBe('number');
            expect(DataTypeUtils.getJavaScriptType(DataTypeChoices.FLOAT)).toBe('number');
            expect(DataTypeUtils.getJavaScriptType(DataTypeChoices.JSON)).toBe('object');
            expect(DataTypeUtils.getJavaScriptType(DataTypeChoices.ARRAY)).toBe('object');
            expect(DataTypeUtils.getJavaScriptType(DataTypeChoices.IMAGE)).toBe('string');
            expect(DataTypeUtils.getJavaScriptType(DataTypeChoices.AUDIO)).toBe('string');
            expect(DataTypeUtils.getJavaScriptType(DataTypeChoices.DATETIME)).toBe('string');
        });
    });

    describe('getSourceChoices', () => {
        test('should return formatted source choices', () => {
            const choices = DataTypeUtils.getSourceChoices();
            expect(choices).toBeInstanceOf(Array);
            expect(choices.length).toBeGreaterThan(0);
            
            const evaluationChoice = choices.find(c => c.value === 'evaluation');
            expect(evaluationChoice).toBeDefined();
            expect(evaluationChoice?.displayName).toBe('Evaluation');

            const runPromptChoice = choices.find(c => c.value === 'run_prompt');
            expect(runPromptChoice).toBeDefined();
            expect(runPromptChoice?.displayName).toBe('Run Prompt');
        });
    });
});

describe('createColumn', () => {
    test('should create a valid column with required fields', () => {
        const column = createColumn({
            name: 'test_column',
            data_type: DataTypeChoices.TEXT,
        });

        expect(column.id).toBeDefined();
        expect(column.name).toBe('test_column');
        expect(column.data_type).toBe(DataTypeChoices.TEXT);
        expect(column.source).toBe(SourceChoices.OTHERS);
        expect(column.is_frozen).toBe(false);
        expect(column.is_visible).toBe(true);
        expect(column.eval_tags).toEqual([]);
        expect(column.metadata).toEqual({});
        expect(column.order_index).toBe(0);
    });

    test('should create a column with all optional fields', () => {
        const column = createColumn({
            name: 'test_column',
            data_type: DataTypeChoices.INTEGER,
            source: SourceChoices.EVALUATION,
            source_id: 'eval-123',
            metadata: { key: 'value' },
            is_frozen: true,
            is_visible: false,
            eval_tags: ['tag1', 'tag2'],
            average_score: 0.85,
            order_index: 5,
        });

        expect(column.name).toBe('test_column');
        expect(column.data_type).toBe(DataTypeChoices.INTEGER);
        expect(column.source).toBe(SourceChoices.EVALUATION);
        expect(column.source_id).toBe('eval-123');
        expect(column.metadata).toEqual({ key: 'value' });
        expect(column.is_frozen).toBe(true);
        expect(column.is_visible).toBe(false);
        expect(column.eval_tags).toEqual(['tag1', 'tag2']);
        expect(column.average_score).toBe(0.85);
        expect(column.order_index).toBe(5);
    });

    test('should throw error for empty column name', () => {
        expect(() => {
            createColumn({
                name: '',
                data_type: DataTypeChoices.TEXT,
            });
        }).toThrow('Column name cannot be empty');
    });

    test('should throw error for long column name', () => {
        const longName = 'a'.repeat(256);
        expect(() => {
            createColumn({
                name: longName,
                data_type: DataTypeChoices.TEXT,
            });
        }).toThrow('Column name too long (max 255 characters)');
    });

    test('should trim column name', () => {
        const column = createColumn({
            name: '  test_column  ',
            data_type: DataTypeChoices.TEXT,
        });

        expect(column.name).toBe('test_column');
    });
});

describe('createCell', () => {
    test('should create a valid cell with required fields', () => {
        const cell = createCell({
            column_id: 'col-123',
            row_id: 'row-456',
        });

        expect(cell.column_id).toBe('col-123');
        expect(cell.row_id).toBe('row-456');
        expect(cell.value_infos).toEqual([]);
        expect(cell.metadata).toEqual({});
    });

    test('should create a cell with all optional fields', () => {
        const cell = createCell({
            column_id: 'col-123',
            row_id: 'row-456',
            column_name: 'test_column',
            value: 'test_value',
            value_infos: [{ info: 'test' }],
            metadata: { key: 'value' },
            status: 'completed',
            failure_reason: 'none',
        });

        expect(cell.column_id).toBe('col-123');
        expect(cell.row_id).toBe('row-456');
        expect(cell.column_name).toBe('test_column');
        expect(cell.value).toBe('test_value');
        expect(cell.value_infos).toEqual([{ info: 'test' }]);
        expect(cell.metadata).toEqual({ key: 'value' });
        expect(cell.status).toBe('completed');
        expect(cell.failure_reason).toBe('none');
    });

    test('should throw error for very long cell value', () => {
        const longValue = 'a'.repeat(65536);
        expect(() => {
            createCell({
                column_id: 'col-123',
                row_id: 'row-456',
                value: longValue,
            });
        }).toThrow('Cell value too long (max 65535 characters)');
    });
});

describe('createRow', () => {
    test('should create a valid row with cells', () => {
        const cells = [
            createCell({ column_id: 'col-1', row_id: 'row-1' }),
            createCell({ column_id: 'col-2', row_id: 'row-1' }),
        ];

        const row = createRow({ cells });

        expect(row.id).toBeDefined();
        expect(row.cells).toEqual(cells);
        expect(row.order).toBe(0);
    });

    test('should create a row with custom order', () => {
        const cells = [
            createCell({ column_id: 'col-1', row_id: 'row-1' }),
        ];

        const row = createRow({ cells, order: 5 });

        expect(row.order).toBe(5);
    });

    test('should throw error for empty cells array', () => {
        expect(() => {
            createRow({ cells: [] });
        }).toThrow('Row must have at least one cell');
    });

    test('should throw error for negative order', () => {
        const cells = [
            createCell({ column_id: 'col-1', row_id: 'row-1' }),
        ];

        expect(() => {
            createRow({ cells, order: -1 });
        }).toThrow('Row order must be non-negative');
    });
});

describe('DatasetTableUtils', () => {
    const mockTable: DatasetTable = {
        id: 'table-123',
        columns: [
            {
                id: 'col-1',
                name: 'name',
                data_type: DataTypeChoices.TEXT,
                source: SourceChoices.OTHERS,
                metadata: {},
                is_frozen: false,
                is_visible: true,
                eval_tags: [],
                order_index: 0,
            },
            {
                id: 'col-2',
                name: 'age',
                data_type: DataTypeChoices.INTEGER,
                source: SourceChoices.OTHERS,
                metadata: {},
                is_frozen: false,
                is_visible: true,
                eval_tags: [],
                order_index: 1,
            },
        ],
        rows: [
            {
                id: 'row-1',
                order: 0,
                cells: [
                    createCell({ column_id: 'col-1', row_id: 'row-1', value: 'John' }),
                    createCell({ column_id: 'col-2', row_id: 'row-1', value: 25 }),
                ],
            },
            {
                id: 'row-2',
                order: 1,
                cells: [
                    createCell({ column_id: 'col-1', row_id: 'row-2', value: 'Jane' }),
                    createCell({ column_id: 'col-2', row_id: 'row-2', value: 30 }),
                ],
            },
        ],
        metadata: {},
    };

    describe('toJson', () => {
        test('should convert table to JSON string', () => {
            const json = DatasetTableUtils.toJson(mockTable);
            expect(json).toBeTruthy();
            expect(typeof json).toBe('string');
            
            const parsed = JSON.parse(json);
            expect(parsed.id).toBe('table-123');
            expect(parsed.columns).toHaveLength(2);
            expect(parsed.rows).toHaveLength(2);
        });
    });

    describe('toCsv', () => {
        test('should convert table to CSV string', () => {
            const csv = DatasetTableUtils.toCsv(mockTable);
            expect(csv).toBeTruthy();
            expect(typeof csv).toBe('string');
            
            const lines = csv.split('\n');
            expect(lines[0]).toBe('name,age');
            expect(lines[1]).toBe('John,25');
            expect(lines[2]).toBe('Jane,30');
        });

        test('should handle empty table', () => {
            const emptyTable: DatasetTable = {
                id: 'empty',
                columns: [],
                rows: [],
                metadata: {},
            };
            
            const csv = DatasetTableUtils.toCsv(emptyTable);
            expect(csv).toBe('');
        });

        test('should escape CSV values with commas', () => {
            const tableWithCommas: DatasetTable = {
                id: 'table-commas',
                columns: [
                    {
                        id: 'col-1',
                        name: 'description',
                        data_type: DataTypeChoices.TEXT,
                        source: SourceChoices.OTHERS,
                        metadata: {},
                        is_frozen: false,
                        is_visible: true,
                        eval_tags: [],
                        order_index: 0,
                    },
                ],
                rows: [
                    {
                        id: 'row-1',
                        order: 0,
                        cells: [
                            createCell({ column_id: 'col-1', row_id: 'row-1', value: 'Hello, World!' }),
                        ],
                    },
                ],
                metadata: {},
            };
            
            const csv = DatasetTableUtils.toCsv(tableWithCommas);
            expect(csv).toContain('"Hello, World!"');
        });
    });

    describe('convertValue', () => {
        test('should convert boolean values', () => {
            expect(DatasetTableUtils.convertValue(true, DataTypeChoices.BOOLEAN)).toBe(true);
            expect(DatasetTableUtils.convertValue('true', DataTypeChoices.BOOLEAN)).toBe(true);
            expect(DatasetTableUtils.convertValue('false', DataTypeChoices.BOOLEAN)).toBe(false);
            expect(DatasetTableUtils.convertValue('anything', DataTypeChoices.BOOLEAN)).toBe(false);
        });

        test('should convert integer values', () => {
            expect(DatasetTableUtils.convertValue('123', DataTypeChoices.INTEGER)).toBe(123);
            expect(DatasetTableUtils.convertValue(456, DataTypeChoices.INTEGER)).toBe(456);
            expect(DatasetTableUtils.convertValue('123.45', DataTypeChoices.INTEGER)).toBe(123);
        });

        test('should convert float values', () => {
            expect(DatasetTableUtils.convertValue('123.45', DataTypeChoices.FLOAT)).toBe(123.45);
            expect(DatasetTableUtils.convertValue(678.9, DataTypeChoices.FLOAT)).toBe(678.9);
        });

        test('should convert JSON values', () => {
            const jsonString = '{"key": "value"}';
            const result = DatasetTableUtils.convertValue(jsonString, DataTypeChoices.JSON);
            expect(result).toEqual({ key: 'value' });
            
            const jsonObject = { key: 'value' };
            const result2 = DatasetTableUtils.convertValue(jsonObject, DataTypeChoices.JSON);
            expect(result2).toEqual(jsonObject);
        });

        test('should convert array values', () => {
            const array = [1, 2, 3];
            const result = DatasetTableUtils.convertValue(array, DataTypeChoices.ARRAY);
            expect(result).toEqual(array);
            
            const singleValue = 'test';
            const result2 = DatasetTableUtils.convertValue(singleValue, DataTypeChoices.ARRAY);
            expect(result2).toEqual(['test']);
        });

        test('should convert datetime values', () => {
            const dateString = '2023-01-01T00:00:00Z';
            const result = DatasetTableUtils.convertValue(dateString, DataTypeChoices.DATETIME);
            expect(result).toBe('2023-01-01T00:00:00.000Z');
        });

        test('should convert text values', () => {
            expect(DatasetTableUtils.convertValue(123, DataTypeChoices.TEXT)).toBe('123');
            expect(DatasetTableUtils.convertValue('hello', DataTypeChoices.TEXT)).toBe('hello');
        });

        test('should handle null values', () => {
            expect(DatasetTableUtils.convertValue(null, DataTypeChoices.TEXT)).toBe(null);
            expect(DatasetTableUtils.convertValue(undefined, DataTypeChoices.TEXT)).toBe(null);
        });

        test('should handle conversion errors gracefully', () => {
            // Invalid JSON should fall back to string
            const result = DatasetTableUtils.convertValue('invalid json', DataTypeChoices.JSON);
            expect(result).toBe('invalid json');
        });
    });
}); 