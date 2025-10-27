export type MessageContent =
  | string
  | Array<{ type: string; text?: string; [key: string]: any }>;

export class MessageBase {
  role: 'system' | 'user' | 'assistant' | string;
  content: MessageContent;

  constructor(role: 'system' | 'user' | 'assistant' | string, content: MessageContent) {
    this.role = role;
    this.content = content;
  }
}

export class UserMessage extends MessageBase {
  role: 'user';
  variable_names?: string[];

  constructor(content: MessageContent, variable_names?: string[]) {
    super('user', content);
    this.role = 'user';
    this.variable_names = variable_names;
  }
}

export class SystemMessage extends MessageBase {
  role: 'system';

  constructor(content: MessageContent) {
    super('system', content);
    this.role = 'system';
  }
}

export class AssistantMessage extends MessageBase {
  role: 'assistant';

  constructor(content: MessageContent) {
    super('assistant', content);
    this.role = 'assistant';
  }
}

export class ModelConfig {
  model_name: string;
  temperature: number;
  frequency_penalty: number;
  presence_penalty: number;
  max_tokens?: number;
  top_p: number;
  response_format?: Record<string, any> | string | null;
  tool_choice?: string | null;
  tools?: Array<Record<string, any>> | null;

  constructor(config: Partial<ModelConfig> = {}) {
    this.model_name = config.model_name ?? 'gpt-4o-mini';
    this.temperature = config.temperature ?? 0.7;
    this.frequency_penalty = config.frequency_penalty ?? 0;
    this.presence_penalty = config.presence_penalty ?? 0;
    this.max_tokens = config.max_tokens;
    this.top_p = config.top_p ?? 1.0;
    this.response_format = config.response_format ?? null;
    this.tool_choice = config.tool_choice ?? null;
    this.tools = config.tools ?? null;
  }
}

export class PromptTemplate {
  id?: string;
  name?: string;
  messages: MessageBase[];
  model_configuration?: ModelConfig;
  variable_names?: Record<string, string[]>;
  description?: string;
  version?: string;
  is_default?: boolean;
  evaluation_configs?: Array<Record<string, any>>;
  status?: string;
  error_message?: string;
  labels?: Array<{ id: string; name: string; type: string }>;
  placeholders?: Record<string, any[]>;

  constructor(template: Partial<PromptTemplate> = {}) {
    this.messages = template.messages || [];
    Object.assign(this, template);
  }
}

export type Variables = Record<string, string | string[]>;
