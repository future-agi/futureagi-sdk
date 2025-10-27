from typing import Dict, Optional

from fi.api.auth import APIKeyAuth
from fi.api.types import HttpMethod, RequestConfig
from fi.utils.errors import SDKException
from fi.utils.logging import logger
from fi.utils.routes import Routes


class LabelManagementMixin:
    """Mixin providing label management functionality for Prompt client."""

    # ------------------------------------------------------------------
    # Label management helpers
    # ------------------------------------------------------------------

    def list_labels(self) -> Dict:
        """List available labels (system + custom for org). Returns raw JSON."""
        response = self.request(
            config=RequestConfig(
                method=HttpMethod.GET,
                url=self._base_url + "/" + Routes.prompt_labels.value,
            ),
            response_handler=self._get_simple_json_response_handler(),
        )
        return response

    def get_label_by_name(self, name: str) -> Optional[Dict]:
        """Fetch a label by case-insensitive name from list_labels() result."""
        data = self.list_labels()
        items = data.get("results") if isinstance(data, dict) else data
        if not isinstance(items, list):
            return None
        for item in items:
            if str(item.get("name", "")).lower() == name.lower():
                return item
        return None

    def assign_label(self, label: str, *, version: Optional[str] = None) -> Dict:
        """Assign a label by name to the given or current version (creates the label if missing)."""
        # Prevent assignment to drafts
        if version is None and self._current_version_is_draft():
            self._pending_label = label
            return {"detail": "Label will be assigned after commit", "queued": True}
        if version is not None and version == (self.template.version if self.template else None) and self._current_version_is_draft():
            self._pending_label = label
            return {"detail": "Label will be assigned after commit", "queued": True}
        return self._assign_label_by_name(label, version=version)

    def remove_label_from_current_version(self, label: str) -> Dict:
        """Detach a label by name from the client's current version."""
        if not self.template or not self.template.id or not self.template.version:
            raise ValueError("Template and current version must be loaded")
        return self._remove_label_by_name(label, self.template.version)

    def remove_label(self, label: str, *, version: Optional[str] = None) -> Dict:
        """Detach a label by name from the given or current version."""
        if not self.template or not self.template.id:
            raise ValueError("Template must be loaded")
        version_name = version or self.template.version
        if not version_name:
            raise ValueError("Version must be specified or available on the client")
        return self._remove_label_by_name(label, version_name)

    @classmethod
    def assign_label_to_template_version(
        cls,
        *,
        template_name: str,
        version: str,
        label: str,
        fi_api_key: Optional[str] = None,
        fi_secret_key: Optional[str] = None,
        fi_base_url: Optional[str] = None,
    ) -> Dict:
        """Assign a label by name to a template/version using only names."""
        client = cls(
            fi_api_key=fi_api_key,
            fi_secret_key=fi_secret_key,
            fi_base_url=fi_base_url,
        )
        try:
            return client._assign_label_to_template_version_by_names(template_name, version, label)
        finally:
            client.close()

    @classmethod
    def remove_label_from_template_version(
        cls,
        *,
        template_name: str,
        version: str,
        label: str,
        fi_api_key: Optional[str] = None,
        fi_secret_key: Optional[str] = None,
        fi_base_url: Optional[str] = None,
    ) -> Dict:
        """Remove a label by name from a template/version using only names."""
        client = cls(
            fi_api_key=fi_api_key,
            fi_secret_key=fi_secret_key,
            fi_base_url=fi_base_url,
        )
        try:
            return client._remove_label_from_template_version_by_names(template_name, version, label)
        finally:
            client.close()

    @classmethod
    def set_default_version(
        cls,
        *,
        template_name: str,
        version: str,
        fi_api_key: Optional[str] = None,
        fi_secret_key: Optional[str] = None,
        fi_base_url: Optional[str] = None,
    ) -> Dict:
        """Set default version for a template by name."""
        client = APIKeyAuth(
            fi_api_key=fi_api_key,
            fi_secret_key=fi_secret_key,
            fi_base_url=fi_base_url,
        )
        try:
            response = client.request(
                config=RequestConfig(
                    method=HttpMethod.POST,
                    url=client._base_url + "/" + Routes.prompt_label_set_default.value,
                    json={"template_name": template_name, "version": version},
                ),
                response_handler=None,  # Will use SimpleJsonResponseHandler when called
            )
            return response.json()
        finally:
            client.close()

    @classmethod
    def get_template_labels(
        cls,
        *,
        template_name: Optional[str] = None,
        template_id: Optional[str] = None,
        fi_api_key: Optional[str] = None,
        fi_secret_key: Optional[str] = None,
        fi_base_url: Optional[str] = None,
    ) -> Dict:
        """List versions and labels for a template by name or id. Returns raw JSON."""
        if not template_name and not template_id:
            raise ValueError("template_name or template_id is required")
        client = APIKeyAuth(
            fi_api_key=fi_api_key,
            fi_secret_key=fi_secret_key,
            fi_base_url=fi_base_url,
        )
        try:
            params = {"template_name": template_name} if template_name else {"template_id": template_id}
            response = client.request(
                config=RequestConfig(
                    method=HttpMethod.GET,
                    url=client._base_url + "/" + Routes.prompt_label_template_labels.value,
                    params=params,
                ),
                response_handler=None,  # Will use SimpleJsonResponseHandler when called
            )
            return response.json()
        finally:
            client.close()

    # ------------------------------------------------------------------
    # Internal label helpers
    # ------------------------------------------------------------------

    def _get_label_id(self, name: str) -> Optional[str]:
        """Get label ID by name (case-insensitive). Returns None if not found."""
        item = self.get_label_by_name(name)
        if item and item.get("id"):
            return str(item["id"])
        return None

    def create_label(self, name: str) -> Dict:
        """Create a custom label with the given name. Returns raw JSON."""
        response = self.request(
            config=RequestConfig(
                method=HttpMethod.POST,
                url=self._base_url + "/" + Routes.prompt_labels.value,
                json={"name": name, "type": "custom"},
            ),
            response_handler=self._get_simple_json_response_handler(),
        )
        return response

    def _assign_label_by_name(self, name: str, *, version: Optional[str] = None) -> Dict:
        """Internal: assign label by name to version."""
        label_id = self._get_label_id(name)
        if not label_id:
            raise SDKException(f"Label '{name}' not found. Create it first, then assign.")
        
        tpl_id = str(self.template.id) if self.template and self.template.id else None
        ver = version or (self.template.version if self.template else None)
        if not tpl_id or not ver:
            raise ValueError("template_id and version are required")
        
        response = self.request(
            config=RequestConfig(
                method=HttpMethod.POST,
                url=self._base_url + "/" + Routes.prompt_label_assign_by_id.value.format(template_id=tpl_id, label_id=label_id),
                json={"version": ver},
            ),
            response_handler=self._get_simple_json_response_handler(),
        )
        return response

    def _remove_label_by_name(self, label_name: str, version_name: str) -> Dict:
        """Internal: remove label by name from version by name."""
        # Get version_id
        version_id = self._get_version_id_by_name(version_name)
        if not version_id:
            raise SDKException(f"Could not resolve version_id for version '{version_name}'")
        
        # Get label_id
        item = self.get_label_by_name(label_name)
        if not item or not item.get("id"):
            raise SDKException(f"Label '{label_name}' not found")
        
        response = self.request(
            config=RequestConfig(
                method=HttpMethod.POST,
                url=self._base_url + "/" + Routes.prompt_label_remove.value,
                json={"label_id": str(item["id"]), "version_id": str(version_id)},
            ),
            response_handler=self._get_simple_json_response_handler(),
        )
        return response

    def _assign_label_to_template_version_by_names(self, template_name: str, version: str, label: str) -> Dict:
        """Internal: assign label to template/version using only names."""
        
        # 1) Resolve template_id
        template_resp = self.request(
            config=RequestConfig(
                method=HttpMethod.GET,
                url=self._base_url + "/" + Routes.get_template_id_by_name.value,
                params={"search": template_name},
            ),
        )
        # Extract template_id from response 
        data = template_resp.json()
        if "search=" in template_resp.url:
            results = data.get("results", [])
            for item in results:
                if item["name"] == template_name:
                    template_id = item["id"]
                    break
            else:
                raise SDKException(f"No template found with name: {template_name}")
        else:
            template_id = str(data.get("id", ""))

        # 2) Ensure version exists and is not draft
        history_resp = self.request(
            config=RequestConfig(
                method=HttpMethod.GET,
                url=self._base_url + "/" + Routes.get_template_version_history.value,
                params={"template_id": template_id},
            )
        )
        history = history_resp.json().get("results", [])
        matched = None
        for entry in history:
            if str(entry.get("templateVersion")) == version:
                matched = entry
                break
        if not matched:
            raise SDKException(f"No version '{version}' found for template '{template_name}'")
        is_draft = matched.get("isDraft") if matched.get("isDraft") is not None else matched.get("is_draft")
        if is_draft:
            raise SDKException("Cannot assign label to a draft version. Commit the version first.")

        # 3) Resolve or create label_id
        label_id = self._get_label_id(label)
        if not label_id:
            raise SDKException(f"Label '{label}' not found. Create it first, then assign.")

        # 4) Assign
        resp = self.request(
            config=RequestConfig(
                method=HttpMethod.POST,
                url=self._base_url + "/" + Routes.prompt_label_assign_by_id.value.format(template_id=template_id, label_id=label_id),
                json={"version": version},
            ),
            response_handler=self._get_simple_json_response_handler(),
        )
        return resp

    def _remove_label_from_template_version_by_names(self, template_name: str, version: str, label: str) -> Dict:
        """Internal: remove label from template/version using only names."""
        
        # 1) Resolve template_id
        template_resp = self.request(
            config=RequestConfig(
                method=HttpMethod.GET,
                url=self._base_url + "/" + Routes.get_template_id_by_name.value,
                params={"search": template_name},
            ),
        )
        # Extract template_id from response 
        data = template_resp.json()
        if "search=" in template_resp.url:
            results = data.get("results", [])
            for item in results:
                if item["name"] == template_name:
                    template_id = item["id"]
                    break
            else:
                raise SDKException(f"No template found with name: {template_name}")
        else:
            template_id = str(data.get("id", ""))
        
        # 2) Resolve version_id
        history_resp = self.request(
            config=RequestConfig(
                method=HttpMethod.GET,
                url=self._base_url + "/" + Routes.get_template_version_history.value,
                params={"template_id": template_id},
            )
        )
        history = history_resp.json().get("results", [])
        version_id = None
        for entry in history:
            if str(entry.get("templateVersion")) == version:
                for key in ("id", "versionId", "executionId"):
                    if entry.get(key):
                        version_id = str(entry.get(key))
                        break
                break
        if not version_id:
            raise SDKException(f"No version '{version}' found for template '{template_name}'")

        # 3) Resolve label_id
        item = self.get_label_by_name(label)
        if not item or not item.get("id"):
            raise SDKException(f"Label '{label}' not found")

        # 4) Remove
        resp = self.request(
            config=RequestConfig(
                method=HttpMethod.POST,
                url=self._base_url + "/" + Routes.prompt_label_remove.value,
                json={"label_id": str(item["id"]), "version_id": version_id},
            ),
            response_handler=self._get_simple_json_response_handler(),
        )
        return resp

    def _get_version_id_by_name(self, version_name: str) -> Optional[str]:
        """Lookup internal version_id by version name via history endpoint."""
        history = self._fetch_template_version_history()
        for entry in history:
            if str(entry.get("templateVersion")) == version_name:
                # Try common id keys
                for key in ("id", "versionId", "executionId"):
                    if entry.get(key):
                        return str(entry[key])
        return None

    def _get_simple_json_response_handler(self):
        """Return the SimpleJsonResponseHandler class for use in requests."""
        # Import here to avoid circular imports
        from fi.prompt.client import SimpleJsonResponseHandler
        return SimpleJsonResponseHandler
