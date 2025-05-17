import re
import os
import asyncio 
import logging
import random
import requests
import tempfile

from camoufox import AsyncCamoufox
from websites.base import Base, VideoNotFound

PLAYWRIGHT_HOST = os.getenv("PLAYWRIGHT_HOST", "ws://127.0.0.1:3000/")

logger = logging.getLogger(__name__)


class Instagram(Base):
    _download_url = None

    def __init__(self, url: str):
        super().__init__(url)
        self.async_download = True
        
    def find_reel_id(self):
        # Instagram share link is different from actual video
        # Redirect fixes it
        # So catch this to make sure we are pulling the correct one
        real_url = requests.head(self.url, allow_redirects=True).url
        pattern = r'https?://(?:www\.)?instagram\.com/(?:reel|p)/([^/?]+)'
        match = re.search(pattern, real_url)
        if match:
            return match.group(1)

    async def get_download_url(self):
        # Try to get the video URL using Playwright CamouFox
        async with AsyncCamoufox(
            headless=True
        ) as browser:
            page = await browser.new_page()

            videos = []
            audios = []
            async def handle_response(response):
                # logger.info(response.url)
                if response.url.startswith("https://instagram.ftia9-1.fna.fbcdn.net/o1/v/t16"):
                    audios.append(response.url)
                if response.url.startswith("https://instagram.ftia9-1.fna.fbcdn.net/o1/v/t2"):
                    videos.append(response.url)
            
            def predicate(response):
                if response.url.startswith("https://instagram.ftia9-1.fna.fbcdn.net/o1/v"):
                    logger.info(response.url)
                    return True
                return False
            
            page.on("response", handle_response)

            await page.goto(self.url)

            await page.wait_for_load_state("networkidle")
            await page.press("body","Enter")
            try:
                await page.wait_for_event("response", timeout=20000, predicate=predicate)
            except:
                logger.error("Timeout waiting for response")
                raise VideoNotFound("Timeout waiting for response")
            await page.wait_for_timeout(int(random.random() * 2000) + 5000)

        
        if len(videos) == 0 and len(audios) == 0:
            logger.error("No videos or audios found in the response.")
            raise VideoNotFound("No videos or audios found in the response.")
        
        # if only one of them is empty, output all as video
        if len(videos) == 0:
            videos = audios
            video_url = re.sub(r"&bytestart=\d+&byteend=\d+", "", videos[0])
            return {"video": video_url}
        
        video_url = re.sub(r"&bytestart=\d+&byteend=\d+", "", videos[0])
        audio_url = re.sub(r"&bytestart=\d+&byteend=\d+", "", audios[0])
        
        return {"video": video_url, "audio": audio_url}

    @property
    async def download_url_async(self):
        if self._download_url is None:
            self._download_url = await self.get_download_url()
        return self._download_url

    async def download_video_async(self):
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_file:
            output_name = temp_file.name
            self.output_path.append(output_name)

        if (await self.download_url_async).get("audio") is None:
            # If no audio URL is found, download the video only
            video_content = requests.get((await self.download_url_async)["video"]).content
            with open(output_name, "wb") as file:
                file.write(video_content)
                return
        else: # If audio URL is found, download both video and audio, then merge them
            with tempfile.NamedTemporaryFile(delete=True, suffix='.mp4') as video,\
                    tempfile.NamedTemporaryFile(delete=True, suffix='.aac') as audio:

                with open(video.name, "wb") as file:
                    video_content = requests.get((await self.download_url_async)["video"]).content
                    file.write(video_content)
                with open(audio.name, "wb") as file:
                    audio_content = requests.get((await self.download_url_async)["audio"]).content
                    file.write(audio_content)

                await self._merge_audio_video(video.name, audio.name, output_name)
    
    async def _merge_audio_video(self,video_path, audio_path, output_path):
        try:
            cmd = [
                'ffmpeg',
                '-i', video_path,
                '-i', audio_path,
                '-c:v', "copy",
                '-c:a', 'aac',
                '-y',
                output_path
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