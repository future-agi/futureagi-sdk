import { APIKeyAuth, APIKeyAuthConfig } from '../src/api/auth';
import { Dataset } from '../src/datasets/dataset';
import { KnowledgeBase } from '../src/kb/client';
import { Prompt } from '../src/prompt/client';
import { MissingAuthError, SDKException } from '../src/utils/errors';

const cases = [
    { label: 'both keys', fiApiKey: undefined, fiSecretKey: undefined, missing: "'fiApiKey', 'fiSecretKey'" },
    { label: 'API key', fiApiKey: undefined, fiSecretKey: 'synthetic-secret-key', missing: "'fiApiKey'" },
    { label: 'secret key', fiApiKey: 'synthetic-api-key', fiSecretKey: undefined, missing: "'fiSecretKey'" }
];
const clients: Array<[string, (config: APIKeyAuthConfig) => APIKeyAuth]> = [
    ['APIKeyAuth', config => new APIKeyAuth(config)],
    ['Dataset', config => new Dataset(config)],
    ['Prompt', config => new Prompt(undefined, config)],
    ['KnowledgeBase', config => new KnowledgeBase(undefined, config)]
];

function expectActionable(error: unknown, missing: string): void {
    expect(error).toBeInstanceOf(Error);
    expect(error).toBeInstanceOf(SDKException);
    expect(error).toBeInstanceOf(MissingAuthError);
    const authError = error as MissingAuthError;
    expect(authError.message).toBe(authError.getMessage());
    expect(authError.message).toContain('FI_API_KEY');
    expect(authError.message).toContain('FI_SECRET_KEY');
    expect(authError.message).toContain('fiApiKey');
    expect(authError.message).toContain('fiSecretKey');
    expect(authError.message).toContain(`Missing: ${missing}`);
    expect(authError.message).not.toContain('fi_api_key');
    expect(authError.message).not.toContain('fi_secret_key');
    expect(authError.message).not.toContain('synthetic-api-key');
    expect(authError.message).not.toContain('synthetic-secret-key');
    expect(authError.stack).toContain(`MissingAuthError: ${authError.message}`);
    expect(String(authError)).toContain(authError.message);
    expect(authError.name).toBe('MissingAuthError');
    expect(authError.getErrorCode()).toBe('MISSING_FI_CLIENT_AUTHENTICATION');
}

describe('legacy missing-credential diagnostics', () => {
    beforeEach(() => {
        jest.replaceProperty(process, 'env', { ...process.env });
        delete process.env.FI_API_KEY;
        delete process.env.FI_SECRET_KEY;
        delete process.env.FI_API_KEY_NAME;
        delete process.env.FI_SECRET_KEY_NAME;
    });
    afterEach(() => jest.restoreAllMocks());

    it.each(cases)('populates Error.message and stack when missing $label', ({ fiApiKey, fiSecretKey, missing }) => {
        const cause = new Error('synthetic configuration failure');
        const error = new MissingAuthError(fiApiKey, fiSecretKey, cause);
        expectActionable(error, missing);
        expect(error.cause).toBe(cause);
        expect(error.missingApiKey).toBe(!fiApiKey);
        expect(error.missingSecretKey).toBe(!fiSecretKey);
    });

    describe.each(clients)('%s', (_label, create) => {
        it.each(cases)('explains missing $label through normal error logging', ({ fiApiKey, fiSecretKey, missing }) => {
            let error: unknown;
            try {
                create({ fiApiKey, fiSecretKey });
            } catch (caught) {
                error = caught;
            }
            expectActionable(error, missing);
        });

        it('still accepts synthetic credentials through environment fallback', async () => {
            process.env.FI_API_KEY = 'synthetic-api-key';
            process.env.FI_SECRET_KEY = 'synthetic-secret-key';
            const client = create({ fiBaseUrl: 'https://sdk.invalid' });
            try {
                expect(client.fiApiKey).toBe('synthetic-api-key');
                expect(client.fiSecretKey).toBe('synthetic-secret-key');
            } finally {
                await client.close();
            }
        });
    });

    it('treats empty strings as missing credentials', () => {
        const error = new MissingAuthError('', '');
        expectActionable(error, "'fiApiKey', 'fiSecretKey'");
        expect(error.missingApiKey).toBe(true);
        expect(error.missingSecretKey).toBe(true);
    });
});
