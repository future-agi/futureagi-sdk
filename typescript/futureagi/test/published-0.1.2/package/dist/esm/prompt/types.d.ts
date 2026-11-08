// Generated public declarations from @future-agi/sdk 0.1.2; do not edit.
export type MessageContent = string | Array<{
    type: string;
    text?: string;
    [key: string]: any;
}>;
export declare class MessageBase {
    role: 'system' | 'user' | 'assistant' | string;
    content: MessageContent;
    constructor(role: 'system' | 'user' | 'assistant' | string, content: MessageContent);
}
export declare class UserMessage extends MessageBase {
    role: 'user';
    variable_names?: string[];
    constructor(content: MessageContent, variable_names?: string[]);
}
export declare class SystemMessage extends MessageBase {
    role: 'system';
    constructor(content: MessageContent);
}
export declare class AssistantMessage extends MessageBase {
    role: 'assistant';
    constructor(content: MessageContent);
}
export declare class ModelConfig {
    model_name: string;
    temperature: number;
    frequency_penalty: number;
    presence_penalty: number;
    max_tokens?: number;
    top_p: number;
    response_format?: Record<string, any> | string | null;
    tool_choice?: string | null;
    tools?: Array<Record<string, any>> | null;
    constructor(config?: Partial<ModelConfig>);
}
export declare class PromptTemplate {
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
    labels?: Array<{
        id: string;
        name: string;
        type: string;
    }>;
    placeholders?: Record<string, any[]>;
    constructor(template?: Partial<PromptTemplate>);
}
export type Variables = Record<string, string | string[]>;
