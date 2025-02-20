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


By default it is not possible to get the download url from the shared link. Beautiful Soup 4 cannot find the url either because the page has to load first.
For this case we have to use a web browser automation tool like Selenium to open the link, let the page load and then get the actual mp4 content. Then we can proceed to download the video and upload to discord.


