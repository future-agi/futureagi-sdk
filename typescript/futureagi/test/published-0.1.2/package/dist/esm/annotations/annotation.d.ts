// Generated public declarations from @future-agi/sdk 0.1.2; do not edit.
import { APIKeyAuth } from '../api/auth.js';
import { AnnotationLabel, Project, BulkAnnotationResponse, AnnotationRecord, AnnotationOptions } from './types.js';
export declare class Annotation extends APIKeyAuth {
    /**
     * SDK client for logging human annotations using flat DataFrame-style format.
     *
     */
    constructor(options?: AnnotationOptions);
    logAnnotations(records: AnnotationRecord[], options?: {
        projectName?: string;
        timeout?: number;
    }): Promise<BulkAnnotationResponse>;
    getLabels(options?: {
        projectId?: string;
        timeout?: number;
    }): Promise<AnnotationLabel[]>;
    listProjects(options?: {
        projectType?: string;
        name?: string;
        pageNumber?: number;
        pageSize?: number;
        timeout?: number;
    }): Promise<Project[]>;
}
export type PublishedCall365 = (records: AnnotationRecord[], options?: {
    projectName?: string;
    timeout?: number;
}) => Promise<BulkAnnotationResponse>;
export type PublishedCall522 = (options?: {
    projectId?: string;
    timeout?: number;
}) => Promise<AnnotationLabel[]>;
export type PublishedCall638 = (options?: {
    projectType?: string;
    name?: string;
    pageNumber?: number;
    pageSize?: number;
    timeout?: number;
}) => Promise<Project[]>;
