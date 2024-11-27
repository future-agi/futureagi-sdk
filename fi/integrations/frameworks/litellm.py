import os

from fi.integrations.providers import ProviderModels


class LiteLLMModelManager:
    def __init__(self, model_name):
        self.model_name = model_name
        self.models = ProviderModels().models

    def set_api_key(self):
        api_key_name = None
        for model in self.models:
            if self.model_name == model.get("model_name"):
                api_key_name = model.get("api_key_name")
                break

        if api_key_name is None:
            raise ValueError(f"LiteLLMModel {self.model_name} not found")

        fi_api_key = os.environ.get(api_key_name)
        if fi_api_key is None:
            raise ValueError(
                f"API key not found for {model.provider.value}. Please set the {api_key_name} environment variable."
            )

        os.environ[api_key_name] = fi_api_key

    def get_provider(self, model_name):
        provider = None
        for model in self.models:
            if model_name == model.get("model_name"):
                provider = model.get("providers")

        if provider is None:
            raise ValueError(f"LiteLLMModel provider for {model_name} not found")

        return provider

    def get_model_by_provider(self, provider):
        model_name = []
        for model in self.models:
            if provider == model.get("providers"):
                model_name.append(model.get("model_name"))

        return model_name
