import { createServer, type Server } from 'node:http';
import type { AddressInfo } from 'node:net';
import { Prompt } from '../client';
import { PromptTemplate, UserMessage } from '../types';
import { SDKException } from '../../utils/errors';

// A loopback backend that answers generate-prompt and improve-prompt the way the
// server does today: with the id of a queued job instead of the generated text.
describe('Prompt generate and improve with queued jobs', () => {
  let server: Server;
  let baseUrl: string;
  let replies: unknown[];
  let received: Array<{ method?: string; url?: string; body: unknown }>;

  beforeAll(async () => {
    server = createServer((req, res) => {
      let data = '';
      req.on('data', chunk => { data += chunk; });
      req.on('end', () => {
        received.push({ method: req.method, url: req.url, body: data ? JSON.parse(data) : undefined });
        const reply = replies.shift();
        res.writeHead(reply === undefined ? 500 : 200, { 'Content-Type': 'application/json', Connection: 'close' });
        res.end(JSON.stringify(reply ?? { status: false, result: 'no reply queued' }));
      });
    });
    await new Promise<void>(resolve => server.listen(0, '127.0.0.1', resolve));
    baseUrl = `http://127.0.0.1:${(server.address() as AddressInfo).port}`;
  });

  afterAll(async () => {
    await new Promise(resolve => server.close(resolve));
  });

  beforeEach(() => {
    replies = [];
    received = [];
  });

  const newPrompt = () => new Prompt(
    new PromptTemplate({ name: 'support-summary', messages: [new UserMessage('Summarize the ticket.')] }),
    { fiApiKey: 'synthetic-api-key', fiSecretKey: 'synthetic-secret-key', fiBaseUrl: baseUrl },
  );
  const contents = (prompt: Prompt) => prompt.template!.messages.map(message => message.content);

  it('returns the generation job id and keeps the messages', async () => {
    replies.push({ status: true, result: { generation_id: 'generate_job-1' } });
    const prompt = newPrompt();
    const result = await prompt.generate('Summarize a support ticket in two sentences.');
    expect(contents(prompt)).toEqual(['Summarize the ticket.']);
    expect(result).toEqual({ jobId: 'generate_job-1' });
    expect(received).toEqual([
      { method: 'POST', url: '/model-hub/prompt-templates/generate-prompt/', body: { statement: 'Summarize a support ticket in two sentences.' } },
    ]);
  });

  it('sends the unchanged prompt to improve() after a queued generation', async () => {
    replies.push({ status: true, result: { generation_id: 'generate_job-1' } });
    replies.push({ status: true, result: { improve_id: 'improve_job-2' } });
    const prompt = newPrompt();
    await prompt.generate('Summarize a support ticket in two sentences.');
    const result = await prompt.improve('Keep it under 40 words.');
    expect(received[1]).toEqual({
      method: 'POST',
      url: '/model-hub/prompt-templates/improve-prompt/',
      body: { existing_prompt: 'Summarize the ticket.', improvement_requirements: 'Keep it under 40 words.' },
    });
    expect(contents(prompt)).toEqual(['Summarize the ticket.']);
    expect(result).toEqual({ jobId: 'improve_job-2' });
  });

  it.each(['generate', 'improve'] as const)('%s() applies prompt text the server returns directly', async (method) => {
    replies.push({ status: true, result: { prompt: 'Summarize the ticket in two sentences.' } });
    const prompt = newPrompt();
    await expect(prompt[method]('Two sentences.')).resolves.toEqual({ prompt: 'Summarize the ticket in two sentences.' });
    expect(contents(prompt)).toEqual(['Summarize the ticket in two sentences.']);
  });

  it('applies prompt text given beside an empty result', async () => {
    replies.push({ status: true, result: {}, prompt: 'Summarize the ticket in two sentences.' });
    const prompt = newPrompt();
    await expect(prompt.generate('Two sentences.')).resolves.toEqual({ prompt: 'Summarize the ticket in two sentences.' });
    expect(contents(prompt)).toEqual(['Summarize the ticket in two sentences.']);
  });

  it('rejects improve() of a last message that is not text before sending', async () => {
    const prompt = newPrompt();
    prompt.template!.messages[0].content = [{ type: 'text', text: 'Summarize the ticket.' }];
    await expect(prompt.improve('Keep it under 40 words.')).rejects.toBeInstanceOf(SDKException);
    expect(received).toEqual([]);
  });

  it.each([
    ['a status false answer', { status: false, result: { generation_id: 'generate_job-1', prompt: 'Text' } }],
    ['an empty result', { status: true, result: {} }],
    ['an empty prompt', { status: true, result: { prompt: '' } }],
    ['a non-string job id', { status: true, result: { generation_id: 7 } }],
  ])('%s from generate() rejects and keeps the messages', async (_label, reply) => {
    replies.push(reply);
    const prompt = newPrompt();
    await expect(prompt.generate('Two sentences.')).rejects.toBeInstanceOf(SDKException);
    expect(contents(prompt)).toEqual(['Summarize the ticket.']);
  });
});
