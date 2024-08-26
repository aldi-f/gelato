from abc import ABC, abstractmethod
from typing import Optional
from pydantic import HttpUrl

class Base(ABC):
    def __init__(self, url: HttpUrl):
        self.url = url
        self.downloaded = False
        self.content = bytes()

    @property
    def download_url(self):
        return self.url
    
    @abstractmethod
    def download_video(self):
        pass

    @property
    def content_length(self) -> Optional[int]:
        return len(self.content)

    def save_video(self, filename: str):
        with open(filename, "wb") as f:
            f.write(self.content)

    