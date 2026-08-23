import time
import asyncio
import discord
import logging

from discord.ext import commands

from utils import is_9gag_url, is_youtube_url, is_instagram_reels_url, is_twitter_url, is_reddit_url, convert_size
from websites import Generic, Youtube, NineGAG, Instagram, Twitter, Reddit
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


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.lock = asyncio.Lock()
        self.recent_conversions = {}

    @commands.command(name='music', aliases=['m',])
    async def music(self, ctx: commands.Context, url: str | None = None, users_mentioned: commands.Greedy[discord.Member] = None, roles_mentioned: commands.Greedy[discord.Role] = None):

        # max_bytes = ctx.guild.filesize_limit if ctx.guild else 10485760
        max_bytes = 10485760

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
                if is_youtube_url(url):
                    website = Youtube(url, audio_only=True)
                    logger.info("youtube")
                else:
                    raise NotImplementedError("Website not supported yet")
            except NotImplementedError as e:
                await status_message.edit(content="❌ Only YouTube URLs are supported for now!")
                await error_reaction(ctx)
                logger.exception(e)
                return
            except Exception as e:
                await status_message.edit(content="❌ Invalid URL!")
                await error_reaction(ctx)
                logger.exception(e)
                return

            # Check for size before downloading
            try:

                size_before = website.content_length_before if not website.async_download else await website.content_length_before_async
            except VideoNotFound as e:
                await status_message.edit(content=f"❌ {e}")
                await error_reaction(ctx)
                return
            except Exception as e:
                await status_message.edit(content="❌ Error retrieving audio")
                await error_reaction(ctx)
                logger.exception(e)
                return

            if size_before is None:
                await status_message.edit(content="❌ Error getting audio size")
                await error_reaction(ctx)
                return
            if size_before == 0 or size_before > max_bytes * 2:
                await error_reaction(ctx,f"File either empty or too big ({convert_size(size_before)})")
                return

            await status_message.edit(content="🔒 Waiting for lock...")
            async with self.lock:
                try:
                    # Download the actual video
                    try:
                        await status_message.edit(content="⬇️ Downloading Audio...")
                        if website.async_download:
                            await website.download_video_async()
                        else:
                            website.download_video()
                    except RestrictedVideo:
                        await status_message.edit(content="❌ Audio is restricted!")
                        await error_reaction(ctx)
                        return
                    except Exception as e:
                        await status_message.edit(content="❌ Download failed!")
                        await error_reaction(ctx)
                        logger.exception(e)
                        return
                    # Convert to mp4
                    # Discord does not like mkv
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
                    elif size_after > max_bmax_bytes * 2:
                        await status_message.edit(content=f"❌ File size too large! ({convert_size(size_after)})")
                        await error_reaction(ctx)
                        return
                    elif size_after > max_bytes:
                        try: # Encaplusate all compression errors here

                            # Firstly we try simple hardware compression
                            if size_after > max_bytes:
                                await status_message.edit(content=f"🔄 File too large ({convert_size(size_after)}). Trying hardware compression...")
                                await website.compress_video_hardware_light()
                                size_after = website.content_length_after

                            # Try again with hardware compression but lower bitrate
                            if size_after > max_bytes:
                                await status_message.edit(content=f"🔄 Light hardware compression insufficient ({convert_size(size_after)}). Trying medium hardware compression...")
                                await website.compress_video_hardware_medium()
                                size_after = website.content_length_after

                            # Then try 3 levels of software compression
                            if size_after > max_bytes:
                                await status_message.edit(content=f"🔄 Medium hardware compression insufficient({convert_size(size_after)}). Trying light software compression...")
                                await website.compress_video_light()
                                size_after = website.content_length_after

                            if size_after > max_bytes:
                                await status_message.edit(content=f"🔄 Light compression insufficient ({convert_size(size_after)}). Trying medium software compression...")
                                await website.compress_video_medium()
                                size_after = website.content_length_after

                            if size_after > max_bytes:
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
                    elif size_after > max_bytes:
                        await status_message.edit(content=f"❌ File size too large even after compressing! ({convert_size(size_after)})")
                        await error_reaction(ctx)
                        return

                    logger.info(f"Final size: {size_after} (limit {max_bytes})")
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
                        del self.recent_conversions[ctx.message.id]
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

        await self.music(
                context,
                url=conversion_info['url'],
                users_mentioned=conversion_info['users_mentioned'],
                roles_mentioned=conversion_info['roles_mentioned']
            )


async def setup(bot):
    await bot.add_cog(Music(bot))
