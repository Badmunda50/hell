from pyrogram import filters
from pyrogram.types import CallbackQuery, Message

from config import Config
from Music.core.clients import hellbot
from Music.core.decorators import UserWrapper, check_mode
from Music.helpers.formatters import formatter
from Music.utils.pages import MakePages
from Music.utils.youtube import ytube

# Define the COOKIES_FILE variable
COOKIES_FILE = 'cookies/cookies.txt'

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
