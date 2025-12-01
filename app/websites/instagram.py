import logging
import re
import tempfile

import requests
from websites.base import Base
from yt_dlp import YoutubeDL

logger = logging.getLogger(__name__)


class Instagram(Base):
    _download_url = None
    yt_params: dict[str, bool | str | int] = {
        "format": "best",
        "quiet": False,
        "no_warnings": True,
        "geo_bypass": True,
        "overwrites": True,
        "playlist_items": "1",
    }

    def __init__(self, url: str):
        super().__init__(url)
        self.async_download = False

    def find_reel_id(self):
        # Instagram share link is different from actual video
        # Redirect fixes it
        # So catch this to make sure we are pulling the correct one
        real_url = requests.head(self.url, allow_redirects=True).url
        pattern = r"https?://(?:www\.)?instagram\.com/(?:reel|p)/([^/?]+)"
        match = re.search(pattern, real_url)
        if match:
            return match.group(1)

    @property
    def content_length_before(self) -> int:
        # try:
        with YoutubeDL(self.yt_params) as ydl:
            info = ydl.extract_info(self.download_url["video"], download=False) or {}

        test_url = info.get("url")
        if test_url:
            response = requests.head(test_url, allow_redirects=True)
            return int(response.headers.get("Content-Length", 0))

        if "entries" in info:
            return info["entries"][0].get("filesize", 0) or info["entries"][0].get(
                "filesize_approx", 0
            )

        return info.get("filesize", 0) or info.get("filesize_approx", 0)

    def download_video(self):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_file:
            output_name = temp_file.name
            self.output_path.append(output_name)

        self.yt_params["outtmpl"] = output_name

        # download video
        with YoutubeDL(self.yt_params) as foo:
            foo.download([self.download_url["video"]])
