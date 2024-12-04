from copy import deepcopy
from dataclasses import dataclass
from typing import List

from fi.testcases.llm_test_case import LLMTestCase


@dataclass
class ConversationalTestCase:
    messages: List[LLMTestCase]

    def __post_init__(self):
        if len(self.messages) == 0:
            raise TypeError("'messages' must not be empty")

        copied_messages = []
        for message in self.messages:
            if not isinstance(message, LLMTestCase):
                raise TypeError("'messages' must be a list of `LLMTestCases`")
            copied_messages.append(deepcopy(message))

        self.messages = copied_messages
