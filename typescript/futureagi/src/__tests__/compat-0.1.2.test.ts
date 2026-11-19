import * as fs from 'node:fs';
import * as path from 'node:path';
import * as ts from 'typescript';
import * as root from '../index';

interface PublishedExport {
  name: string;
  type: boolean;
  runtime: string | null;
}
const fixture: { exports: PublishedExport[] } = JSON.parse(
  fs.readFileSync(path.join(__dirname, 'compat-0.1.2.json'), 'utf8'),
);
const packageRoot = path.resolve(__dirname, '../..');

describe('published @future-agi/sdk 0.1.2 root exports', () => {
  test.each(fixture.exports.filter(item => item.runtime !== null))(
    '$name remains a runtime $runtime export',
    ({ name, runtime }) => {
      expect(Object.prototype.hasOwnProperty.call(root, name)).toBe(true);
      expect(typeof (root as Record<string, unknown>)[name]).toBe(runtime);
    },
  );

  test('the tsc type pin covers every fixture entry, including erased interfaces', () => {
    const text = fs.readFileSync(path.join(packageRoot, 'test/compat-0.1.2.types.ts'), 'utf8');
    const typeNames = [...text.matchAll(/^  Root\.(\w+),$/gm)].map(match => match[1]);
    const valueNames = [...text.matchAll(/^  typeof Root\.(\w+),$/gm)].map(match => match[1]);
    expect(typeNames).toEqual(fixture.exports.filter(item => item.type).map(item => item.name));
    expect(valueNames).toEqual(fixture.exports.filter(item => item.runtime !== null).map(item => item.name));
  });

  test('published properties, required inputs, constructors and return types compile against the current root', () => {
    // Use the same compiler/config as `tsc -p test/tsconfig.compat-0.1.2.json`.
    // No subprocess, output files, network, or SDK client construction.
    const configFile = path.join(packageRoot, 'test/tsconfig.compat-0.1.2.json');
    const read = ts.readConfigFile(configFile, ts.sys.readFile);
    expect(read.error).toBeUndefined();
    const config = ts.parseJsonConfigFileContent(read.config, ts.sys, path.dirname(configFile));
    expect(config.errors).toEqual([]);
    const program = ts.createProgram(config.fileNames, config.options);
    const diagnostics = ts.getPreEmitDiagnostics(program);
    expect(ts.formatDiagnostics(diagnostics, {
      getCanonicalFileName: file => file,
      getCurrentDirectory: () => packageRoot,
      getNewLine: () => '\n',
    })).toBe('');
  });

  test('private published constructors are not mistaken for public call contracts', () => {
    const baseline = JSON.parse(fs.readFileSync(path.join(__dirname, 'compat-0.1.2.json'), 'utf8'));
    expect(baseline.declarations['package/dist/esm/api/apikeys.d.ts']).toContain('private constructor();');
    expect(baseline.surface.APIKeyManager.value.constructors).toEqual([]);
    expect(baseline.surface.Annotation.value.constructors.length).toBeGreaterThan(0);
    const generated = fs.readFileSync(path.join(packageRoot, 'test/compat-0.1.2.types.ts'), 'utf8');
    expect(generated).not.toContain('const construct_APIKeyManager_value:');
    expect(generated).toContain('const construct_Annotation_value:');
  });

  test('strict call checks reject required arguments/options and changed returns', () => {
    const generated = fs.readFileSync(path.join(packageRoot, 'test/compat-0.1.2.types.ts'), 'utf8');
    const helper = generated.split('\n').find(line => line.startsWith('type StrictCall<'));
    expect(helper).toBeDefined();
    const file = path.join(packageRoot, 'test/synthetic-compat.ts');
    const constructorHelper = generated.split('\n').find(line => line.startsWith('type StrictConstruct<'));
    expect(constructorHelper).toBeDefined();
    const text = `${helper}\n${constructorHelper}
      interface Old { method(options?: { value?: string }): string }
      declare const requiredArgument: { method(options: { value?: string }): string };
      declare const requiredOption: { method(options?: { value: string }): string };
      declare const changedReturn: { method(options?: { value?: string }): number };
      declare const compatible: { method(options?: { value?: string; extra?: number }): string };
      const required_arg: StrictCall<Old['method']> = requiredArgument.method;
      const required_option: StrictCall<Old['method']> = requiredOption.method;
      const changed_return: StrictCall<Old['method']> = changedReturn.method;
      const accepted: StrictCall<Old['method']> = compatible.method;
      declare const renamed: { newField: number };
      const removed_field: { oldField: number } = renamed;
      declare const input: { value?: number };
      const required_field: { value: number } = input;
      declare class OldConstructor { constructor(options?: { value?: string }); }
      declare class RequiredConstructor { constructor(options: { value?: string }); }
      declare class RequiredConstructorOption { constructor(options?: { value: string }); }
      const constructor_argument: StrictConstruct<typeof OldConstructor> = RequiredConstructor;
      const constructor_option: StrictConstruct<typeof OldConstructor> = RequiredConstructorOption;
      declare abstract class AbstractConstructor { constructor(options?: { value?: string }); }
      const abstract_constructor: StrictConstruct<typeof AbstractConstructor> = AbstractConstructor;
    `;
    const options: ts.CompilerOptions = { strict: true, noEmit: true, types: [], skipLibCheck: true };
    const host = ts.createCompilerHost(options);
    const original = host.getSourceFile;
    host.getSourceFile = (name, languageVersion, onError, shouldCreateNewSourceFile) => name === file
      ? ts.createSourceFile(name, text, languageVersion, true)
      : original(name, languageVersion, onError, shouldCreateNewSourceFile);
    const program = ts.createProgram([file], options, host);
    const diagnostics = ts.getPreEmitDiagnostics(program);
    expect(diagnostics).toHaveLength(7);
    const lines = diagnostics.map(d => d.file!.text.slice(d.file!.getLineStarts()[
      d.file!.getLineAndCharacterOfPosition(d.start!).line]).split('\n')[0].trim());
    expect(lines.map(line => line.match(/^const (\w+)/)![1])).toEqual([
      'required_arg', 'required_option', 'changed_return', 'removed_field', 'required_field',
      'constructor_argument', 'constructor_option',
    ]);
  });
});
