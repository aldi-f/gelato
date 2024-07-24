import re
import io
import json
import math
import logging
import requests
from bs4 import BeautifulSoup

from discord.ext import commands
import discord

import ffmpeg
import subprocess
import asyncio
from yt_dlp import YoutubeDL
from tempfile import NamedTemporaryFile
from database import Servers, Convert, Session
from utils import what_website, get_tweet_result
from browser import ChromeBrowser

logger = logging.getLogger(__name__)


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


async def error_reaction(ctx, message):
    """
    Save me some time by wrapping both error message and the x reaction to original command issuer
    """
    await ctx.send(message)
    await ctx.message.add_reaction("❌")


class convert(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.lock = asyncio.Lock()
        # self.pattern: re.Pattern = re.compile(r"https://img-9gag-fun\.9cache\.com.+")

    @commands.command(name='convert', aliases=['c','mp4','con'])
    async def convert(self, ctx: commands.Context, *, url:str = None):
        async with ctx.typing():
            reply_to = None
            if ctx.message.reference:
                reply_to = await ctx.fetch_message(ctx.message.reference.message_id)
            title = ""
            if not url:
                await error_reaction(ctx,"No url provided")
                return 
            website = what_website(url)
            if website == "9gag_mobile": #mobile shit link
                mobile = requests.get(url)
                soup = BeautifulSoup(mobile.text)
                contents = json.loads(soup.find("script", type="application/ld+json").text)
                
                url = contents['video']['contentUrl'] # real link here
            elif website == "reel":
                url = ChromeBrowser.reel_download_url(url)
            elif website == "twitter":
                # for now it's a paid api while i figure out how to get it through selenium
                response = get_tweet_result(url)
                if response.status_code != 200:
                    await error_reaction(ctx,"Broken")
                    logger.error(response.json())
                    return
                data = response.json()[0]
                if data['urls'][0]['extension'] != "mp4":
                    await error_reaction(ctx,"No video link found")
                    return
                # i could use this later, but for now let's just get the highest quality
                sorted_urls = sorted(data['urls'],reverse=True, key=lambda x: x['quality'])
                url = sorted_urls[0]['url']
            elif website == "youtube":
                yt_params = {
                    "outtmpl": "-",
                    "logtostderr": False,
                    "quiet": True,
                    "no_warnings": True,
                    "geo_bypass": True,
                    "format": "ba[filesize<25M]"
                }

                try:
                    with YoutubeDL(yt_params) as ydl:
                        info = ydl.extract_info(url, download=False)

                except:
                    # try again with no format
                    try:
                        yt_params = {
                            "outtmpl": "-",
                            "logtostderr": False,
                            "quiet": True,
                            "no_warnings": True,
                            "geo_bypass": True,
                        }
                        with YoutubeDL(yt_params) as ydl:
                            info = ydl.extract_info(url, download=False)
                    except:
                        await error_reaction(ctx,f"Cannot download.")
                        return

                content_length = info.get("filesize") or info.get("filesize_approx")

                title += f"\n\n`{info.get('title')}`" if "title" in info else ""
                
            if website != "youtube":
                
                try:
                    # make sure to check the headers first so we can get the size
                    head_data = requests.head(url, allow_redirects=True).headers
                except:
                    await error_reaction(ctx,"Not valid url.")
                    return
                        
                content_length = int(head_data.get("Content-Length", 0))
                content_type = head_data.get("Content-Type", "")

                if not "video" in content_type:
                    await error_reaction(ctx,"Not a video download link")
                    return
                
            if content_length == 0 or content_length > 26000000:
                await error_reaction(ctx,f"File either empty or too big ({convert_size(content_length)})")
                return
            
            if website != "youtube":
                data = requests.get(url, allow_redirects=True)
            
            delete = False
            async with self.lock: # lock each convert so they are synchronous
                with NamedTemporaryFile(mode="w+") as tf: # use a temporary file for saving
                    try:
                        if website != "youtube":
                            logger.info(content_type)
                            prefix = re.sub(".*/","",content_type) # content-type = "video/mp4" -> "mp4"
                            if not prefix:
                                await error_reaction(ctx,"Didn't find prefix")
                                raise Exception

                        if website in ("9gag","9gag_mobile"):
                            process: subprocess.Popen = (
                                    ffmpeg
                                    .input("pipe:", f=f"{prefix}")
                                    .output(tf.name, f='mp4', vcodec='libx264')
                                    .overwrite_output()
                                    .run_async(pipe_stdin=True, pipe_stdout= True, quiet=True)
                                    )
                            
                            process.communicate(input=data.content)

                            tf.seek(0,2) # take me to the last byte of the video
                            
                            vid_size = tf.tell()
                            
                            tf.seek(0) # back to start so i can stream
                            video = discord.File(tf.name, filename="output.mp4")
                        elif website == "youtube":
                            yt_params['outtmpl'] = tf.name
                            with YoutubeDL(yt_params) as ydl:
                                ydl.download([url])

                            with open(f"{tf.name}.mp4", "rb") as f:

                                f.seek(0,2) # take me to the last byte of the video
                                vid_size = f.tell()
                            
                            video = discord.File(f"{tf.name}.mp4", filename="output.mp4")
                        else:
                            vid_size = content_length
                            video = discord.File(io.BytesIO(data.content), filename="output.mp4")

                        user = str(ctx.author.id)
                        source = website
                        server = str(ctx.guild.id)
                        no_error = True
                        try:
                            if vid_size < 5: # check for less than 5 bytes(empty file but is binary coded with endline)
                                await error_reaction(ctx,"Didn't find prefix")
                                return
                            elif vid_size > 26000000:
                                await error_reaction(ctx,f"File too big ({convert_size(vid_size)})")
                                return
                            server_stats = Session.get(Servers, server)
                            # make sure we have this row
                            if not server_stats: 
                                Session.add(Servers(
                                    server_id = server,
                                    server_name = ctx.guild.name
                                ))
                                Session.commit()
                            # now update the data
                            current_id =  server_stats.total_videos + 1
                            server_stats.total_videos = current_id

                            current_total = server_stats.total_storage + vid_size
                            server_stats.total_storage = current_total

                            Session.add(Convert(
                                server_id = server,
                                user_id = user,
                                source = source,
                                download_size = vid_size
                            ))
                            Session.commit()
                            if reply_to:
                                await reply_to.reply(f"[{current_id}]Conversion for {ctx.author.mention}\n{convert_size(vid_size)} ({convert_size(current_total)})\n{title}",file=video)
                            else:
                                await ctx.send(f"[{current_id}]Conversion for {ctx.author.mention}\n{convert_size(vid_size)} ({convert_size(current_total)})\n{title}",file=video)
                            delete = True
                            no_error = False
                        except Exception as e:
                            await ctx.send("DB error (no stats saved)")
                            logger.error(e)

                        if no_error:
                            if reply_to:
                                await reply_to.reply(f"Conversion for {ctx.author.mention}\n{convert_size(vid_size)}{title}",file=video, mention_author=False)
                            else:
                                await ctx.send(f"Conversion for {ctx.author.mention}\n{convert_size(vid_size)}{title}",file=video, mention_author=False)
                        
                    except Exception as e:
                        await error_reaction(ctx,"Something went wrong!")
                        logger.error(e)
                    finally:
                        if delete:
                            await ctx.message.delete()

    @commands.command(name='exec', aliases=['exe'])
    async def exec(self, ctx: commands.Context, mode = None, *, text = ""):
        if ctx.author.id != 336563297648246785:
            file = discord.File("silicate.jpg")
            await ctx.reply("blehhhh",file=file, ephemeral=True)
            return
        elif not mode:
            await ctx.send("No method provided")
            return
        if mode == "SELECT":
            data = Session.get(Servers, str(ctx.guild.id))
            field = f"""
                    {data.server_name=}
                    {data.server_id=}
                    {data.total_storage=}
                    {data.total_videos=}
                    """
            await ctx.send(field)
            return
        elif mode == "UPDATE":
            if len(text) != 0:
                try:
                    the_dict = json.loads(text)
                    data = Session.get(Servers, str(ctx.guild.id))
                    data.total_storage = the_dict["total_storage"]
                    data.total_videos = the_dict["total_videos"]
                    Session.commit()
                    await ctx.send("Succesfully updated")
                except Exception as e:
                    await ctx.send("invalid json or db failed")
                    logger.error(e)
                    return
        else:
            await ctx.send("invalid")


async def setup(bot):
    await bot.add_cog(convert(bot))
