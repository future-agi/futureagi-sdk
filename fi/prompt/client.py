from typing import Dict, Optional

from fi.api.auth import APIKeyAuth, ResponseHandler
from fi.api.types import HttpMethod, RequestConfig
from fi.prompt.types import ModelConfig, PromptTemplate
from fi.utils.errors import InvalidAuthError, TemplateAlreadyExists
from fi.utils.logging import logger
from fi.utils.routes import Routes


class PromptResponseHandler(ResponseHandler[Dict, PromptTemplate]):
    """Handles responses for prompt requests"""

    @classmethod
    def _parse_success(cls, response) -> Dict:
        """Handles responses for prompt requests"""
        data = response.json()

        # Handle search endpoint
        if "search=" in response.url:
            results = data.get("results", [])
            name = response.url.split("search=")[1]
            for item in results:
                if item["name"] == name:
                    return item["id"]
            raise ValueError(f"No template found with the given name: {name}")

        # Handle GET template by ID endpoint
        if response.request.method == HttpMethod.GET.value:
            prompt_config = data.get("promptConfig", {})
            # Transform response data to match PromptTemplate structure
            prompt_config = prompt_config[0]
            model_config = ModelConfig(
                model_name=prompt_config.get("configuration", {}).get(
                    "modelName", "gpt-4o-mini"
                ),
                temperature=prompt_config.get("configuration", {}).get(
                    "temperature", 0.7
                ),
                frequency_penalty=prompt_config.get("configuration", {}).get(
                    "frequencyPenalty", 0
                ),
                presence_penalty=prompt_config.get("configuration", {}).get(
                    "presencePenalty", 0
                ),
                max_tokens=prompt_config.get("configuration", {}).get(
                    "maxTokens", 1000
                ),
                top_p=prompt_config.get("configuration", {}).get("topP", 1.0),
                response_format=prompt_config.get("configuration", {}).get(
                    "responseFormat", None
                ),
                tool_choice=prompt_config.get("configuration", {}).get(
                    "toolChoice", None
                ),
                tools=prompt_config.get("configuration", {}).get("tools", None),
            )
            template_data = {
                "id": data.get("id"),
                "name": data.get("name"),
                "description": data.get("description", ""),
                "messages": prompt_config.get("messages", []),
                "model_configuration": model_config,
                "variable_names": data.get("variableNames", {}),
                "version": data.get("version"),
                "is_default": data.get("isDefault", True),
                "evaluation_configs": data.get("evaluationConfigs", []),
                "status": data.get("status"),
                "error_message": data.get("errorMessage"),
            }
            return PromptTemplate(**template_data)

        if response.request.method == HttpMethod.POST.value and response.url.endswith(
            Routes.create_template.value
        ):
            return data["result"]

        # Return raw data for other endpoints
        return data

    @classmethod
    def _handle_error(cls, response) -> None:
        if response.status_code == 403:
            raise InvalidAuthError()
        else:
            response.raise_for_status()


class PromptClient(APIKeyAuth):
    _template_id_cache = {}

    def __init__(
        self,
        template: Optional[PromptTemplate] = None,
        fi_api_key: Optional[str] = None,
        fi_secret_key: Optional[str] = None,
        fi_base_url: Optional[str] = None,
        **kwargs,
    ):
        super().__init__(
            fi_api_key=fi_api_key,
            fi_secret_key=fi_secret_key,
            fi_base_url=fi_base_url,
            **kwargs,
        )

        if template and not template.id:
            try:
                self.template = self._fetch_template_by_name(template.name)
            except Exception as e:
                logger.warning(
                    "Template not found in the backend. Create a new template before running."
                )
                self.template = template
        else:
            self.template = template
            if self.template:
                logger.warning(
                    f"Current template: {self.template.name} does not exist in the backend. Please create it first before running."
                )
            else:
                logger.warning(
                    "No template provided. Please provide a template before running."
                )

        if not self.template:
            raise ValueError("No template configured")

    def generate(self, requirements: str) -> "PromptClient":
        """Generate a prompt and return self for chaining"""
        if not self.template:
            raise ValueError("No template configured")
        response = self.request(
            config=RequestConfig(
                method=HttpMethod.POST,
                url=self._base_url + "/" + Routes.generate_prompt.value,
                json={"statement": requirements},
            ),
            response_handler=PromptResponseHandler,
        )
        self.template.messages[-1].content = response["result"]["prompt"]
        return self

    def improve(self, requirements: str) -> "PromptClient":
        """Improve prompt and return self for chaining"""
        if not self.template:
            raise ValueError("No template configured")

        existing_prompt = (
            self.template.messages[-1].content if self.template.messages else ""
        )

        improved_response = self.request(
            config=RequestConfig(
                method=HttpMethod.POST,
                url=self._base_url + "/" + Routes.improve_prompt.value,
                json={
                    "existing_prompt": existing_prompt,
                    "improvement_requirements": requirements,
                },
            ),
            response_handler=PromptResponseHandler,
        )
        self.template.messages[-1].content = improved_response["result"]["prompt"]
        return self

    def create(self) -> "PromptClient":
        """Create a draft prompt template and return self for chaining"""
        if not self.template:
            raise ValueError("template must be set")

        if self.template.id:
            raise TemplateAlreadyExists(self.template.name)

        method = HttpMethod.POST
        url = self._base_url + "/" + Routes.create_template.value

        messages = []
        for message in self.template.messages:
            message_dict = message.model_dump()
            if isinstance(message_dict.get("content"), str):
                message_dict["content"] = [
                    {"type": "text", "text": message_dict["content"]}
                ]
            messages.append(message_dict)

        json = {
            "name": self.template.name,
            "prompt_config": [
                {
                    "messages": messages,
                    "configuration": {
                        "model": self.template.model_configuration.model_name,
                        "temperature": self.template.model_configuration.temperature,
                        "max_tokens": self.template.model_configuration.max_tokens,
                        "top_p": self.template.model_configuration.top_p,
                        "frequency_penalty": self.template.model_configuration.frequency_penalty,
                        "presence_penalty": self.template.model_configuration.presence_penalty,
                    },
                }
            ],
            "variable_names": self.template.variable_names,
            "evaluation_configs": self.template.evaluation_configs or [],
        }

        response = self.request(
            config=RequestConfig(
                method=method,
                url=url,
                json=json,
            ),
            response_handler=PromptResponseHandler,
        )

        self.template.id = response["id"]
        self.template.name = response["name"]

        return self

    def run(
        self,
        variables: Optional[Dict] = None,
    ) -> Dict:
        """Run a prompt template and return the response"""
        if not self.template:
            raise ValueError("No template configured")

        # validate variable names
        if self.template.variable_names:
            for var_name in self.template.variable_names:
                if var_name not in variables:
                    raise ValueError(
                        f"Variable name {var_name} not found in variable_names"  # noqa: E713
                    )

        messages = []
        for message in self.template.messages:
            message_dict = message.model_dump()
            if isinstance(message_dict.get("content"), str):
                message_dict["content"] = [
                    {"type": "text", "text": message_dict["content"]}
                ]
            messages.append(message_dict)

        model_config = {
            "model": self.template.model_configuration.model_name,
            "temperature": self.template.model_configuration.temperature,
            "max_tokens": self.template.model_configuration.max_tokens,
            "top_p": self.template.model_configuration.top_p,
            "frequency_penalty": self.template.model_configuration.frequency_penalty,
            "presence_penalty": self.template.model_configuration.presence_penalty,
        }

        # Transform variable_names to match expected format
        formatted_variables = {
            k: [v] if not isinstance(v, list) else v
            for k, v in (variables or {}).items()
        }

        response = self.request(
            config=RequestConfig(
                method=HttpMethod.POST,
                url=self._base_url
                + "/"
                + Routes.run_template.value.format(template_id=self.template.id),
                json={
                    "name": self.template.name,
                    "prompt_config": [
                        {
                            "messages": messages,
                            "configuration": {
                                "model": self.template.model_configuration.model_name,
                                "temperature": self.template.model_configuration.temperature,
                                "max_tokens": self.template.model_configuration.max_tokens,
                                "top_p": self.template.model_configuration.top_p,
                                "frequency_penalty": self.template.model_configuration.frequency_penalty,
                                "presence_penalty": self.template.model_configuration.presence_penalty,
                            },
                        }
                    ],
                    "variable_names": formatted_variables,
                    "evaluation_configs": self.template.evaluation_configs or [],
                    "is_run": "prompt",
                },
            ),
            response_handler=PromptResponseHandler,
        )

        return response

    # Keep existing methods but update them to work with PromptTemplate
    def _fetch_template_by_name(self, name: str) -> PromptTemplate:
        """Fetch template configuration by name"""
        template_id = self._fetch_id_by_name(name)
        template = self._fetch_template_by_id(template_id)
        return template

    def _fetch_template_by_id(self, template_id: str) -> PromptTemplate:
        """Fetch template configuration by ID"""
        response = self.request(
            config=RequestConfig(
                method=HttpMethod.GET,
                url=self._base_url
                + "/"
                + Routes.get_template_by_id.value.format(template_id=template_id),
            ),
            response_handler=PromptResponseHandler,
        )
        return response

    def _fetch_id_by_name(self, name: str) -> str:
        """Fetch template ID by name"""
        response = self.request(
            config=RequestConfig(
                method=HttpMethod.GET,
                url=self._base_url + "/" + Routes.get_template_id_by_name.value,
                params={"search": name},
            ),
            response_handler=PromptResponseHandler,
        )
        return response
