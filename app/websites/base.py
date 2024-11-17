import os
import requests
import logging
import ffmpeg
import tempfile

from abc import ABC, abstractmethod
from pydantic import HttpUrl

FFMPEG_CODEC = os.getenv("FFMPEG_CODEC", "libx264")
logger = logging.getLogger(__name__)

class Base(ABC):
    def __init__(self, url: HttpUrl):
        self.url = url
        self.downloaded = False
        self.output_path = []
        self._ffmpeg_codec = FFMPEG_CODEC
        self.convert_to_mp4 = False

    @property
    def download_url(self):
        return self.url

    @property
    def content(self) -> bytes:
        if self.output_path:
            with open(self.output_path[-1], "rb") as file:
                data = file.read()
            
            return data
        raise ValueError("Output path is empty")


    @property
    def content_length_before(self) -> int:
        head_data = requests.head(self.download_url, allow_redirects=True).headers
        return int(head_data.get("Content-Length", 0))
    

    @property
    def content_length_after(self) -> int:
        return len(self.content)
    

    @abstractmethod
    def download_video(self):
        pass


    def compress_video(self):
        input_file = self.output_path[-1]
        target_size_bytes = 10 * 1024 * 1024  # 10MB

        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_file:
            output_name = temp_file.name
            self.output_path.append(output_name)

        # Get video duration and properties
        probe = ffmpeg.probe(input_file)
        duration = float(probe['format']['duration'])
        
        # Calculate target bitrate (95% of theoretical maximum)
        target_bitrate = int((target_size_bytes * 8) / duration * 0.95)

        try:
            # First compression attempt - balanced settings
            (ffmpeg
            .input(input_file)
            .output(output_name,
                    f='mp4',
                    vcodec=self._ffmpeg_codec,
                    crf=28,
                    maxrate=f'{target_bitrate}',
                    bufsize=f'{target_bitrate//2}',
                    acodec='aac',
                    audio_bitrate='96k')
            .overwrite_output()
            .run(capture_stdout=True, capture_stderr=True))

            # If still too large, try stronger compression
            if os.path.getsize(output_name) > target_size_bytes:
                (ffmpeg
                .input(input_file)
                .output(output_name,
                        f='mp4',
                        vcodec=self._ffmpeg_codec,
                        crf=32,
                        maxrate=f'{target_bitrate}',
                        bufsize=f'{target_bitrate//2}',
                        preset='slow',
                        acodec='aac',
                        audio_bitrate='64k')
                .overwrite_output()
                .run(capture_stdout=True, capture_stderr=True))

                # Final attempt with maximum compression if still too large
                if os.path.getsize(output_name) > target_size_bytes:
                    (ffmpeg
                    .input(input_file)
                    .output(output_name,
                            f='mp4',
                            vcodec=self._ffmpeg_codec,
                            crf=35,
                            maxrate=f'{target_bitrate}',
                            bufsize=f'{target_bitrate//2}',
                            preset='veryslow',
                            acodec='aac',
                            audio_bitrate='32k',
                            s='854x480')  # Reduce resolution if needed
                    .overwrite_output()
                    .run(capture_stdout=True, capture_stderr=True))

        except ffmpeg.Error as e:
            print(f"FFmpeg error occurred: {e.stderr.decode()}")
            raise


    def save_video(self, filename: str):
        with open(filename, "wb") as f:
            f.write(self.content)


    def cleanup(self):
        return
        for path in self.output_path:
            os.remove(path)
