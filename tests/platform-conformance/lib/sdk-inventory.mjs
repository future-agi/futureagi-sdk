/** Read generated policy data, not the contract, to independently check SDK route absence. */
import { readFileSync } from "node:fs";
import { execFileSync } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";
const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../../..");

export function sdkInventory(root = ROOT) {
  const file = path.join(root, "typescript/futureagi/src/generated/platform/policy.gen.ts");
  const text = readFileSync(file, "utf8");
  // The generator emits a JSON object literal. Require the entire expression to be
  // valid JSON; never evaluate code or silently ignore an unfamiliar emission shape.
  const prefix = "export const PLATFORM_OPERATIONS = ";
  const suffix = " as const satisfies OperationTable;";
  if (text.split(prefix).length !== 2 || text.split(suffix).length !== 2) throw new Error("unrecognized SDK policy declaration");
  const expression = text.split(prefix)[1].split(suffix)[0];
  // The emitter terminates every operation row with a comma, including the last.
  const ts = Object.values(JSON.parse(expression.replace(/,\s*\}$/, "}")));
  const py = JSON.parse(execFileSync(process.env.SDKCONF_PYTHON ?? "python3", ["-I", "-c", `
import ast,json,sys
module=ast.parse(open(sys.argv[1]).read())
rows=[n.value for n in module.body if isinstance(n,ast.AnnAssign) and isinstance(n.target,ast.Name) and n.target.id=='OPERATIONS']
assert len(rows)==1 and isinstance(rows[0],ast.Dict)
out=[]
for key,value in zip(rows[0].keys,rows[0].values):
    assert isinstance(value,ast.Call)
    fields={k.arg:k.value for k in value.keywords}
    out.append({'name':ast.literal_eval(key),'method':ast.literal_eval(fields['method']),'path':ast.literal_eval(fields['path'])})
print(json.dumps(out))
`, path.join(root, "python/fi/generated/platform/policy.py")], { encoding: "utf8" }));
  return [...ts.map((o) => ({ ...o, language: "ts" })), ...py.map((o) => ({ ...o, language: "py" }))];
}
