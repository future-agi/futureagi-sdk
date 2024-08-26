# My Project

![Company Logo](./Logo.png)

Welcome to Future Agi project!

# Overview

We help GenAI teams maintain high-accuracy for their Models in production
Purpose Built, Scalable & 10X faster than traditional methods

We know that GenAI teams struggle with ensuring optimal performance in production. We are simplifying this by streamlining the process and empowering AI teams to focus on what they do best—developing exceptional AI models

Get evaluation without 
Human-in-the-Loop or Ground Truth

Performance Score for each output: 

Why send every GenAI output to a big QA team (Human-in-th-loop). FutureAGI lets you score your outputs immediately without subject-matter-experts presence. Your QA team can now focus on much more important tasks instead of evaluating your AI app’s output. Get their QA copilot and free upto 10X  bandwidth 


Analytics of Errors
Why analyse the errors manually in an excel, when you can get ready-to-use insights in form of error-enalytics. For all errors, our system tags the type, and can segment and analyse which specific topics or categories are showing errors and where re-training might be required.

Configurable metrics
Why restrict to standard metrics like relevance for every use case? Only you know what metrics matter for your app. FutureAGI allows you to create your own custom metrics to evaluate your GenAI model’s accuracy. Quantified score for what is important to you.


## Quickstart
**Installation**

To install the client, you can clone the repository or install the library:

Install the  library in an environment using Python >= 3.6.
```
$ pip3 install futureagi
```
Or clone the repo:

```
$ git clone https://github.com/future-agi/client
```

**Initialisation**
To initialise the Fi AI Client, you need to provide your api_key and secret_key, which are associated with your Fi AI account.

Get your service API key When you create an account, we generate a service API key. You will need this API Key and your Space Key for logging authentication.
Instrument your code Python Client If you are using the Future Agi python client, add a few lines to your code to log your data. Logs are sent to us asynchronously.
from fi_client import Client

```
api_key = os.environ["FI_API_KEY"]
secret_key = os.environ["FI_SECRET_KEY"]
base_url = os.environ["FI_API_URL"]

client = Client(api_key=api_key, secret_key=secret_key,
        uri=base_url,
        max_workers=8,
        max_queue_bound=5000,
        timeout=200,
        additional_headers=None,
)
```

**Initializes the Fi Client**
api_key: provided API key associated with your account.
secret_key:provided identifier to connect records to spaces.
uri: RI to send your records to Fi AI.
max_workers: maximum number of concurrent requests to Fi. Defaults to 8.
max_queue_bound: maximum number of concurrent future objects generated for publishing to Fi. Defaults to 5000.
timeout: how long to wait for the server to send data before giving up. Defaults to 200.
additional_headers: Dictionary of additional headers to append to request

You can also set these keys as environment variables:
```
export FI_API_KEY=your_api_key
export FI_SECRET_KEY=your_secret_key
```
And then initialise the client without passing the keys directly:

```
from fi.utils.types import ModelTypes, Environments

client.log(
    model_id="your_model_id",
    model_type=ModelTypes.GENERATIVE_LLM,
    environment=Environments.PRODUCTION,
    model_version="1.0.0",
    prediction_timestamp=1625216400,
    conversation={
        "chat_history": [
            {"role": "user", "content": "How do I implement a neural network in Python?"}
        ]
    },
    tags={"project": "AI project"}
)
```

**Parameters**
•	model_id: The ID of the model. Must be a string.
•	model_type: The type of the model. Must be an instance of ModelTypes.
•	environment: The environment in which the model is running. Must be an instance of Environments.
•	model_version: The version of the model. Must be a string.
•	prediction_timestamp: (Optional) The timestamp of the prediction. Must be an integer.
•	conversation:  The conversation data. Must be a dictionary containing either chat_history or chat_graph.
•	tags: (Optional) Additional tags for the event. Must be a dictionary.

**Conversation Format**

**Chat History**
The chat_history must be a list of dictionaries with the following keys:
•	role: The role of the participant (e.g., “user”, “assistant”). Must be a string.
•	content: The content of the message. Must be a string.
•	context: (Optional) The context of the message. Must be a list of pairs of strings in the format [["", ""]...].

**Chat History with conversation ID**
The chat_history must be a list of dictionaries with the following keys:
•	conversation_id: The ID of the conversation. Must be a string.
•	role: The role of the participant (e.g., “user”, “assistant”). Must be a string.
•	content: The content of the message. Must be a string.
•	context: (Optional) The context of the message. Must be a list of pairs of strings in the format [["", ""]...].

**Chat Graph**
The chat_graph must be a dictionary with the following keys:
•	conversation_id: The ID of the conversation. Must be a string.
•	nodes: A list of nodes, each containing:
•	message: A dictionary with the message details.
•	node_id: The ID of the node. Must be a string.
•	parent_id: The ID of the parent node. Must be a string.
•	timestamp: The timestamp of the node. Must be an integer.

**Error Handling**
The client raises specific exceptions for different types of errors:
•	AuthError: Raised if the API key or secret key is missing.
•	InvalidAdditionalHeaders: Raised if there are conflicting additional headers.
•	InvalidValueType: Raised if a parameter has an invalid type.
•	InvalidSupportedType: Raised if a model type is not supported.
•	MissingRequiredKey: Raised if a required key is missing.
•	InvalidVectorLength: Raised if the vector length is invalid.



1. **Logging data individually:** For example, "chat_history" may include a list of dictionaries where each dictionary represents a message with attributes like "role" (str) and "content" (str) .

```
{
        "chat_history": [
            {
                "role": "system",
                "content": "You are a helpful assistant."
            },
            {
                "role": "user",
                "content": "Who won the world series in 2020?"
            },
            {
                "role": "assistant",
                "content": "The Los Angeles Dodgers won the World Series in 2020."
            }
        ]
    }
```

1. **Logging data all at once:** This involves logging structured conversations in a unified format:
    
    ```json
    [{
        "conversation_id": "",
        "title": "",
        "root_node": "",
        "metadata": {},
        "nodes": [{
            "parent_node": "",
            "child_node": "",
            "message": {
                "id": "",
                "author": {
                            "role": "assistant",
                            "metadata": {}
                        },
                "content": {
                            "content_type": "text",
                            "parts": [
                                "The user is interested to do this task..."
                            ]
                        }
                "context": ""
            }
        }]
    }]
    
    ```


# FAQ’s:

1. How do you give a performance score without human in the loop?
Our secret Sauce is a Critique AI agent that cana deliver powerful evaluation framework without need for human in the loop. What’s more is that it is 100% configurable as per new evolving use cases. Now anything that you canimagine your AI system should deliver - you can configure our platform to manage it.

2. What all inputs FutureAGI platform needs?
We would need only the input-output database, training dataset if available, and User-analytics. We do not need to understand the model and how it is taking decisions.

3. I don't want to share data with Future AGI, can I still use it?
Yes, you can now intall our SDK in your private cloud and take advantage of our strong platform to align your Ai system to your users.

4. My use case is unique, would you provide service to customise your platform as per my use case?
Our platform if 100% customisable and easy to configure for all types of models and modalities by the AI teams. However, our customer-success engineer would be happy to assist you for figuring out solutions to your unique use cases.

5. My app uses multiple models with multiple modalities, can you work with images and videos also?
Yes we can.

6. How much time does it take to integrate the  Future AGI platform? How much bandwidth would be required?
It takes just 2 minutes to integrate a few lines of code and your data starts showing on our platform. Try it today.


# Website
Visit Us At: https://www.futureagi.com/
Gitbook: https://docs.futureagi.com/
PyPi : https://pypi.org/project/futureagi/





