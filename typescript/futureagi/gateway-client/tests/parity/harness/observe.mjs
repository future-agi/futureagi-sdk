// Turn whatever a case returns or throws into stable, JSON-able data.
// Classes are named by constructor name. Strings lose stack-frame locations and
// install paths; harness/hygiene.mjs refuses any other local path at write time.

// A frame's location says where code sits, not what it does: "(<file URL>:84:71)",
// "(/srv/x.js:1:2)" and "(node:internal/x:3:4)" all become "(<frame>)", line and
// column included, and a bare "at /srv/x.js:1:2" becomes "at <frame>". Only an
// absolute location matches, so an ISO time ("...T00:00:05") never does.
const FRAME = /\((?:file:\/\/|node:|\/)[^()\n]*:\d+:\d+\)/g;
const BARE_FRAME = /\bat (?:file:\/\/|node:|\/)\S*:\d+:\d+/g;
const PATH = /(?:file:\/\/)?(?:\/[\w.@+-]+)+\/node_modules\//g;
const MAX_DEPTH = 8;
export const UNDEFINED = "<undefined>";

export function clean(text) {
  return String(text).replace(FRAME, "(<frame>)").replace(BARE_FRAME, "at <frame>").replace(PATH, "<path>/node_modules/");
}

function ctorName(value) {
  return value?.constructor?.name ?? Object.prototype.toString.call(value);
}

function chain(value) {
  const names = [];
  let proto = Object.getPrototypeOf(value);
  while (proto && proto !== Object.prototype) {
    names.push(proto.constructor?.name ?? "?");
    proto = Object.getPrototypeOf(proto);
  }
  return names;
}

export function observeError(err, depth = 0) {
  const attrs = {};
  for (const key of Object.keys(err).sort()) {
    if (key === "response" || key === "request") continue;
    attrs[key] = observe(err[key], depth + 1);
  }
  const out = {
    __exception__: err.name ?? ctorName(err),
    class: ctorName(err),
    chain: chain(err),
    message: clean(err.message ?? ""),
    toString: clean(String(err)),
    attrs,
  };
  if (err.cause !== undefined) out.cause = err.cause instanceof Error ? { name: err.cause.name, message: clean(err.cause.message) } : observe(err.cause, depth + 1);
  if (err.response instanceof Response) out.response_status = err.response.status;
  return out;
}

function entries(obj, depth) {
  const out = {};
  for (const key of Object.keys(obj).sort()) out[key] = observe(obj[key], depth + 1);
  return out;
}

export function observe(value, depth = 0) {
  if (depth > MAX_DEPTH) return { __truncated__: ctorName(value) };
  if (value === undefined) return UNDEFINED;
  if (value === null || typeof value === "boolean" || typeof value === "string") return typeof value === "string" ? clean(value) : value;
  if (typeof value === "number") return Number.isFinite(value) ? value : String(value);
  if (typeof value === "bigint") return { __bigint__: String(value) };
  if (typeof value === "symbol") return { __symbol__: String(value) };
  if (typeof value === "function") return { __function__: value.name || "<anonymous>", class: /^class\s/.test(Function.prototype.toString.call(value)) };
  if (value instanceof Error) return observeError(value, depth);
  if (value instanceof Response) return { __response__: value.status, type: value.headers.get("content-type") };
  if (value instanceof Headers) return { __headers__: [...value.entries()].sort() };
  if (value instanceof Uint8Array || value instanceof ArrayBuffer) return { __bytes__: new TextDecoder().decode(value) };
  if (Array.isArray(value)) return value.map((v) => observe(v, depth + 1));
  if (value instanceof Map) return { __map__: [...value.entries()].map(([k, v]) => [observe(k), observe(v, depth + 1)]).sort((a, b) => (JSON.stringify(a[0]) < JSON.stringify(b[0]) ? -1 : 1)) };
  if (value instanceof Set) return { __set__: [...value].map((v) => observe(v, depth + 1)).sort((a, b) => (JSON.stringify(a) < JSON.stringify(b) ? -1 : 1)) };
  if (typeof value.then === "function") return { __promise__: true };
  if (typeof value[Symbol.asyncIterator] === "function" && Object.keys(value).length === 0) return { __async_iterable__: ctorName(value) };
  const proto = Object.getPrototypeOf(value);
  if (proto === Object.prototype || proto === null) return entries(value, depth);
  return { __object__: ctorName(value), attrs: entries(value, depth) };
}

function sortKeys(value) {
  if (Array.isArray(value)) return value.map(sortKeys);
  if (value && typeof value === "object") {
    const out = {};
    for (const key of Object.keys(value).sort()) out[key] = sortKeys(value[key]);
    return out;
  }
  return value;
}

// The one serialisation goldens use (same layout as Python's json.dumps(indent=1,
// sort_keys=True, ensure_ascii=True)): sorted keys, 1-space indent, ASCII only.
export function dump(data) {
  const text = JSON.stringify(sortKeys(data), null, 1);
  return text.replace(/[\u007f-￿]/g, (c) => "\\u" + c.charCodeAt(0).toString(16).padStart(4, "0")) + "\n";
}
