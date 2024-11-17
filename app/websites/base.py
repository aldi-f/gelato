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
        """
        URL to download the video from
        """
        return self.url

    @property
    def content(self) -> bytes:
        """
        Content of the video in bytes
        """
        if self.output_path:
            with open(self.output_path[-1], "rb") as file:
                data = file.read()
            
            return data
        raise ValueError("Output path is empty")


    @property
    def content_length_before(self) -> int:
        """
        Content length of the video calculated before downloading. Will not be 100% accurate.
        """
        head_data = requests.head(self.download_url, allow_redirects=True).headers
        return int(head_data.get("Content-Length", 0))
    

    @property
    def content_length_after(self) -> int:
        """
        Content length of the video calculated after downloading. Will be 100% accurate.
        """
        return len(self.content)
    
    @property
    def resolution(self):
        """
        Resolution of the video in format (width, height)
        """
        if self.output_path:
            input_file = self.output_path[-1]
            probe = ffmpeg.probe(input_file)
            video_info = next(s for s in probe['streams'] if s['codec_type'] == 'video')
            width = int(video_info['width'])
            height = int(video_info['height'])
            return width, height
        raise ValueError("Output path is empty")

    @abstractmethod
    def download_video(self):
        pass

    def convert_video(self):
        pass

    def lower_resolution(self, new_height: int):
        """
        Lower the resolution of the video to specified height
        """
        input_file = self.output_path[-1]
        current_width, current_height = self.resolution

        # Add resolution scaling if current height > 480p
        if current_height > new_height:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_file:
                output_name = temp_file.name
                self.output_path.append(output_name)
            
            new_width = int((current_width * current_height) / new_height)
            new_width = new_width - (new_width % 2)
            vf = f'scale={new_width}:{new_height}'

            try:
                (ffmpeg
                .input(input_file)
                .output(output_name,
                        f='mp4',
                        vcodec=self._ffmpeg_codec,
                        crf=28,
                        vf=vf,
                        acodec='aac',
                        audio_bitrate='96k')
                .overwrite_output()
                .run(capture_stdout=True, capture_stderr=True))
            except ffmpeg.Error as e:
                print(f"FFmpeg error occurred: {e.stderr.decode()}")
                raise

    def compress_video_light(self):
        """
        Compress the video with light compression
        """
        input_file = self.output_path[-1]
        target_size_bytes = 10 * 1024 * 1024  # 10MB

        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_file:
            output_name = temp_file.name
            self.output_path.append(output_name)

        probe = ffmpeg.probe(input_file)
        duration = float(probe['format']['duration'])
        target_bitrate = int((target_size_bytes * 8) / duration * 0.95)

        try:
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
        except ffmpeg.Error as e:
            print(f"FFmpeg error occurred: {e.stderr.decode()}")
            raise

    def compress_video_medium(self):
        input_file = self.output_path[-1]
        target_size_bytes = 10 * 1024 * 1024
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_file:
            output_name = temp_file.name
            self.output_path.append(output_name)

        probe = ffmpeg.probe(input_file)
        duration = float(probe['format']['duration'])
        target_bitrate = int((target_size_bytes * 8) / duration * 0.95)

        try:
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
        except ffmpeg.Error as e:
            print(f"FFmpeg error occurred: {e.stderr.decode()}")
            raise

    def compress_video_maximum(self):
        input_file = self.output_path[-1]
        target_size_bytes = 10 * 1024 * 1024

        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_file:
            output_name = temp_file.name
            self.output_path.append(output_name)

        probe = ffmpeg.probe(input_file)
        duration = float(probe['format']['duration'])
        target_bitrate = int((target_size_bytes * 8) / duration * 0.95)

        try:
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
                    s='854x480')
            .overwrite_output()
            .run(capture_stdout=True, capture_stderr=True))
        except ffmpeg.Error as e:
            print(f"FFmpeg error occurred: {e.stderr.decode()}")
            raise


    def save_video(self, filename: str):
        with open(filename, "wb") as f:
            f.write(self.content)


    def cleanup(self):
        for path in self.output_path:
            os.remove(path)
