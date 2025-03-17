import asyncio
import random

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
from Music.utils.youtube import ytube
from Music.utils.jiosaavn import JioSaavnAPI  # Import JioSaavnAPI

@hellbot.app.on_message(
    filters.command(["play", "vplay", "fplay", "fvplay"]) & filters.group & ~Config.BANNED_USERS
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
        except Exception as e:
            print(f"Error updating user: {e}")

    hell = await message.reply_text("Processing ...")
    # initialise variables
    video, force, url, tgaud, tgvid = context.values()
    play_limit = formatter.mins_to_secs(f"{Config.PLAY_LIMIT}:00")

    # JioSaavn Integration
    jio_saavn_api = JioSaavnAPI()

    # if the user replied to a message and that message is an audio file
    if tgaud:
        size_check = formatter.check_limit(tgaud.file_size, Config.TG_AUDIO_SIZE_LIMIT)
        if not size_check:
            return await hell.edit(
                f"Audio file size exceeds the size limit of {formatter.bytes_to_mb(Config.TG_AUDIO_SIZE_LIMIT)}MB."
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

    # if the user replied to a message and that message is a video file
    if tgvid:
        size_check = formatter.check_limit(tgvid.file_size, Config.TG_VIDEO_SIZE_LIMIT)
        if not size_check:
            return await hell.edit(
                f"Video file size exceeds the size limit of {formatter.bytes_to_mb(Config.TG_VIDEO_SIZE_LIMIT)}MB."
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

    # if the user replied to or sent a youtube link
    if url:
        if not ytube.check(url):
            return await hell.edit("Invalid YouTube URL.")
        if "playlist" in url:
            await hell.edit("Processing the playlist ...")
            song_list = await ytube.get_playlist(url)
            random.shuffle(song_list)
            context = {
                "user_id": message.from_user.id,
                "user_mention": message.from_user.mention,
            }
            await player.playlist(hell, context, song_list, video)
            return
        try:
            await hell.edit("Searching ...")
            result = await ytube.get_data(url, False)
        except Exception as e:
            print(f"Error fetching YouTube data: {e}")
            await hell.edit("YouTube cookies failed, trying JioSaavn...")
            jiosaavn_result = await jio_saavn_api.search_song(url.split("v=")[-1] if "v=" in url else url)
            if not jiosaavn_result:
                return await hell.edit("Song not found on JioSaavn either.")
            result = [jiosaavn_result]

        context = {
            "chat_id": message.chat.id,
            "user_id": message.from_user.id,
            "duration": result[0].get("duration", "Unknown"),
            "file": result[0]["id"],
            "title": result[0]["title"],
            "user": message.from_user.mention,
            "video_id": result[0]["id"],
            "vc_type": "video" if video else "voice",
            "force": force,
        }
        await player.play(hell, context)
        return

    # For query handling section
    query = message.text.split(" ", 1)[1]
    try:
        await hell.edit("Searching ...")
        result = await ytube.get_data(query, False)
    except Exception as e:
        print(f"Error fetching YouTube data: {e}")
        await hell.edit("YouTube cookies failed, trying JioSaavn...")
        jiosaavn_result = await jio_saavn_api.search_song(query)
        if not jiosaavn_result:
            return await hell.edit("Song not found on JioSaavn either.")
        result = [jiosaavn_result]

    context = {
        "chat_id": message.chat.id,
        "user_id": message.from_user.id,
        "duration": result[0].get("duration", "Unknown"),
        "file": result[0]["id"],
        "title": result[0]["title"],
        "user": message.from_user.mention,
        "video_id": result[0]["id"],
        "vc_type": "video" if video else "voice",
        "force": force,
    }
    await player.play(hell, context)
