import { APIKeyAuth, ResponseHandler } from '../api/auth';
import { RequestConfig, HttpMethod } from '../api/types';
import { Routes } from '../utils/routes';
import {
    KnowledgeBaseConfig,
    KnowledgeBaseCreateResponse,
    KnowledgeBaseUpdateResponse,
    KnowledgeBaseListResponse,
    KnowledgeBaseOptions,
    SUPPORTED_FILE_TYPES,
    SupportedFileType
} from './types';
import {
    SDKException,
    InvalidAuthError,
    FileNotFoundException,
    UnsupportedFileType
} from '../utils/errors';
import { AxiosResponse } from 'axios';
import * as fs from 'fs';
import * as path from 'path';
import axios from 'axios';

/**
 * Response handler for Knowledge Base operations
 */
class KBResponseHandler extends ResponseHandler<
    KnowledgeBaseCreateResponse | KnowledgeBaseUpdateResponse | KnowledgeBaseListResponse | Record<string, any>,
    KnowledgeBaseConfig
> {
    /**
     * Parse successful knowledge base response
     */
    public static _parseSuccess(response: AxiosResponse): any {
        const data = response.data;
        const method = response.config.method?.toUpperCase();
        const url = response.config.url || '';

        // Treat backend payloads with { status: false } as errors
        if (data?.status === false) {
            const msg = data.result || data.detail || 'Knowledge Base operation failed';
            throw new SDKException(msg);
        }

        if (method === HttpMethod.POST && url.includes(Routes.knowledge_base)) {
            return data.result;
        }

        if (method === HttpMethod.PATCH && url.includes(Routes.knowledge_base)) {
            return data.result;
        }

        if (method === HttpMethod.DELETE) {
            return data;
        }

        return data;
    }

    /**
     * Handle knowledge base operation errors
     */
    public static _handleError(response: AxiosResponse): never {
        if (response.status === 403) {
            throw new InvalidAuthError();
        }

        const extractMsg = () => {
            return (
                response.data?.result ||
                response.data?.detail ||
                response.data?.message ||
                response.statusText
            );
        };

        if (response.status === 429) {
            throw new SDKException(extractMsg() || 'Rate limit exceeded.');
        }

        if (response.status >= 400 && response.status < 500) {
            throw new SDKException(extractMsg() || `Client error ${response.status}`);
        }

        if (response.status >= 500) {
            throw new SDKException(extractMsg() || 'Server encountered an error.');
        }

        // Fallback: throw generic error
        throw new SDKException('Knowledge base operation failed.');
    }
}

/**
 * Knowledge Base client for managing knowledge bases and file operations
 */
export class KnowledgeBase extends APIKeyAuth {
    public kb?: KnowledgeBaseConfig;
    private _validFilePaths: string[] = [];

    constructor(kbName?: string, options: KnowledgeBaseOptions = {}) {
        super({
            fiApiKey: options.fiApiKey,
            fiSecretKey: options.fiSecretKey,
            fiBaseUrl: options.fiBaseUrl,
            timeout: options.timeout
        });

        this.kb = undefined;

        if (kbName) {
            // Resolve name → id at construction time
            this._getKbFromName(kbName)
                .then(foundKb => {
                    this.kb = foundKb;
                })
                .catch(() => {
                    throw new SDKException(
                        `Knowledge Base with name '${kbName}' not found. Please create it first.`
                    );
                });
        }
    }

    /**
     * Update name of Knowledge Base and/or add files to it
     */
    async updateKb({
        kbName,
        newName,
        filePaths
    }: {
        kbName: string;
        newName?: string;
        filePaths?: string | string[];
    }): Promise<KnowledgeBase> {
        try {
            // Resolve target KB by name if needed
            if (!this.kb || this.kb.name !== kbName) {
                this.kb = await this._getKbFromName(kbName);
            }

            if (filePaths) {
                try {
                    await this._checkFilePaths(filePaths);
                } catch (error) {
                    if (error instanceof FileNotFoundException || error instanceof UnsupportedFileType) {
                        throw new SDKException(
                            "Knowledge Base update failed due to a file processing issue.",
                            error
                        );
                    } else if (error instanceof SDKException) {
                        throw new SDKException(
                            "Knowledge Base update failed due to invalid file path arguments.",
                            error
                        );
                    } else {
                        throw new SDKException(
                            "An unexpected error occurred during file path validation for update.",
                            error as Error
                        );
                    }
                }
            }

            const url = `${this.baseUrl}/${Routes.knowledge_base}`;

            // Prepare form fields
            const bodyFields: Record<string, any> = {
                name: newName ?? this.kb.name,
                kb_id: this.kb.id
            };

            // Prepare files map for multipart upload (key uniqueness: file0, file1, ...)
            const files: Record<string, any> = {};
            this._validFilePaths.forEach((filePath, idx) => {
                const fileName = path.basename(filePath);
                const fileExt = path.extname(filePath).slice(1).toLowerCase() as SupportedFileType;

                // Validate supported types again (defensive)
                if (!SUPPORTED_FILE_TYPES.includes(fileExt)) {
                    throw new UnsupportedFileType(fileExt, fileName);
                }

                files[`file${idx}`] = fs.createReadStream(filePath);
            });

            const response = await this.request({
                method: HttpMethod.PATCH,
                url,
                data: bodyFields,
                files,
                timeout: 300_000 // 5-min timeout similar to Python
            } as RequestConfig, KBResponseHandler) as KnowledgeBaseUpdateResponse;

            // Check if server reported any files that failed to upload
            if (response.notUploaded && response.notUploaded.length > 0) {
                throw new SDKException(
                    `Server reported that some files were not uploaded successfully: ${response.notUploaded.join(', ')}`
                );
            }

            if (response && this.kb) {
                if (response.id) this.kb.id = response.id;
                if (response.name) this.kb.name = response.name;
                if (response.files) this.kb.files = response.files;
            }

            return this;

        } catch (error) {
            if (error instanceof SDKException) {
                throw error;
            }
            throw new SDKException(
                "Failed to update the Knowledge Base due to an unexpected error.",
                error as Error
            );
        }
    }

    /**
     * Delete files from the Knowledge Base
     */
    async deleteFilesFromKb({
        kbName,
        fileNames
    }: {
        kbName: string;
        fileNames: string[];
    }): Promise<KnowledgeBase> {
        try {
            if (!this.kb || this.kb.name !== kbName) {
                this.kb = await this._getKbFromName(kbName);
            }

            if (!fileNames || fileNames.length === 0) {
                throw new SDKException(
                    "Files to be deleted not found or list is empty. Please provide correct File Names."
                );
            }

            const url = `${this.baseUrl}/${Routes.knowledge_base_files}`;
            const data = {
                file_names: fileNames,
                kb_id: this.kb.id
            };

            await this.request({
                method: HttpMethod.DELETE,
                url,
                json: data,
                headers: { 'Content-Type': 'application/json' }
            } as RequestConfig, KBResponseHandler);

            return this;

        } catch (error) {
            if (error instanceof SDKException) {
                throw error;
            }
            throw new SDKException(
                "Failed to delete files from the Knowledge Base due to an unexpected error.",
                error as Error
            );
        }
    }

    /**
     * Delete a Knowledge Base
     */
    async deleteKb({
        kbNames,
        kbIds
    }: {
        kbNames?: string | string[];
        kbIds?: string | string[];
    } = {}): Promise<KnowledgeBase> {
        try {
            const resolvedIds: string[] = [];

            // Resolve names first
            if (kbNames) {
                const namesArr = Array.isArray(kbNames) ? kbNames : [kbNames];
                for (const n of namesArr) {
                    try {
                        const conf = await this._getKbFromName(n);
                        resolvedIds.push(String(conf.id));
                    } catch {
                        // ignore names that weren't found
                    }
                }
                if (resolvedIds.length === 0) {
                    throw new SDKException('None of the provided Knowledge Base names could be resolved.');
                }
            }

            // Legacy ids param
            if (kbIds) {
                if (typeof kbIds === 'string') {
                    resolvedIds.push(kbIds);
                } else if (Array.isArray(kbIds)) {
                    resolvedIds.push(...kbIds.map(id => String(id)));
                } else {
                    throw new SDKException('kb_ids must be a string or a list of strings.');
                }
            }

            // Fallback to cached KB
            if (resolvedIds.length === 0 && this.kb?.id) {
                resolvedIds.push(this.kb.id);
            }

            if (resolvedIds.length === 0) {
                throw new SDKException('No Knowledge Base specified for deletion.');
            }

            const url = `${this.baseUrl}/${Routes.knowledge_base}`;
            const jsonPayload = { kb_ids: resolvedIds };

            await this.request({
                method: HttpMethod.DELETE,
                url,
                json: jsonPayload,
                headers: { 'Content-Type': 'application/json' }
            } as RequestConfig, KBResponseHandler);

            // Clear current KB if it was deleted
            if (this.kb && this.kb.id && resolvedIds.includes(this.kb.id)) {
                this.kb = undefined;
            }

            return this;

        } catch (error) {
            if (error instanceof SDKException) {
                throw error;
            }
            throw new SDKException(
                "Failed to delete Knowledge Base(s) due to an unexpected error.",
                error as Error
            );
        }
    }

    /**
     * Create a Knowledge Base
     */
    async createKb(
        name?: string,
        filePaths: string | string[] = []
    ): Promise<KnowledgeBase> {
        try {

            const finalKbName = name || (this.kb?.name) || "Unnamed KB";
            const url = `${this.baseUrl}/${Routes.knowledge_base}`;

            // Prepare fields
            const bodyFields: Record<string, any> = { name: finalKbName };

            // Handle optional files
            const files: Record<string, any> = {};
            if (filePaths) {
                await this._checkFilePaths(filePaths);

                this._validFilePaths.forEach((filePath, idx) => {
                    const fileName = path.basename(filePath);
                    const fileExt = path.extname(filePath).slice(1).toLowerCase() as SupportedFileType;

                    if (!SUPPORTED_FILE_TYPES.includes(fileExt)) {
                        throw new UnsupportedFileType(fileExt, fileName);
                    }

                    files[`file${idx}`] = fs.createReadStream(filePath);
                });
            }

            const response = await this.request({
                method: HttpMethod.POST,
                url,
                data: bodyFields,
                files: Object.keys(files).length > 0 ? files : undefined,
                timeout: 300_000
            } as RequestConfig, KBResponseHandler) as KnowledgeBaseCreateResponse;

            // Check if server reported any files that failed to upload during creation
            if (response.notUploaded && response.notUploaded.length > 0) {
                throw new SDKException(
                    `Server reported that some files were not uploaded during Knowledge Base creation: ${response.notUploaded.join(', ')}`
                );
            }

            this.kb = {
                id: response.kbId,
                name: response.kbName,
                files: response.fileIds || []
            };

            return this;

        } catch (error) {
            if (error instanceof SDKException) {
                throw error;
            }
            throw new SDKException(
                "Failed to create the Knowledge Base due to an unexpected error.",
                error as Error
            );
        }
    }

    /**
     * List all knowledge bases
     */
    async listKbs(search?: string): Promise<KnowledgeBaseConfig[]> {
        try {
            const params = search ? { search } : {};
            
            const response = await this.request({
                method: HttpMethod.GET,
                url: `${this.baseUrl}/${Routes.knowledge_base_list}`,
                params
            } as RequestConfig, KBResponseHandler) as KnowledgeBaseListResponse;

            return response.result.tableData.map(item => ({
                id: item.id,
                name: item.name,
                status: item.status,
                files: item.files
            }));

        } catch (error) {
            if (error instanceof SDKException) {
                throw error;
            }
            throw new SDKException(
                "Failed to list Knowledge Bases due to an unexpected error.",
                error as Error
            );
        }
    }

    /**
     * Get knowledge base by name
     */
    private async _getKbFromName(kbName: string): Promise<KnowledgeBaseConfig> {
        const response = await this.request({
            method: HttpMethod.GET,
            url: `${this.baseUrl}/${Routes.knowledge_base_list}`,
            params: { search: kbName }
        } as RequestConfig, KBResponseHandler) as KnowledgeBaseListResponse;

        const data = response.result.tableData;
        if (!data || data.length === 0) {
            throw new SDKException(`Knowledge Base with name '${kbName}' not found.`);
        }

        return {
            id: data[0].id,
            name: data[0].name,
            status: data[0].status,
            files: data[0].files
        };
    }

    /**
     * Validate file paths
     */
    private async _checkFilePaths(filePaths: string | string[]): Promise<boolean> {
        this._validFilePaths = [];

        if (typeof filePaths === 'string') {
            try {
                const stats = await fs.promises.stat(filePaths);
                
                if (stats.isDirectory()) {
                    const files = await fs.promises.readdir(filePaths);
                    const allFiles: string[] = [];
                    
                    for (const file of files) {
                        const fullPath = path.join(filePaths, file);
                        const fileStats = await fs.promises.stat(fullPath);
                        if (fileStats.isFile()) {
                            allFiles.push(fullPath);
                        }
                    }
                    
                    if (allFiles.length === 0) {
                        throw new FileNotFoundException(
                            filePaths,
                            `The directory '${filePaths}' is empty or contains no files.`
                        );
                    }
                    
                    this._validFilePaths = allFiles;
                    return true;
                } else if (stats.isFile()) {
                    this._validFilePaths = [filePaths];
                    return true;
                } else {
                    throw new FileNotFoundException(
                        filePaths,
                        `The provided path '${filePaths}' is not a valid file or directory.`
                    );
                }
            } catch (error) {
                if (error instanceof FileNotFoundException) {
                    throw error;
                }
                throw new FileNotFoundException(
                    filePaths,
                    `The provided path '${filePaths}' does not exist or is not accessible.`
                );
            }
        } else if (Array.isArray(filePaths)) {
            if (filePaths.length === 0) {
                throw new FileNotFoundException(
                    filePaths,
                    "The provided list of file paths is empty."
                );
            }

            const validPaths: string[] = [];
            const missingFiles: string[] = [];

            for (const filePath of filePaths) {
                try {
                    const stats = await fs.promises.stat(filePath);
                    if (stats.isFile()) {
                        validPaths.push(filePath);
                    } else {
                        missingFiles.push(filePath);
                    }
                } catch {
                    missingFiles.push(filePath);
                }
            }

            if (missingFiles.length > 0) {
                throw new FileNotFoundException(
                    missingFiles,
                    `Some file paths are invalid, not files, or do not exist: ${missingFiles.join(', ')}`
                );
            }

            if (validPaths.length === 0) {
                throw new FileNotFoundException(
                    filePaths,
                    "No valid files found in the provided list."
                );
            }

            this._validFilePaths = validPaths;
            return true;
        } else {
            throw new SDKException(
                `Unsupported type for file_paths: ${typeof filePaths}. Expected string or array.`
            );
        }
    }
}

export default KnowledgeBase; 