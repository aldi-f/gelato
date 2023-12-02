import re

def is_instagram_reels_url(url) -> bool:
    pattern = r"https?://(?:www\.)?instagram\.com/reel/.*"
    match = re.match(pattern, url)
    if match:
        return True
    return False

def is_9gag_url(url) -> bool:
    pattern = r"^https?://img-9gag-fun\.9cache\.com/.*'"
    match = re.match(pattern, url)
    if match:
        return True
    return False

def what_website(url) -> str:
    if "https://9gag.com/gag/" in url: # mobile 9gag
        return "9gag_mobile"
    elif is_9gag_url(url): # 9gag
        return "9gag"
    elif is_instagram_reels_url(url): # instagram reel
        return "reel"
    else:
        return "unknown"