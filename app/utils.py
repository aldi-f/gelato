import re
import os 
import json
import requests
import math

def is_instagram_reels_url(url: str) -> bool:
    pattern = r"https?://(?:www\.)?instagram\.com/reel/.*"
    match = re.match(pattern, url)
    if match:
        return True
    # new instagram url format for sharing links
    pattern = r"https?://(?:www\.)?instagram\.com/share/reel/.*"
    match = re.match(pattern, url)
    if match:
        return True
    return False

def is_9gag_url(url: str) -> bool:
    return url.startswith("https://img-9gag-fun.9cache.com")

def is_twitter_url(url: str) -> bool:
    pattern = r"https?://(?:www\.)?((vx)?twitter|x)(\.com)?/\w+/status/.*"
    match = re.match(pattern, url)
    if match:
        return True
    return False

def is_youtube_url(url: str) -> bool:
    pattern = r"https?://(www\.)?youtu(\.?be)?.*"
    match = re.match(pattern, url)
    if match:
        return True
    return False

def what_website(url: str) -> str:
    if is_9gag_url(url):
        return "9gag"
    elif is_instagram_reels_url(url): # instagram reel
        return "reel"
    elif is_twitter_url(url):
        return "twitter"
    elif is_youtube_url(url):
        return "youtube"
    else:
        return "unknown"
    
def convert_size(size_bytes):
   """
   Given size in bytes, convert it into readable number
   """
   if size_bytes == 0:
       return "0B"
   size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
   i = int(math.floor(math.log(size_bytes, 1024)))
   p = math.pow(1024, i)
   s = round(size_bytes / p, 2)
   return "%s %s" % (s, size_name[i])
