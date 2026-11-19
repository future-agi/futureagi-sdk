// Generated public declarations from @future-agi/sdk 0.1.2; do not edit.
import { APIKeyAuth, APIKeyAuthConfig } from '../api/auth.js';
import { PromptTemplate, Variables } from './types.js';
import { PromptLabels } from './labels.js';
/**
 * Main Prompt client – allows programmatic CRUD and execution of prompt templates.
 */
export declare class Prompt extends APIKeyAuth {
    template?: PromptTemplate;
    /**
     * List all prompt templates (raw JSON payload).
     */
    static listTemplates(options?: APIKeyAuthConfig): Promise<Record<string, any>>;
    /**
     * Convenience: fetch template by exact name.
     */
    static getTemplateByName(name: string, { label, version, ...options }?: APIKeyAuthConfig & {
        label?: string;
        version?: string;
    }): Promise<PromptTemplate>;
    /**
     * Delete template by name (helper).
     */
    static deleteTemplateByName(name: string, options?: APIKeyAuthConfig): Promise<boolean>;
    /** Set default version for a template by name (class helper). */
    static setDefaultVersion(templateName: string, version: string, options?: APIKeyAuthConfig): Promise<Record<string, any>>;
    /** List versions and labels for a template by name or id. */
    static getTemplateLabels(args?: APIKeyAuthConfig & {
        template_name?: string;
        template_id?: string;
    }): Promise<Record<string, any>>;
    /** Assign label to template/version using only names. */
    static assignLabelToTemplateVersion(templateName: string, version: string, label: string, options?: APIKeyAuthConfig): Promise<Record<string, any>>;
    /** Remove label by name from template/version using only names. */
    static removeLabelFromTemplateVersion(templateName: string, version: string, label: string, options?: APIKeyAuthConfig): Promise<Record<string, any>>;
    constructor(template?: PromptTemplate, options?: APIKeyAuthConfig);
    /**
     * Create a new draft prompt template.
     */
    open(): Promise<Prompt>;
    /** Public: list full version history */
    listTemplateVersions(): Promise<any[]>;
    /** Save current draft state to backend */
    saveCurrentDraft(): Promise<boolean>;
    /** Commit current draft version */
    commitCurrentVersion(message?: string, set_default?: boolean, label?: string | undefined): Promise<boolean>;
    /** Commit current draft if needed then open a new draft version */
    createNewVersion({ template, commit_message, set_default, }?: {
        template?: PromptTemplate;
        commit_message?: string;
        set_default?: boolean;
    }): Promise<Prompt>;
    /** Accessor: label service for instance operations */
    labels(): PromptLabels;
    /**
     * Execution support removed – this SDK variant focuses solely on template management.
     */
    /**
     * Delete the current template.
     */
    delete(): Promise<boolean>;
    /** Compile the template messages with provided variables.
     * Replaces {{var}} occurrences in string contents; preserves structured contents.
     */
    compile(variables?: Variables): Array<{
        role: string;
        content: string | any[];
    }>;
}
declare const _default: {
    Prompt: typeof Prompt;
};
export default _default;
export type PublishedCall1845 = () => Promise<Prompt>;
export type PublishedCall2060 = () => Promise<any[]>;
export type PublishedCall2332 = () => Promise<boolean>;
export type PublishedCall2421 = (message?: string, set_default?: boolean, label?: string | undefined) => Promise<boolean>;
export type PublishedCall2574 = ({ template, commit_message, set_default, }?: {
    template?: PromptTemplate;
    commit_message?: string;
    set_default?: boolean;
}) => Promise<Prompt>;
export type PublishedCall2838 = () => PromptLabels;
export type PublishedCall2925 = () => Promise<boolean>;
export type PublishedCall3191 = (variables?: Variables) => Array<{
    role: string;
    content: string | any[];
}>;
export type PublishedCall362 = (options?: APIKeyAuthConfig) => Promise<Record<string, any>>;
export type PublishedCall515 = (name: string, { label, version, ...options }?: APIKeyAuthConfig & {
    label?: string;
    version?: string;
}) => Promise<PromptTemplate>;
export type PublishedCall761 = (name: string, options?: APIKeyAuthConfig) => Promise<boolean>;
export type PublishedCall911 = (templateName: string, version: string, options?: APIKeyAuthConfig) => Promise<Record<string, any>>;
export type PublishedCall1108 = (args?: APIKeyAuthConfig & {
    template_name?: string;
    template_id?: string;
}) => Promise<Record<string, any>>;
export type PublishedCall1331 = (templateName: string, version: string, label: string, options?: APIKeyAuthConfig) => Promise<Record<string, any>>;
export type PublishedCall1546 = (templateName: string, version: string, label: string, options?: APIKeyAuthConfig) => Promise<Record<string, any>>;
