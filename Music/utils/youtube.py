import asyncio
import os
import re
import time
from typing import Union

import requests
import yt_dlp
from lyricsgenius import Genius
from pyrogram.types import CallbackQuery, Message
from youtubesearchpython.__future__ import VideosSearch

from config import Config
from Music.core.clients import hellbot
from Music.core.logger import LOGS
from Music.helpers.strings import TEXTS


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


cookies_file = "cookies/cookies.txt"

def is_on_off(value: int) -> bool:
    # Example implementation, replace with your actual logic
    return value == 1

class YouTube:
    # Existing code...

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

ytube = YouTube()

    async def format_link(self, link: str, video_id: bool) -> str:
        link = link.strip()
        if video_id:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        return link

    async def get_data(self, link: str, video_id: bool, limit: int = 1) -> list:
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

    async def get_playlist(self, link: str) -> list:
        yt_url = await self.format_link(link, False)
        with yt_dlp.YoutubeDL(self.yt_playlist_opts) as ydl:
            results = ydl.extract_info(yt_url, False)
            playlist = [video['id'] for video in results['entries']]
        return playlist

    async def download(self, link: str, video_id: bool, video: bool = False) -> str:
        yt_url = await self.format_link(link, video_id)
        if video:
            dlp = yt_dlp.YoutubeDL(self.yt_opts_video)
            info = dlp.extract_info(yt_url, False)
        else:
            dlp = yt_dlp.YoutubeDL(self.yt_opts_audio)
            info = dlp.extract_info(yt_url, False)
        path = os.path.join("downloads", f"{info['id']}.{info['ext']}")
        if not os.path.exists(path):
            dlp.download([yt_url])
        return path

    async def send_song(
        self, message: CallbackQuery, rand_key: str, key: int, video: bool = False
    ) -> dict:
        track = Config.SONG_CACHE[rand_key][key]
        ydl_opts = self.video_opts if video else self.audio_opts
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

    async def get_lyrics(self, song: str, artist: str) -> dict:
        context = {}
        if not self.client:
            return context
        results = self.client.search_song(song, artist)
        if results:
            results.to_dict()
            title = results["full_title"]
            image = results["song_art_image_url"]
            lyrics = results["lyrics"]
            context = {
                "title": title,
                "image": image,
                "lyrics": lyrics,
            }
        return context

    async def details(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            title = result["title"]
            duration_min = result["duration"]
            thumbnail = result["thumbnails"][0]["url"].split("?")[0]
            vidid = result["id"]
            if str(duration_min) == "None":
                duration_sec = 0
            else:
                duration_sec = int(time_to_seconds(duration_min))
        return title, duration_min, duration_sec, thumbnail, vidid

    async def title(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            title = result["title"]
        return title

    async def duration(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            duration = result["duration"]
        return duration

    async def thumbnail(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            thumbnail = result["thumbnails"][0]["url"].split("?")[0]
        return thumbnail

    async def video(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        proc = await asyncio.create_subprocess_exec(
            "yt-dlp",
            "--cookies", cookies_file,
            "-g",
            "-f",
            "best[height<=?720][width<=?1280]",
            f"{link}",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        if stdout:
            return 1, stdout.decode().split("\n")[0]
        else:
            return 0, stderr.decode()

    async def playlist(self, link, limit, user_id, videoid: Union[bool, str] = None):
        if videoid:
            link = self.listbase + link
        if "&" in link:
            link = link.split("&")[0]
        playlist = await shell_cmd(
            f"yt-dlp --cookies {cookies_file} -i --get-id --flat-playlist --playlist-end {limit} --skip-download {link}"
        )
        try:
            result = playlist.split("\n")
            for key in result:
                if key == "":
                    result.remove(key)
        except:
            result = []
        return result

    async def track(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            title = result["title"]
            duration_min = result["duration"]
            vidid = result["id"]
            yturl = result["link"]
            thumbnail = result["thumbnails"][0]["url"].split("?")[0]
        track_details = {
            "title": title,
            "link": yturl,
            "vidid": vidid,
            "duration_min": duration_min,
            "thumb": thumbnail,
        }
        return track_details, vidid

    async def formats(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        ytdl_opts = {"quiet": True, "cookiefile": cookies_file}
        ydl = yt_dlp.YoutubeDL(ytdl_opts)
        with ydl:
            formats_available = []
            r = ydl.extract_info(link, download=False)
            for format in r["formats"]:
                try:
                    str(format["format"])
                except:
                    continue
                if not "dash" in str(format["format"]).lower():
                    try:
                        format["format"]
                        format["filesize"]
                        format["format_id"]
                        format["ext"]
                        format["format_note"]
                    except:
                        continue
                    formats_available.append(
                        {
                            "format": format["format"],
                            "filesize": format["filesize"],
                            "format_id": format["format_id"],
                            "ext": format["ext"],
                            "format_note": format["format_note"],
                            "yturl": link,
                        }
                    )
        return formats_available, link

    async def slider(
        self,
        link: str,
        query_type: int,
        videoid: Union[bool, str] = None,
    ):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        a = VideosSearch(link, limit=10)
        result = (await a.next()).get("result")
        title = result[query_type]["title"]
        duration_min = result[query_type]["duration"]
        vidid = result[query_type]["id"]
        thumbnail = result[query_type]["thumbnails"][0]["url"].split("?")[0]
        return title, duration_min, thumbnail, vidid

    async def download(
        self,
        link: str,
        mystic,
        video: Union[bool, str] = None,
        videoid: Union[bool, str] = None,
        songaudio: Union[bool, str] = None,
        songvideo: Union[bool, str] = None,
        format_id: Union[bool, str] = None,
        title: Union[bool, str] = None,
    ) -> str:
        if videoid:
            link = self.base + link
        loop = asyncio.get_running_loop()

        def audio_dl():
            ydl_optssx = {
                "format": "bestaudio/best",
                "outtmpl": "downloads/%(id)s.%(ext)s",
                "geo_bypass": True,
                "nocheckcertificate": True,
                "quiet": True,
                "no_warnings": True,
                "cookiefile": cookies_file,
            }
            x = yt_dlp.YoutubeDL(ydl_optssx)
            info = x.extract_info(link, False)
            xyz = os.path.join("downloads", f"{info['id']}.{info['ext']}")
            if os.path.exists(xyz):
                return xyz
            x.download([link])
            return xyz

        def video_dl():
            ydl_optssx = {
                "format": "(bestvideo[height<=?720][width<=?1280][ext=mp4])+(bestaudio[ext=m4a])",
                "outtmpl": "downloads/%(id)s.%(ext)s",
                "geo_bypass": True,
                "nocheckcertificate": True,
                "quiet": True,
                "no_warnings": True,
                "cookiefile": cookies_file,
            }
            x = yt_dlp.YoutubeDL(ydl_optssx)
            info = x.extract_info(link, False)
            xyz = os.path.join("downloads", f"{info['id']}.{info['ext']}")
            if os.path.exists(xyz):
                return xyz
            x.download([link])
            return xyz

        def song_video_dl():
            formats = f"{format_id}+140"
            fpath = f"downloads/{title}"
            ydl_optssx = {
                "format": formats,
                "outtmpl": fpath,
                "geo_bypass": True,
                "nocheckcertificate": True,
                "quiet": True,
                "no_warnings": True,
                "prefer_ffmpeg": True,
                "merge_output_format": "mp4",
                "cookiefile": cookies_file,  # Add cookie file option here
            }
            x = yt_dlp.YoutubeDL(ydl_optssx)
            x.download([link])

        def song_audio_dl():
            fpath = f"downloads/{title}.%(ext)s"
            ydl_optssx = {
                "format": format_id,
                "outtmpl": fpath,
                "geo_bypass": True,
                "nocheckcertificate": True,
                "quiet": True,
                "no_warnings": True,
                "prefer_ffmpeg": True,
                "postprocessors": [
                    {
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                        "preferredquality": "192",
                    }
                ],
                "cookiefile": cookies_file,  # Add cookie file option here
            }
            x = yt_dlp.YoutubeDL(ydl_optssx)
            x.download([link])

        if songvideo:
            await loop.run_in_executor(None, song_video_dl)
            fpath = f"downloads/{title}.mp4"
            return fpath
        elif songaudio:
            await loop.run_in_executor(None, song_audio_dl)
            fpath = f"downloads/{title}.mp3"
            return fpath
        elif video:
            if is_on_off(1):
                direct = True
                downloaded_file = await loop.run_in_executor(None, video_dl)
            else:
                proc = await asyncio.create_subprocess_exec(
                    "yt-dlp",
                    "--cookies", cookies_file,
                    "-g",
                    "-f",
                    "best[height<=?720][width<=?1280]",
                    f"{link}",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, stderr = await proc.communicate()
                if stdout:
                    downloaded_file = stdout.decode().split("\n")[0]
                    direct = None
                else:
                    return
        else:
            direct = True
            downloaded_file = await loop.run_in_executor(None, audio_dl)
        return downloaded_file, direct
        
ytube = YouTube()
