import ffmpeg
import logging
import tempfile

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
        "playlist_items": '1',
    }
    convert_to_mp4 = False

    @property
    def content_length_before(self) -> int:
        # try:
        with YoutubeDL(self.yt_params) as ydl:
            info = ydl.extract_info(self.download_url, download=False) or {}

        if "entries" in info:
            return info["entries"][0].get("filesize",0) or info["entries"][0].get("filesize_approx",0)
        return info.get("filesize",0) or info.get("filesize_approx",0)    
    
    @property
    def title(self) -> str:
        """
        Title of the video
        """
        with YoutubeDL(self.yt_params) as ydl:
            info = ydl.extract_info(self.download_url, download=False) or {}
        
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
            foo.download([self.download_url])
