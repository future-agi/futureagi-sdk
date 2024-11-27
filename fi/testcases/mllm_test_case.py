import os
from typing import Optional, Union
from urllib.parse import urlparse

from pydantic import BaseModel

from fi.testcases.general import TestCase


class MLLMImage(BaseModel):
    url: str
    local: Optional[bool] = None

    def __post_init__(self):
        if self.local is None:
            self.local = self.is_local_path(self.url)
        if self.local:
            raise ValueError("Local images are not supported yet")

    @staticmethod
    def is_local_path(url):
        # Parse the URL
        parsed_url = urlparse(url)

        # Check if it's a file scheme or an empty scheme with a local path
        if parsed_url.scheme == "file" or parsed_url.scheme == "":
            # Check if the path exists on the filesystem
            return os.path.exists(parsed_url.path)

        return False


class MLLMTestCase(TestCase):
    image_url: Optional[Union[str, MLLMImage]] = None
    input_image_url: Optional[Union[str, MLLMImage]] = None
    output_image_url: Optional[Union[str, MLLMImage]] = None
