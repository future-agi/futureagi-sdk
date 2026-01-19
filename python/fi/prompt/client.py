import time
import threading
from typing import Dict, Optional

from fi.api.auth import APIKeyAuth, ResponseHandler
from fi.api.types import HttpMethod, RequestConfig
from fi.prompt.types import ModelConfig, PromptTemplate
from fi.utils.errors import InvalidAuthError, SDKException, TemplateAlreadyExists
from fi.utils.errors import TemplateNotFound
from fi.utils.logging import logger
from fi.utils.routes import Routes
from fi.prompt.cache import prompt_cache
from fi.prompt.label_management import LabelManagementMixin


class SimpleJsonResponseHandler(ResponseHandler[Dict, Dict]):
    """Simply parses JSON and handles common errors."""

    @classmethod
    def _parse_success(cls, response) -> Dict:
        return response.json()

    @classmethod
    def _handle_error(cls, response) -> None:
        if response.status_code == 403:
            raise InvalidAuthError()
        if response.status_code == 404:
            raise TemplateNotFound("Could not find template during polling.")
        else:
            try:
                detail = response.json()
                raise SDKException(
                    f"Polling failed: {detail.get('message', response.text)}"
                )
            except Exception:
                response.raise_for_status()


class PromptResponseHandler(ResponseHandler[Dict, PromptTemplate]):
    """Handles responses for prompt requests"""

    @classmethod
    def _parse_success(cls, response) -> Dict:
        """Handles responses for prompt requests"""
        data = response.json()

        if isinstance(data, dict) and data.get("status") is False:

            cls._handle_error(response)

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
            # Support both camelCase and snake_case keys from backend
            # Unwrap common {"result": {...}} envelope if present
            if isinstance(data, dict) and "result" in data and isinstance(data["result"], dict):
                data = data["result"]
            pc = data.get("promptConfig") or data.get("prompt_config") or [{}]
            if isinstance(pc, list):
                prompt_config_raw = pc[0] if pc else {}
            else:
                prompt_config_raw = pc
            cfg_src = (prompt_config_raw or {}).get("configuration", {})
            cfg = {
                "modelName": cfg_src.get("modelName") or cfg_src.get("model"),
                "temperature": cfg_src.get("temperature"),
                "frequencyPenalty": cfg_src.get("frequencyPenalty") or cfg_src.get("frequency_penalty"),
                "presencePenalty": cfg_src.get("presencePenalty") or cfg_src.get("presence_penalty"),
                "maxTokens": cfg_src.get("maxTokens") or cfg_src.get("max_tokens"),
                "topP": cfg_src.get("topP") or cfg_src.get("top_p"),
                "responseFormat": cfg_src.get("responseFormat") or cfg_src.get("response_format"),
                "toolChoice": cfg_src.get("toolChoice") or cfg_src.get("tool_choice"),
                "tools": cfg_src.get("tools"),
            }
            model_config = ModelConfig(
                model_name=cfg["modelName"] or "unavailable",
                temperature=cfg["temperature"] if cfg["temperature"] is not None else 0,
                frequency_penalty=cfg["frequencyPenalty"] if cfg["frequencyPenalty"] is not None else 0,
                presence_penalty=cfg["presencePenalty"] if cfg["presencePenalty"] is not None else 0,
                max_tokens=cfg["maxTokens"],
                top_p=cfg["topP"] if cfg["topP"] is not None else 0,
                response_format=cfg["responseFormat"],
                tool_choice=cfg["toolChoice"],
                tools=cfg["tools"],
            )
            template_data = {
                "id": data.get("id"),
                "name": data.get("name"),
                "description": data.get("description", ""),
                "messages": (prompt_config_raw or {}).get("messages", []),
                "model_configuration": model_config,
                "variable_names": data.get("variableNames") or data.get("variable_names", {}),
                "version": data.get("version"),
                "is_default": data.get("isDefault", True) if data.get("isDefault") is not None else data.get("is_default", True),
                "evaluation_configs": data.get("evaluationConfigs") or data.get("evaluation_configs", []),
                "status": data.get("status"),
                "error_message": data.get("errorMessage"),
                "metadata": data.get("metadata"),
                "placeholders": (prompt_config_raw or {}).get("placeholders", {}),
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
        if response.status_code == 404:
            # Attempt to extract 'name' query param for better message
            import urllib.parse as _up

            parsed = _up.urlparse(response.request.url)
            qs = _up.parse_qs(parsed.query)
            name_param = qs.get("name", [None])[0]
            raise TemplateNotFound(name_param or "unknown")
        if response.status_code == 400:
            try:
                detail = response.json()
                error_code = detail.get("errorCode") if isinstance(detail, dict) else None
            except Exception:
                error_code = None

            if error_code == "TEMPLATE_ALREADY_EXIST":
                raise TemplateAlreadyExists(detail.get("name", "<unknown>"))

            # Handle specific "No version found for label" error from get-by-name
            if isinstance(detail, dict) and "result" in detail and "No version found for label" in detail["result"]:
                 raise TemplateNotFound(f"Label '{detail.get('label')}'")

            raise SDKException(
                detail.get("message", "Bad request – please verify request body.")
            )
        else:
            response.raise_for_status()


class Prompt(APIKeyAuth, LabelManagementMixin):
    # Use global prompt_cache; keep TTL alias for backward compat
    CACHE_TTL_SEC: int = prompt_cache._ttl_sec

    @staticmethod
    def _dict_to_prompt_template(item: Dict) -> PromptTemplate:
        """Safely convert backend JSON to PromptTemplate."""

        prompt_config_raw = item.get("promptConfig") or item.get("prompt_config")

        if prompt_config_raw:
            pc = prompt_config_raw[0] if isinstance(prompt_config_raw, list) else prompt_config_raw
            cfg_raw = pc.get("configuration", {})
            # Normalize key casing / naming
            cfg = {
                "modelName": cfg_raw.get("modelName") or cfg_raw.get("model"),
                "temperature": cfg_raw.get("temperature"),
                "frequencyPenalty": cfg_raw.get("frequencyPenalty") or cfg_raw.get("frequency_penalty"),
                "presencePenalty": cfg_raw.get("presencePenalty") or cfg_raw.get("presence_penalty"),
                "maxTokens": cfg_raw.get("maxTokens") or cfg_raw.get("max_tokens"),
                "topP": cfg_raw.get("topP") or cfg_raw.get("top_p"),
                "responseFormat": cfg_raw.get("responseFormat") or cfg_raw.get("response_format"),
                "toolChoice": cfg_raw.get("toolChoice") or cfg_raw.get("tool_choice"),
                "tools": cfg_raw.get("tools"),
            }
            model_config = ModelConfig(
                model_name=cfg["modelName"] or "unavailable",
                temperature=cfg["temperature"] if cfg["temperature"] is not None else 0,
                frequency_penalty=cfg["frequencyPenalty"] if cfg["frequencyPenalty"] is not None else 0,
                presence_penalty=cfg["presencePenalty"] if cfg["presencePenalty"] is not None else 0,
                max_tokens=cfg["maxTokens"],
                top_p=cfg["topP"] if cfg["topP"] is not None else 0,
                response_format=cfg["responseFormat"] if cfg["responseFormat"] is not None else None,
                tool_choice=cfg["toolChoice"] if cfg["toolChoice"] is not None else None,
                tools=cfg["tools"] if cfg["tools"] is not None else None,
            )
            messages = pc.get("messages", [])
        else:
            # Backend list endpoint doesn't include promptConfig; leave these
            # attributes unset so we don't mislead users with fake defaults.
            model_config = None
            messages = None

        return PromptTemplate(
            id=item.get("id"),
            name=item.get("name"),
            description=item.get("description", ""),
            messages=messages or [],
            model_configuration=model_config or ModelConfig(),
            variable_names=item.get("variableNames") or item.get("variable_names", {}),
            version=item.get("version"),
            is_default=item.get("isDefault", True),
            evaluation_configs=item.get("evaluationConfigs", []),
            status=item.get("status"),
            error_message=item.get("errorMessage"),
            metadata=item.get("metadata"),
            placeholders=item.get("placeholders", {}),
        )

    @classmethod
    def list_templates(
        cls,
        fi_api_key: Optional[str] = None,
        fi_secret_key: Optional[str] = None,
        fi_base_url: Optional[str] = None,
    ) -> Dict:
        """Return the raw JSON payload from GET /model-hub/prompt-templates/.
        """

        auth_client = APIKeyAuth(
            fi_api_key=fi_api_key,
            fi_secret_key=fi_secret_key,
            fi_base_url=fi_base_url,
        )

        response = auth_client.request(
            config=RequestConfig(
                method=HttpMethod.GET,
                url=auth_client._base_url + "/" + Routes.list_templates.value,
            )
        )

        data = response.json()

        auth_client.close()

        return data

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

        # Label requested during draft create; will be assigned on commit
        self._pending_label: Optional[str] = None

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

    def generate(self, requirements: str) -> "Prompt":
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

    def improve(self, requirements: str) -> "Prompt":
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

    def create(self, *, label: Optional[str] = None) -> "Prompt":
        """Create a draft prompt template and return self for chaining.

        If a label is provided, it will be assigned after the draft is committed
        (labels cannot be assigned to drafts). The label is remembered and
        applied on the next commit of this template version.
        """
        if not self.template:
            raise ValueError("template must be set")

        # Enforce maximum 10 variables per template at creation time
        if self.template.variable_names and len(self.template.variable_names) > 10:
            raise ValueError(
                f"A maximum of 10 unique variables is allowed; received {len(self.template.variable_names)}."
            )

        if self.template.id:
            raise TemplateAlreadyExists(self.template.name)

        method = HttpMethod.POST
        url = self._base_url + "/" + Routes.create_template.value

        messages, placeholders = self._prepare_messages_and_placeholders()

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
                    "placeholders": list(placeholders.keys()),
                }
            ],
            "variable_names": self.template.variable_names,
            "evaluation_configs": self.template.evaluation_configs or [],
            "metadata": self.template.metadata or {},
            "placeholders": placeholders,
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
        self.template.version = response.get("templateVersion") or response.get("createdVersion") or "v1"
        self.template.metadata = response.get("metadata", {})

        # Remember label for assignment on commit (cannot assign on drafts)
        if label is not None:
            self._pending_label = label

        return self
    def _create_new_draft(self, *, label: Optional[str] = None) -> None:
        """
        Calls the internal add-new-draft endpoint to create a new version
        and updates the client's state with the new version number.
        """
        if not self.template or not self.template.id:
            raise ValueError("Template must be created before creating a new version.")

        url = (
            self._base_url
            + "/"
            + Routes.add_new_draft.value.format(template_id=self.template.id)
        )

        messages, placeholders = self._prepare_messages_and_placeholders()

        model_config = {
            "model": self.template.model_configuration.model_name,
            "temperature": self.template.model_configuration.temperature,
            "max_tokens": self.template.model_configuration.max_tokens,
            "top_p": self.template.model_configuration.top_p,
            "frequency_penalty": self.template.model_configuration.frequency_penalty,
            "presence_penalty": self.template.model_configuration.presence_penalty,
        }

        draft_entry = {
            "prompt_config": [
                {
                    "messages": messages,
                    "configuration": model_config,
                    "placeholders": list(placeholders.keys()),
                }
            ],
            "variable_names": self.template.variable_names,
            "evaluation_configs": self.template.evaluation_configs or [],
            "metadata": self.template.metadata or {},
            "placeholders": placeholders,
        }

        body = {"new_prompts": [draft_entry]}

        response = self.request(
            config=RequestConfig(method=HttpMethod.POST, url=url, json=body),
            response_handler=PromptResponseHandler,
        )

        if isinstance(response, dict) and response:
            result = response.get("result")
            if isinstance(result, list) and result:
                new_version_data = result[0]
                self.template.version = new_version_data.get("templateVersion")
        else:
            logger.error(
                "Failed to create new version, unexpected response format from server."
            )

    def delete(self) -> bool:
        """Delete the current template (requires `self.template.id`).

        Returns True when deletion succeeds. If the template has no `id`, a
        ValueError is raised.
        """
        if not self.template or not self.template.id:
            raise ValueError("Template ID missing; cannot delete.")

        self.request(
            config=RequestConfig(
                method=HttpMethod.DELETE,
                url=self._base_url
                + "/"
                + Routes.delete_template.value.format(template_id=self.template.id),
            ),
            response_handler=None,
        )

        # Clear local reference so user knows it's gone.
        self.template = None
        return True

    @classmethod
    def delete_template_by_name(
        cls,
        name: str,
        fi_api_key: Optional[str] = None,
        fi_secret_key: Optional[str] = None,
        fi_base_url: Optional[str] = None,
    ) -> bool:
        """Delete a template by its exact name.
        """

        client = APIKeyAuth(
            fi_api_key=fi_api_key,
            fi_secret_key=fi_secret_key,
            fi_base_url=fi_base_url,
        )

        try:
            tmpl: PromptTemplate = client.request(
                config=RequestConfig(
                    method=HttpMethod.GET,
                    url=client._base_url + "/" + Routes.prompt_label_get_by_name.value,
                    params={"name": name},
                ),
                response_handler=PromptResponseHandler,
            )

            client.request(
                config=RequestConfig(
                    method=HttpMethod.DELETE,
                    url=client._base_url
                    + "/"
                    + Routes.delete_template.value.format(template_id=tmpl.id),
                ),
                response_handler=None,
            )
            return True
        finally:
            client.close()

    # Keep existing methods but update them to work with PromptTemplate
    def _fetch_template_by_name(self, name: str) -> PromptTemplate:
        """Fetch template configuration by exact name using dedicated endpoint"""
        response = self.request(
            config=RequestConfig(
                method=HttpMethod.GET,
                url=self._base_url + "/" + Routes.prompt_label_get_by_name.value,
                params={"name": name},
            ),
            response_handler=PromptResponseHandler,
        )
        return response
    
    def _fetch_template_version_history(self):
        """Fetch template version history"""
        logger.info(f"Fetching template version history for {self.template.name}")

        response = self.request(
            config=RequestConfig(
                method=HttpMethod.GET,
                url=self._base_url + "/" + Routes.get_template_version_history.value,
                params={"template_id": self.template.id},
            )
        )

        results = response.json().get("results", [])
        if not results:
            raise ValueError(f"No template found with name: {self.template.name}")

        return results

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    def list_template_versions(self):
        """Return full version history as provided by the backend.

        Each element in the returned list is the raw JSON entry that includes
        at least these keys: ``templateVersion``, ``isDraft`` and
        ``createdAt``.
        """
        return self._fetch_template_version_history()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _current_version_is_draft(self) -> bool:
        """Check backend state to know if the current version is still draft."""
        history = self._fetch_template_version_history()
        for entry in history:
            if entry.get("templateVersion") == self.template.version:
                return bool(entry.get("isDraft"))
        # If not found assume draft (conservative)
        return True

    def _fetch_model_details(self, model_name: str):
        if not model_name:
            raise ValueError("Model name is required")
        """Fetch model details"""
        response = self.request(
            config=RequestConfig(
                method=HttpMethod.GET,
                url=self._base_url + "/" + Routes.get_model_details.value,
                params={"model_name": model_name}
            )
        )

        results = response.json().get("results", [])
        if not results:
            raise ValueError(f"No model found with name: {model_name}")

        return results[0]

    # Public convenience
    @classmethod
    def get_template_by_name(
        cls,
        name: str,
        label: Optional[str] = None,
        version: Optional[str] = None,
        fi_api_key: Optional[str] = None,
        fi_secret_key: Optional[str] = None,
        fi_base_url: Optional[str] = None,
    ) -> "Prompt":
        """
        Retrieve a prompt template by its exact name.

        If a version or label is specified, it will be fetched directly.
        If neither is provided, it will first attempt to fetch the version with the
        'production' label, and if that fails, it will fall back to the server's
        default version resolution (e.g., the latest committed version).
        """
        cache_key = prompt_cache.make_key(name, version=version, label=label)

        fresh = prompt_cache.get(cache_key)
        if fresh is not None:
            return cls(
                template=fresh,
                fi_api_key=fi_api_key,
                fi_secret_key=fi_secret_key,
                fi_base_url=fi_base_url,
            )

        stale = prompt_cache.get_stale(cache_key)
        # Note: Async refresh logic is not applied here to simplify the fallback flow.
        # If stale data is present, it will be used only if the live fetch fails.

        client = APIKeyAuth(
            fi_api_key=fi_api_key,
            fi_secret_key=fi_secret_key,
            fi_base_url=fi_base_url,
        )

        try:
            template = None
            # If a specific version or label is provided, use the direct endpoint. No fallback.
            if version or label:
                params = {"name": name}
                if version:
                    params["version"] = version
                if label:
                    params["label"] = label

                template = client.request(
                    config=RequestConfig(
                        method=HttpMethod.GET,
                        url=client._base_url
                        + "/"
                        + Routes.prompt_label_get_by_name.value,
                        params=params,
                    ),
                    response_handler=PromptResponseHandler,
                )
            else:
                # No version or label, so try 'production' with fallback.
                try:
                    params = {"name": name, "label": "production"}
                    template = client.request(
                        config=RequestConfig(
                            method=HttpMethod.GET,
                            url=client._base_url
                            + "/"
                            + Routes.prompt_label_get_by_name.value,
                            params=params,
                        ),
                        response_handler=PromptResponseHandler,
                    )
                except (TemplateNotFound, SDKException):
                    logger.info(
                        "Template with label 'production' not found for '%s'. Falling back to default.",
                        name,
                    )
                    fallback_params = {"name": name}
                    template = client.request(
                        config=RequestConfig(
                            method=HttpMethod.GET,
                            url=client._base_url
                            + "/"
                            + Routes.get_template_by_name.value,
                            params=fallback_params,
                        ),
                        response_handler=PromptResponseHandler,
                    )

            prompt_cache.set(cache_key, template)
            return cls(
                template=template,
                fi_api_key=fi_api_key,
                fi_secret_key=fi_secret_key,
                fi_base_url=fi_base_url,
            )

        except Exception as exc:
            if stale:
                logger.warning(
                    "Using stale cached template '%s' due to fetch failure: %s",
                    name,
                    exc,
                )
                return cls(
                    template=stale,
                    fi_api_key=fi_api_key,
                    fi_secret_key=fi_secret_key,
                    fi_base_url=fi_base_url,
                )
            raise
        finally:
            client.close()

    def commit_current_version(self, message: str = "", *, set_default: bool = False, label: Optional[str] = None) -> bool:
        """Commit the current draft version.

        Parameters
        ----------
        message : str, optional
            Commit message describing this version. Defaults to empty string.
        set_default : bool, optional
            If True, mark this version as the default one for the template.
        label : str, optional
            Label to assign to this version (e.g., "production", "staging").
        """
        if not self.template or not self.template.id:
            raise ValueError("Template must exist before it can be committed.")
        if not self.template.version:
            raise ValueError("Cannot commit because template version is unknown.")

        body = {
            "version_name": self.template.version,
            "message": message,
            "set_default": set_default,
            "is_draft": False,
            "metadata": self.template.metadata or {},
        }

        self.request(
            config=RequestConfig(
                method=HttpMethod.POST,
                url=self._base_url + "/" + Routes.commit_template.value.format(template_id=self.template.id),
                json=body,
            ),
            response_handler=SimpleJsonResponseHandler,
        )

        # Perform label assignment after successful commit if requested
        label_to_assign = label or self._pending_label
        if label_to_assign is not None and self.template and self.template.id and self.template.version:
            try:
                self._assign_label_by_name(label_to_assign)
            except Exception as exc:
                logger.error("Failed to assign label '%s' to version %s after commit: %s", label_to_assign, self.template.version, exc)
            finally:
                # Clear pending label regardless of success
                self._pending_label = None

        # After successful commit we refresh status info using history
        if not self._current_version_is_draft():
            self.template.status = "committed"
        return True

    def create_new_version(
        self,
        *,
        template: Optional[PromptTemplate] = None,
        commit_message: str = "Auto-commit via SDK",
        set_default: bool = False,
        label: Optional[str] = None,
    ) -> "Prompt":
        """Commit current draft (if any) then create a fresh draft version.

        The helper guarantees we never leave an uncommitted draft behind.
        Returns self so the call can be chained (e.g. ``client.create_new_version().generate(...)``).
        """
        if not self.template:
            raise ValueError("Template must be configured before creating a new version.")

        # If caller supplied a new template object, merge its data into the current
        if template is not None:
            self._apply_template_updates(template)

        # If the current version is still in draft (backend-checked), commit it first.
        if self._current_version_is_draft():
            self.commit_current_version(message=commit_message, set_default=set_default, label=label)

        # Now create a fresh draft version
        self._create_new_draft()
        return self

    # ------------------------------------------------------------------
    # Draft update helpers
    # ------------------------------------------------------------------

    def _apply_template_updates(self, tpl: PromptTemplate) -> None:
        """Replace editable fields of ``self.template`` with those from *tpl*."""
        mutable_fields = (
            "messages",
            "description",
            "variable_names",
            "model_configuration",
            "evaluation_configs",
        )

        for field in mutable_fields:
            new_val = getattr(tpl, field, None)
            if new_val is not None:
                setattr(self.template, field, new_val)

    def save_current_draft(self) -> bool:
        """Push the current in-memory template state to the backend draft version."""
        if not self.template or not self.template.id:
            raise ValueError("Template must be created before it can be updated.")
        # Ensure the current version is still a draft according to backend
        if not self._current_version_is_draft():
            raise ValueError("Current version is already committed; create a new draft version first.")

        # Prepare messages and configuration just like in _create_new_draft
        messages, placeholders = self._prepare_messages_and_placeholders()

        model_cfg = {
            "model": self.template.model_configuration.model_name,
            "temperature": self.template.model_configuration.temperature,
            "max_tokens": self.template.model_configuration.max_tokens,
            "top_p": self.template.model_configuration.top_p,
            "frequency_penalty": self.template.model_configuration.frequency_penalty,
            "presence_penalty": self.template.model_configuration.presence_penalty,
        }

        body = {
            "is_run": "draft",  # purely save changes
            "is_sdk": True,
            "version": self.template.version,
            "prompt_config": [
                {
                    "messages": messages,
                    "configuration": model_cfg,
                    "placeholders": list(placeholders.keys()),
                }
            ],
            "variable_names": self.template.variable_names,
            "evaluation_configs": self.template.evaluation_configs or [],
            "metadata": self.template.metadata or {},
            "placeholders": placeholders,
        }

        self.request(
            config=RequestConfig(
                method=HttpMethod.POST,
                url=self._base_url + "/" + Routes.run_template.value.format(template_id=self.template.id),
                json=body,
            ),
            response_handler=SimpleJsonResponseHandler,
        )

        return True

    def compile(self, **kwargs) -> list[dict]:
        """Return a fully-rendered list of chat messages. By Substituting variables and placeholders.
        """

        if not self.template or not self.template.messages:
            raise ValueError("Template must be loaded before compilation.")

        import re

        def _substitute_vars(text: str) -> str:
            """Replace {{var}} occurrences inside *text* using *kwargs*."""

            def _repl(match):
                var_name = match.group(1).strip()
                return str(kwargs.get(var_name, match.group(0)))

            return re.sub(r"\{\{\s*(\w+)\s*\}\}", _repl, text)

        compiled: list[dict] = []

        for msg in self.template.messages:
            # Allow both pydantic objects (MessageBase) and raw dicts
            if isinstance(msg, dict) and msg.get("type") == "placeholder":
                ph_name = msg.get("name")
                if ph_name in kwargs and isinstance(kwargs[ph_name], list):
                    # Insert each provided chat message
                    for ph_msg in kwargs[ph_name]:
                        if isinstance(ph_msg, dict) and "role" in ph_msg and "content" in ph_msg:
                            compiled.append({
                                "role": ph_msg["role"],
                                "content": _substitute_vars(str(ph_msg["content"])),
                            })
                        else:
                            raise ValueError(
                                f"Each chat message for placeholder '{ph_name}' must include 'role' and 'content'."
                            )
                else:
                    # Placeholder unresolved – keep as-is
                    compiled.append(msg)
            else:
                # Handle MessageBase or raw dict with role/content
                role = getattr(msg, "role", msg.get("role") if isinstance(msg, dict) else None)
                content = getattr(msg, "content", msg.get("content") if isinstance(msg, dict) else None)
                if role is None:
                    raise ValueError("Message object missing 'role' attribute")
                compiled.append({
                    "role": role,
                    "content": _substitute_vars(str(content)),
                })

        return compiled

    def _prepare_messages_and_placeholders(self) -> tuple[list[dict], dict]:
        """Extract placeholder entries from messages and return (messages, placeholders)."""
        if not self.template:
            return [], {}

        messages: list[dict] = []
        placeholders: dict = {}

        # Check if there's a system message in the template messages
        has_system_message = any(
            (hasattr(msg, "role") and getattr(msg, "role") == "system")
            or (isinstance(msg, dict) and msg.get("role") == "system")
            for msg in (self.template.messages or [])
        )

        # Add a default empty system prompt if none exists
        if not has_system_message:
            messages.append(
                {"role": "system", "content": [{"type": "text", "text": ""}]}
            )

        for message in self.template.messages or []:
            message_dict = (
                message.model_dump()
                if hasattr(message, "model_dump")
                else dict(message)
                if isinstance(message, dict)
                else message.__dict__
            )

            # Placeholder entry – move to placeholders map and skip adding to messages
            if message_dict.get("type") == "placeholder":
                name = message_dict.get("name")
                if name:
                    # Initialize with empty array; runtime chat history can be supplied separately
                    placeholders.setdefault(name, [])
                continue

            # Normalize string content -> structured parts
            if isinstance(message_dict.get("content"), str):
                message_dict["content"] = [
                    {"type": "text", "text": message_dict["content"]}
                ]
            messages.append(message_dict)

        return messages, placeholders
