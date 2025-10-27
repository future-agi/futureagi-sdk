from typing import Dict, Optional, List, Union

from fi.api.auth import APIKeyAuth, ResponseHandler
from fi.api.types import HttpMethod, RequestConfig
from fi.kb.types import KnowledgeBaseConfig

from fi.utils.errors import InvalidAuthError
from fi.utils.routes import Routes
from fi.utils.errors import FileNotFoundException, UnsupportedFileType, SDKException
import os

class KBResponseHandler(ResponseHandler[Dict, KnowledgeBaseConfig]):

    @classmethod
    def _parse_success(cls, response) -> Dict:
        """Handles responses for prompt requests"""
        data = response.json()

        if data is not None and data.get("status") is False:
            err_msg = data.get("result") or data.get("detail") or "Knowledge Base operation failed."
            raise SDKException(err_msg)
        
        if response.request.method == HttpMethod.POST.value and response.url.endswith(
            Routes.knowledge_base.value
        ):
            return data["result"]
        
        if response.request.method == HttpMethod.PATCH.value and response.url.endswith(
            Routes.knowledge_base.value
        ):
            return data["result"]
        
        if response.request.method == HttpMethod.DELETE.value:
            return data
        
        return data
    
    @classmethod
    def _handle_error(cls, response) -> None:
        if response.status_code == 403:
            raise InvalidAuthError()
        elif response.status_code == 429:
            # Too many requests / quota exceeded – backend typically returns JSON with the reason.
            try:
                data = response.json()
                err_msg = (
                    data.get("result")
                    or data.get("detail")
                    or data.get("message")
                    or "Rate limit exceeded. Please try again later."
                )
            except Exception:
                err_msg = "Rate limit exceeded. Please try again later."
            raise SDKException(err_msg)
        elif 400 <= response.status_code < 500:
            # Other client-side errors (validation, not found, etc.)
            try:
                data = response.json()
                err_msg = (
                    data.get("result")
                    or data.get("detail")
                    or data.get("message")
                    or f"Client error {response.status_code}."
                )
            except Exception:
                err_msg = f"Client error {response.status_code}."
            raise SDKException(err_msg)
        elif response.status_code >= 500:
            # Server-side error
            try:
                data = response.json()
                err_msg = (
                    data.get("result")
                    or data.get("detail")
                    or data.get("message")
                    or "Server encountered an error. Please try again later."
                )
            except Exception:
                err_msg = "Server encountered an error. Please try again later."
            raise SDKException(err_msg)
        else:
            response.raise_for_status()

class KnowledgeBase(APIKeyAuth):

    def __init__(
        self,
        kb_name: Optional[str] = None,
        fi_api_key: Optional[str] = None,
        fi_secret_key: Optional[str] = None,
        fi_base_url: Optional[str] = None,
        **kwargs,
    ):
        """Create a KnowledgeBase client.

        Args:
            kb_name (Optional[str]): Name of an existing Knowledge Base you want this client to work with.
                If provided, the SDK will look it up server-side and cache its id for subsequent calls.
        """

        super().__init__(
            fi_api_key=fi_api_key,
            fi_secret_key=fi_secret_key,
            fi_base_url=fi_base_url,
            **kwargs,
        )

        # Internal cache of the current KB (instance of KnowledgeBaseConfig)
        self.kb: Optional[KnowledgeBaseConfig] = None

        if kb_name:
            try:
                self.kb = self._get_kb_from_name(kb_name)
            except Exception:
                raise SDKException(
                    f"Knowledge Base with name '{kb_name}' not found. Please create it first or verify the name."
                )
        
    def update_kb(
        self,
        kb_name: str,
        new_name: Optional[str] = None,
        file_paths: Optional[Union[str, List[str]]] = None,
    ):
        """
        Update name of Knowledge Base and/or add files to it.
        
        Args:
            name Optional[str]: Name of the Knowledge Base
            file_path Union[str, List[str]]: List of file paths or a directory path
        
        Returns:
            self for chaining
        """
        try:
            import requests  
            
            # Resolve the KB if not already cached or if a different kb_name is provided
            if not self.kb or self.kb.name != kb_name:
                try:
                    self.kb = self._get_kb_from_name(kb_name)
                except Exception:
                    raise SDKException(
                        f"Knowledge Base named '{kb_name}' not found when attempting to update."
                    )

            if file_paths:
                try:
                    self._check_file_paths(file_paths)
                except (FileNotFoundException, UnsupportedFileType) as e: 
                    raise SDKException("Knowledge Base update failed due to a file processing issue.", cause=e)
                except SDKException as e:
                    raise SDKException("Knowledge Base update failed due to invalid file path arguments.", cause=e)
                except Exception as e:
                    raise SDKException("An unexpected error occurred during file path validation for update.", cause=e)
            
            url = self._base_url + "/" + Routes.knowledge_base.value
            
            data = {
                "kb_id": str(self.kb.id),
                "name": self.kb.name if new_name is None else new_name,
            }
            
            files = []
            
            try:
                if self._valid_file_paths:
                    for file_path in self._valid_file_paths:
                        file_name = os.path.basename(file_path)
                        file_ext = file_path.split('.')[-1].lower()
                        
                        if file_ext not in ['pdf', 'docx', 'txt', 'rtf']:
                            raise UnsupportedFileType(file_ext=file_ext, file_name=file_name)
                        file_handle = None
                        try:
                            file_handle = open(file_path, 'rb')
                            content_type = self._get_content_type(file_ext)
                            files.append(('file', (file_name, file_handle, content_type)))
                        except Exception as e:
                            if file_handle:
                                file_handle.close()
                            raise SDKException(f"Error preparing file '{os.path.basename(file_path)}' for upload.", cause=e)
                
                headers = {
                    'Accept': 'application/json',
                    'X-Api-Key': self._fi_api_key,
                    'X-Secret-Key': self._fi_secret_key,
                }
                
                response = requests.patch(
                    url=url,
                    data=data,
                    files=files,  
                    headers=headers,
                    timeout=300
                )
                
                KBResponseHandler._handle_error(response)
                parsed_result_data = KBResponseHandler._parse_success(response)

                if 'notUploaded' in parsed_result_data and parsed_result_data['notUploaded']:
                    raise SDKException("Server reported that some files were not uploaded successfully.")
                
                if parsed_result_data:
                    # Server may return updated info – refresh local cache
                    self.kb.id = parsed_result_data.get("id", self.kb.id)
                    self.kb.name = parsed_result_data.get("name", self.kb.name)
                    if "files" in parsed_result_data:
                        self.kb.files = parsed_result_data["files"]

                return self
            
            finally:
                for file_tuple in files:
                    if hasattr(file_tuple[1][1], 'close') and not file_tuple[1][1].closed:
                        file_tuple[1][1].close()
            
        except SDKException:
            raise
        except Exception as e:
            for _, (_name, fh, _type) in files:
                if hasattr(fh, 'close') and not fh.closed:
                    fh.close()
            raise SDKException("Failed to update the Knowledge Base due to an unexpected error.", cause=e)

    def delete_files_from_kb(
        self,
        file_names: List[str],
        kb_name: Optional[str] = None,
    ):
        """
        Delete files from the Knowledge Base.
        
        Args:
            file_names List[str]: List of file names to be deleted
        
        Returns:
            self for chaining
        """
        try:
            # If kb_name provided, resolve it; otherwise fallback to cached self.kb
            if kb_name is not None:
                try:
                    self.kb = self._get_kb_from_name(kb_name)
                except SDKException:
                    raise SDKException(
                        f"Knowledge Base named '{kb_name}' not found when attempting to delete files."
                    )

            if not self.kb or not self.kb.id:
                raise SDKException(
                    "No Knowledge Base targeted. Provide kb_name or have a current Knowledge Base configured."
                )
                
            if not file_names:
                raise SDKException("Files to be deleted not found or list is empty. Please provide correct File Names.")
                
            method = HttpMethod.DELETE
            url = self._base_url + "/" + Routes.knowledge_base_files.value
            
            data = {
                "file_names": file_names,
                "kb_id": str(self.kb.id)
            }
            
            response = self.request(
                config=RequestConfig(
                    method=method,
                    url=url,
                    json=data,
                    headers={'Content-Type': 'application/json'}
                ),
                response_handler=KBResponseHandler,
            )

            return self
        
        except SDKException:
            raise
        except Exception as e:
            raise SDKException("Failed to delete files from the Knowledge Base due to an unexpected error.", cause=e)

    def delete_kb(
        self,
        kb_ids: Optional[Union[str, List[str]]] = None,
        kb_names: Optional[Union[str, List[str]]] = None,
    ):
        """
        Delete a Knowledge Base and return the Knowledge Base client.
        
        Args:
            name Optional[str]: Name of the Knowledge Base
            kb_ids Optional[Union[str, List[str]]]: List of kb_ids to delete
        
        """
        try:
            # Resolve provided kb_names into ids (if any)
            resolved_ids: list[str] = []

            if kb_names is not None:
                names_list = (
                    [kb_names]
                    if isinstance(kb_names, str)
                    else kb_names  # assume list
                )
                for name in names_list:
                    try:
                        kb_conf = self._get_kb_from_name(name)
                        resolved_ids.append(str(kb_conf.id))
                    except SDKException:
                        # If a name isn't found we skip & warn later
                        continue

                if not resolved_ids:
                    raise SDKException(
                        "None of the provided Knowledge Base names could be resolved to existing IDs."
                    )

            # Handle legacy kb_ids arg
            if kb_ids is not None:
                if isinstance(kb_ids, str):
                    resolved_ids.append(kb_ids)
                elif isinstance(kb_ids, list):
                    resolved_ids.extend([str(kb_id) for kb_id in kb_ids])
                else:
                    raise SDKException("kb_ids must be a string or a list of strings.")

            # Fallback to cached KB if nothing else provided
            if not resolved_ids and self.kb and self.kb.id:
                resolved_ids.append(str(self.kb.id))

            if not resolved_ids:
                raise SDKException(
                    "No Knowledge Base specified for deletion (provide kb_names, kb_ids, or have a current KB cached)."
                )
            
            method = HttpMethod.DELETE
            url = self._base_url + "/" + Routes.knowledge_base.value       
            json_payload = {"kb_ids": resolved_ids}
            
            response = self.request(
                config=RequestConfig(
                    method=method,
                    url=url,
                    json=json_payload,
                    headers={'Content-Type': 'application/json'}
                ),
                response_handler=KBResponseHandler,
            )

            if self.kb and self.kb.id and str(self.kb.id) in resolved_ids:
                self.kb = None
            
            return self
        
        except SDKException:
            raise
        except Exception as e:
            raise SDKException("Failed to delete Knowledge Base(s) due to an unexpected error.", cause=e)

    def create_kb(self, name: Optional[str] = None, file_paths: Optional[Union[str, List[str]]] = None):
        """
        Create a Knowledge Base and return the Knowledge Base client.
        
        Args:
            name Optional[str]: Name of the Knowledge Base
            file_paths Optional[Union[str, List[str]]]: List of file paths or a directory path
        
        Returns:
            self for chaining
        """
        import requests
        
        final_kb_name = name or "Unnamed KB"

        try:
            data = {"name": final_kb_name}
                
            method = HttpMethod.POST
            url = self._base_url + "/" + Routes.knowledge_base.value
            
            files = []
            
            try:
                if file_paths:
                    self._check_file_paths(file_paths)
                    for file_path in self._valid_file_paths:
                        file_name = os.path.basename(file_path)
                        file_ext = file_path.split('.')[-1].lower()
                        
                        if file_ext not in ['pdf', 'docx', 'txt', 'rtf']:
                            raise UnsupportedFileType(file_ext=file_ext, file_name=file_name)
                        file_handle = None
                        try:
                            file_handle = open(file_path, 'rb')
                            content_type = self._get_content_type(file_ext)
                            files.append(('file', (file_name, file_handle, content_type)))
                        except Exception as e:
                            if file_handle:
                                file_handle.close()
                            raise SDKException(f"Error preparing file '{os.path.basename(file_path)}' for Knowledge Base creation.", cause=e)
                
                headers = {
                    'Accept': 'application/json',
                    'X-Api-Key': self._fi_api_key,
                    'X-Secret-Key': self._fi_secret_key,
                }
                
                response = requests.post(
                    url=url,
                    data=data,
                    files=files,  
                    headers=headers,
                    timeout=300
                )
                KBResponseHandler._handle_error(response)
                parsed_result_data = KBResponseHandler._parse_success(response)

                if 'notUploaded' in parsed_result_data and parsed_result_data['notUploaded']:
                    raise SDKException("Server reported that some files were not uploaded during Knowledge Base creation.")
                
                self.kb = KnowledgeBaseConfig(
                    id=parsed_result_data.get("kbId"),
                    name=parsed_result_data.get("kbName"),
                    files=parsed_result_data.get("fileIds", []),
                )
                return self
                
            finally:
                for file_tuple in files:
                    if hasattr(file_tuple[1][1], 'close') and not file_tuple[1][1].closed:
                        file_tuple[1][1].close()
        
        except SDKException:
            raise
        except Exception as e:
            for _, (_name, fh, _type) in files:
                if hasattr(fh, 'close') and not fh.closed:
                    fh.close()
            raise SDKException("Failed to create the Knowledge Base due to an unexpected error.", cause=e)

    def _check_file_paths(self, file_paths: Union[str, List[str]]) -> bool:
        """
        Validates the given file paths or directory path.
        
        Args:
            file_paths (Union[str, List[str]]): List of file paths or a directory path
        
        Returns:
            bool: True if all files exist or directory contains valid files, else False
        """
        self._valid_file_paths = []

        if isinstance(file_paths, str):
            if os.path.isdir(file_paths):
                all_files = [
                    os.path.join(file_paths, f)
                    for f in os.listdir(file_paths)
                    if os.path.isfile(os.path.join(file_paths, f))
                ]
                if not all_files:
                    raise FileNotFoundException(file_path=file_paths, message=f"The directory '{file_paths}' is empty or contains no files.")
                self._valid_file_paths = all_files
                return True
            else:
                raise FileNotFoundException(file_path=file_paths, message=f"The provided path '{file_paths}' is not a valid directory.")
        
        elif isinstance(file_paths, list):
            if not file_paths:
                 raise FileNotFoundException(file_path=file_paths, message="The provided list of file paths is empty.")

            valid_paths = []
            missing_files = []
            for path in file_paths:
                if isinstance(path, str) and os.path.isfile(path):
                    valid_paths.append(path)
                else:
                    missing_files.append(str(path))

            if missing_files:
                raise FileNotFoundException(
                    file_path=missing_files,
                    message=f"Some file paths are invalid, not files, or do not exist: {', '.join(missing_files)}"
                )
            
            if not valid_paths:
                raise FileNotFoundException(file_path=file_paths, message="No valid files found in the provided list.")

            self._valid_file_paths = valid_paths
            return True
        
        raise SDKException(f"Unsupported type for file_paths: {type(file_paths)}. Expected str or list.")

    def _get_content_type(self, file_ext):
        """
        Get the correct content type for a file extension
        
        Args:
            file_ext (str): File extension
        Returns:
            str: Content type
        """
        content_types = {
            "pdf": "application/pdf",
            "rtf": "application/rtf",
            "txt": "text/plain",
            "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        }
        return content_types.get(file_ext, "application/octet-stream")

    def _get_kb_from_name(self, kb_name):
        """
        Validates the given file paths or directory path.
        
        Args:
            kb_name (str): Name of the Knowledge Base
        
        Returns:
            Knowledge BaseConfig: Knowledge Base Config object 
        """
        response = self.request(
            config=RequestConfig(
                method=HttpMethod.GET,
                url=self._base_url + "/" + Routes.knowledge_base_list.value,
                params={"search": kb_name},
            ),
            response_handler=KBResponseHandler,
        )
        data = response["result"].get("tableData")
        if not data:
            raise SDKException(f"Knowledge Base with name '{kb_name}' not found.")
        return KnowledgeBaseConfig(id=data[0].get("id"), name=data[0].get("name"))