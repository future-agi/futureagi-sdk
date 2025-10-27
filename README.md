<div align="center">

![Future AGI Logo](https://fi-content.s3.ap-south-1.amazonaws.com/Logo.png)

# Future AGI SDK

**The world's most accurate AI evaluation, observability and optimization platform**

[![PyPI version](https://badge.fury.io/py/futureagi.svg)](https://pypi.org/project/futureagi/)
[![Python Support](https://img.shields.io/pypi/pyversions/futureagi.svg)](https://pypi.org/project/futureagi/)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE.md)

[Documentation](https://docs.futureagi.com) | [Website](https://www.futureagi.com) | [Community](https://www.linkedin.com/company/futureagi)

</div>

---

## 🚀 What is Future AGI?

Future AGI empowers GenAI teams to build near-perfect AI applications through comprehensive evaluation, monitoring, and optimization. Our platform provides everything you need to develop, test, and deploy production-ready AI systems with confidence.

### ✨ Key Features

- **🎯 World-Class Evaluations** — Industry-leading evaluation frameworks powered by our Critique AI agent
- **⚡ Ultra-Fast Guardrails** — Real-time safety checks with sub-100ms latency
- **📊 Dataset Management** — Programmatically create, update, and manage AI training datasets
- **🎨 Prompt Workbench** — Version control, A/B testing, and deployment management for prompts
- **📚 Knowledge Base** — Intelligent document management and retrieval for RAG applications
- **📈 Advanced Analytics** — Deep insights into model performance and behavior
- **🤖 Simulate your AI system** — Simulate your AI system with different scenarios and see how it performs
- **Add Observability** — Add observability to your AI system to monitor its performance and behavior


---

## 📦 Installation

### Python
```bash
pip install futureagi
```

### TypeScript/JavaScript
```bash
npm install @futureagi/sdk
# or
pnpm add @futureagi/sdk
```

**Requirements:** Python >= 3.6 | Node.js >= 14

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
os.environ["FI_BASE_URL"] = "https://api.futureagi.com"
```

---

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
from fi.prompt import Prompt, PromptTemplate, ModelConfig, MessageBase

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
await client.open()  # Draft v1
await client.commitCurrentVersion("Initial version", set_as_default=True)

# Assign deployment labels
await client.labels().assign("Production", "v1")

# Compile with variables
compiled = client.compile({"customer_name": "Bob", "issue_type": "refund"})
print(compiled)
```

**A/B Testing Example:**

```python
import OpenAI from "openai"
from fi.prompt import Prompt

# Fetch different variants
variant_a = await Prompt.getTemplateByName("customer_support", label="variant-a")
variant_b = await Prompt.getTemplateByName("customer_support", label="variant-b")

# Randomly select and use
import random
selected = random.choice([variant_a, variant_b])
client = Prompt(selected)
compiled = client.compile({"customer_name": "Alice", "issue_type": "refund"})

# Send to your LLM provider
openai = OpenAI(api_key="your_key")
response = openai.chat.completions.create(model="gpt-4o", messages=compiled)
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
    file_paths=["manual.pdf", "faq.txt", "guide.md"]
)

print(f"✓ Knowledge base created: {kb.kb.name}")
print(f"  Files uploaded: {len(kb.kb.file_names)}")

# Update with more files
updated_kb = kb_client.update_kb(
    kb_id=kb.kb.id,
    file_paths=["updates.pdf"]
)

# Delete specific files
kb_client.delete_files_from_kb(file_ids=["file_id_here"])

# Clean up
kb_client.delete_kb(kb_ids=[kb.kb.id])
```

---

## 🎯 Core Use Cases

| Feature | Use Case | Benefit |
|---------|----------|---------|
| **Datasets** | Store and version training/test data | Reproducible experiments, automated evaluations |
| **Prompt Workbench** | Version control for prompts | A/B testing, deployment management, rollback |
| **Knowledge Base** | RAG document management | Intelligent retrieval, document versioning |
| **Evaluations** | Automated quality checks | No human-in-the-loop, 100% configurable |
| **Guardrails** | Real-time safety filters | Sub-100ms latency, production-ready |

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
| **TypeScript/JavaScript** | `@futureagi/sdk` | ✅ Full Support |
| **REST API** | cURL/HTTP | ✅ Available |

---

## 🆘 Support & Community

- **📧 Email:** support@futureagi.com
- **💼 LinkedIn:** [Future AGI Company](https://www.linkedin.com/company/futureagi)
- **🐦 X (Twitter):** [@FutureAGI_](https://x.com/FutureAGI_)
- **📰 Substack:** [Future AGI Blog](https://substack.com/@futureagi)

---

## 💡 Why Future AGI?

### 🤖 Human-Free Evaluations
Our Critique AI agent delivers powerful evaluations without human-in-the-loop. It's 100% configurable for any use case — if you can imagine it, you can evaluate it.

### 🔒 Privacy First
Don't want to share data? Install our SDK in your private cloud and get all the benefits while keeping your data secure.

### 🎨 Multimodal Support
Work with text, images, audio, video, or any data type. Our platform is truly data-agnostic.

### ⚡ 2-Minute Integration
Just a few lines of code and your data starts flowing. No complex setup, no lengthy onboarding.

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details.

---

<div align="center">

**[Get Started Now](https://app.futureagi.com) | [View Documentation](https://docs.futureagi.com)**

Made with ❤️ by the Future AGI Team

</div>
