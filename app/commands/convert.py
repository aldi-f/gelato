import logging

from discord.ext import commands
import discord

from utils import is_9gag_url, is_youtube_url, is_instagram_reels_url, convert_size
from websites import Generic, Youtube, NineGAG, Instagram

logger = logging.getLogger(__name__)


async def error_reaction(ctx, message=None):
    """
    Save me some time by wrapping both error message and the x reaction to original command issuer
    """
    if message:
        await ctx.send(message)
    await ctx.message.add_reaction("❌")


class convert(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='convert', aliases=['c',])
    async def convert(self, ctx: commands.Context, url: str | None = None, users_mentioned: commands.Greedy[discord.Member] = None, roles_mentioned: commands.Greedy[discord.Role] = None):
        async with ctx.typing():
            if not url:
                await error_reaction(ctx,"No url provided")
                return
            
            status_message = await ctx.send("🔍 Checking URL...")
            
            reply_to = None
            mention_message = ""
            title = ""

            if ctx.message.reference:
                reply_to = await ctx.fetch_message(ctx.message.reference.message_id)
            if users_mentioned:
                mention_message += " ".join([user.mention for user in users_mentioned])
            if roles_mentioned:
                mention_message += " ".join([role.mention for role in roles_mentioned])

            if is_9gag_url(url):
                website = NineGAG(url)
            elif is_youtube_url(url):
                website = Youtube(url)
            elif is_instagram_reels_url(url):
                website = Instagram(url)
            else:
                website = Generic(url)

            # Check for size before downloading
            size_before = website.content_length_before
            if size_before == 0 or size_before > 10485760:
                await error_reaction(ctx,f"File either empty or too big ({convert_size(size_before)})")
                return
            
            try:
                # Download the actual video
                try:
                    await status_message.edit(content="⬇️ Downloading video...")
                    website.download_video()
                except Exception as e:
                    await status_message.edit(content="❌ Download failed!")
                    await error_reaction(ctx)
                    logger.error(e)
                    return
                # Convert to mp4 if needed
                if website.convert_to_mp4:
                    await status_message.edit(content="⚙️ Converting video...")
                    website.convert_video()
                
                # Check for size after converting
                size_after = website.content_length_after
                if size_after < 5: # empty file but is binary coded with endline)
                    await status_message.edit(content="❌ Conversion failed!")
                    await error_reaction(ctx)
                    return
                elif size_after > 104857600: # 100MB
                    await status_message.edit(content=f"❌ File size too large! ({convert_size(size_after)})")
                    await error_reaction(ctx)
                    return
                elif size_after > 10485760: # 10MB
                    # Lower resolution if it is higher than 480p
                    await status_message.edit(content=f"🔄 File too large ({convert_size(size_after)}). Trying to lower resolution..")
                    _, height = website.resolution

                    # If video is higher than 720p, lower it to 720p
                    if height > 720: 
                        website.lower_resolution(720)
                    # Otherwise, lower it to 480p. If it is already 480p, it will not change anything
                    else:
                        website.lower_resolution(480)

                    if website.content_length_after > 10485760:
                        # Try compressing with increasing levels
                        await status_message.edit(content=f"🔄 File too large ({convert_size(size_after)}). Trying light compression...")
                        website.compress_video_light()
                    
                    if website.content_length_after > 10485760:
                        await status_message.edit(content=f"🔄 Light compression insufficient ({convert_size(size_after)}). Trying medium compression...")
                        website.compress_video_medium()

                        
                        size_after = website.content_length_after
                        if size_after > 10485760:
                            await status_message.edit(content=f"🔄 Medium compression insufficient ({convert_size(size_after)}). Trying maximum compression...")
                            website.compress_video_maximum()
                
                # Check for size after compressing
                size_after = website.content_length_after
                if size_after < 5: # empty file but is binary coded with endline)
                    await status_message.edit(content="❌ Compression failed!")
                    await error_reaction(ctx)
                    return
                elif size_after > 10485760: # 10MB
                    await status_message.edit(content=f"❌ File size too large even after compressing! ({convert_size(size_after)})")
                    await error_reaction(ctx)
                    return
                
                await status_message.edit(content="📤 Uploading to Discord...")
                video = discord.File(website.output_path[-1], filename="output.mp4")

                # TODO: database path

                if reply_to:
                    await reply_to.reply(f"Conversion for {ctx.author.mention}\n{convert_size(size_after)}{mention_message}{title}",file=video, mention_author=False)
                else:
                    await ctx.send(f"Conversion for {ctx.author.mention}\n{convert_size(size_after)}{mention_message}{title}",file=video, mention_author=False)

                await status_message.edit(content="✅ Conversion complete!", delete_after=5)
            except Exception as e:
                await status_message.edit(content="❌ Process failed!")
                await error_reaction(ctx)
                logger.error(e)
            finally:
                # remove temp files whatever happens
                website.cleanup()


async def setup(bot):
    await bot.add_cog(convert(bot))
