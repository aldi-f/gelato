import tempfile

from yt_dlp import YoutubeDL

from websites.base import Base


class Youtube(Base):
    _ffmpeg_codec = "libx264"
    yt_params: dict[str,bool|str|int] = {
        "quiet": True,
        "no_warnings": True,
        "geo_bypass": True,
        "overwrites": True,
        "format": "bv*[ext=mp4][filesize<9M]+ba[filesize<1M]"
    }

    @property
    def content_length_before(self) -> int:
        try:
            with YoutubeDL(self.yt_params) as ydl:
                info = ydl.extract_info(self.url, download=False)
        except:
            # try again with no format
            self.yt_params["format"] = "bv*+ba/b"
            with YoutubeDL(self.yt_params) as ydl:
                info = ydl.extract_info(self.url, download=False)

        return info.get("filesize") or info.get("filesize_approx")    


    def download_video(self):
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_file:
            output_name = temp_file.name
            self.output_path.append(output_name)

        self.yt_params["outtmpl"]= output_name

        # download video
        with YoutubeDL(self.yt_params) as foo:
            foo.download([self.download_url])

