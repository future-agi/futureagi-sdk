import time
import pandas as pd

from fi.client import Client
from fi.utils.types import Environments, ModelTypes
fi_client = Client(
    uri="https://dev.api.futureagi.com",
    api_key="8437d413519a4b7aad0a9d73bee01f2d",
    secret_key="880e66bafcb04352aaae824f8f2334cc",
)


response = fi_client.log(
    "rags-data",
    ModelTypes.GENERATIVE_LLM,
    Environments.PRODUCTION,
    "1.2",
    int(time.time()),
    {
        "chat_history": [
            {"role": "user", "content": "What element has the chemical symbol 'O'?", "context": [
                ["Oxygen is a chemical element with the symbol 'O'.", " It is essential for respiration in most living organisms."],
                ["Hydrogen is the lightest element.", " It has the chemical symbol 'H'."],
                ["Carbon is a chemical element with the symbol 'C'.", " It is the basis of all known life on Earth."]
            ]},
            {"role": "assistant",
             "content": "Oxygen."},
            {"role": "user", "content": "Who developed the theory of relativity?", "context": [
                ["The theory of relativity was developed by Albert Einstein.", " It revolutionized physics."],
                ["Quantum mechanics is a fundamental theory in physics.", " It describes physical phenomena at the scale of atoms and subatomic particles."],
                ["Classical mechanics is a branch of physics.", " It deals with the motion of bodies under the action of forces."]
            ]},
            {"role": "assistant",
             "content": "Albert Einstein"},
            {"role": "user", "content": "What is the largest planet in our solar system?", "context": [
                ["Jupiter is the largest planet in our solar system.", " It is a gas giant."],
                ["Mars is the fourth planet from the Sun.", " It is known as the Red Planet."],
                ["Earth is the third planet from the Sun.", " It is the only known planet to support life."]
            ]},
            {"role": "assistant",
             "content": "Earth"}
        ]
    }
).result()
print(response)