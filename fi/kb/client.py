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
        else:
            response.raise_for_status()

class KnowledgeBase(APIKeyAuth):

    def __init__(
        self,
        kbase: Optional[KnowledgeBaseConfig] = None,
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
        self.kb = None
        if kbase and not kbase.id:
            try:
                self.kb = self._get_kb_from_name(kbase.name)
            except Exception:
                raise SDKException("Knowledge Base not found in backend. Create a new knowledge base before running.")
        else:
            self.kb = kbase
            if self.kb and self.kb.id:
                raise SDKException("Knowledge Base already exists. Please delete the existing knowledge base before running.")
        
    def update_kb(self, name : Optional[str] = None, file_paths: Optional[Union[str, List[str]]] = []):
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
            
            if not self.kb or not self.kb.id:
                raise SDKException("No existing Knowledge Base configured or ID is missing. Please create or load a knowledge base first.")

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
            
            data = {}
            if name or self.kb:
                data.update({
                    "name": self.kb.name if not name else name,
                    "kb_id": str(self.kb.id)
                })
            
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

    def delete_files_from_kb(self, file_names: List[str]):
        """
        Delete files from the Knowledge Base.
        
        Args:
            file_names List[str]: List of file names to be deleted
        
        Returns:
            self for chaining
        """
        try:
            if not self.kb or not self.kb.id:
                raise SDKException("No knowledge base provided or configured. Please provide a knowledge base before running.")
                
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

    def delete_kb(self, kb_ids : Optional[Union[str, List[str]]] = None):
        """
        Delete a Knowledge Base and return the Knowledge Base client.
        
        Args:
            name Optional[str]: Name of the Knowledge Base
            kb_ids Optional[Union[str, List[str]]]: List of kb_ids to delete
        
        """
        try:        
            target_kb_ids_to_delete = []
            if kb_ids:
                if isinstance(kb_ids, str):
                    target_kb_ids_to_delete = [kb_ids]
                elif isinstance(kb_ids, list):
                    target_kb_ids_to_delete = [str(kb_id) for kb_id in kb_ids]
                else:
                    raise SDKException("kb_ids must be a string or a list of strings.")
            elif self.kb and self.kb.id:
                target_kb_ids_to_delete = [str(self.kb.id)]
            else:
                raise SDKException("No knowledge base ID provided and no current knowledge base is configured.")
            
            method = HttpMethod.DELETE
            url = self._base_url + "/" + Routes.knowledge_base.value       
            json_payload = {
                "kb_ids": target_kb_ids_to_delete
            }
            
            response = self.request(
                config=RequestConfig(
                    method=method,
                    url=url,
                    json=json_payload,
                    headers={'Content-Type': 'application/json'}
                ),
                response_handler=KBResponseHandler,
            )

            if self.kb and self.kb.id and str(self.kb.id) in target_kb_ids_to_delete:
                self.kb = None
            
            return self
        
        except SDKException:
            raise
        except Exception as e:
            raise SDKException("Failed to delete Knowledge Base(s) due to an unexpected error.", cause=e)

    def create_kb(self, name : Optional[str] = None, file_paths : Optional[Union[str, List[str]]] = []):
        """
        Create a Knowledge Base and return the Knowledge Base client.
        
        Args:
            name Optional[str]: Name of the Knowledge Base
            file_paths Optional[Union[str, List[str]]]: List of file paths or a directory path
        
        Returns:
            self for chaining
        """
        import requests
        
        if self.kb and self.kb.id:
            raise SDKException(
                f"Cannot create Knowledge Base: an existing Knowledge Base '{self.kb.name}' (ID: {self.kb.id}) is already configured for this client instance."
            )
        
        final_kb_name = name
        if not final_kb_name:
            if self.kb and self.kb.name:
                final_kb_name = self.kb.name
            else:
                final_kb_name = "Unnamed KB"

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
                    files=parsed_result_data.get("fileIds", [])
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
        data = response['result'].get('tableData')
        return KnowledgeBaseConfig(id=data[0].get("id"), name= data[0].get("name"))