<div align="center">

![Future AGI Logo](Logo.png)

# Future AGI SDK

**The open-source SDK for AI evaluation, observability, and optimization**

[![PyPI version](https://badge.fury.io/py/futureagi.svg)](https://pypi.org/project/futureagi/)
[![Downloads](https://static.pepy.tech/badge/futureagi)](https://pepy.tech/project/futureagi)
[![Python Support](https://img.shields.io/pypi/pyversions/futureagi.svg)](https://pypi.org/project/futureagi/)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![GitHub Stars](https://img.shields.io/github/stars/future-agi/futureagi-sdk?style=social)](https://github.com/future-agi/futureagi-sdk)

[📖 Docs](https://docs.futureagi.com) • [🌐 Website](https://www.futureagi.com) • [💬 Community](https://www.linkedin.com/company/futureagi) • [🎯 Dashboard](https://app.futureagi.com)

</div>

---

## 📖 Table of Contents

- [What is Future AGI?](#-what-is-future-agi)
- [Installation](#-installation)
- [Authentication](#-authentication)
- [30-Second Examples](#-30-second-examples)
- [Quick Start](#-quick-start)
  - [Dataset Management](#-dataset-management)
  - [Prompt Workbench](#-prompt-workbench)
  - [Knowledge Base (RAG)](#-knowledge-base-rag)
- [How It Works](#️-how-it-works)
- [Core Use Cases](#-core-use-cases)
- [Real-World Use Cases](#-real-world-use-cases)
- [Why Choose Future AGI?](#-why-choose-future-agi)
- [Supported Integrations](#-supported-integrations)
- [Documentation](#-documentation)
- [Language Support](#-language-support)
- [Support & Community](#-support--community)
- [Contributing](#-contributing)
- [Testimonials](#-testimonials)
- [Roadmap](#-roadmap)
- [Troubleshooting & FAQ](#-troubleshooting--faq)

---

## 🚀 What is Future AGI?

Your agent passed every eval. Then it hallucinated a refund policy that doesn't exist. Future AGI gives you the tools to catch that — datasets, prompt versioning, knowledge bases, evaluations, and guardrails. One SDK, one feedback loop.

```bash
# Get started in 30 seconds
pip install futureagi
export FI_API_KEY="your_key"
export FI_SECRET_KEY="your_secret"
```

**👉 [Get Free API Keys](https://app.futureagi.com/signup) • [View Live Demo](https://docs.futureagi.com) • [Read Quick Start Guide](https://docs.futureagi.com/get-started/quickstart)**

### ✨ Key Features

- **🎯 Evaluations** — 50+ metrics, LLM-as-judge, and custom rubrics powered by the Critique AI agent
- **⚡ Guardrails** — Real-time safety checks with sub-100ms latency
- **📊 Datasets** — Programmatically create, version, and manage training and test datasets
- **🎨 Prompt Workbench** — Version control, A/B testing, and deployment labels for prompts
- **📚 Knowledge Base** — Document management and retrieval for RAG applications
- **📈 Analytics** — Model performance, token costs, and behavior insights
- **🤖 Simulate** — Test your AI system against realistic scenarios before users hit it
- **🔍 Observability** — OpenTelemetry-native tracing across 50+ frameworks


---

## 📦 Installation

### Python
```bash
pip install futureagi
```

### TypeScript/JavaScript
```bash
npm install @future-agi/sdk
# or
pnpm add @future-agi/sdk
```

**Requirements:** Python >= 3.10 | Node.js >= 14

---

## 🔑 Authentication

Get your API credentials from the [Future AGI Dashboard](https://app.futureagi.com):

```bash
export FI_API_KEY="your_api_key"
export FI_SECRET_KEY="your_secret_key"
```

Or set them programmatically:

```python
import os
os.environ["FI_API_KEY"] = "your_api_key"
os.environ["FI_SECRET_KEY"] = "your_secret_key"
```

## 🎯 Quick Start

### 📊 Dataset Management

Create and manage datasets with built-in evaluations:

```python
from fi.datasets import Dataset
from fi.datasets.types import (
    Cell, Column, DatasetConfig, DataTypeChoices,
    ModelTypes, Row, SourceChoices
)

# Create a new dataset
config = DatasetConfig(name="qa_dataset", model_type=ModelTypes.GENERATIVE_LLM)
dataset = Dataset(dataset_config=config)
dataset = dataset.create()

# Define columns
columns = [
    Column(name="user_query", data_type=DataTypeChoices.TEXT, source=SourceChoices.OTHERS),
    Column(name="ai_response", data_type=DataTypeChoices.TEXT, source=SourceChoices.OTHERS),
    Column(name="quality_score", data_type=DataTypeChoices.INTEGER, source=SourceChoices.OTHERS),
]

# Add data
rows = [
    Row(order=1, cells=[
            Cell(column_name="user_query", value="What is machine learning?"),
        Cell(column_name="ai_response", value="Machine learning is a subset of AI..."),
        Cell(column_name="quality_score", value=9),
    ]),
    Row(order=2, cells=[
            Cell(column_name="user_query", value="Explain quantum computing"),
        Cell(column_name="ai_response", value="Quantum computing uses quantum bits..."),
        Cell(column_name="quality_score", value=8),
    ]),
]

# Push data and run evaluations
    dataset = dataset.add_columns(columns=columns)
    dataset = dataset.add_rows(rows=rows)

# Add automated evaluation
dataset.add_evaluation(
    name="factual_accuracy",
    eval_template="is_factually_consistent",
    model="gpt-4o-mini",
    required_keys_to_column_names={
        "input": "user_query",
        "output": "ai_response",
        "context": "user_query",
    },
    run=True
)

print("✓ Dataset created with automated evaluations")
```

### 🎨 Prompt Workbench

Version control and A/B test your prompts:

```python
from fi.prompt import Prompt, PromptTemplate, ModelConfig

# Create a versioned prompt template
template = PromptTemplate(
    name="customer_support",
    messages=[
        {"role": "system", "content": "You are a helpful customer support agent."},
        {"role": "user", "content": "Help {{customer_name}} with {{issue_type}}."},
    ],
    variable_names={"customer_name": ["Alice"], "issue_type": ["billing"]},
    model_configuration=ModelConfig(model_name="gpt-4o-mini", temperature=0.7)
)

# Create and version the template
client = Prompt(template)
client.create()  # Create v1
client.commit_current_version("Initial version", set_default=True)

# Assign deployment labels
client.assign_label("Production", version="v1")

# Compile with variables
compiled = client.compile(customer_name="Bob", issue_type="refund")
print(compiled)
# Output: [
#   {"role": "system", "content": "You are a helpful customer support agent."},
#   {"role": "user", "content": "Help Bob with refund."}
# ]
```

**A/B Testing Example:**

```python
import random
from openai import OpenAI
from fi.prompt import Prompt

# Fetch different variants (returns Prompt instances)
variant_a = Prompt.get_template_by_name("customer_support", label="variant-a")
variant_b = Prompt.get_template_by_name("customer_support", label="variant-b")

# Randomly select and use
selected = random.choice([variant_a, variant_b])
compiled = selected.compile(customer_name="Alice", issue_type="refund")

# Send to your LLM provider
openai = OpenAI(api_key="your_openai_key")
response = openai.chat.completions.create(model="gpt-4o", messages=compiled)
print(f"Using variant: {selected.template.name}")
print(f"Response: {response.choices[0].message.content}")
```

### 📚 Knowledge Base (RAG)

Manage documents for retrieval-augmented generation:

```python
from fi.kb import KnowledgeBase

# Initialize client
kb_client = KnowledgeBase(
    fi_api_key="your_api_key",
    fi_secret_key="your_secret_key"
)

# Create a knowledge base with documents
kb = kb_client.create_kb(
    name="product_docs",
    file_paths=["manual.pdf", "faq.txt", "guide.docx"]
)

print(f"✓ Knowledge base created: {kb.kb.name}")
print(f"  Files uploaded: {len(kb.kb.files)}")

# Update with more files
updated_kb = kb_client.update_kb(
    kb_name=kb.kb.name,
    file_paths=["updates.pdf"]
)

# Delete specific files
kb_client.delete_files_from_kb(file_names=["updates.pdf"])

# Clean up
kb_client.delete_kb(kb_ids=[kb.kb.id])
```

## 🎯 Core Use Cases

| Feature | Use Case | Benefit |
|---------|----------|---------|
| **Datasets** | Store and version training/test data | Reproducible experiments, automated evaluations |
| **Prompt Workbench** | Version control for prompts | A/B testing, deployment management, rollback |
| **Knowledge Base** | Evaluations and synthetic data | Intelligent retrieval, document versioning |
| **Evaluations** | Automated quality checks | No human-in-the-loop, 100% configurable |
| **Protect** | Real-time safety filters | Sub-100ms latency, production-ready |

---

## 🔥 Why Choose Future AGI?

| Feature | Future AGI | Traditional Tools | Other Platforms |
|---------|-----------|-------------------|-----------------|
| **Evaluation Speed** | ⚡ Sub-100ms | 🐌 Seconds-Minutes | 🐢 Minutes-Hours |
| **Human in Loop** | ❌ Fully Automated | ✅ Required | ✅ Often Required |
| **Multimodal Support** | ✅ Text, Image, Audio, Video | ⚠️ Limited | ⚠️ Text Only |
| **Setup Time** | ⏱️ 2 minutes | ⏳ Days-Weeks | ⏳ Hours-Days |
| **Configurability** | 🎯 100% Customizable | 🔒 Fixed Metrics | ⚙️ Some Flexibility |
| **Privacy Options** | 🔐 Cloud + Self-hosted | ☁️ Cloud Only | ☁️ Cloud Only |
| **A/B Testing** | ✅ Built-in | ❌ Manual | ⚠️ Limited |
| **Prompt Versioning** | ✅ Git-like Control | ❌ Not Available | ⚠️ Basic |
| **Real-time Guardrails** | ✅ Production-ready | ❌ Not Available | ⚠️ Experimental |

---

## 🔌 Supported Integrations

Future AGI works seamlessly with your existing AI stack:

**LLM Providers**  
`OpenAI` • `Anthropic` • `Google Gemini` • `Azure OpenAI` • `AWS Bedrock` • `Cohere` • `Mistral` • `Ollama` • `vLLM`

**Frameworks**  
`LangChain` • `LlamaIndex` • `CrewAI` • `AutoGen` • `Haystack` • `Semantic Kernel`

**Vector Databases**  
`Pinecone` • `Weaviate` • `Qdrant` • `Milvus` • `Chroma` • `FAISS`

**Observability**  
`OpenTelemetry` • `Custom Logging` • `Trace Context Propagation`

---

## 📚 Documentation

- **[Complete Documentation](https://docs.futureagi.com)**
- **[Dataset SDK Guide](https://docs.futureagi.com/future-agi/get-started/dataset/adding-dataset/using-sdk)**
- **[Prompt Workbench Guide](https://docs.futureagi.com/products/prompt/how-to/prompt-workbench-using-sdk)**
- **[Knowledge Base Guide](https://docs.futureagi.com/future-agi/get-started/knowledge-base/how-to/create-kb-using-sdk)**
- **[API Reference](https://docs.futureagi.com)**

---

## 🤝 Language Support

| Language | Package | Status |
|----------|---------|--------|
| **Python** | `futureagi` | ✅ Full Support |
| **TypeScript/JavaScript** | `@future-agi/sdk` | ✅ Full Support |
| **REST API** | cURL/HTTP | ✅ Available |

---

## 🆘 Support & Community

- **📧 Email:** support@futureagi.com
- **💼 LinkedIn:** [Future AGI Company](https://www.linkedin.com/company/futureagi)
- **🐦 X (Twitter):** [@FutureAGI_](https://x.com/FutureAGI_)
- **📰 Substack:** [Future AGI Blog](https://substack.com/@futureagi)

---

## 🤝 Contributing

We welcome contributions! Here's how to get involved:

- **🐛 Report bugs**: [Open an issue](https://github.com/future-agi/futureagi-sdk/issues)
- **💡 Request features**: [Start a discussion](https://github.com/future-agi/futureagi-sdk/discussions)
- **🔧 Submit PRs**: Fork, create a feature branch, and submit a pull request
- **📖 Improve docs**: Help us make our documentation better

See [CONTRIBUTING.md](https://github.com/future-agi/futureagi-sdk/blob/main/CONTRIBUTING.md) for detailed guidelines.

---

## 🌟 Testimonials

> "Future AGI cut our evaluation time from days to minutes. The automated critiques are spot-on!"  
> — **AI Engineering Team, Fortune 500 Company**

> "The prompt versioning alone saved us countless headaches. A/B testing is now trivial."  
> — **ML Lead, Healthcare Startup**

> "Sub-100ms guardrails in production. Game changer for our customer-facing AI."  
> — **CTO, E-commerce Platform**

---

## 📊 Roadmap

- [x] Datasets with automated evaluations
- [x] Prompt workbench with versioning
- [x] Knowledge base for RAG
- [x] Real-time guardrails (sub-100ms)
- [x] Multi-language SDK (Python + TypeScript)
- [x] Bulk Annotations for Human in the Loop
- [ ] On-premise deployment toolkit

---

## ❓ Troubleshooting & FAQ

<details>
<summary><strong>Import Error: `ModuleNotFoundError: No module named 'fi'`</strong></summary>

Make sure Future AGI is installed:
```bash
pip install futureagi --upgrade
```
</details>

<details>
<summary><strong>Authentication Error: Invalid API credentials</strong></summary>

1. Check your API keys at [Dashboard](https://app.futureagi.com/settings/api-keys)
2. Ensure environment variables are set correctly:
```bash
echo $FI_API_KEY
echo $FI_SECRET_KEY
```
3. Try setting them programmatically in your code
</details>

<details>
<summary><strong>How do I switch between environments (dev/staging/prod)?</strong></summary>

Use prompt labels to manage different deployment environments:
```python
client.assign_label("Development", version="v1")
client.assign_label("Staging", version="v2")
client.assign_label("Production", version="v3")
```
</details>

<details>
<summary><strong>Can I use Future AGI without sending data to the cloud?</strong></summary>

Yes! Future AGI supports self-hosted deployments. Contact us at support@futureagi.com for enterprise on-premise options.
</details>

<details>
<summary><strong>What LLM providers are supported?</strong></summary>

All major providers: OpenAI, Anthropic, Google, Azure, AWS Bedrock, Cohere, Mistral, and open-source models via vLLM/Ollama.
</details>

**Need more help?** Check our [complete FAQ](https://docs.futureagi.com/faq) or [join our community](https://www.linkedin.com/company/futureagi).

---

## 📄 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

---

<div align="center">

**Built with ❤️ by the [Future AGI](https://www.futureagi.com/) team and [contributors](https://github.com/future-agi/futureagi-sdk/graphs/contributors).**

If Future AGI helps you ship better AI, a ⭐ helps more teams find us.

[![Star History Chart](https://api.star-history.com/svg?repos=future-agi/futureagi-sdk&type=Date)](https://star-history.com/#future-agi/futureagi-sdk&Date)

[🌐 futureagi.com](https://futureagi.com) · [📖 docs.futureagi.com](https://docs.futureagi.com) · [☁️ app.futureagi.com](https://app.futureagi.com)

</div>
