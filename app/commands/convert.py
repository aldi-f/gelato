from discord.ext import commands
import discord
from requests import get
import re  
import ffmpeg
import subprocess
import io
import sys
from tempfile import NamedTemporaryFile

class convert(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # self.pattern: re.Pattern = re.compile(r"https://img-9gag-fun\.9cache\.com.+")

    @commands.command(name='convert', aliases=['c','mp4','con'])
    async def convert(self, ctx: discord.TextChannel, *, url:str = None):
        if not url:
            await ctx.send("No url provided")
            return 
        # check = self.pattern.findall(url)
        # if not check:
        #     await ctx.send("Wrong url provided")
        #     return 
        data = get(url)
        print(f"Byte size of {sys.getsizeof(data.content)}")
        if sys.getsizeof(data.content) > 25000000:
            await ctx.send("File too big")
            return
        prefix = re.findall("\.\w{3,4}$", url)[0][1:]

        with NamedTemporaryFile(mode="w+") as tf:
            try:
                process: subprocess.Popen = (
                        ffmpeg
                        .input("pipe:", f=f"{prefix}")
                        .output(tf.name, f='mp4', vcodec='libx264')
                        .overwrite_output()
                        .run_async(pipe_stdin=True, pipe_stdout= True)
                        )
                process.communicate(input=data.content)
                video = discord.File(tf.name, filename="output.mp4")
                await ctx.reply(file=video, mention_author=False)
            except Exception as e:
                await ctx.send("Something went wrong!")
                print(e)
        
async def setup(bot):
    await bot.add_cog(convert(bot))