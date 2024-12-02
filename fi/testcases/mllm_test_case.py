import base64
import os
from typing import Optional, Union
from urllib.parse import urlparse

from pydantic import BaseModel

from fi.testcases.general import TestCase


class MLLMImage(BaseModel):
    url: str
    local: Optional[bool] = None

    def model_post_init(self, __context) -> None:
        if self.local is None:
            self.local = self.is_local_path(self.url)
        if self.local:
            self.url = self._convert_to_base64(self.url)

    @staticmethod
    def is_local_path(url):
        # Parse the URL
        parsed_url = urlparse(url)

        # Check if it's a file scheme or an empty scheme with a local path
        if parsed_url.scheme == "file" or parsed_url.scheme == "":
            # Check if the path exists on the filesystem
            return os.path.exists(parsed_url.path)

        return False

    def _convert_to_base64(self, path: str) -> str:
        with open(path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode("utf-8")
            return f"data:image/jpeg;base64,{encoded_string}"


class MLLMTestCase(TestCase):
    image_url: Optional[Union[str, MLLMImage]] = None
    input_image_url: Optional[Union[str, MLLMImage]] = None
    output_image_url: Optional[Union[str, MLLMImage]] = None

    def model_post_init(self, __context) -> None:
        if isinstance(self.image_url, str):
            self.image_url = MLLMImage(url=self.image_url).url
        elif isinstance(self.image_url, MLLMImage):
            self.image_url = self.image_url.url

        if isinstance(self.input_image_url, str):
            self.input_image_url = MLLMImage(url=self.input_image_url).url
        elif isinstance(self.input_image_url, MLLMImage):
            self.input_image_url = self.input_image_url.url

        if isinstance(self.output_image_url, str):
            self.output_image_url = MLLMImage(url=self.output_image_url).url
        elif isinstance(self.output_image_url, MLLMImage):
            self.output_image_url = self.output_image_url.url
