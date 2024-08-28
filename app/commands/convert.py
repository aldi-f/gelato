import math
import logging

from discord.ext import commands
import discord

from utils import is_9gag_url, is_youtube_url, convert_size
from websites import Generic, Youtube, NineGAG

logger = logging.getLogger(__name__)


async def error_reaction(ctx, message):
    """
    Save me some time by wrapping both error message and the x reaction to original command issuer
    """
    await ctx.send(message)
    await ctx.message.add_reaction("❌")


class convert(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='convert', aliases=['c','mp4','con'])
    async def convert(self, ctx: commands.Context, url:str = None, user_mentioned:discord.Member = None):
        async with ctx.typing():
            if not url:
                await error_reaction(ctx,"No url provided")
                return
            
            reply_to = None
            mention_message = ""
            title = ""

            if ctx.message.reference:
                reply_to = await ctx.fetch_message(ctx.message.reference.message_id)
            if user_mentioned:
                mention_message = f"\n{user_mentioned.mention}"
            

            if is_9gag_url(url):
                website = NineGAG(url)
            elif is_youtube_url(url):
                website = Youtube(url)
            else:
                website = Generic(url)

            # Check for size before downloading
            size_before = website.content_length_before
            if size_before == 0 or size_before > 26000000:
                await error_reaction(ctx,f"File either empty or too big ({convert_size(size_before)})")
                return
            try:

                # Download the actual video
                try:
                    website.download_video()
                except Exception as e:
                    await error_reaction(ctx,"Could not download video!")
                    logger.error(e)

                # Check for size after downloading
                size_after = website.content_length_after
                if size_after < 5: # empty file but is binary coded with endline)
                    await error_reaction(ctx,"Converting failed!")
                    return
                elif size_after > 26000000:
                    await error_reaction(ctx,f"File too big ({convert_size(size_after)})")
                    return
                
                video = discord.File(website.output_path[-1], filename="output.mp4")

                # TODO: database path

                if reply_to:
                    await reply_to.reply(f"Conversion for {ctx.author.mention}\n{convert_size(vid_size)}{mention_message}{title}",file=video, mention_author=False)
                else:
                    await ctx.send(f"Conversion for {ctx.author.mention}\n{convert_size(vid_size)}{mention_message}{title}",file=video, mention_author=False)
            except Exception as e:
                await error_reaction(ctx,"Something went wrong!")
                logger.error(e)
            finally:
                # remove temp files whatever happens
                website.cleanup()


async def setup(bot):
    await bot.add_cog(convert(bot))
