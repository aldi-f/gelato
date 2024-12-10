import re
import json
import requests
import tempfile

from websites.base import Base, RestrictedVideo

def find_reel_id(url:str):
    pattern = r'https?://(?:www\.)?instagram\.com/(?:reel|p)/([^/?]+)'
    match = re.search(pattern, url)
    if match:
        return match.group(1)
    
def get_reel_video_url(url:str):
    video_id = find_reel_id(url)
    
    url = "https://www.instagram.com/graphql/query"
    payload = {
        "variables": json.dumps({"shortcode": video_id}),
        "doc_id": "8845758582119845"
    }

    response = requests.post(url, data=payload)
    data = response.json()
    if not data["data"]["xdt_shortcode_media"]:
        raise RestrictedVideo("No video found")
    return data['data']['xdt_shortcode_media']['video_url']


class Instagram(Base):

    @property
    def download_url(self):
        return get_reel_video_url(self.url)

    def download_video(self):
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_file:
            output_name = temp_file.name
            self.output_path.append(output_name)

        content = requests.get(self.download_url).content
        with open(output_name, "wb") as file:
            file.write(content)
