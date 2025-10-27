import os
import uuid

import pytest

from fi.prompt import Prompt, PromptTemplate, SystemMessage, UserMessage, AssistantMessage


@pytest.fixture
def prompt_template():
    """Create a test prompt template with unique name"""
    unique_name = f"test_template_{uuid.uuid4().hex[:8]}"
    return PromptTemplate(
        name=unique_name,
        description="Test template for SDK testing",
        messages=[
            SystemMessage(content="You are a helpful assistant."),
            UserMessage(
                content=(
                    "Please write a detailed paragraph introducing {{name}}, "
                    "who is {{age}} years old, lives in {{city}}, loves the color {{color}}, "
                    "and enjoys {{hobby}}. Make the paragraph engaging and unique."
                )
            ),
        ],
        variable_names={
            "name": ["Alice", "Bob", "Charlie"],
            "age": ["25", "30", "35"],
            "city": ["New York", "Paris", "Tokyo"],
            "color": ["blue", "red", "green"],
            "hobby": ["painting", "cycling", "reading"]
        },
        model_configuration={
            "model": "gpt-4o",
            "temperature": 0.5,
            "max_tokens": 1000,
            "top_p": 1,
            "frequency_penalty": 0,
            "presence_penalty": 0,
            "stop": None,
        }
    )


@pytest.fixture
def prompt_client(prompt_template):
    return Prompt(template=prompt_template)


def test_prompt_lifecycle(prompt_client):
    """Test complete prompt template lifecycle: create, generate, improve, run, and cleanup"""

    try:
        # Create template
        client = prompt_client.create()
        assert client.template.name == prompt_client.template.name
        assert client.template.id is not None

        # Test fetching template version history
        version_history = client._fetch_template_version_history()
        assert version_history is not None

        # Commit current draft and create a follow-up draft version
        client.commit_current_version(message="initial commit", set_default=True)
        old_version = client.template.version

        # Modify template in-place and save draft
        client.template.description = "updated description"
        assert client.save_current_draft() is True

        # Build a separate PromptTemplate object to update via create_new_version
        updated_tpl = PromptTemplate(
            name=client.template.name,
            messages=client.template.messages,
            description="second update",
            variable_names=client.template.variable_names,
            model_configuration=client.template.model_configuration,
        )

        client.create_new_version(template=updated_tpl)
        assert client.template.version != old_version

        # Fetch version history via public helper
        history = client.list_template_versions()
        assert len(history) >= 2

    except ValueError as e:
        if "template_not_found" in str(e):
            pytest.skip("Server missing required template configuration")
        raise
    finally:
        # Cleanup - Delete template
        if hasattr(client, "delete") and callable(client.delete):
            client.delete()
            assert client.template is None
