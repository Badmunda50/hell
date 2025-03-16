from os import getenv

from dotenv import load_dotenv
from pyrogram import filters

load_dotenv()

class Config(object):
    # required config variables
    API_HASH = "b35b715fe8dc0a58e8048988286fc5b6"             # get from my.telegram.org
    API_ID = 25742938                # get from my.telegram.org
    BOT_TOKEN = "7693811299:AAGHUfvr3OHMsOeOMBBUwycSGsQ3-dhKCHE"              # get from @BotFather
    DATABASE_URL = "mongodb+srv://BADMUNDA:BADMYDAD@badhacker.i5nw9na.mongodb.net/"     # from https://cloud.mongodb.com/
    HELLBOT_SESSION = "BQGIzloAfTzsHcVU6ZeD55a-1vlAm8VbeoLXHNdFya6IsRY4Aq9oE9VdzVOr1vaVF96qvaJ81fBc5KvVxwSXEwk0FBy7kbFO3yFw8Tey8vPkrFX0UmnhMcHpp0_77l2gF2wZ2t2crJNQpAgJFcq-TLQWSPU3cgTc6202iyRFHvGuC-e8mPLhN3OCE4qPdBH8ggwCAl2JekXKAAAqn6zpmJXt7iOksGPZExqNRPqM4KDGPyDJ2MAzKhtGa4WKqnk-Gp8a71QXWLAqJhdu717Bd4shI7y1m3JV6POJKxV-_dYWINXU3lQtg1zOotw4hdhHJ6cSH7gzSqPG4ZrYmByjP7aci-1i4QAAAAG82-HiAA"  # enter your session string here
    LOGGER_ID = -1002093247039         # make a channel and get its ID
    OWNER_ID = getenv("OWNER_ID", "7588172591")              # enter your id here

    # optional config variables
    BLACK_IMG = getenv("BLACK_IMG", "https://telegra.ph/file/2c546060b20dfd7c1ff2d.jpg")        # black image for progress
    BOT_NAME = getenv("BOT_NAME", "\x40\x4d\x75\x73\x69\x63\x5f\x48\x65\x6c\x6c\x42\x6f\x74")   # dont put fancy texts here.
    BOT_PIC = getenv("BOT_PIC", "https://te.legra.ph/file/5d5642103804ae180e40b.jpg")           # put direct link to image here
    LEADERBOARD_TIME = getenv("LEADERBOARD_TIME", "3:00")   # time in 24hr format for leaderboard broadcast
    LYRICS_API = getenv("LYRICS_API", None)             # from https://docs.genius.com/
    MAX_FAVORITES = int(getenv("MAX_FAVORITES", 30))    # max number of favorite tracks
    PLAY_LIMIT = int(getenv("PLAY_LIMIT", 0))           # time in minutes. 0 for no limit
    PRIVATE_MODE = getenv("PRIVATE_MODE", "off")        # "on" or "off" to enable/disable private mode
    SONG_LIMIT = int(getenv("SONG_LIMIT", 0))           # time in minutes. 0 for no limit
    TELEGRAM_IMG = getenv("TELEGRAM_IMG", None)         # put direct link to image here
    TG_AUDIO_SIZE_LIMIT = int(getenv("TG_AUDIO_SIZE_LIMIT", 104857600))     # size in bytes. 0 for no limit
    TG_VIDEO_SIZE_LIMIT = int(getenv("TG_VIDEO_SIZE_LIMIT", 1073741824))    # size in bytes. 0 for no limit
    TZ = getenv("TZ", "Asia/Kolkata")   # https://en.wikipedia.org/wiki/List_of_tz_database_time_zones

    # do not edit these variables
    BANNED_USERS = filters.user()
    CACHE = {}
    CACHE_DIR = "./cache/"
    DELETE_DICT = {}
    DWL_DIR = "./downloads/"
    GOD_USERS = filters.user()
    PLAYER_CACHE = {}
    QUEUE_CACHE =  {}
    SONG_CACHE = {}
    SUDO_USERS = filters.user()


# get all config variables in a list
all_vars = [i for i in Config.__dict__.keys() if not i.startswith("__")]
