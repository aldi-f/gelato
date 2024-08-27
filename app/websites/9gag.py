import json
import ffmpeg
import requests
import tempfile

from bs4 import BeautifulSoup
from yt_dlp import YoutubeDL

from app.websites.base import Base


class NineGAG(Base):
    _ffmpeg_codec = "libx264"

    @property
    def download_url(self):
        if self.url.startswith("https://9gag.com/gag/"): # mobile 9gag
            mobile = requests.get(self.url)
            soup = BeautifulSoup(mobile.text)
            contents = json.loads(soup.find("script", type="application/ld+json").text)

            return contents['video']['contentUrl'] # real link here

        return self.url 


    def download_video(self):
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_file:
            output_name = temp_file.name
            self.output_path.append(output_name)

        ydl_opts = {
            'outtmpl': output_name,
            "quiet": True,
            "no_warnings": True,
            "geo_bypass": True,
        }

        # download video
        with YoutubeDL(ydl_opts) as foo:
            foo.download([self.download_url])

        # extra steps after downloading
        self._convert_to_mp4()
        # self._compress()


    def _convert_to_mp4(self):
        input_file = self.output_path[-1]
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_file:
            output_name = temp_file.name
            self.output_path.append(output_name)

        (ffmpeg
        .input(input_file)
        .output(output_name, f='mp4', vcodec=self._ffmpeg_codec)
        .run())


    def _compress(self):
        input_file = self.output_path[-1]
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_file:
            output_name = temp_file.name
            self.output_path.append(output_name)

        # compress logic here
