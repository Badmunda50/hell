import asyncio
import requests
from bs4 import BeautifulSoup

class JioSaavnAPI:
    def __init__(self):
        self.base = "https://www.jiosaavn.com"
        self.regex = r"(?:jiosaavn\.com)"
    
    async def search_song(self, song_name: str):
        """Search for a song by its name."""
        search_url = f"{self.base}/search/?query={song_name.replace(' ', '%20')}"
        response = requests.get(search_url)
        
        if response.status_code != 200:
            return None
        
        soup = BeautifulSoup(response.content, "html.parser")
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
        
        response = requests.get(url)
        if response.status_code != 200:
            return None
        
        soup = BeautifulSoup(response.content, "html.parser")
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
    
    async def download_song(self, song_name: str):
        """Download the song after searching it."""
        details = await self.search_song(song_name)
        if not details:
            return None

        song_url = details['song_url']
        song_title = details['title']
        song_path = f"downloads/{song_title}.mp3"
        
        # Download song using requests
        with open(song_path, "wb") as f:
            response = requests.get(song_url)
            f.write(response.content)
        
        return song_path
    
    async def play_song(self, song_name: str):
        """Play the song by searching its name and downloading it."""
        song_path = await self.download_song(song_name)
        if not song_path:
            return "Song not found or error occurred!"
        
        return f"Now playing: {song_path}"
