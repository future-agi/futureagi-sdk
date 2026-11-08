/** Pinned hey-api 0.97.3 omits its fetch client's response-style type parameter. */
import fs from "node:fs";

const [sdkPath, specPath, scopePath] = process.argv.slice(2);
const spec = JSON.parse(fs.readFileSync(specPath, "utf8"));
const scope = JSON.parse(fs.readFileSync(scopePath, "utf8"));
if (scope.operations.length !== 6 || new Set(scope.operations).size !== 6)
  throw new Error("Expected six lifecycle operations");

let source = fs.readFileSync(sdkPath, "utf8");
for (const operation of scope.operations) {
  const [method, path] = operation.split(" ");
  const id = spec.paths[path]?.[method.toLowerCase()]?.operationId;
  if (!id || !/^\w+$/.test(id))
    throw new Error(`Missing operation ID: ${operation}`);
  const pattern = new RegExp(`^export const ${id} = .*`, "gm");
  const matches = [...source.matchAll(pattern)];
  if (matches.length !== 1)
    throw new Error(`Expected one generated operation: ${id}`);
  const original = matches[0][0];
  if (original.includes("TResponseStyle extends ResponseStyle")) {
    if (
      !original.includes("TResponseStyle extends ResponseStyle = 'fields'") ||
      !original.includes("responseStyle?: TResponseStyle") ||
      !original.includes(", ThrowOnError, TResponseStyle>(")
    )
      throw new Error(`Incomplete native response-style signature: ${id}`);
    continue;
  }
  const updated = original
    .replace(
      "<ThrowOnError extends boolean = false>",
      "<ThrowOnError extends boolean = false, TResponseStyle extends ResponseStyle = 'fields'>",
    )
    .replace(
      /options: Options<(\w+), ThrowOnError>/,
      "options: Options<$1, ThrowOnError> & { responseStyle?: TResponseStyle }",
    )
    .replace(
      /\.(get|post)<(\w+), (\w+), ThrowOnError>\(/,
      ".$1<$2, $3, ThrowOnError, TResponseStyle>(",
    );
  // Fail if the pinned generator's shape changes; do not silently patch a
  // partial signature or alter its existing fields default.
  if (
    !updated.includes("TResponseStyle extends ResponseStyle = 'fields'") ||
    !updated.includes("{ responseStyle?: TResponseStyle }") ||
    !updated.includes(", ThrowOnError, TResponseStyle>(")
  )
    throw new Error(`Unsupported generated signature: ${id}`);
  source = source.replace(original, updated);
}

const importLine = "import type { ResponseStyle } from './client';\n";
if (!source.includes(importLine)) source = importLine + source;
fs.writeFileSync(sdkPath, source);
