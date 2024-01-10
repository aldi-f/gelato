import re
import os 
import requests

RAPID_URL = os.getenv("RAPID_URL")
RAPID_KEY = os.getenv("RAPID_KEY")
RAPID_HOST = os.getenv("RAPID_HOST")

def is_instagram_reels_url(url: str) -> bool:
    pattern = r"https?://(?:www\.)?instagram\.com/reel/.*"
    match = re.match(pattern, url)
    if match:
        return True
    return False

def is_9gag_url(url: str) -> bool:
    pattern = r"^https?://img-9gag-fun\.9cache\.com/.*'"
    match = re.match(pattern, url)
    if match:
        return True
    return False

def is_twitter_url(url: str) -> bool:
    pattern = r"https?://(?:www\.)?((vx)?twitter|x)(\.com)?/\w+/status/.*"
    match = re.match(pattern, url)
    if match:
        return True
    return False

def what_website(url: str) -> str:
    if "https://9gag.com/gag/" in url: # mobile 9gag
        return "9gag_mobile"
    elif is_9gag_url(url): # 9gag
        return "9gag"
    elif is_instagram_reels_url(url): # instagram reel
        return "reel"
    elif is_twitter_url(url):
        return "twitter"
    else:
        return "unknown"
    
def get_tweet_result(url: str) -> requests.Response:

    # it only works with the default twitter url
    if "x.com" in url:
        url = url.replace("x.com","twitter.com")
    if "vxtwitter.com" in url:
        url = url.replace("vxtwitter.com","twitter.com")

    headers = {
        "content-type": "application/json",
        "X-RapidAPI-Key": RAPID_KEY,
        "X-RapidAPI-Host": RAPID_HOST
        }

    payload = { "url": url }
    response = requests.post(RAPID_URL, json=payload, headers=headers)
    return response