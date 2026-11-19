// Generated public declarations from @future-agi/sdk 0.1.2; do not edit.
import { APIKeyAuth } from '../api/auth.js';
import { KnowledgeBaseConfig, KnowledgeBaseOptions } from './types.js';
/**
 * Knowledge Base client for managing knowledge bases and file operations
 */
export declare class KnowledgeBase extends APIKeyAuth {
    kb?: KnowledgeBaseConfig;
    constructor(kbName?: string, options?: KnowledgeBaseOptions);
    /**
     * Update name of Knowledge Base and/or add files to it
     */
    updateKb({ kbName, newName, filePaths }: {
        kbName: string;
        newName?: string;
        filePaths?: string | string[];
    }): Promise<KnowledgeBase>;
    /**
     * Delete files from the Knowledge Base
     */
    deleteFilesFromKb({ kbName, fileNames }: {
        kbName: string;
        fileNames: string[];
    }): Promise<KnowledgeBase>;
    /**
     * Delete a Knowledge Base
     */
    deleteKb({ kbNames, kbIds }?: {
        kbNames?: string | string[];
        kbIds?: string | string[];
    }): Promise<KnowledgeBase>;
    /**
     * Create a Knowledge Base
     */
    createKb(name?: string, filePaths?: string | string[]): Promise<KnowledgeBase>;
    /**
     * List all knowledge bases
     */
    listKbs(search?: string): Promise<KnowledgeBaseConfig[]>;
}
export default KnowledgeBase;
export type PublishedCall379 = ({ kbName, newName, filePaths }: {
    kbName: string;
    newName?: string;
    filePaths?: string | string[];
}) => Promise<KnowledgeBase>;
export type PublishedCall623 = ({ kbName, fileNames }: {
    kbName: string;
    fileNames: string[];
}) => Promise<KnowledgeBase>;
export type PublishedCall815 = ({ kbNames, kbIds }?: {
    kbNames?: string | string[];
    kbIds?: string | string[];
}) => Promise<KnowledgeBase>;
export type PublishedCall1002 = (name?: string, filePaths?: string | string[]) => Promise<KnowledgeBase>;
export type PublishedCall1133 = (search?: string) => Promise<KnowledgeBaseConfig[]>;
