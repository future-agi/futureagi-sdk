import fs from 'fs';
import path from 'path';
import { KnowledgeBase } from '../../kb';
import { HttpMethod } from '../../api/types';

// Temporary directory for test files
const TMP_DIR = path.join(__dirname, '__tmp__');
const TEST_FILE_1 = path.join(TMP_DIR, 'test_kb_1.txt');
const TEST_FILE_2 = path.join(TMP_DIR, 'test_kb_2.txt');
const TEST_FILE_3 = path.join(TMP_DIR, 'test_kb_3.txt');

const TEST_KB_NAME = `sdk-test-kb-${Date.now()}`;
const KB_ID = 'kb-id-123';

/** Helper to ensure tmp files exist */
function ensureTmpFiles() {
    if (!fs.existsSync(TMP_DIR)) {
        fs.mkdirSync(TMP_DIR, { recursive: true });
    }
    [TEST_FILE_1, TEST_FILE_2, TEST_FILE_3].forEach((file) => {
        if (!fs.existsSync(file)) {
            fs.writeFileSync(file, 'dummy content');
        }
    });
}

/** Cleanup tmp directory */
function cleanupTmpFiles() {
    if (fs.existsSync(TMP_DIR)) {
        fs.readdirSync(TMP_DIR).forEach((file) => fs.unlinkSync(path.join(TMP_DIR, file)));
        fs.rmdirSync(TMP_DIR);
    }
}

describe('KnowledgeBase SDK – happy path', () => {
    let kb: KnowledgeBase;

    // Mock the HTTP layer once for all tests
    const requestMock = jest.spyOn(KnowledgeBase.prototype as any, 'request');

    beforeAll(() => {
        ensureTmpFiles();

        requestMock.mockImplementation(async (config: any) => {
            switch (config.method) {
                case HttpMethod.POST: {
                    // createKb
                    return {
                        kbId: KB_ID,
                        kbName: TEST_KB_NAME,
                        fileIds: ['file1', 'file3'],
                    };
                }
                case HttpMethod.PATCH: {
                    // updateKb
                    return {
                        id: KB_ID,
                        name: TEST_KB_NAME,
                        files: ['file1', 'file3', 'file2'],
                    };
                }
                case HttpMethod.DELETE: {
                    // deleteFiles or deleteKb → just ack
                    return {};
                }
                case HttpMethod.GET: {
                    // listKbs / getKbFromName
                    return {
                        result: {
                            tableData: [
                                { id: KB_ID, name: TEST_KB_NAME, files: ['file1', 'file3'] },
                            ],
                        },
                    };
                }
                default:
                    return {};
            }
        });
    });

    afterAll(() => {
        requestMock.mockRestore();
        // Leave temp files on disk; Node will clean up when jest exits
    });

    it('creates a knowledge base', async () => {
        kb = new KnowledgeBase();
        await kb.createKb(TEST_KB_NAME, [TEST_FILE_1, TEST_FILE_3]);

        expect(kb).toBeDefined();
        expect(kb.kb?.id).toBe(KB_ID);
        expect(kb.kb?.name).toBe(TEST_KB_NAME);
        expect(kb.kb?.files?.length).toBeGreaterThan(0);
    });

    it('updates an existing knowledge base by adding files', async () => {
        const originalFiles = kb.kb?.files?.length || 0;
        await kb.updateKb({ kbName: TEST_KB_NAME, filePaths: [TEST_FILE_2] });
        expect(kb.kb?.files?.length).toBeGreaterThan(originalFiles);
    });

    it('deletes files from a knowledge base', async () => {
        await kb.deleteFilesFromKb({ kbName: TEST_KB_NAME, fileNames: ['file3.txt'] });
        expect(requestMock).toHaveBeenLastCalledWith(
            expect.objectContaining({ method: HttpMethod.DELETE }),
            expect.anything()
        );
    });

    it('deletes the knowledge base', async () => {
        await kb.deleteKb({ kbIds: kb.kb?.id });
        expect(kb.kb).toBeUndefined();
    });
}); 