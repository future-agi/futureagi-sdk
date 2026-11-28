import * as ts from "typescript";

export const FIXTURE_ID = "00000000-0000-4000-8000-000000000001";
type Case = Record<string, any>;
const camel = (value: string) => value.replace(/_([a-z])/g, (_, c: string) => c.toUpperCase());

export function publicPath(row: Case): string {
  if (row.public_wrappers?.ts) return row.public_wrappers.ts.ts;
  if (row.wrapper) return row.wrapper.ts;
  if (row.adapter === "platform") return row.wrappers[0].ts;
  const name = row.adapter === "catalog" ? row.catalog.public : row.name;
  return "client." + name.split(".").map(camel).join(".");
}

export function methodAt(client: any, path: string, handles: Record<string, any> = {}) {
  const [root, ...parts] = path.split(".");
  let owner = root === "client" ? client : handles[root];
  if (!owner) throw new Error(`public handle fixture required for ${path}; no executor fallback`);
  for (const part of parts.slice(0, -1)) {
    owner = owner[part];
    if (!owner) throw new Error(`missing public namespace ${part} in ${path}`);
  }
  const method = owner[parts[parts.length - 1]];
  if (typeof method !== "function") throw new TypeError(`public method is not callable: ${path}`);
  return { owner, method };
}

function valueFor(name: string, row: Case): any {
  if (row.path_values && name in row.path_values) return row.path_values[name];
  const snake = name.replace(/[A-Z]/g, c => "_" + c.toLowerCase());
  if (row.query_example && snake in row.query_example) return row.query_example[snake];
  if (name === "body") {
    if (row.name === "prompts.create") return { name: "fixture", prompt_config: [{ messages: [] }] };
    return row.request_example ?? {};
  }
  if (["query", "params"].includes(name)) return row.query_example ?? {};
  if (name === "options" && row.stream) return { bounds: { maxReconnects: 0, maxConsecutiveFailures: 1 } };
  if (name === "options" && row.adapter === "platform") return { ...row.request_example, wait: false };
  if (["options", "selector"].includes(name)) return { version: "v1", wait: false };
  if (name === "fileNames") return ["fixture.txt"];
  if (name === "name" && row.name === "knowledgeBases.documents.addText") return "fixture.txt";
  if (name === "sourceType") return "trace";
  if (name === "id" || name.endsWith("Id") || name.endsWith("Pk")) return FIXTURE_ID;
  if (["limit", "page", "pageSize", "count"].includes(name)) return 1;
  if (name === "wait") return false;
  if (["version", "label"].includes(name)) return "v1";
  return "fixture";
}

/** Inspect only the call signature to supply valid inputs, never its routing body.
 * HTTP expectations still come from the pinned contract, not the public method.
 * Complex/destructured calls must provide an explicit invocation fixture.
 */
function parameters(method: Function, path: string): readonly ts.ParameterDeclaration[] {
  const source = ts.createSourceFile("wrapper.ts", `class Wrapper { ${method.toString()} }`, ts.ScriptTarget.Latest, true);
  const declaration = source.statements[0];
  const member = ts.isClassDeclaration(declaration) ? declaration.members[0] : undefined;
  if (!member || !ts.isMethodDeclaration(member)) throw new Error(`explicit public invocation fixture required for ${path}`);
  return member.parameters;
}

export function invokePublic(client: any, row: Case, handles: Record<string, any> = {}): any {
  const path = publicPath(row);
  const { owner, method } = methodAt(client, path, handles);
  const explicit = row.invocation?.ts ?? row.wrapper?.contract?.ts;
  if (explicit) return method.apply(owner, structuredClone(explicit.args));
  const args = parameters(method, path).map(parameter => {
    if (!ts.isIdentifier(parameter.name) || parameter.dotDotDotToken) throw new Error(`explicit public invocation fixture required for ${path}`);
    const name = parameter.name.text;
    if (parameter.initializer && !["body", "selector"].includes(name) && !(name === "options" && row.stream)) return undefined;
    return valueFor(name, row);
  });
  return method.apply(owner, args);
}
