# Future AGI

![Company Logo](https://github.com/future-agi/client/blob/main/Logo.png)

Welcome to Future AGI - Empowering GenAI Teams with Advanced Performance Management

# Overview

Future AGI provides a cutting-edge platform designed to help GenAI teams maintain peak model accuracy in production environments.
Our solution is purpose-built, scalable, and delivers results 10x faster than traditional methods.

**Key Features**

* **_Simplified GenAI Performance Management_**: Streamline your workflow and focus on developing cutting-edge AI models.
* **_Instant Evaluation_**: Score outputs without human-in-the-loop or ground truth, increasing QA team efficiency by up to 10x.
* **_Advanced Error Analytics_**: Gain ready-to-use insights with comprehensive error tagging and segmentation.
* **_Configurable Metrics_**: Define custom metrics tailored to your specific use case for precise model evaluation.

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

To initialise the Future AGI Client, you need to provide your fi_api_key and fi_secret_key, which are associated with your Future AGI account.

Get your service API key When you create an account, we generate a service API key. You will need this API Key and your Space Key for logging authentication.
Instrument your code Python Client If you are using the Future AGI python client, add a few lines to your code to log your data. Logs are sent to us asynchronously.

```
from fi.client import Client

fi_api_key = os.environ["FI_API_KEY"]
fi_secret_key = os.environ["FI_SECRET_KEY"]
base_url = os.environ["FI_API_URL"]

client = Client(fi_api_key=fi_api_key, fi_secret_key=fi_secret_key,
        max_workers=8,
        max_queue_bound=5000,
        timeout=200,
        additional_headers=None,
)
```

**Initialises the Future AGI Client**
* _fi_api_key_: provided API key associated with your account.
* _fi_secret_key_: provided identifier to connect records to spaces.
* _uri_: URI to send your records to Future AGI client.
* _max_workers_: maximum number of concurrent requests to Future AGI. Defaults to 8.
* _max_queue_bound_: maximum number of concurrent future objects generated for publishing to Future AGI. Defaults to 5000.
* _timeout_: how long to wait for the server to send data before giving up. Defaults to 200.
* _additional_headers_: Dictionary of additional headers to append to request

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
* 	_model_id_: The ID of the model. Must be a string.
* 	_model_type_: The type of the model. Must be an instance of ModelTypes.
* 	_environment_: The environment in which the model is running. Must be an instance of Environments.
* 	_model_version_: The version of the model. Must be a string.
* 	_prediction_timestamp_: (Optional) The timestamp of the prediction. Must be an integer.
* 	_conversation_:  The conversation data. Must be a dictionary containing either chat_history or chat_graph.
* 	_tags_: (Optional) Additional tags for the event. Must be a dictionary.

**_[For full details, see our docs.](https://docs.futureagi.com/)_**


**Conversation Format**

**Chat History**
The chat_history must be a list of dictionaries with the following keys:
* 	_role_: The role of the participant (e.g., “user”, “assistant”). Must be a string.
* 	_content_: The content of the message. Must be a string.
* 	_context_: (Optional) The context of the message. Must be a list of pairs of strings in the format [["", ""]...].

**Chat History with conversation ID**
The chat_history must be a list of dictionaries with the following keys:
* 	_conversation_id_: The ID of the conversation. Must be a string.
* 	_role_: The role of the participant (e.g., “user”, “assistant”). Must be a string.
* 	_content_: The content of the message. Must be a string.
* 	_context_: (Optional) The context of the message. Must be a list of pairs of strings in the format [["", ""]...].

**Chat Graph**
The chat_graph must be a dictionary with the following keys:
* 	_conversation_id_: The ID of the conversation. Must be a string.
* 	_nodes_: A list of nodes, each containing:
* 	_message_: A dictionary with the message details.
* 	_node_id_: The ID of the node. Must be a string.
* 	_parent_id_: The ID of the parent node. Must be a string.
* 	_timestamp_: The timestamp of the node. Must be an integer.


1. **Logging data individually:** For example, "chat_history" may include a list of dictionaries where each dictionary represents a message with attributes like "role" (str) and "content" (str) .

```
{
        "chat_history": [
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
```
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
**Error Handling**
The client raises specific exceptions for different types of errors:
* 	_AuthError_: Raised if the API key or secret key is missing.
* 	_InvalidAdditionalHeaders_: Raised if there are conflicting additional headers.
* 	_InvalidValueType_: Raised if a parameter has an invalid type.
* 	_InvalidSupportedType_: Raised if a model type is not supported.
* 	_MissingRequiredKey_: Raised if a required key is missing.
* 	_InvalidVectorLength_: Raised if the vector length is invalid.

# FAQ’s:

1. Q: How do you give a performance score without human in the loop?

Our secret Sauce is a Critique AI agent that can deliver powerful evaluation framework without need for human in the loop. What’s more is that it is 100% configurable as per new evolving use cases. Now anything that you can imagine your AI system should deliver - you can configure our platform to manage it.

2. Q: What all inputs Future AGI platform needs?

We would need only the input-output database, training dataset if available, and User-analytics. We do not need to understand the model and how it is taking decisions.

3. Q: I don't want to share data with Future AGI, can I still use it?

Yes, you can now install our SDK in your private cloud and take advantage of our strong platform to align your AI system to your users.


4. Q: My use case is unique, would you provide service to customise your platform as per my use case?

Our platform is 100% customisable and easy to configure for all types of models and modalities by the AI teams. However, our customer-success engineer would be happy to assist you for figuring out solutions to your unique use cases.

5. Q: My app uses multiple models with multiple modalities, can you work with images and videos also?

Yes we can.

6. Q: How much time does it take to integrate the Future AGI platform? How much bandwidth would be required?

It takes just 2 minutes to integrate a few lines of code and your data starts showing on our platform. Try it today.


# Resources

**Website**: https://www.futureagi.com/

**Documentation**: https://docs.futureagi.com/

**PyPI** : https://pypi.org/project/futureagi/
