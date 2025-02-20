# Gelato

This is a simple discord bot made to download and convert links into embeddable videos for discord.

For now this supports: 
- 9GAG
- Twitter/X
- Youtube
- Instagram reels

### Running it
Clone the repository:
```bash
git clone https://github.com/muji06/gelato
cd gelato
```

(Optional, but recommended for RaspberryPI) Build ffmpeg from source first for the Raspberry Pi. This is because the default ffmpeg package in the repositories does not have the necessary codecs to convert the videos.

```bash
cd ffmpeg
docker build -t gelato-ffmpeg:latest .
```

Then build the main image with docker compose and run it:
```bash
docker compose up --build
```

Create a `.env` file inside app/ folder for the discord token, or pass it as an environment variable:
```
TOKEN=<discord-token-here>
```


## 9GAG
Requirements:
- FFMPEG
- Beautiful Soup 4
  
9GAG has certain issues with its videos. They are either WebM format or MP4 format.

WebM videos will propely embed in discord, but to be sure the video doesn't get deleted, this bot will download it, convert to mp4, then upload on discord.

MP4 videos from 9GAG use an encoder which does not embed on discord. So we again will donwload this video, convert to proper mp4 and upload to discord.

Additionally, mobile link does not provide the download url. Instead we use Beautiful Soup 4 to read the html content and get the actual download url.

## Instagram Reels
Requirements:
- Selenium
- Firefox browser and Gecko webdriver(I am using a Raspberry Pi server and this was the simpliest to setup for ARM CPU )

By default it is not possible to get the download url from the shared link. Beautiful Soup 4 cannot find the url either because the page has to load first.
For this case we have to use a web browser automation tool like Selenium to open the link, let the page load and then get the actual mp4 content. Then we can proceed to download the video and upload to discord.


