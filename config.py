from os import getenv

from dotenv import load_dotenv
from pyrogram import filters

load_dotenv()

class Config(object):
    # required config variables
    API_HASH = "b35b715fe8dc0a58e8048988286fc5b6"             # get from my.telegram.org
    API_ID = 25742938                # get from my.telegram.org
    BOT_TOKEN = "7614786681:AAEqGbq3jQ3XK3Nx9JmGLN8_SNOjUwpWQ9Q"              # get from @BotFather
    DATABASE_URL = "mongodb+srv://BADMUNDA:BADMYDAD@badhacker.i5nw9na.mongodb.net/"     # from https://cloud.mongodb.com/
    HELLBOT_SESSION = "BQGIzloAr4p6_F7Pio7Jirj1-_ry579AlrwJaurALELnkENhuRsZoZm4wEaKI6jlp5kSkFURVPDLzWVwy25Kp8OF0VhuWufeItruEenA9S6hl0EgJmmhz5ZVyMtLLt8dwc15tG-bUEKYUQo_lOE1R9xU8h0CLIlRrkuXG4yaDbz5Hly-kyqYRM69oOUqzQ1J234_n3K-6a55uZvOZSyd2hjKW4kh9LzHAcaYptaNqOnrP1cwogr8Cs7gOl02cohpIfPvKQ6UmSa2-HBScwsdW5Yypv3LUWJx96AHTCNliNy6OG6gwJbCchBNFfNdwZQ2Vu7tpxp52hsoP7IpkP_5RIWSU4lecQAAAAGyMKeQAA"  # enter your session string here
    LOGGER_ID = "-1002093247039         # make a channel and get its ID
    OWNER_ID = 7009601543              # enter your id here

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
