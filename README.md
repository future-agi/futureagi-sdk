# Future AGI

![Company Logo](https://fi-content.s3.ap-south-1.amazonaws.com/Logo.png)

Welcome to Future AGI - Empowering GenAI Teams with Advanced Performance Management

# Overview

Future AGI is the world's most accurate AI evaluation, observability and optimization platform. We help teams build near perfect AI applications across software and hardware through comprehensive model monitoring, testing and optimization.

**Key Features**

* **_World's Best Evaluations_**: Power your AGI development with industry-leading evaluation frameworks and metrics.
* **_Ultra-Fast Guardrails_**: Implement real-time safety checks with sub-100ms latency for production-ready AI systems.
* **_Comprehensive SDKs_**: Rapidly prototype and observe agent behavior with our developer-friendly toolkits.
* **_Advanced Analytics_**: Monitor and optimize agent performance with detailed insights and actionable metrics.

# Quickstart
**Installation**

To install the client, you can clone the repository or install the library:

Install the library in an environment using Python >= 3.6.
```
$ pip3 install futureagi
```
Or clone the repo:

```
$ git clone https://github.com/future-agi/client
```

**Initialisation**

To Start working with Future AGI, you need to create an account and get your API key and secret key.
You will be needing these keys to work with the Future AGI platform.

Start working by uploading your data to the platform

```
# pip install futureagi

import os
from fi.datasets import Dataset
from fi.datasets.types import (
    Cell,
    Column,
    DatasetConfig,
    DataTypeChoices,
    ModelTypes,
    Row,
    SourceChoices,
)

# Set environment variables
os.environ["FI_API_KEY"] = "<Your API Key>"
os.environ["FI_SECRET_KEY"] = "<Your Secret Key>"

# Get existing dataset
config = DatasetConfig(name="example_dataset", model_type= ModelTypes.GENERATIVE_LLM)
dataset = Dataset(dataset_config=config)
dataset = dataset.create_dataset(dataset_config=config)

# Define columns
columns = [
    Column(
        name="user_query",
        data_type=DataTypeChoices.TEXT,
        source=SourceChoices.OTHERS
    ),
    Column(
        name="response_quality",
        data_type=DataTypeChoices.INTEGER,
        source=SourceChoices.OTHERS
    ),
    Column(
        name="is_helpful",
        data_type=DataTypeChoices.BOOLEAN,
        source=SourceChoices.OTHERS
    )
]

# Define rows
rows = [
    Row(
        order=1,
        cells=[
            Cell(column_name="user_query", value="What is machine learning?"),
            Cell(column_name="response_quality", value=8),
            Cell(column_name="is_helpful", value=True)
        ]
    ),
    Row(
        order=2,
        cells=[
            Cell(column_name="user_query", value="Explain quantum computing"),
            Cell(column_name="response_quality", value=9),
            Cell(column_name="is_helpful", value=True)
        ]
    )
]

try:
    # Add columns and rows to dataset
    dataset = dataset.add_columns(columns=columns)
    dataset = dataset.add_rows(rows=rows)
    print("✓ Data added successfully")
    
except Exception as e:
    print(f"Failed to add data: {e}")

```

**Initialises the Future AGI Dataset Client**
* _fi_api_key_: provided API key associated with your account.
* _fi_secret_key_: provided identifier to connect records to spaces.
* _DatasetConfig_: The configuration for the dataset.
* _create_dataset_: The function to create the dataset.


You can also set these keys as environment variables:
```
export FI_API_KEY=your_api_key
export FI_SECRET_KEY=your_secret_key
```
And then initialise the Dataset without passing the keys directly:

**_[For full details, see our docs.](https://docs.futureagi.com/)_**


# FAQ’s:

1. Q: How do you give a Evaluation score without human in the loop?

Our secret Sauce is a Critique AI agent that can deliver powerful evaluation framework without need for human in the loop. What’s more is that it is 100% configurable as per new evolving use cases. Now anything that you can imagine your AI system should deliver - you can configure our platform to manage it.

2. Q: What all inputs Future AGI platform needs?

We are a data-agnostic platform and can work with any data kind of that you have. Whether it is text, image, audio, video, or any other data type, we can help you annotate, evaluate, optimize and monitor your AI system.

3. Q: I don't want to share data with Future AGI, can I still use it?

Yes, you can now install our SDK in your private cloud and take advantage of our strong platform to align your AI system to your users.


4. Q: My app uses multiple models with multiple modalities, can you work with images and audio also?

Yes we can.

5. Q: How much time does it take to integrate the Future AGI platform? How much bandwidth would be required?

It takes just 2 minutes to integrate a few lines of code and your data starts showing on our platform. Try it today.


# Resources

**Website**: https://www.futureagi.com/

**Documentation**: https://docs.futureagi.com/

**PyPI** : https://pypi.org/project/futureagi/

# Connect with us

**Email**: support@futureagi.com


**LinkedIn**: https://www.linkedin.com/company/futureagi

**X**: https://x.com/FutureAGI_

**Reddit**: https://www.reddit.com/user/Future_AGI/submitted/

**Substack**: https://substack.com/@futureagi
