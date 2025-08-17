import logging
import tempfile
import requests

from yt_dlp import YoutubeDL
from websites.base import Base, VideoNotFound

logger = logging.getLogger(__name__)

class Reddit(Base):
    yt_params: dict = {
        "quiet": False,
        "no_warnings": True,
        "geo_bypass": True,
        "overwrites": True,
        "playlist_items": "1",
        "compat_opts": ["manifest-filesize-approx"],
        "format_sort": ["size:9.5M"],
    }
    def __init__(self, url: str):
        super().__init__(url)
        self.convert_to_mp4 = True

    @property
    def download_url(self) -> dict[str, str]:
        """
        Returns a dictionary with the video URL. 
        Mobile link doesn't work by default, so we use redirects to get the actual video URL.
        """
        res = requests.head(self.url, allow_redirects=True)
        if res.status_code != 200:
            raise VideoNotFound("Reddit video not found or inaccessible")
        
        real_url = res.url
        return {"video": real_url}

    @property
    def content_length_before(self) -> int:
        with YoutubeDL(self.yt_params) as ydl:
            info = ydl.extract_info(self.download_url["video"], download=False) or {}

        if "entries" in info:
            return info["entries"][0].get("filesize",0) or info["entries"][0].get("filesize_approx",0)
        return info.get("filesize",0) or info.get("filesize_approx",0)    
    
    @property
    def title(self) -> str:
        """
        Title of the video
        """
        with YoutubeDL(self.yt_params) as ydl:
            info = ydl.extract_info(self.download_url["video"], download=False) or {}
        
        if info.get("entries", []):
            text = info["entries"][0].get("title", "")
        else: 
            text = info.get("title", "")

        return "\n`" + text + "`"


    def download_video(self):
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_file:
            output_name = temp_file.name
            self.output_path.append(output_name)

        self.yt_params["outtmpl"]= output_name

        # download video
        with YoutubeDL(self.yt_params) as foo:
            foo.download([self.download_url["video"]])
