import time

import pytest

from fi.client import Client
from fi.utils.types import Environments, ModelTypes


@pytest.fixture
def fi_client():
    return Client()


def test_log_rag_data(fi_client):

    # Test case 1: Theory of relativity
    response = fi_client.log(
        "rag-data",
        ModelTypes.GENERATIVE_LLM,
        Environments.PRODUCTION,
        "1.2",
        int(time.time()),
        {
            "chat_history": [
                {
                    "role": "user",
                    "content": "Who developed the theory of relativity?",
                    "context": [
                        [
                            "The theory of relativity was developed by Albert Einstein.",
                            " It revolutionized physics.",
                        ]
                    ],
                }
            ]
        },
    )
    assert response["status"] == "success"

    # Test case 2: Quantum mechanics
    response = fi_client.log(
        "rag-data",
        ModelTypes.GENERATIVE_LLM,
        Environments.PRODUCTION,
        "1.2",
        int(time.time()),
        {
            "chat_history": [
                {
                    "role": "user",
                    "content": "What is quantum mechanics?",
                    "context": [
                        [
                            "Quantum mechanics is a fundamental theory in physics.",
                            " It describes physical phenomena at the scale of atoms and subatomic particles.",
                        ]
                    ],
                }
            ]
        },
    )
    assert response["status"] == "success"

    # Test case 3: Classical mechanics
    response = fi_client.log(
        "rag-data",
        ModelTypes.GENERATIVE_LLM,
        Environments.PRODUCTION,
        "1.2",
        int(time.time()),
        {
            "chat_history": [
                {
                    "role": "user",
                    "content": "What is classical mechanics?",
                    "context": [
                        [
                            "Classical mechanics is a branch of physics.",
                            " It deals with the motion of bodies under the action of forces.",
                        ]
                    ],
                }
            ]
        },
    )
    assert response["status"] == "success"
