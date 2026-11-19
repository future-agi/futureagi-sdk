/**
 * Shared command-line parsing for the runners: `--name value`, `--name=value`, `--switch`.
 * Pure. Unknown flags are refused so a typo never runs a different suite.
 */

export function parseFlags(argv, { values = [], switches = [], lists = [] } = {}) {
  const flags = {};
  for (let i = 0; i < argv.length; i += 1) {
    const match = /^--([a-z][a-z0-9-]*)(?:=(.*))?$/.exec(argv[i]);
    if (!match) throw new Error(`unexpected argument '${argv[i]}'`);
    const [, name, inline] = match;
    if (switches.includes(name)) {
      flags[name] = true;
      continue;
    }
    if (!values.includes(name) && !lists.includes(name)) throw new Error(`unknown flag --${name}`);
    const value = inline ?? argv[++i];
    if (value === undefined) throw new Error(`--${name} needs a value`);
    flags[name] = lists.includes(name) ? value.split(",").map((s) => s.trim()).filter(Boolean) : value;
  }
  return flags;
}

export function need(flags, name) {
  if (flags[name] === undefined || flags[name] === "") throw new Error(`--${name} is required`);
  return flags[name];
}

/** A run id: UTC time plus a random suffix, safe in paths and resource names. */
export function newRunId(now = new Date()) {
  const stamp = now.toISOString().replace(/[-:]/g, "").replace(/\.\d+Z$/, "z").toLowerCase();
  return `${stamp}-${Math.random().toString(16).slice(2, 8)}`;
}
