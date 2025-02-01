from pyrogram import filters
from pyrogram.types import CallbackQuery, Message

from config import Config
from Music.core.clients import hellbot
from Music.core.decorators import UserWrapper, check_mode
from Music.helpers.formatters import formatter
from Music.utils.pages import MakePages

import asyncio
import os
import re
import time
from typing import Union
import requests
import yt_dlp
from lyricsgenius import Genius
from youtubesearchpython.__future__ import VideosSearch
from Music.helpers.strings import TEXTS


# Define the COOKIES_FILE variable
COOKIES_FILE = 'cookies/cookies.txt'

async def shell_cmd(cmd):
    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    out, errorz = await proc.communicate()
    if errorz:
        if "unavailable videos are hidden" in (errorz.decode("utf-8")).lower():
            return out.decode("utf-8")
        else:
            return errorz.decode("utf-8")
    return out.decode("utf-8")

def is_on_off(value: int) -> bool:
    return value == 1

class YouTube:
    async def get_data(self, link: str, video_id: bool, limit: int = 1, cookies_file: str = None) -> list:
        yt_url = await self.format_link(link, video_id)
        collection = []
        results = VideosSearch(yt_url, limit=limit)
        for result in (await results.next())["result"]:
            vid = result["id"]
            channel = result["channel"]["name"]
            channel_url = result["channel"]["link"]
            duration = result["duration"]
            published = result["publishedTime"]
            thumbnail = f"https://i.ytimg.com/vi/{result['id']}/hqdefault.jpg"
            title = result["title"]
            url = result["link"]
            views = result["viewCount"]["short"]
            context = {
                "id": vid,
                "ch_link": channel_url,
                "channel": channel,
                "duration": duration,
                "link": url,
                "published": published,
                "thumbnail": thumbnail,
                "title": title,
                "views": views,
            }
            collection.append(context)
        return collection[:limit]

    async def send_song(self, message: CallbackQuery, rand_key: str, key: int, video: bool = False, cookies_file: str = None) -> dict:
        track = Config.SONG_CACHE[rand_key][key]
        ydl_opts = self.video_opts if video else self.audio_opts
        if cookies_file:
            ydl_opts["cookiefile"] = cookies_file
        hell = await message.message.reply_text("Downloading...")
        await message.message.delete()
        try:
            output = None
            thumb = f"{track['id']}{time.time()}.jpg"
            _thumb = requests.get(track["thumbnail"], allow_redirects=True)
            open(thumb, "wb").write(_thumb.content)
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                yt_file = ydl.extract_info(track["link"], download=video)
                if not video:
                    output = ydl.prepare_filename(yt_file)
                    ydl.process_info(yt_file)
                    await message.message.reply_audio(
                        audio=output,
                        caption=TEXTS.SONG_CAPTION.format(
                            track["title"],
                            track["link"],
                            track["views"],
                            track["duration"],
                            message.from_user.mention,
                            hellbot.app.mention,
                        ),
                        duration=int(yt_file["duration"]),
                        performer=TEXTS.PERFORMER,
                        title=yt_file["title"],
                        thumb=thumb,
                    )
                else:
                    output = f"{yt_file['id']}.mp4"
                    await message.message.reply_video(
                        video=output,
                        caption=TEXTS.SONG_CAPTION.format(
                            track["title"],
                            track["link"],
                            track["views"],
                            track["duration"],
                            message.from_user.mention,
                            hellbot.app.mention,
                        ),
                        duration=int(yt_file["duration"]),
                        thumb=thumb,
                        supports_streaming=True,
                    )
            chat = message.message.chat.title or message.message.chat.first_name
            await hellbot.logit(
                "Video" if video else "Audio",
                f"**⤷ User:** {message.from_user.mention} [`{message.from_user.id}`]\n**⤷ Chat:** {chat} [`{message.message.chat.id}`]\n**⤷ Link:** [{track['title']}]({track['link']})",
            )
            await hell.delete()
        except Exception as e:
            await hell.edit_text(f"**Error:**\n`{e}`")
        try:
            Config.SONG_CACHE.pop(rand_key)
            os.remove(thumb)
            os.remove(output)
        except Exception:
            pass

    async def format_link(self, link: str, video_id: bool) -> str:
        link = link.strip()
        if video_id:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        return link

ytube = YouTube()

@hellbot.app.on_message(filters.command("song") & ~Config.BANNED_USERS)
@check_mode
@UserWrapper
async def songs(_, message: Message):
    if len(message.command) == 1:
        return await message.reply_text("Nothing given to search.")
    query = message.text.split(None, 1)[1]
    hell = await message.reply_photo(
        Config.BLACK_IMG, caption=f"<b><i>Searching</i></b> “`{query}`” ..."
    )
    all_tracks = await ytube.get_data(query, False, 10, COOKIES_FILE)
    rand_key = formatter.gen_key(str(message.from_user.id), 5)
    Config.SONG_CACHE[rand_key] = all_tracks
    await MakePages.song_page(hell, rand_key, 0)

@hellbot.app.on_callback_query(filters.regex(r"song_dl(.*)$") & ~Config.BANNED_USERS)
async def song_cb(_, cb: CallbackQuery):
    _, action, key, rand_key = cb.data.split("|")
    user = rand_key.split("_")[0]
    key = int(key)
    if cb.from_user.id != int(user):
        await cb.answer("You are not allowed to do that!", show_alert=True)
        return
    if action == "adl":
        await ytube.send_song(cb, rand_key, key, False, COOKIES_FILE)
        return
    elif action == "vdl":
        await ytube.send_song(cb, rand_key, key, True, COOKIES_FILE)
        return
    elif action == "close":
        Config.SONG_CACHE.pop(rand_key)
        await cb.message.delete()
        return
    else:
        all_tracks = Config.SONG_CACHE[rand_key]
        length = len(all_tracks)
        if key == 0 and action == "prev":
            key = length - 1
        elif key == length - 1 and action == "next":
            key = 0
        else:
            key = key + 1 if action == "next" else key - 1
    await MakePages.song_page(cb, rand_key, key)
