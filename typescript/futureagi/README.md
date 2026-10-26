# Future AGI TypeScript SDK <!-- omit in toc -->

The official TypeScript / Node.js client for the **Future AGI** platform.  
Use it to create and manage evaluation datasets, run prompt–template
experiments, build knowledge-bases, and monitor the quality of your
generative-AI models – all from code.

* **Website:** <https://futureagi.com>  
* **API docs:** <https://docs.futureagi.com>  
* **NPM:** [`@future-agi/sdk`](https://www.npmjs.com/package/@future-agi/sdk)

---

- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Authentication](#authentication)
- [Quick-start](#quick-start)
- [API overview](#api-overview)
- [Error handling](#error-handling)
- [Contributing](#contributing)
- [License](#license)

---

## Features

• 📊 **Datasets** – create, mutate, download & evaluate tabular datasets.  
• 📜 **Prompt templates** – full CRUD, versioning and execution of
  templates (including OpenAI-style chat messages & variables).  
• 📚 **Knowledge-bases** – upload files, list and delete KB assets.  
• ⚙️ **Utilities** – bounded executors, helper constants and strong
  TypeScript types for all request / response payloads.  
• 🤝 **Modern build** – ships both **ESM (ES2020)** *and*
  **CommonJS (ES2016)** bundles; works in Node 18+ and all modern bundlers.

## Requirements

* Node.js **18 or later** (the SDK targets ES2020 for ESM builds).  
* An **API&nbsp;key** and **Secret key** obtained from your Future AGI
  account.

## Installation

```bash
# npm
npm install @future-agi/sdk

# pnpm
pnpm add @future-agi/sdk

# yarn
yarn add @future-agi/sdk
```

The package automatically selects the build that matches your
environment:

| Import style       | Runtime requirement | File served                |
| ------------------ | ------------------- | -------------------------- |
| `import … from`    | ES modules (Node 14+, browsers) | `dist/esm/**` (ES2020) |
| `require('…')`     | CommonJS (all Node versions)    | `dist/src/**` (ES2016) |

## Authentication

Set your credentials as environment variables **once**:

```bash
export FI_API_KEY="YOUR_API_KEY"
export FI_SECRET_KEY="YOUR_SECRET_KEY"
```

…or pass them explicitly when creating a client:

```ts
import { Dataset } from '@future-agi/sdk';

const ds = await Dataset.open('my-dataset', {
  fiApiKey: 'YOUR_API_KEY',
  fiSecretKey: 'YOUR_SECRET_KEY',
  createIfMissing: true
});
```

## Quick-start

### 0. The platform client (every API, one object)

`Client` covers the whole platform (158 operations across datasets, prompts, evals, traces, annotation
queues, knowledge bases, gateways, dashboards, ...). It is generated from the API contract, so method
names match the Python SDK and the MCP tools; see `sdkgen/README.md` in the repository.

```ts
import { Client } from '@future-agi/sdk';

const client = new Client();   // FI_API_KEY, FI_SECRET_KEY, FI_BASE_URL (or pass apiKey/secretKey/baseUrl)

const ds = await client.datasets.create({ new_dataset_name: 'qa-set' });
await client.datasets.columns.add(ds.dataset_id!, { new_columns_data: [{ name: 'question', data_type: 'text' }] });
for await (const d of client.datasets.list({ search_text: 'qa' })) console.log(d.name);   // walks every page
await client.knowledgeBases.create({ name: 'docs', file: ['./notes.txt'] });               // multipart upload
await client.datasets.get(ds.dataset_id!, {}, { timeout: 5_000, headers: { 'X-Trace': 't1' } });  // per-call options
await client.request('GET', '/some/new/endpoint/', { query: { page: 1 } });              // anything else, same auth/retries
```

Errors are typed (`platform.NotFoundError`, `platform.BadRequestError`, ...) and carry the backend's `type`,
`code` and `detail`; 429 is retried, and 5xx only for calls that are safe to repeat. Extend the client by
adding methods in `src/platform/resources/<name>.ts` (never regenerated) or passing your own classes:
`new Client({ resources: { datasets: MyDatasets } })`.

The classes below (`Dataset`, `Prompt`, `KnowledgeBase`, ...) keep working unchanged.

### 1. Create a dataset & add rows

```ts
import { Dataset, DataTypeChoices } from '@future-agi/sdk';

async function main() {
  // Open (or create) a dataset
  const ds = await Dataset.open('translations', { createIfMissing: true });

  // Add two columns
  await ds.addColumns([
    { name: 'prompt',  dataType: DataTypeChoices.TEXT },
    { name: 'answer',  dataType: DataTypeChoices.TEXT }
  ]);

  // Add a couple of rows
  await ds.addRows([
    { prompt: 'Translate “Hello World” to French', answer: 'Bonjour le monde' },
    { prompt: 'Translate “Good night”  to German', answer: 'Gute Nacht'      }
  ]);

  console.log('Dataset ready:', ds.getConfig());
}
```

### 2. Create & execute a prompt template

```ts
import { Prompt, MessageBase, ModelConfig } from '@future-agi/sdk';

const prompt = new Prompt();

await prompt.createNewVersion({
  template: {
    name: 'translator',
    messages: [
      { role: 'system', content: 'You are a translator.' } as MessageBase,
      { role: 'user',   content: 'Translate {{text}} to French.' } as MessageBase
    ],
    variable_names: { text: 'string' },
    model_configuration: new ModelConfig({ model_name: 'gpt-3.5-turbo' })
  }
});

// Run the template with variables
const result = await prompt.template?.run({ text: 'Good morning' });
console.log(result);
```

### 3. Build a knowledge base

```ts
import { KnowledgeBase } from '@future-agi/sdk';

const kb = new KnowledgeBase();
await kb.createKb('docs', ['./README.md', './whitepaper.pdf']);

const list = await kb.listKbs();
console.log(`You now have ${list.length} knowledge-bases!`);
```

## API overview

```ts
import {
  Dataset,          // datasets / evaluations
  KnowledgeBase,    // RAG knowledge-bases
  Prompt,           // prompt templates
  constants,        // misc constants
  errors            // rich error classes
} from '@future-agi/sdk';
```

See the full **TypeDoc API reference** at  
<https://futureagi.com/docs/sdk/typescript>.

## Error handling

All SDK-specific failures extend `SDKException`.

```ts
import { SDKException } from '@future-agi/sdk/dist/src/utils/errors';

try {
  await Dataset.open('missing-dataset');
} catch (err) {
  if (err instanceof SDKException) {
    console.error(err.getErrorCode(), err.getMessage());
  } else {
    console.error('Unexpected error', err);
  }
}
```

Common subclasses include:

* `InvalidAuthError` – wrong or missing credentials.  
* `DatasetNotFoundError` – dataset name not found.  
* `RateLimitError` – API quota exceeded.

## Contributing

1. Fork the repo and create your branch from `main`.  
2. Run `pnpm i && pnpm test` to ensure the test-suite is green.  
3. Submit a pull-request – please include unit tests for new behaviour.

See `CONTRIBUTING.md` at the project root for more details.

## License

This project is distributed under a BSD-style license – see
[LICENSE.md](../../LICENSE.md) for the full text.