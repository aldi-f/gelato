import ffmpeg
import logging
import tempfile

from bs4 import BeautifulSoup
from yt_dlp import YoutubeDL

from websites.base import Base

logger = logging.getLogger(__name__)

class Twitter(Base):
    yt_params: dict[str,bool|str|int]= {
        'format': 'best',
        'quiet': False,
        'no_warnings': True,
        'geo_bypass': True,
        "overwrites": True,
    }
    convert_to_mp4 = False

    @property
    def content_length_before(self) -> int:
        # try:
        with YoutubeDL(self.yt_params) as ydl:
            info = ydl.extract_info(self.download_url, download=False) or {}

        return info.get("filesize",0) or info.get("filesize_approx",0)    

    def download_video(self):
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_file:
            output_name = temp_file.name
            self.output_path.append(output_name)

        self.yt_params["outtmpl"]= output_name

        # download video
        with YoutubeDL(self.yt_params) as foo:
            foo.download([self.download_url])
