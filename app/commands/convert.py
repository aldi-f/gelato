import logging

from discord.ext import commands
import discord
import asyncio
import time

from utils import is_9gag_url, is_youtube_url, is_instagram_reels_url, is_twitter_url, convert_size
from websites import Generic, Youtube, NineGAG, Instagram, Twitter
from websites.base import RestrictedVideo, VideoNotFound

logger = logging.getLogger(__name__)


async def error_reaction(ctx, message=None):
    """
    Save me some time by wrapping both error message and the x reaction to original command issuer
    """
    if message:
        await ctx.send(message, delete_after=5)
    await ctx.message.add_reaction("❌")
    # Add retry reaction to error messages
    await ctx.message.add_reaction("🔄")


class convert(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.lock = asyncio.Lock()
        self.recent_conversions = {}

    @commands.command(name='convert', aliases=['c',])
    async def convert(self, ctx: commands.Context, url: str | None = None, users_mentioned: commands.Greedy[discord.Member] = None, roles_mentioned: commands.Greedy[discord.Role] = None):
        self.recent_conversions[ctx.message.id] = {
            'url': url,
            'users_mentioned': users_mentioned,
            'roles_mentioned': roles_mentioned,
            'timestamp': time.time()
        }
        async with ctx.typing():
            if not url:
                await error_reaction(ctx,"No url provided")
                return
            
            status_message = await ctx.send("🔍 Checking URL...")
            
            reply_to = None
            delete = False
            mention_message = ""
            start = time.time()

            if ctx.message.reference:
                reply_to = await ctx.fetch_message(ctx.message.reference.message_id)
            if users_mentioned:
                mention_message += " ".join([user.mention for user in users_mentioned])
            if roles_mentioned:
                mention_message += " ".join([role.mention for role in roles_mentioned])

            try: 
                if is_9gag_url(url):
                    website = NineGAG(url)
                    logger.info("9gag")
                elif is_twitter_url(url):
                    website = Twitter(url)
                    logger.info("twitter")
                elif is_youtube_url(url):
                    website = Youtube(url)
                    logger.info("youtube")
                elif is_instagram_reels_url(url):
                    website = Instagram(url)
                    logger.info("instagram")
                else:
                    website = Generic(url)
                    logger.info("generic")
            except Exception as e:
                await status_message.edit(content="❌ Invalid URL!")
                await error_reaction(ctx)
                logger.exception(e)
                return

            # Check for size before downloading
            try:

                size_before = website.content_length_before if not website.async_download else await website.content_length_before_async
            except VideoNotFound:
                await status_message.edit(content="❌ Video not found!")
                await error_reaction(ctx)
                return
            except Exception as e:
                await status_message.edit(content="❌ Error retrieving video")
                await error_reaction(ctx)
                logger.exception(e)
                return
            
            if size_before is None:
                await status_message.edit(content="❌ Error getting video size")
                await error_reaction(ctx)
                return
            if size_before == 0 or size_before > 104857600:
                await error_reaction(ctx,f"File either empty or too big ({convert_size(size_before)})")
                return
        
            await status_message.edit(content="🔒 Waiting for lock...")
            async with self.lock:
                try:
                    # Download the actual video
                    try:
                        await status_message.edit(content="⬇️ Downloading video...")
                        if website.async_download:
                            await website.download_video_async()
                        else:
                            website.download_video()
                    except RestrictedVideo:
                        await status_message.edit(content="❌ Video is restricted!")
                        await error_reaction(ctx)
                        return
                    except Exception as e:
                        await status_message.edit(content="❌ Download failed!")
                        await error_reaction(ctx)
                        logger.exception(e)
                        return
                    # Convert to mp4 if needed
                    if "h264" not in website.vcodec or website.convert_to_mp4:
                        await status_message.edit(content="⚙️ Converting video...")
                        try:
                            await website.convert_video()
                        except Exception as e:
                            await status_message.edit(content="❌ Conversion failed!")
                            await error_reaction(ctx)
                            logger.exception(e)
                            return
                    # Check for size after converting
                    size_after = website.content_length_after
                    if size_after < 5: # empty file but is binary coded with endline)
                        logger.error(f"Empty file: {website.output_path[-1]}")
                        await status_message.edit(content="❌ Conversion failed!")
                        await error_reaction(ctx)
                        return
                    elif size_after > 104857600: # 100MB
                        await status_message.edit(content=f"❌ File size too large! ({convert_size(size_after)})")
                        await error_reaction(ctx)
                        return
                    elif size_after > 10485760: # 10MB
                        try: # Encaplusate all compression errors here
                            # Lower resolution if it is higher than 480p

                            # If video is higher than 720p, lower it to 720p
                            _, height = website.resolution
                            if height > 720 or size_after: # 25MB
                                await status_message.edit(content=f"🔄 File too large ({convert_size(size_after)}) but resolution is over 720p. Lowering to 720p...")
                                await website.lower_resolution(720)
                                size_after = website.content_length_after

                            # For files bigger than 25MB, lower to 480p
                            if size_after  > 10485760 * 2.5 and height > 480: # 25MB
                                await status_message.edit(content=f"🔄 File too large ({convert_size(size_after)}). Lowering to 480p...")
                                await website.lower_resolution(480)
                                size_after = website.content_length_after

                            # Firstly we try simple hardware compression
                            if size_after > 10485760:
                                await status_message.edit(content=f"🔄 File too large ({convert_size(size_after)}). Trying hardware compression...")
                                await website.compress_video_hardware_light()
                                size_after = website.content_length_after

                            # Try again with hardware compression but lower bitrate
                            if size_after > 10485760:
                                await status_message.edit(content=f"🔄 Light hardware compression insufficient ({convert_size(size_after)}). Trying medium hardware compression...")
                                await website.compress_video_hardware_medium()
                                size_after = website.content_length_after

                            # Then try 3 levels of software compression
                            if size_after > 10485760:
                                await status_message.edit(content=f"🔄 Medium hardware compression insufficient({convert_size(size_after)}). Trying light software compression...")
                                await website.compress_video_light()
                                size_after = website.content_length_after

                            if size_after > 10485760:
                                await status_message.edit(content=f"🔄 Light compression insufficient ({convert_size(size_after)}). Trying medium software compression...")
                                await website.compress_video_medium()
                                size_after = website.content_length_after

                            if size_after > 10485760:
                                await status_message.edit(content=f"🔄 Medium compression insufficient ({convert_size(size_after)}). Trying maximum software compression...")
                                await website.compress_video_maximum()
                                size_after = website.content_length_after

                        except Exception as e:
                            await status_message.edit(content="❌ Compression failed!")
                            await error_reaction(ctx)
                            logger.exception(e)
                            return
                    
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
                    end = time.time()
                    # convert time to seconds 
                    elapsed = int(end - start)
                    logger.info(f"Total time: {elapsed} seconds")
                    if reply_to:
                        await reply_to.reply(f"Conversion for {ctx.author.mention}\n[{elapsed} seconds]\n{convert_size(size_after)}{mention_message}{website.title}",file=video, mention_author=False)
                    else:
                        await ctx.send(f"Conversion for {ctx.author.mention}\n[{elapsed} seconds]\n{convert_size(size_after)}{mention_message}{website.title}",file=video, mention_author=False)

                    delete = True
                    await status_message.edit(content="✅ Conversion complete!", delete_after=5)

                except Exception as e:
                    await status_message.edit(content="❌ Process failed!")
                    await error_reaction(ctx)
                    logger.exception(e)
                finally:
                    if delete:
                        await ctx.message.delete()
                    # # Delete all temp files
                    website.cleanup()

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction: discord.Reaction, user: discord.User):
        if user.bot:
            return
        
        if str(reaction.emoji) != "🔄":
            return
            
        message = reaction.message
        
        # Clean up old entries (older than 1 hour)
        current_time = time.time()
        self.recent_conversions = {
            k: v for k, v in self.recent_conversions.items() 
            if current_time - v['timestamp'] < 3600
        }
        
        conversion_info = None
        if message.id in self.recent_conversions:
            conversion_info = self.recent_conversions[message.id]

        if not conversion_info:
            return

        context = await self.bot.get_context(message)

        await self.convert(
                context,
                url=conversion_info['url'],
                users_mentioned=conversion_info['users_mentioned'],
                roles_mentioned=conversion_info['roles_mentioned']
            )
        
        del self.recent_conversions[message.id]


async def setup(bot):
    await bot.add_cog(convert(bot))
