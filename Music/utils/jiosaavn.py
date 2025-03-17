import asyncio
import aiohttp
import os
import time
import re
from typing import Union
from bs4 import BeautifulSoup
import logging

class JioSaavnAPI:
    def __init__(self):
        self.base = "https://www.jiosaavn.com"
        self.regex = r"(?:jiosaavn\.com)"
        self.audio_opts = {"format": "bestaudio[ext=m4a]"}
        self.video_opts = {
            "format": "best",
            "addmetadata": True,
            "key": "FFmpegMetadata",
            "prefer_ffmpeg": True,
            "geo_bypass": True,
            "nocheckcertificate": True,
            "postprocessors": [
                {"key": "FFmpegVideoConvertor", "preferedformat": "mp4"}
            ],
            "outtmpl": "%(id)s.mp4",
            "logtostderr": False,
            "quiet": True,
        }

    def check(self, link: str):
        return bool(re.match(self.regex, link))

    async def format_link(self, link: str) -> str:
        link = link.strip()
        if "&" in link:
            link = link.split("&")[0]
        return link

    async def search_song(self, song_name: str):
        """Search for a song by its name."""
        search_url = f"{self.base}/search/?query={song_name.replace(' ', '%20')}"
        async with aiohttp.ClientSession() as session:
            async with session.get(search_url) as response:
                if response.status != 200:
                    return None
                
                soup = BeautifulSoup(await response.text(), "html.parser")
                song_data = soup.find("div", class_="result-song")
                
                if not song_data:
                    return None
                
                song_id = song_data.find("a")["href"].split("/")[-1]
                title = song_data.find("span", class_="title").text.strip()
                artist = song_data.find("span", class_="sub-title").text.strip()
                song_url = f"{self.base}/song/{song_id}"
                
                return {"title": title, "artist": artist, "song_url": song_url}

    async def get_song_details(self, link: str):
        """Scrape JioSaavn for song details."""
        song_id = link.split("/")[-1]  # Assuming the song ID is at the end of the URL
        url = f"{self.base}/song/{song_id}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    return None
                
                soup = BeautifulSoup(await response.text(), "html.parser")
                title = soup.find("h1", class_="song-title").text.strip()
                artist = soup.find("a", class_="singer-name").text.strip()
                thumbnail = soup.find("img", class_="song-artwork")['src']
                song_url = soup.find("source", {'type': 'audio/mp4'})['src']
                
                return {
                    "title": title,
                    "artist": artist,
                    "thumbnail": thumbnail,
                    "song_url": song_url,
                }

    async def download_song(self, link: str, video: bool = False) -> str:
        """Download the song using aiohttp."""
        details = await self.get_song_details(link)
        if not details:
            return None

        song_url = details['song_url']
        song_title = details['title']
        song_path = f"downloads/{song_title}.mp3" if not video else f"downloads/{song_title}.mp4"
        
        # Download song using aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.get(song_url) as response:
                with open(song_path, "wb") as f:
                    f.write(await response.read())
        
        return song_path

    async def play_song(self, link: str):
        """Play the song by downloading it."""
        song_path = await self.download_song(link)
        if not song_path:
            return "Song not found or error occurred!"
        
        return f"Now playing: {song_path}"

    async def get_lyrics(self, song: str, artist: str) -> dict:
        # Implementation for getting lyrics using an API like Genius
        pass

    async def get_playlist(self, link: str) -> list:
        # Implementation for getting playlist details
        pass

    async def get_data(self, link: str, limit: int = 1) -> list:
        # Implementation for getting data about a song
        pass

    async def details(self, link: str) -> dict:
        # Implementation for getting detailed information about a song
        pass

    async def duration(self, link: str) -> str:
        # Implementation for getting duration of a song
        pass

    async def thumbnail(self, link: str) -> str:
        # Implementation for getting thumbnail of a song
        pass

    async def send_song(
        self, message: str, rand_key: str, key: int, video: bool = False
    ) -> dict:
        # Implementation for sending song details
        pass

    async def download(
        self, link: str, video: Union[bool, str] = False, videoid: Union[bool, str] = None
    ) -> str:
        # Implementation for downloading the song in various formats
        pass

async def main():
    logging.basicConfig(level=logging.DEBUG)
    jio_saavn_api = JioSaavnAPI()
    query = "Your Song Name"  # Replace with your actual query

    try:
        # Example usage
        song_details = await jio_saavn_api.search_song(query)
        logging.debug(f"JioSaavn result: {song_details}")
        if not song_details:
            logging.debug("Song not found on JioSaavn.")
        else:
            logging.debug(f"Found song: {song_details['title']} by {song_details['artist']}")
    except Exception as e:
        logging.debug(f"An error occurred: {e}")

JioSaavn = JioSaavnAPI()
