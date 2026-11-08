import * as path from 'node:path';
import * as ts from 'typescript';
import { Routes } from '../index';

const packageRoot = path.resolve(__dirname, '../..');

describe('published 0.2.0 contracts', () => {
  test('canonical object construction and required reads compile', () => {
    const configFile = path.join(packageRoot, 'test/tsconfig.compat-0.2.0.json');
    const read = ts.readConfigFile(configFile, ts.sys.readFile);
    expect(read.error).toBeUndefined();
    const config = ts.parseJsonConfigFileContent(read.config, ts.sys, path.dirname(configFile));
    expect(config.errors).toEqual([]);
    const program = ts.createProgram(config.fileNames, config.options);
    expect(ts.formatDiagnostics(ts.getPreEmitDiagnostics(program), {
      getCanonicalFileName: file => file,
      getCurrentDirectory: () => packageRoot,
      getNewLine: () => '\n',
    })).toBe('');
  });

  test('the retired log_model route remains available from the root export', () => {
    // Property lookup keeps this runtime regression runnable before the fix.
    expect(Reflect.get(Routes, 'log_model')).toBe('sdk/api/v1/log/model/');
  });
});
