import logging
import tempfile

from yt_dlp import YoutubeDL
from websites.base import Base

logger = logging.getLogger(__name__)

class NineGAG(Base):
    yt_params: dict[str,bool|str|int]= {
        "quiet": True,
        "no_warnings": True,
        "geo_bypass": True,
        "overwrites": True,
    }
    
    def __init__(self, url: str):
        super().__init__(url)
        self.convert_to_mp4 = True

    @property
    def title(self) -> str:
        try:
            page_url = "https://9gag.com/gag"
            video_id = self.url.split('/')[-1].split('_')[0]
            with YoutubeDL(self.yt_params) as foo:
                info = foo.extract_info(f"{page_url}/{video_id}", download=False) or {}
            return "\n`" + info.get("title", "") + "`"
        except Exception as e:
            logger.error(e)
            return ""


    def download_video(self):
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_file:
            output_name = temp_file.name
            self.output_path.append(output_name)

        self.yt_params["outtmpl"]= output_name
        # download video
        with YoutubeDL(self.yt_params) as foo:
            foo.download([self.download_url["video"]])


