from pyrogram import filters
from pyrogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton

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
from Music.core.logger import LOGS
from lyricsgenius import Genius
from youtubesearchpython.__future__ import VideosSearch
from youtube_search import YoutubeSearch
from Music.helpers.strings import TEXTS


# Define the COOKIES_FILE variable
COOKIES_FILE = 'cookies/cookies.txt'

# Define a dictionary to track the last message timestamp for each user
user_last_message_time = {}
user_command_count = {}

# Define the threshold for command spamming (e.g., 2 commands within 5 seconds)
SPAM_THRESHOLD = 2
SPAM_WINDOW_SECONDS = 5

# Quality options for songs
SONG_QUALITY_OPTIONS = {
    'low': 'worstaudio',
    'medium': 'bestaudio[ext=m4a]',
    'high': 'bestaudio'
}

# Quality options for videos
VIDEO_QUALITY_OPTIONS = {
    '144p': '144',
    '240p': '240',
    '360p': '360',
    '480p': '480',
    '720p': '720',
    '1080p': '1080',
    '1440p': '1440',
    '2160p': '2160',
}

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
    def __init__(self):
        self.audio_opts = {
            'format': 'bestaudio/best',
            'outtmpl': '%(id)s.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }
        self.video_opts = {
            'format': 'bestvideo+bestaudio',
            'outtmpl': '%(id)s.%(ext)s',
        }

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
                    if os.path.exists(output):
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
                        raise ValueError(f"Failed to decode {output}. The file does not exist.")
                else:
                    output = f"{yt_file['id']}.mp4"
                    if os.path.exists(output):
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
                    else:
                        raise ValueError(f"Failed to decode {output}. The file does not exist.")
            chat = message.message.chat.title or message.message.chat.first_name
            await hellbot.logit(
                "Video" if video else "Audio",
                f"**⤷ User:** {message.from_user.mention} [`{message.from_user.id}`]\n**⤷ Chat:** {chat} [`{message.message.chat.id}`]\n**⤷ Link:** [{track['title']}]({track['link']})",
            )
            await hell.delete()
        except Exception as e:
            LOGS.error(f"Error sending song: {e}")
            await hell.edit_text(f"**Error:**\n`{e}`")
        try:
            Config.SONG_CACHE.pop(rand_key)
            if os.path.exists(thumb):
                os.remove(thumb)
            if output and os.path.exists(output):
                os.remove(output)
        except Exception as e:
            LOGS.error(f"Error cleaning up files: {e}")

    async def format_link(self, link: str, video_id: bool) -> str:
        link = link.strip()
        if video_id:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        return link

ytube = YouTube()

async def send_quality_buttons(message: Message, query: str, type: str, thumbnail: str, sizes: list):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"{size} MB", callback_data=f"{type}_{query}_{index}")]
        for index, size in enumerate(sizes)
    ])
    await message.reply_photo(photo=thumbnail, caption="ꜱᴇʟᴇᴄᴛ Qᴜᴀʟɪᴛʏ ᴍᴘ3:", reply_markup=keyboard)

async def send_video_quality_buttons(message: Message, query: str, thumbnail: str):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"144p", callback_data=f"video_{query}_144p"), 
         InlineKeyboardButton(f"240p", callback_data=f"video_{query}_240p"),
         InlineKeyboardButton(f"360p", callback_data=f"video_{query}_360p")],
        [InlineKeyboardButton(f"480p", callback_data=f"video_{query}_480p"), 
         InlineKeyboardButton(f"720p", callback_data=f"video_{query}_720p"),
         InlineKeyboardButton(f"1080p", callback_data=f"video_{query}_1080p")],
        [InlineKeyboardButton(f"1440p", callback_data=f"video_{query}_1440p"), 
         InlineKeyboardButton(f"2160p", callback_data=f"video_{query}_2160p")]
    ])
    await message.reply_photo(photo=thumbnail, caption="ꜱᴇʟᴇᴄᴛ Qᴜᴀʟɪᴛʏ ᴍᴘ4:", reply_markup=keyboard)

@hellbot.app.on_message(filters.command("song") & ~Config.BANNED_USERS)
@check_mode
@UserWrapper
async def songs(_, message: Message):
    user_id = message.from_user.id
    current_time = time()
    
    # Spam protection: Prevent multiple commands within a short time
    last_message_time = user_last_message_time.get(user_id, 0)
    if current_time - last_message_time < SPAM_WINDOW_SECONDS:
        user_last_message_time[user_id] = current_time
        user_command_count[user_id] = user_command_count.get(user_id, 0) + 1
        if user_command_count[user_id] > SPAM_THRESHOLD:
            hu = await message.reply_text(f"**{message.from_user.mention} ᴘʟᴇᴀsᴇ ᴅᴏɴᴛ ᴅᴏ sᴘᴀᴍ, ᴀɴᴅ ᴛʀʏ ᴀɢᴀɪɴ ᴀғᴛᴇʀ 5 sᴇᴄ**")
            await asyncio.sleep(3)
            await hu.delete()
            return
    else:
        user_command_count[user_id] = 1
        user_last_message_time[user_id] = current_time
    
    query = " ".join(message.command[1:])
    if not query:
        await message.reply("Please provide a song name or URL to search for.")
        return

    await message.delete()

    results = YoutubeSearch(query, max_results=1).to_dict()
    if not results:
        await message.reply("⚠️ No results found. Please make sure you typed the correct name.")
        return

    thumbnail = results[0]["thumbnails"][0]
    
    sizes = []
    for quality in SONG_QUALITY_OPTIONS.values():
        ydl_opts = {
            "format": quality,
            "noplaylist": True,
            "quiet": True,
            "logtostderr": False,
            "cookiefile": COOKIES_FILE,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(f"https://youtube.com{results[0]['url_suffix']}", download=False)
            size = info_dict.get('filesize') or info_dict.get('filesize_approx') or 0
            sizes.append(size / (1024 * 1024))

    await send_quality_buttons(message, query, 'song', thumbnail, [f"{size:.2f}" for size in sizes])

@hellbot.app.on_message(filters.command("video") & ~Config.BANNED_USERS)
@check_mode
@UserWrapper
async def download_video(_, message: Message):
    user_id = message.from_user.id
    current_time = time()
    
    last_message_time = user_last_message_time.get(user_id, 0)
    if current_time - last_message_time < SPAM_WINDOW_SECONDS:
        user_last_message_time[user_id] = current_time
        user_command_count[user_id] = user_command_count.get(user_id, 0) + 1
        if user_command_count[user_id] > SPAM_THRESHOLD:
            hu = await message.reply_text(f"**{message.from_user.mention} ᴘʟᴇᴀsᴇ ᴅᴏɴᴛ ᴅᴏ sᴘᴀᴍ, ᴀɴᴅ ᴛʀʏ ᴀɢᴀɪɴ ᴀғᴛᴇʀ 5 sᴇᴄ**")
            await asyncio.sleep(3)
            await hu.delete()
            return
    else:
        user_command_count[user_id] = 1
        user_last_message_time[user_id] = current_time
    
    query = " ".join(message.command[1:])
    if not query:
        await message.reply("Please provide a video name or URL to search for.")
        return

    await message.delete()

    results = YoutubeSearch(query, max_results=1).to_dict()
    if not results:
        await message.reply("⚠️ No results found. Please make sure you typed the correct name.")
        return

    thumbnail = results[0]["thumbnails"][0]
    
    await send_video_quality_buttons(message, query, thumbnail)

@hellbot.app.on_callback_query(filters.regex(r"^(song|video)_(.+)_(\d+)$"))
async def callback_query_handler(client, query):
    type, query_text, quality_index = query.data.split("_")
    
    if type == "song":
        quality = list(SONG_QUALITY_OPTIONS.values())[int(quality_index)]
        ydl_opts = {
            "format": quality,
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }],
            "noplaylist": True,
            "quiet": True,
            "logtostderr": False,
            "cookiefile": COOKIES_FILE,
        }
    else:
        quality = list(VIDEO_QUALITY_OPTIONS.values())[int(quality_index)]
        ydl_opts = {
            "format": f"bestvideo[ext=mp4][height<={quality}]+bestaudio/best[ext=mp4][height<={quality}]",
            "noplaylist": True,
            "quiet": True,
            "logtostderr": False,
            "cookiefile": COOKIES_FILE,
        }

    try:
        m = await query.message.reply("🔄 **Searching...**")
        results = YoutubeSearch(query_text, max_results=1).to_dict()
        if not results:
            await m.edit("**⚠️ No results found. Please make sure you typed the correct name.**")
            return

        link = f"https://youtube.com{results[0]['url_suffix']}"
        title = results[0]["title"]
        thumbnail = results[0]["thumbnails"][0]
        thumb_name = f"{title}.jpg"
        
        thumb = requests.get(thumbnail, allow_redirects=True)
        open(thumb_name, "wb").write(thumb.content)
        duration = results[0]["duration"]
        views = results[0]["views"]
        channel_name = results[0]["channel"]

        await m.edit("📥 **Downloading...**")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(link, download=False)
            file = ydl.prepare_filename(info_dict)
            ydl.download([link])

        dur = sum(int(x) * 60 ** i for i, x in enumerate(reversed(duration.split(":"))))
        
        await m.edit("📤 **Uploading...**")
        if type == "song":
            await query.message.reply_audio(
                file,
                thumb=thumb_name,
                title=title,
                caption=f"{title}\nRequested by ➪ {query.from_user.mention}\nViews ➪ {views}\nChannel ➪ {channel_name}",
                duration=dur
            )
        else:
            await query.message.reply_video(
                file,
                thumb=thumb_name,
                caption=f"{title}\nRequested by ➪ {query.from_user.mention}\nViews ➪ {views}\nChannel ➪ {channel_name}",
                duration=dur
            )

        os.remove(file)
        os.remove(thumb_name)
        await m.delete()

    except Exception as e:
        await m.edit("⚠️ **An error occurred!**")
        print(f"Error: {str(e)}")
