import re  
import json
import math

import requests
from bs4 import BeautifulSoup

from discord.ext import commands
import discord

import ffmpeg
import subprocess
import asyncio
from tempfile import NamedTemporaryFile
import pickledb


db = pickledb.load("/data/counters.db", True)
# 2 counters:
#       - megabytes
#       - internal counter

def convert_size(size_bytes):
   if size_bytes == 0:
       return "0B"
   size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
   i = int(math.floor(math.log(size_bytes, 1024)))
   p = math.pow(1024, i)
   s = round(size_bytes / p, 2)
   return "%s %s" % (s, size_name[i])


async def error_reaction(ctx, message):
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
            
            if "https://9gag.com/gag/" in url: #mobile shit link
                mobile = requests.get(url)
                soup = BeautifulSoup(mobile.text)
                contents = json.loads(soup.find("script", type="application/ld+json").text)
                
                url = contents['video']['contentUrl']
            
            if not url:
                await error_reaction(ctx,"No url provided")
                return 

            try:
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
            
            
            data = requests.get(url, allow_redirects=True)
            
            delete = False
            async with self.lock:
                with NamedTemporaryFile(mode="w+") as tf:
                    try:
                        print(content_type)
                        prefix = re.sub(".*/","",content_type)
                        if not prefix:
                            await error_reaction(ctx,"Didn't find prefix")
                            raise Exception
                        
                        process: subprocess.Popen = (
                                ffmpeg
                                .input("pipe:", f=f"{prefix}")
                                .output(tf.name, f='mp4', vcodec='libx264')
                                .overwrite_output()
                                .run_async(pipe_stdin=True, pipe_stdout= True)
                                )
                        
                        process.communicate(input=data.content)

                        tf.seek(0,2)
                        
                        vid_size = tf.tell()
                        if tf.tell() < 5: # check for less than 5 bytes(empty file but is binary coded with endline)
                            await error_reaction(ctx,"Didn't find prefix")
                            raise Exception
                        elif tf.tell() > 26000000:
                            await error_reaction(ctx,f"File too big ({convert_size(tf.tell())})")
                            raise Exception
                        
                        tf.seek(0)
                        video = discord.File(tf.name, filename="output.mp4")

                        if not db.exists("downloaded"):
                            db.set("downloaded", 0)
                            db.set("counter", 1)
                        else:
                            downloaded = db.get("downloaded")
                            counter = db.get("counter")
                            id = counter + 1
                            total_size = downloaded + vid_size
                            db.set("downloaded", total_size)
                            db.set("counter", id)
                        
                        await ctx.send(f"[{id}]Conversion for {ctx.author.mention}\n{convert_size(vid_size)} ({convert_size(total_size)})",file=video, mention_author=False)
                        delete = True
                        
                        
                    except Exception as e:
                        await error_reaction(ctx,"Something went wrong!")
                        print(e)
                    finally:
                        if delete:
                            await ctx.message.delete()
                        tf.close()
                        return
        
async def setup(bot):
    await bot.add_cog(convert(bot))