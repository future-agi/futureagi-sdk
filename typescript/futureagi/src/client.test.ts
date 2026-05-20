import { Client, Environments, ModelTypes } from './';

describe('Client', () => {
  it('logs model conversations with canonical backend payload', async () => {
    const client = new Client({
      fiApiKey: 'test-api-key',
      fiSecretKey: 'test-secret-key',
      fiBaseUrl: 'http://localhost:8000',
    });
    const requestMock = jest.spyOn(client as any, 'request').mockResolvedValue({
      status: 'success',
      result: { log_id: 'log-123' },
    });

    const result = await client.log({
      modelId: 'model-e2e',
      modelType: ModelTypes.GENERATIVE_LLM,
      environment: Environments.PRODUCTION,
      modelVersion: 'v1',
      predictionTimestamp: 1767225600,
      conversation: {
        chat_history: [
          { role: 'user', content: 'hello' },
          { role: 'assistant', content: 'hi there' },
        ],
      },
      tags: { sdk_compliance: true },
    });

    expect(result.result.log_id).toBe('log-123');
    expect(requestMock).toHaveBeenCalledWith(
      expect.objectContaining({
        method: 'POST',
        url: 'http://localhost:8000/sdk/api/v1/log/model/',
        json: expect.objectContaining({
          model_id: 'model-e2e',
          model_type: 'GenerativeLLM',
          environment: 3,
          model_version: 'v1',
          prediction_timestamp: 1767225600,
          tags: { sdk_compliance: true },
        }),
      }),
      expect.anything(),
    );
  });

  it('validates chat history shape before logging', async () => {
    const client = new Client({
      fiApiKey: 'test-api-key',
      fiSecretKey: 'test-secret-key',
      fiBaseUrl: 'http://localhost:8000',
    });

    await expect(
      client.log({
        modelId: 'model-e2e',
        modelType: ModelTypes.GENERATIVE_LLM,
        environment: Environments.PRODUCTION,
        conversation: { chat_history: [{ role: 'user' }] },
      }),
    ).rejects.toThrow("Missing required key 'content'");
  });
});
