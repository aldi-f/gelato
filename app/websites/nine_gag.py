import ffmpeg
import logging
import tempfile

from bs4 import BeautifulSoup
from yt_dlp import YoutubeDL

from websites.base import Base

logger = logging.getLogger(__name__)

class NineGAG(Base):
    yt_params: dict[str,bool|str|int]= {
        # "quiet": True,
        # "no_warnings": True,
        "geo_bypass": True,
        "overwrites": True,
    }
    convert_to_mp4 = True
    
    @property
    def download_url(self):
        # if self.url.startswith("https://9gag.com/gag/"): # mobile 9gag
        #     mobile = requests.get(self.url)
        #     soup = BeautifulSoup(mobile.text)
        #     contents = json.loads(soup.find("script", type="application/ld+json").text)

        #     return contents['video']['contentUrl'] # real link here

        return self.url 


    def download_video(self):
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_file:
            output_name = temp_file.name
            self.output_path.append(output_name)

        self.yt_params["outtmpl"]= output_name
        # download video
        with YoutubeDL(self.yt_params) as foo:
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
        .overwrite_output()
        .run())


    # def compress_video(self):
    #     input_file = self.output_path[-1]
    #     with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_file:
    #         output_name = temp_file.name
    #         self.output_path.append(output_name)

    #     # compress logic here