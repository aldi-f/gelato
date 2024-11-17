import tempfile

from yt_dlp import YoutubeDL

import ffmpeg

from websites.base import Base


class Youtube(Base):
    _ffmpeg_codec = "libx264"
    yt_params: dict[str,bool|str|int] = {
        # "quiet": True,
        # "no_warnings": True,
        "logtostderr": True,
        "geo_bypass": True,
        "overwrites": True,
        "format": "bv*+ba/b"
    }

    @property
    def content_length_before(self) -> int:
        # try:
        with YoutubeDL(self.yt_params) as ydl:
            info = ydl.extract_info(self.download_url, download=False) or {}
        # except:
        #     # try again with no format
        #     self.yt_params["format"] = "bv*+ba/b"
        #     with YoutubeDL(self.yt_params) as ydl:
        #         info = ydl.extract_info(self.download_url, download=False)

        return info.get("filesize",0) or info.get("filesize_approx",0)    


    def download_video(self):
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_file:
            output_name = temp_file.name
            self.output_path.append(output_name)

        self.yt_params["outtmpl"]= output_name

        # download video
        with YoutubeDL(self.yt_params) as foo:
            foo.download([self.download_url])

