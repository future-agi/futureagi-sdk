// Generated public declarations from @future-agi/sdk 0.1.2; do not edit.
import type { Prompt } from './client.js';
import { APIKeyAuthConfig } from '../api/auth.js';
export declare class PromptLabels {
    constructor(prompt: Prompt);
    list(): Promise<Record<string, any>>;
    getByName(name: string): Promise<Record<string, any> | undefined>;
    create(name: string): Promise<Record<string, any>>;
    assign(name: string, version?: string): Promise<Record<string, any>>;
    remove(name: string, version?: string): Promise<Record<string, any>>;
    removeFromCurrentVersion(name: string): Promise<Record<string, any>>;
}
export declare function setDefaultVersion(templateName: string, version: string, options?: APIKeyAuthConfig): Promise<Record<string, any>>;
export declare function getTemplateLabels({ template_name, template_id, ...options }?: APIKeyAuthConfig & {
    template_name?: string;
    template_id?: string;
}): Promise<Record<string, any>>;
export declare function assignLabelToTemplateVersion(templateName: string, version: string, label: string, options?: APIKeyAuthConfig): Promise<Record<string, any>>;
export declare function removeLabelFromTemplateVersion(templateName: string, version: string, label: string, options?: APIKeyAuthConfig): Promise<Record<string, any>>;
export type PublishedCall639 = (templateName: string, version: string, options?: APIKeyAuthConfig) => Promise<Record<string, any>>;
export type PublishedCall779 = ({ template_name, template_id, ...options }?: APIKeyAuthConfig & {
    template_name?: string;
    template_id?: string;
}) => Promise<Record<string, any>>;
export type PublishedCall975 = (templateName: string, version: string, label: string, options?: APIKeyAuthConfig) => Promise<Record<string, any>>;
export type PublishedCall1141 = (templateName: string, version: string, label: string, options?: APIKeyAuthConfig) => Promise<Record<string, any>>;
