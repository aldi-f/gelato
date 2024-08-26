from app.websites.base import Base
import json
import requests
from bs4 import BeautifulSoup

class NineGAG(Base):

    @property
    def download_url(self):
        if self.url.startswith("https://9gag.com/gag/"): # mobile 9gag
            mobile = requests.get(self.url)
            soup = BeautifulSoup(mobile.text)
            contents = json.loads(soup.find("script", type="application/ld+json").text)
            url = contents['video']['contentUrl'] # real link here

        return self.url 


    def download_video(self):...
        







    # def __init__(self, url: HttpUrl):
    #     self.url = url
    #     self.downloaded = False
    #     self.content = bytes()

    # @abstractmethod
    # def download_video(self):
    #     pass

    # @property
    # def content_length(self) -> Optional[int]:
    #     return len(self.content)


    # def save_video(self, filename: str):
    #     with open(filename, "wb") as f:
    #         f.write(self.content)
