import re
import os
import asyncio
import logging
import requests
import tempfile
from playwright.async_api import async_playwright

from websites.base import Base, VideoNotFound

PLAYWRIGHT_HOST = os.getenv("PLAYWRIGHT_HOST", "ws://127.0.0.1:3000/")

logger = logging.getLogger(__name__)

def find_reel_id(url:str):
    # Instagram share link is different from actual video
    # Redirect fixes it
    # So catch this to make sure we are pulling the correct one
    real_url = requests.head(url, allow_redirects=True).url
    pattern = r'https?://(?:www\.)?instagram\.com/(?:reel|p)/([^/?]+)'
    match = re.search(pattern, real_url)
    if match:
        return match.group(1)
    
    
async def get_reel_video_url(url:str):
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

        await page.goto(url)

        await page.wait_for_load_state("networkidle")

        await context.close()
        await browser.close()

    if len(results) == 0:
        raise VideoNotFound("No video found")
    
    data = None
    for result in results:
        if not result["data"].get("xdt_shortcode_media"):
            continue
        data = result["data"]["xdt_shortcode_media"]["video_url"]
    if not data:
        raise VideoNotFound("No video found")
    return data


class Instagram(Base):

    @property
    def download_url(self):
        return asyncio.run(get_reel_video_url(self.url))

    def download_video(self):
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_file:
            output_name = temp_file.name
            self.output_path.append(output_name)

        content = requests.get(self.download_url).content
        with open(output_name, "wb") as file:
            file.write(content)
