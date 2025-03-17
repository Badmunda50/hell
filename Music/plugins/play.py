import asyncio
import random
import logging
import aiohttp
from pyrogram import filters
from pyrogram.types import Message

from config import Config
from Music.core.clients import hellbot
from Music.core.database import db
from Music.core.decorators import AuthWrapper, PlayWrapper, UserWrapper, check_mode
from Music.helpers.buttons import Buttons
from Music.helpers.formatters import formatter
from Music.helpers.strings import TEXTS
from Music.utils.pages import MakePages
from Music.utils.play import player
from Music.utils.queue import Queue
from Music.utils.thumbnail import thumb

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Basic JioSaavn API implementation
class JioSaavnAPI:
    def __init__(self):
        self.base_url = "https://saavn.dev/api"

    async def search_song(self, query):
        """Search for a song on JioSaavn and return the first result."""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/search/songs?query={query}&limit=1"
                async with session.get(url) as response:
                    if response.status != 200:
                        logger.error(f"JioSaavn API returned status: {response.status}")
                        return None
                    data = await response.json()
                    if not data.get("success") or not data.get("data", {}).get("results"):
                        logger.info(f"No results found for query: {query}")
                        return None
                    
                    song = data["data"]["results"][0]
                    return {
                        "id": song["id"],
                        "title": song["name"],
                        "duration": song.get("duration", "Unknown"),  # Duration in seconds
                        "url": song["downloadUrl"][-1]["url"] if song.get("downloadUrl") else None
                    }
        except Exception as e:
            logger.error(f"JioSaavn API error: {str(e)}")
            return None

@hellbot.app.on_message(
    filters.command(["play", "vplay", "fplay", "fvplay"])
    & filters.group
    & ~Config.BANNED_USERS
)
@check_mode
@PlayWrapper
async def play_music(_, message: Message, context: dict):
    user_name = message.from_user.first_name
    user_id = message.from_user.id
    if not await db.is_user_exist(user_id):
        await db.add_user(user_id, user_name)
    else:
        try:
            await db.update_user(user_id, "user_name", user_name)
        except:
            pass
    
    hell = await message.reply_text("Processing ...")
    video, force, url, tgaud, tgvid = context.values()
    play_limit = formatter.mins_to_secs(f"{Config.PLAY_LIMIT}:00")

    jio_saavn_api = JioSaavnAPI()

    # Handle Telegram audio
    if tgaud:
        size_check = formatter.check_limit(tgaud.file_size, Config.TG_AUDIO_SIZE_LIMIT)
        if not size_check:
            return await hell.edit(
                f"Audio file size exceeds the limit of {formatter.bytes_to_mb(Config.TG_AUDIO_SIZE_LIMIT)}MB."
            )
        time_check = formatter.check_limit(tgaud.duration, play_limit)
        if not time_check:
            return await hell.edit(
                f"Audio duration limit of {Config.PLAY_LIMIT} minutes exceeded."
            )
        await hell.edit("Downloading ...")
        file_path = await hellbot.app.download_media(message.reply_to_message)
        context = {
            "chat_id": message.chat.id,
            "user_id": message.from_user.id,
            "duration": formatter.secs_to_mins(tgaud.duration),
            "file": file_path,
            "title": "Telegram Audio",
            "user": message.from_user.mention,
            "video_id": "telegram",
            "vc_type": "voice",
            "force": force,
        }
        await player.play(hell, context)
        return

    # Handle Telegram video
    if tgvid:
        size_check = formatter.check_limit(tgvid.file_size, Config.TG_VIDEO_SIZE_LIMIT)
        if not size_check:
            return await hell.edit(
                f"Video file size exceeds the limit of {formatter.bytes_to_mb(Config.TG_VIDEO_SIZE_LIMIT)}MB."
            )
        time_check = formatter.check_limit(tgvid.duration, play_limit)
        if not time_check:
            return await hell.edit(
                f"Audio duration limit of {Config.PLAY_LIMIT} minutes exceeded."
            )
        await hell.edit("Downloading ...")
        file_path = await hellbot.app.download_media(message.reply_to_message)
        context = {
            "chat_id": message.chat.id,
            "user_id": message.from_user.id,
            "duration": formatter.secs_to_mins(tgvid.duration),
            "file": file_path,
            "title": "Telegram Video",
            "user": message.from_user.mention,
            "video_id": "telegram",
            "vc_type": "video",
            "force": force,
        }
        await player.play(hell, context)
        return

    # Handle JioSaavn search
    query = message.text.split(" ", 1)[1] if len(message.text.split(" ", 1)) > 1 else url
    if not query:
        return await hell.edit("Please provide a song name or URL to search.")

    await hell.edit(f"Searching '{query}' on JioSaavn...")
    try:
        result = await jio_saavn_api.search_song(query)
        logger.info(f"JioSaavn search result: {result}")
        
        if not result or "title" not in result:
            # Try cleaning the query and search again
            clean_query = " ".join(query.split()).strip()
            await hell.edit(f"No results for '{query}'. Trying '{clean_query}'...")
            result = await jio_saavn_api.search_song(clean_query)
            logger.info(f"JioSaavn retry result: {result}")
            
            if not result or "title" not in result:
                return await hell.edit(
                    f"No results found for '{query}' on JioSaavn. Try a different song name or check spelling."
                )

        # Handle duration
        duration = result.get("duration")
        if duration and isinstance(duration, (int, float)):
            time_check = formatter.check_limit(int(duration), play_limit)
            if not time_check:
                return await hell.edit(
                    f"Audio duration limit of {Config.PLAY_LIMIT} minutes exceeded."
                )
            duration_str = formatter.secs_to_mins(int(duration))
        else:
            duration_str = "Unknown"

        context = {
            "chat_id": message.chat.id,
            "user_id": message.from_user.id,
            "duration": duration_str,
            "file": result.get("url", result["id"]),  # Use URL if available, else ID
            "title": result["title"],
            "user": message.from_user.mention,
            "video_id": result["id"],
            "vc_type": "video" if video else "voice",
            "force": force,
        }
        await player.play(hell, context)
        
    except Exception as e:
        logger.error(f"JioSaavn error: {str(e)}")
        await hell.edit(f"Error searching on JioSaavn: {str(e)}. Please try again later.")
