import os
import requests
import logging

from abc import ABC, abstractmethod
from pydantic import HttpUrl

logger = logging.getLogger(__name__)

class Base(ABC):
    def __init__(self, url: HttpUrl):
        self.url = url
        self.downloaded = False
        self.output_path = []

    @property
    def download_url(self):
        return self.url

    @property
    def content(self) -> bytes:
        if self.output_path:
            with open(self.output_path[-1], "rb") as file:
                data = file.read()
            
            return data
        raise ValueError("Output path is empty")


    @property
    def content_length_before(self) -> int:
        head_data = requests.head(self.download_url, allow_redirects=True).headers
        return int(head_data.get("Content-Length", 0))
    

    @property
    def content_length_after(self) -> int:
        return len(self.content)
    

    @abstractmethod
    def download_video(self):
        pass


    def save_video(self, filename: str):
        with open(filename, "wb") as f:
            f.write(self.content)


    def cleanup(self):
        return
        for path in self.output_path:
            os.remove(path)
