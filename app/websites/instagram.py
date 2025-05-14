import re
import os
import aiohttp
import logging
import requests
import tempfile
from playwright.async_api import async_playwright

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
        async with async_playwright() as p:
            browser = await p.chromium.connect(ws_endpoint=PLAYWRIGHT_HOST)
            context = await browser.new_context()
            page = await context.new_page()

            results = []

            async def handle_request(request):
                if request.url == "https://www.instagram.com/graphql/query" and request.resource_type == "xhr" :
                    response = await request.response()
                    data = await response.json()
                    results.append(data)

            page.on("request", handle_request)

            await page.goto(self.url)

            await page.wait_for_load_state("networkidle")

            retry = 0

            found = False
            while retry < 10 and not found:
                for request in results:
                    if request.get("data") and request["data"].get("xdt_shortcode_media"):
                        found = True
                        break
                if not found:
                    await page.wait_for_timeout(1000)
                    retry += 1
                
            await context.close()
            await browser.close()

        if len(results) == 0:
            logger.error("No graphql requests")
            raise VideoNotFound("No video found")
        
        data = None
        for result in results:
            if not result["data"].get("xdt_shortcode_media"):
                continue
            data = result["data"]["xdt_shortcode_media"]["video_url"]
        if not data:
            logger.error(f"No data: {results=}")
            raise VideoNotFound("No video found")
        return data

    @property
    async def download_url_async(self):
        if self._download_url is None:
            self._download_url = await self.get_download_url()
        return self._download_url

    async def download_video_async(self):
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_file:
            output_name = temp_file.name
            self.output_path.append(output_name)

        content = requests.get(await self.download_url_async).content

        # TODO: fix this
        # async with aiohttp.ClientSession() as session:
        #     async with session.get(await self.download_url_async, timeout=aiohttp.ClientTimeout(total=60)) as response:
        #         content = await response.read()

        with open(output_name, "wb") as file:
            file.write(content)
