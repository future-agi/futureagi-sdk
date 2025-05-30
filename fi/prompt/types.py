import uuid
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, field_validator


# Base class for all messages
class MessageBase(BaseModel):
    role: str
    content: Union[str, List[Dict[str, Any]]]


# UserMessage class with variable handling
class UserMessage(MessageBase):
    role: str = "user"
    content: Union[str, List[Dict[str, Any]]]
    variable_names: Optional[List[str]] = []

    @field_validator("content")
    def validate_content(
        cls, v: Union[str, List[Dict[str, Any]]]
    ) -> Union[str, List[Dict[str, Any]]]:
        """Validate user message content."""
        if not v.strip():
            raise ValueError("Message content cannot be empty.")
        return v.strip()

    def model_post_init(self, __context: Any) -> None:
        """Initialize variable names by inferring them from the content if not already set."""
        if self.variable_names == []:
            # Extract variable names from content by looking for {{name}} patterns
            content = self.content
            var_names = []
            parts = content.split("{{")
            for part in parts[1:]:  # Skip first part before any {{
                if "}}" in part:
                    var_name = part.split("}}")[0].strip()
                    var_names.append(var_name)
            self.variable_names = var_names


# SystemMessage class
class SystemMessage(MessageBase):
    role: str = "system"
    content: Union[str, List[Dict[str, Any]]]

    @field_validator("content")
    def validate_content(
        cls, v: Union[str, List[Dict[str, Any]]]
    ) -> Union[str, List[Dict[str, Any]]]:
        """Validate system message content."""
        if not v.strip():
            raise ValueError("Message content cannot be empty.")
        return v.strip()


# AssistantMessage class
class AssistantMessage(MessageBase):
    role: str = "assistant"
    content: Union[str, List[Dict[str, Any]]]

    @field_validator("content")
    def validate_content(
        cls, v: Union[str, List[Dict[str, Any]]]
    ) -> Union[str, List[Dict[str, Any]]]:
        """Validate assistant message content."""
        if not v.strip():
            raise ValueError("Message content cannot be empty.")
        return v.strip()


class ModelConfig(BaseModel):
    model_name: str = "gpt-4o-mini"
    temperature: Optional[float] = Field(default=0.7, ge=0, le=2)
    frequency_penalty: Optional[float] = Field(default=0, ge=-2, le=2)
    presence_penalty: Optional[float] = Field(default=0, ge=-2, le=2)
    max_tokens: Optional[int] = Field(default=1000, gt=0)
    top_p: Optional[float] = Field(default=1.0, ge=0, le=1)
    response_format: Optional[dict] = None
    tool_choice: Optional[str] = None
    tools: Optional[List[dict]] = None

    class Config:
        frozen = True


class PromptTemplate(BaseModel):
    id: Optional[uuid.UUID] = None
    name: str
    messages: Optional[List[MessageBase]] = []
    model_configuration: Optional[ModelConfig] = ModelConfig()
    variable_names: Optional[Dict[str, List[str]]] = {}
    description: Optional[str] = None
    version: Optional[str] = None
    is_default: bool = True
    evaluation_configs: Optional[List[Dict]] = None
    status: Optional[str] = None
    error_message: Optional[str] = None

    @field_validator("name")
    def validate_name(cls, v: str) -> str:
        """Ensure name is valid."""
        if not v.strip():
            raise ValueError("Prompt name cannot be empty.")
        if len(v) > 255:
            raise ValueError("Prompt name is too long (max 255 characters).")
        return v.strip()

    def model_post_init(self, __context: Any) -> None:
        """Initialize variable names by inferring them from the content if not already set."""
        if self.variable_names == {}:
            # extract variable names from messages
            for message in self.messages:
                if isinstance(message, UserMessage):
                    for var_name in message.variable_names:
                        if var_name not in self.variable_names:
                            self.variable_names[var_name] = []
