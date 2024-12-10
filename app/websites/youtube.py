import tempfile

from yt_dlp import YoutubeDL

import ffmpeg

from websites.base import Base


class Youtube(Base):
    _ffmpeg_codec = "libx264"
    yt_params = {
        "quiet": True,
        "no_warnings": True,
        "geo_bypass": True,
        "overwrites": True,
        "format_sort": ["size:10M", "ext:mp4:m4a", "vcodec:h264"],
        # "format": "bv*+ba/b",
    }

    @property
    def content_length_before(self) -> int:
        with YoutubeDL(self.yt_params) as ydl:
            info = ydl.extract_info(self.download_url, download=False) or {}

        return info.get("filesize",0) or info.get("filesize_approx",0)    

    @property
    def title(self) -> str:
        """
        Title of the video
        """
        with YoutubeDL(self.yt_params) as ydl:
            info = ydl.extract_info(self.download_url, download=False) or {}

        return "\n`" + info.get("title", "") + "`"
    
    def download_video(self):
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            output_name = temp_file.name
            self.output_path.append(output_name)

        self.yt_params["outtmpl"] = output_name + ".%(ext)s"

        # download video
        with YoutubeDL(self.yt_params) as ydl:
            info = ydl.extract_info(self.download_url, download=True)
            # Get actual downloaded file path
            downloaded_file = ydl.prepare_filename(info)
            self.output_path.append(downloaded_file)
