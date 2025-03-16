import os
import glob
import requests
import logging
import ffmpeg
import tempfile
import asyncio
from abc import ABC, abstractmethod
from urllib.parse import urlparse

FFMPEG_CODEC = os.getenv("FFMPEG_CODEC", "libx264")
FFMPEG_HW_CODEC = os.getenv("FFMPEG_HW_CODEC", "h264_qsv")
logger = logging.getLogger(__name__)


class RestrictedVideo(Exception):
    pass


class Base(ABC):
    def __init__(self, url: str):
        # Validate URL
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            raise ValueError(f"Invalid URL: {url}")
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


    @property
    def title(self) -> str:
        """
        Title of the video
        """
        return ""

    @property
    def vcodec(self) -> str:
        """
        Codec of the video
        """
        input_file = self.output_path[-1]
        probe = ffmpeg.probe(input_file)
        video_stream = next((s for s in probe['streams'] if s['codec_type'] == 'video'), None)
        
        if video_stream and 'codec_name' in video_stream:
            codec = video_stream['codec_name']
        else:
            # Fallback if codec_name isn't available in the probe
            codec = probe['format']['format_name']
        return codec
    
    @abstractmethod
    def download_video(self):
        pass

    def _get_video_bitrate(self, file_path: str) -> int:
        probe = ffmpeg.probe(file_path)
        video_stream = next((s for s in probe['streams'] if s['codec_type'] == 'video'), None)
        
        if video_stream and 'bit_rate' in video_stream:
            original_bitrate = int(video_stream['bit_rate'])
        else:
            # Fallback if bit_rate isn't available in the probe
            original_bitrate = int(float(probe['format']['bit_rate'])) 
        return original_bitrate
    

    def _get_required_bitrate(self, file_path: str, target_size_megabytes: float=9) -> int:
        """
        Calculate the required bitrate for the video to be of target size
        """
        target_size_bytes = target_size_megabytes * 1024 * 1024
        probe = ffmpeg.probe(file_path)
        duration = float(probe['format']['duration'])
        target_bitrate = int(((target_size_bytes * 8) / duration) * 0.95) # 5% overhead

        return target_bitrate

    async def lower_resolution(self, new_height: int):
        """
        Lower the resolution of the video to specified height asynchronously
        """
        input_file = self.output_path[-1]
        current_width, current_height = self.resolution

        # Add resolution scaling if current height > 480p
        if current_height > new_height:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_file:
                output_name = temp_file.name
                self.output_path.append(output_name)
            
            aspect_ratio = current_width / current_height
            new_width = int(new_height * aspect_ratio)
            new_width = new_width - (new_width % 2) 
            vf = f'scale_qsv=w={new_width}:h={new_height}'
            
            # Calculate new bitrate proportional to resolution change (area ratio)
            area_ratio = (new_width * new_height) / (current_width * current_height)
            original_bitrate = self._get_video_bitrate(input_file)
            new_bitrate = int(original_bitrate * area_ratio)

            cmd = [
                'ffmpeg',
                '-hwaccel', 'qsv',
                '-i', input_file,
                '-c:v', FFMPEG_HW_CODEC,
                '-b:v', str(new_bitrate),
                '-vf', vf,
                '-acodec', 'copy',
                '-f', 'mp4',
                '-y',
                output_name
            ]

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                raise Exception(f"FFmpeg error: {stderr.decode()}")

    async def compress_video_hardware_light(self):
        """
        Compress the video with light hardware encoder
        """
        input_file = self.output_path[-1]

        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_file:
            output_name = temp_file.name
            self.output_path.append(output_name)

        target_bitrate = self._get_required_bitrate(input_file)

        try:
            # Construct ffmpeg command
            cmd = [
                'ffmpeg',
                '-hwaccel', 'qsv',
                '-i', input_file,
                '-c:v', FFMPEG_HW_CODEC,
                '-b:v', str(target_bitrate),
                '-maxrate', str(target_bitrate),
                '-bufsize', str(target_bitrate//2),
                '-acodec', 'copy',
                '-f', 'mp4',
                '-y',  # Overwrite output
                output_name
            ]

            # Create and run subprocess
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            # Wait for the subprocess to complete
            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                print(f"FFmpeg error occurred: {stderr.decode()}")
                raise Exception('FFmpeg failed', stderr.decode())

        except Exception as e:
            print(f"Error during compression: {str(e)}")
            raise

    async def compress_video_hardware_medium(self):
        """
        Compress the video with medium hardware encoder
        """
        input_file = self.output_path[-1]

        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_file:
            output_name = temp_file.name
            self.output_path.append(output_name)

        target_bitrate = self._get_required_bitrate(input_file)
        target_bitrate = int(target_bitrate * 0.90) 

        try:
            # Construct ffmpeg command
            cmd = [
                'ffmpeg',
                '-hwaccel', 'qsv',
                '-i', input_file,
                '-c:v', FFMPEG_HW_CODEC,
                '-b:v', str(target_bitrate),
                '-maxrate', str(target_bitrate),
                '-bufsize', str(target_bitrate//2),
                '-acodec', 'copy',
                '-f', 'mp4',
                '-y',  # Overwrite output
                output_name
            ]

            # Create and run subprocess
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            # Wait for the subprocess to complete
            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                print(f"FFmpeg error occurred: {stderr.decode()}")
                raise Exception('FFmpeg failed', stderr.decode())

        except Exception as e:
            print(f"Error during compression: {str(e)}")
            raise


    async def compress_video_light(self):
        """
        Compress the video with light compression (async version)
        """
        input_file = self.output_path[-1]

        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_file:
            output_name = temp_file.name
            self.output_path.append(output_name)

        target_bitrate = self._get_required_bitrate(input_file)
        target_bitrate = int(target_bitrate * 0.90) 

        try:
            # Construct ffmpeg command
            cmd = [
                'ffmpeg',
                '-i', input_file,
                '-vcodec', self._ffmpeg_codec,
                '-crf', '28',
                '-maxrate', str(target_bitrate),
                '-bufsize', str(target_bitrate),
                '-acodec', 'copy',
                '-f', 'mp4',
                '-y',  # Overwrite output
                output_name
            ]

            # Create and run subprocess
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            # Wait for the subprocess to complete
            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                print(f"FFmpeg error occurred: {stderr.decode()}")
                raise Exception('FFmpeg failed', stderr.decode())

        except Exception as e:
            print(f"Error during compression: {str(e)}")
            raise

    async def compress_video_medium(self):
        """
        Compress the video with medium compression (async version)
        """
        input_file = self.output_path[-1]
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_file:
            output_name = temp_file.name
            self.output_path.append(output_name)

        target_bitrate = self._get_required_bitrate(input_file)
        target_bitrate = int(target_bitrate * 0.85) # 15% reduction

        try:
            cmd = [
                'ffmpeg',
                '-i', input_file,
                '-vcodec', self._ffmpeg_codec,
                '-crf', '30',
                '-maxrate', str(target_bitrate),
                '-bufsize', str(target_bitrate),
                '-preset', 'slow',
                '-acodec', 'copy',
                '-f', 'mp4',
                '-y',  # Overwrite output
                output_name
            ]

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            # Wait for the subprocess to complete
            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                print(f"FFmpeg error occurred: {stderr.decode()}")
                raise Exception('FFmpeg failed', stderr.decode())

        except Exception as e:
            print(f"Error during compression: {str(e)}")
            raise

    async def compress_video_maximum(self):
        """
        Compress the video with maximum compression (async version)
        """
        input_file = self.output_path[-1]

        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_file:
            output_name = temp_file.name
            self.output_path.append(output_name)

        target_bitrate = self._get_required_bitrate(input_file)
        target_bitrate = int(target_bitrate * 0.80) # 20% reduction

        try:
            cmd = [
                'ffmpeg',
                '-i', input_file,
                '-vcodec', self._ffmpeg_codec,
                '-crf', '35',
                '-maxrate', str(target_bitrate),
                '-bufsize', str(target_bitrate),
                '-preset', 'veryslow',
                '-acodec', 'aac',
                '-b:a', '96k',
                '-f', 'mp4',
                '-y',
                output_name
            ]

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                print(f"FFmpeg error occurred: {stderr.decode()}")
                raise Exception('FFmpeg failed', stderr.decode())

        except Exception as e:
            print(f"Error during compression: {str(e)}")
            raise

    async def convert_video(self):
        input_file = self.output_path[-1]
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_file:
            output_name = temp_file.name
            self.output_path.append(output_name)

        try:
            cmd = [
                'ffmpeg',
                '-i', input_file,
                '-c:v', FFMPEG_HW_CODEC,
                '-f', 'mp4',
                '-y',
                output_name
            ]

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                print(f"FFmpeg error occurred: {stderr.decode()}")
                raise Exception('FFmpeg failed', stderr.decode())

        except Exception as e:
            print(f"Error during conversion: {str(e)}")
            raise


    def save_video(self, filename: str):
        with open(filename, "wb") as f:
            f.write(self.content)


    def cleanup(self):
        for path in self.output_path:
            base_path = os.path.splitext(path)[0]
            
            matching_files = glob.glob(f"{base_path}.*")
            
            for file in matching_files:
                try:
                    os.remove(file)
                except FileNotFoundError:
                    pass
