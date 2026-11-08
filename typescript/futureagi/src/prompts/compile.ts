/** One rendered chat message (role, content and any other fields it carries). */
export type PromptMessage = Record<string, unknown>;
/** Values for `{{name}}` placeholders; a message placeholder takes a list of chat messages. */
export type PromptVariables = Record<string, unknown>;
/** A retrieved template version (with `prompt_config`), or a mapping with `messages`. */
export type CompilablePrompt = Record<string, unknown>;

const isRecord = (value: unknown): value is Record<string, unknown> =>
  value !== null && typeof value === "object" && !Array.isArray(value);

/** Render a retrieved wire template without a request or mutation. Missing variables remain literal. */
export function compilePrompt(template: CompilablePrompt, variables: PromptVariables = {}): PromptMessage[] {
  const owns = (name: string) => Object.prototype.hasOwnProperty.call(variables, name);
  const source = template.result ?? template;
  if (!isRecord(source)) throw new TypeError("template must contain a message mapping");
  let config: unknown = source.prompt_config ?? source;
  if (Array.isArray(config)) config = config[0] ?? {};
  if (!isRecord(config) || !Array.isArray(config.messages)) {
    throw new TypeError("template must contain a messages list");
  }
  const render = (value: unknown): unknown => {
    if (typeof value === "string") {
      return value.replace(/\{\{\s*([A-Za-z0-9_]+)\s*\}\}/g, (match, name: string) =>
        owns(name) ? String(variables[name]) : match);
    }
    if (Array.isArray(value)) return value.map(render);
    if (isRecord(value)) return Object.fromEntries(Object.entries(value).map(([key, item]) => [key, render(item)]));
    return value;
  };
  const clone = (value: unknown): unknown => {
    if (Array.isArray(value)) return value.map(clone);
    if (isRecord(value)) return Object.fromEntries(Object.entries(value).map(([key, item]) => [key, clone(item)]));
    return value;
  };
  const message = (value: unknown): PromptMessage => {
    if (!isRecord(value) || !("role" in value) || !("content" in value)) {
      throw new TypeError("each chat message must include role and content");
    }
    return { ...clone(value) as PromptMessage, content: render(value.content) };
  };
  return config.messages.flatMap((item: unknown) => {
    if (isRecord(item) && item.type === "placeholder") {
      const name = String(item.name);
      if (!owns(name)) return [clone(item) as PromptMessage];
      const replacement = variables[name];
      if (!Array.isArray(replacement)) throw new TypeError("message placeholders must be lists of chat messages");
      return replacement.map(message);
    }
    return [message(item)];
  });
}
