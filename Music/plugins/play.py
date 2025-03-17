import asyncio
import random
import logging
from pyrogram import filters
from pyrogram.types import CallbackQuery, InlineKeyboardMarkup, Message

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
from Music.utils.jiosaavn import JioSaavnAPI

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

    # Initialize JioSaavn API
    jio_saavn_api = JioSaavnAPI()

    # Handle Telegram audio file
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

    # Handle Telegram video file
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

    # Handle URL or search query using JioSaavn
    query = message.text.split(" ", 1)[1] if len(message.text.split(" ", 1)) > 1 else url
    if not query:
        return await hell.edit("Please provide a song name or URL to search.")

    try:
        await hell.edit(f"Searching '{query}' on JioSaavn...")
        result = await jio_saavn_api.search_song(query)
        logger.info(f"JioSaavn search result: {result}")
        
        if not result or "title" not in result:
            return await hell.edit(f"No results found for '{query}' on JioSaavn.")
        
        # Check duration limit if available
        if "duration" in result:
            time_check = formatter.check_limit(
                formatter.mins_to_secs(result["duration"]), play_limit
            )
            if not time_check:
                return await hell.edit(
                    f"Audio duration limit of {Config.PLAY_LIMIT} minutes exceeded."
                )

        context = {
            "chat_id": message.chat.id,
            "user_id": message.from_user.id,
            "duration": result.get("duration", "Unknown"),
            "file": result["id"],
            "title": result["title"],
            "user": message.from_user.mention,
            "video_id": result["id"],
            "vc_type": "video" if video else "voice",
            "force": force,
        }
        await player.play(hell, context)
        
    except Exception as e:
        logger.error(f"JioSaavn error: {str(e)}")
        await hell.edit(f"Error playing song from JioSaavn: {str(e)}")
        
