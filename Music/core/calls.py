import datetime
import os

from pyrogram.enums import ChatMemberStatus
from pyrogram.errors import (
    ChatAdminRequired,
    UserAlreadyParticipant,
    UserNotParticipant,
)
from pyrogram.types import InlineKeyboardMarkup
from pytgcalls import PyTgCalls, filters
from pytgcalls.exceptions import (
    AlreadyJoinedError,
    NoActiveGroupCall,
)
from pytgcalls.types import (
    AudioQuality, 
    VideoQuality,
)
from config import Config
from Music.helpers.buttons import Buttons
from Music.helpers.strings import TEXTS
from Music.utils.exceptions import (
    ChangeVCException,
    JoinGCException,
    JoinVCException,
    UserException,
)
from ntgcalls import TelegramServerError
from pytgcalls.types import (
    GroupCallParticipant,
    MediaStream,
    ChatUpdate, 
    Update,
)
from pytgcalls.types.stream import StreamAudioEnded

from Music.utils.queue import Queue
from Music.utils.thumbnail import thumb
from Music.utils.youtube import ytube

from .clients import hellbot
from .database import db
from .logger import LOGS

from ntgcalls import StreamType

async def __clean__(chat_id: int, force: bool):
    if force:
        Queue.rm_queue(chat_id, 0)
    else:
        Queue.clear_queue(chat_id)
    await db.remove_active_vc(chat_id)


class HellMusic(PyTgCalls):
    def __init__(self):
        super().__init__(hellbot.user)
        self.audience = {}

    async def join_call(self, chat_id: int, input_stream, stream_type):
        try:
            await self.join_group_call(chat_id, input_stream, stream_type)
        except Exception as e:
            raise UserException(f"[UserException]: {e}")

    async def join_vc(self, chat_id: int, file_path: str, video: bool = False):
        # Define input stream
        if video:
            input_stream = MediaStream(
                file_path, AudioQuality.MEDIUM, VideoQuality.MEDIUM
            )
            stream_type = StreamType().video_stream
        else:
            input_stream = MediaStream(file_path, AudioQuality.MEDIUM)
            stream_type = StreamType().pulse_stream  # Fixed this line

        # Join VC
        try:
            await self.join_call(chat_id, input_stream, stream_type)
        except NoActiveGroupCall:
            try:
                await self.join_gc(chat_id)
            except Exception as e:
                await self.leave_vc(chat_id)
                raise JoinGCException(e)
            try:
                await self.join_call(chat_id, input_stream, stream_type)
            except Exception as e:
                await self.leave_vc(chat_id)
                raise JoinVCException(f"[JoinVCException]: {e}")
        except AlreadyJoinedError:
            raise UserException(
                f"[UserException]: Already joined in the voice chat. If this is a mistake then try to restart the voice chat."
            )
        except Exception as e:
            raise UserException(f"[UserException]: {e}")

        await db.add_active_vc(chat_id, "video" if video else "voice")
        self.audience[chat_id] = {}
        users = await self.vc_participants(chat_id)
        user_ids = [user.user_id for user in users]
        await self.autoend(chat_id, user_ids)


hellmusic = HellMusic()
