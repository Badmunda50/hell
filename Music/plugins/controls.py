from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup

from config import Config
from Music.core.calls import hellmusic
from Music.core.clients import hellbot
from Music.core.database import db
from Music.core.decorators import AuthWrapper, check_mode
from Music.helpers.formatters import formatter
from Music.utils.play import player
from Music.utils.queue import Queue
from Music.utils.youtube import ytube


def speed_markup(_, chat_id):
    upl = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    text="🕒 0.5x",
                    callback_data=f"SpeedUP {chat_id}|0.5",
                ),
                InlineKeyboardButton(
                    text="🕓 0.75x",
                    callback_data=f"SpeedUP {chat_id}|0.75",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🕓 0.00x",
                    callback_data=f"SpeedUP {chat_id}|1.0",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🕤 1.5x",
                    callback_data=f"SpeedUP {chat_id}|1.5",
                ),
                InlineKeyboardButton(
                    text="🕛 2.0x",
                    callback_data=f"SpeedUP {chat_id}|2.0",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=_["CLOSE_BUTTON"],
                    callback_data="close",
                ),
            ],
        ]
    )
    return upl


def bass_markup(_, chat_id):
    upl = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    text="🔉 10×",
                    callback_data=f"BassUP {chat_id}|10",
                ),
                InlineKeyboardButton(
                    text="🔉 20×",
                    callback_data=f"BassUP {chat_id}|20",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🔉 00×",  # Default Bass Level with 00 added
                    callback_data=f"BassUP {chat_id}|1",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🔊 30×",
                    callback_data=f"BassUP {chat_id}|30",
                ),
                InlineKeyboardButton(
                    text="🔊 40×",
                    callback_data=f"BassUP {chat_id}|40",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🔊 50×",
                    callback_data=f"BassUP {chat_id}|50",
                ),
                InlineKeyboardButton(
                    text="🔊 60×",
                    callback_data=f"BassUP {chat_id}|60",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🔊 70×",
                    callback_data=f"BassUP {chat_id}|70",
                ),
                InlineKeyboardButton(
                    text="🔊 80×",
                    callback_data=f"BassUP {chat_id}|80",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🔊 90×",
                    callback_data=f"BassUP {chat_id}|90",
                ),
                InlineKeyboardButton(
                    text="🔊 100×",
                    callback_data=f"BassUP {chat_id}|100",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=_["CLOSE_BUTTON"],
                    callback_data="close",
                ),
            ],
        ]
    )
    return upl


@hellbot.app.on_message(
    filters.command("speed") & filters.group & ~Config.BANNED_USERS
)
@check_mode
@AuthWrapper
async def adjust_speed(_, message: Message):
    if len(message.command) < 2:
        buttons = speed_markup(_, message.chat.id)
        return await message.reply_text(
            "Please specify the speed value! \n\n**Example:** \n`/speed 1.5`",
            reply_markup=buttons
        )
    try:
        value = float(message.command[1])
    except ValueError:
        return await message.reply_text("Please enter a valid number!")

    if value not in [0.5, 1.0, 1.5]:
        return await message.reply_text("Valid speed values are 0.5, 1.0, 1.5")
    await hellmusic.adjust_speed(message.chat.id, value)
    return await message.reply_text(
        f"Voice chat speed adjusted to {value}x by {message.from_user.mention}"
    )


@hellbot.app.on_message(
    filters.command("bass") & filters.group & ~Config.BANNED_USERS
)
@check_mode
@AuthWrapper
async def adjust_bass(_, message: Message):
    if len(message.command) < 2:
        buttons = bass_markup(_, message.chat.id)
        return await message.reply_text(
            "Please specify the bass value! \n\n**Example:** \n`/bass 40`",
            reply_markup=buttons
        )
    try:
        value = float(message.command[1])
    except ValueError:
        return await message.reply_text("Please enter a valid number!")

    if value not in [20, 40, 60]:
        return await message.reply_text("Valid bass values are 20, 40, 60")
    await hellmusic.adjust_bass(message.chat.id, value)
    return await message.reply_text(
        f"Bass boosted to {value}x by {message.from_user.mention}"
    )


@hellbot.app.on_message(
    filters.command(["mute", "unmute"]) & filters.group & ~Config.BANNED_USERS
)
@check_mode
@AuthWrapper
async def mute_unmute(_, message: Message):
    is_muted = await db.get_watcher(message.chat.id, "mute")
    if message.command[0][0] == "u":
        if is_muted:
            await db.set_watcher(message.chat.id, "mute", False)
            await hellmusic.unmute_vc(message.chat.id)
            return await message.reply_text(
                f"__VC Unmuted by:__ {message.from_user.mention}"
            )
        else:
            return await message.reply_text("Voice Chat is not muted!")
    else:
        if is_muted:
            return await message.reply_text("Voice Chat is already muted!")
        else:
            await db.set_watcher(message.chat.id, "mute", True)
            await hellmusic.mute_vc(message.chat.id)
            return await message.reply_text(
                f"__VC Muted by:__ {message.from_user.mention}"
            )


@hellbot.app.on_message(
    filters.command(["pause", "resume"]) & filters.group & ~Config.BANNED_USERS
)
@check_mode
@AuthWrapper
async def pause_resume(_, message: Message):
    is_paused = await db.get_watcher(message.chat.id, "pause")
    if message.command[0][0] == "r":
        if is_paused:
            await db.set_watcher(message.chat.id, "pause", False)
            await hellmusic.resume_vc(message.chat.id)
            return await message.reply_text(
                f"__VC Resumed by:__ {message.from_user.mention}"
            )
        else:
            return await message.reply_text("Voice Chat is not paused!")
    else:
        if is_paused:
            return await message.reply_text("Voice Chat is already paused!")
        else:
            await db.set_watcher(message.chat.id, "pause", True)
            await hellmusic.pause_vc(message.chat.id)
            return await message.reply_text(
                f"__VC Paused by:__ {message.from_user.mention}"
            )


@hellbot.app.on_message(
    filters.command(["stop", "end"]) & filters.group & ~Config.BANNED_USERS
)
@check_mode
@AuthWrapper
async def stop_end(_, message: Message):
    await hellmusic.leave_vc(message.chat.id)
    await db.set_loop(message.chat.id, 0)
    await message.reply_text(f"__VC Stopped by:__ {message.from_user.mention}")


@hellbot.app.on_message(filters.command("loop") & filters.group & ~Config.BANNED_USERS)
@check_mode
@AuthWrapper
async def loop(_, message: Message):
    if len(message.command) < 2:
        return await message.reply_text(
            "Please specify the number of times to loop the song! \n\nMaximum loop range is **10**. Give **0** to disable loop."
        )
    try:
        loop = int(message.command[1])
    except Exception:
        return await message.reply_text(
            "Please enter a valid number! \n\nMaximum loop range is **10**. Give **0** to disable loop."
        )
    is_loop = await db.get_loop(message.chat.id)
    if loop == 0:
        if is_loop == 0:
            return await message.reply_text("There is no active loop in this chat!")
        await db.set_loop(message.chat.id, 0)
        return await message.reply_text(
            f"__Loop disabled by:__ {message.from_user.mention}\n\nPrevious loop was: `{is_loop}`"
        )
    if 1 <= loop <= 10:
        final = is_loop + loop
        final = 10 if final > 10 else final
        await db.set_loop(message.chat.id, final)
        await message.reply_text(
            f"__Loop set to:__ `{final}`\n__By:__ {message.from_user.mention} \n\nPrevious loop was: `{is_loop}`"
        )
    else:
        return await message.reply_text(
            "Please enter a valid number! \n\nMaximum loop range is **10**. Give **0** to disable loop."
        )


@hellbot.app.on_message(
    filters.command("replay") & filters.group & ~Config.BANNED_USERS
)
@check_mode
@AuthWrapper
async def replay(_, message: Message):
    is_active = await db.is_active_vc(message.chat.id)
    if not is_active:
        return await message.reply_text("No active Voice Chat found here!")
    hell = await message.reply_text("Replaying...")
    que = Queue.get_queue(message.chat.id)
    if que == []:
        return await hell.edit("No songs in the queue to replay!")
    await player.replay(message.chat.id, hell)


@hellbot.app.on_message(filters.command("skip") & filters.group & ~Config.BANNED_USERS)
@check_mode
@AuthWrapper
async def skip(_, message: Message):
    is_active = await db.is_active_vc(message.chat.id)
    if not is_active:
        return await message.reply_text("No active Voice Chat found here!")
    hell = await message.reply_text("Processing ...")
    que = Queue.get_queue(message.chat.id)
    if que == []:
        return await hell.edit("No songs in the queue to skip!")
    if len(que) == 1:
        return await hell.edit_text(
            "No more songs in queue to skip! Use /end or /stop to stop the VC."
        )
    is_loop = await db.get_loop(message.chat.id)
    if is_loop != 0:
        await hell.edit_text("Disabled Loop to skip the current song!")
        await db.set_loop(message.chat.id, 0)
    await player.skip(message.chat.id, hell)


@hellbot.app.on_message(filters.command("seek") & filters.group & ~Config.BANNED_USERS)
@check_mode
@AuthWrapper
async def seek(_, message: Message):
    is_active = await db.is_active_vc(message.chat.id)
    if not is_active:
        return await message.reply_text("No active Voice Chat found here!")
    if len(message.command) < 2:
        return await message.reply_text(
            "Please specify the time to seek! \n\n**Example:** \n__- Seek  10 secs forward >__ `/seek 10`. \n__- Seek  10 secs backward >__ `/seek -10`."
        )
    hell = await message.reply_text("Seeking...")
    try:
        if message.command[1][0] == "-":
            seek_time = int(message.command[1][1:])
            seek_type = 0  # backward
        else:
            seek_time = int(message.command[1])
            seek_type = 1  # forward
    except:
        return await hell.edit_text("Please enter numeric characters only!")
    que = Queue.get_queue(message.chat.id)
    if que == []:
        return await hell.edit_text("No songs in the queue to seek!")
    played = int(que[0]["played"])
    duration = formatter.mins_to_secs(que[0]["duration"])
    if seek_type == 0:
        if (played - seek_time) <= 10:
            return await hell.edit_text(
                "Cannot seek when only 10 seconds are left! Use a lesser value."
            )
        to_seek = played - seek_time
    else:
        if (duration - (played + seek_time)) <= 10:
            return await hell.edit_text(
                "Cannot seek when only 10 seconds are left! Use a lesser value."
            )
        to_seek = played + seek_time
    video = True if que[0]["vc_type"] == "video" else False
    if que[0]["file"] == que[0]["video_id"]:
        file_path = await ytube.download(que[0]["video_id"], True, video)
    else:
        file_path = que[0]["file"]
    try:
        context = {
            "chat_id": que[0]["chat_id"],
            "file": file_path,
            "duration": que[0]["duration"],
            "seek": formatter.secs_to_mins(to_seek),
            "video": video,
        }
        await hellmusic.seek_vc(context)
    except:
        return await hell.edit_text("Something went wrong!")
    Queue.update_duration(message.chat.id, seek_type, seek_time)
    await hell.edit_text(
        f"Seeked `{seek_time}` seconds {'forward' if seek_type == 1 else 'backward'}!"
            )
