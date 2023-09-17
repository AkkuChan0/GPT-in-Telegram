import calendar
import os
import sqlite3
from datetime import date, timedelta, datetime
import json
import subprocess

from aiogram import types
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from vosk import Model, KaldiRecognizer

from default_data import bot
from info import character_elli


# Отправка сообщения об активности пользователей в специальный чат
async def activityHandler(message: str) -> None:
    await bot.send_message(os.environ["CONSOLE_CHAT"], message)


async def isSubscribed(message: types.Message) -> bool:
    chat = os.environ["BFTBOT_NEWS"]
    sub = await bot.get_chat_member(chat_id=chat, user_id=message.from_user.id)
    if sub.status != types.ChatMemberStatus.LEFT:
        return True
    return False


# БД, которая хранит информацию о чате и её пользователях для сбора статистики
class ElliDataBase:
    chats = {}

    def __init__(self):
        self.db = sqlite3.connect('data_base/chats.sql', check_same_thread=False)
        self.cur = self.db.cursor()
        self.cur.execute("""CREATE TABLE IF NOT EXISTS chats (
            chat_id TEXT PRIMARY KEY,
            chat_name TEXT,
            user_count INTEGER,
            character_elli TEXT,
            status TEXT,
            available_sub TEXT,
            given TEXT,
            response_count INTEGER,
            response_all INTEGER,
            voice_response_count INTEGER,
            voice_response_all INTEGER,
            image_response_count INTEGER,
            image_response_all INTEGER,
            gift TEXT
        )""")
        self.db.commit()

        self.sh = AsyncIOScheduler()
        self.sh.add_job(self.timeUpdateSchedule, 'cron', hour=21, minute=0)
        self.sh.start()

        self.chats = {}

    def startLoadChatInfo(self) -> None:
        self.cur.execute("SELECT * FROM chats")
        if not self.cur.fetchone() is None:
            for chat in self.cur.fetchall():
                self.chats[str(chat[0])] = {"chat_name": chat[1],
                                            "user_count": chat[2],
                                            "character_elli": chat[3],
                                            "status": chat[4],
                                            "available_sub": chat[5],
                                            "given": chat[6],
                                            "response_count": chat[7],
                                            "response_all": chat[8],
                                            "voice_response_count": chat[9],
                                            "voice_response_all": chat[10],
                                            "image_response_count": chat[11],
                                            "image_response_all": chat[12],
                                            "gift": chat[13]}
        else:
            print("Данные не загружены или отсутствуют.")

    def saveChatInfo(self, chat_id: int) -> None:
        self.cur.execute(f"SELECT * FROM chats WHERE chat_id = '{str(chat_id)}'")
        if self.cur.fetchone() is None:
            self.cur.execute("INSERT INTO chats VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                             (str(chat_id),
                              self.chats[str(chat_id)]["chat_name"],
                              self.chats[str(chat_id)]["user_count"],
                              self.chats[str(chat_id)]["character_elli"],
                              self.chats[str(chat_id)]["status"],
                              self.chats[str(chat_id)]["available_sub"],
                              self.chats[str(chat_id)]["given"],
                              self.chats[str(chat_id)]["response_count"],
                              self.chats[str(chat_id)]["response_all"],
                              self.chats[str(chat_id)]["voice_response_count"],
                              self.chats[str(chat_id)]["voice_response_all"],
                              self.chats[str(chat_id)]["image_response_count"],
                              self.chats[str(chat_id)]["image_response_all"],
                              self.chats[str(chat_id)]["gift"]))
            self.db.commit()
        else:
            self.cur.execute(f"UPDATE chats SET chat_name = ?, user_count = ?, character_elli = ?, status = ?, \
            available_sub = ?, given = ?,response_count = ?, response_all = ?, voice_response_count = ?, \
            voice_response_all = ?, image_response_count = ?, image_response_all = ?, gift = ? WHERE chat_id = ?",
                             (self.chats[str(chat_id)]["chat_name"],
                              self.chats[str(chat_id)]["user_count"],
                              self.chats[str(chat_id)]["character_elli"],
                              self.chats[str(chat_id)]["status"],
                              self.chats[str(chat_id)]["available_sub"],
                              self.chats[str(chat_id)]["given"],
                              self.chats[str(chat_id)]["response_count"],
                              self.chats[str(chat_id)]["response_all"],
                              self.chats[str(chat_id)]["voice_response_count"],
                              self.chats[str(chat_id)]["voice_response_all"],
                              self.chats[str(chat_id)]["image_response_count"],
                              self.chats[str(chat_id)]["image_response_all"],
                              self.chats[str(chat_id)]["gift"],
                              str(chat_id)))
            self.db.commit()

    async def concreteChatInfo(self, message: types.Message) -> None:
        chat_id = message.chat.id

        self.cur.execute(f"SELECT * FROM chats WHERE chat_id = '{str(chat_id)}'")
        chat = self.cur.fetchone()
        if chat is not None:
            self.chats[str(chat[0])] = {"chat_name": str(chat[1]),
                                        "user_count": int(chat[2]),
                                        "character_elli": str(chat[3]),
                                        "status": str(chat[4]),
                                        "available_sub": str(chat[5]),
                                        "given": str(chat[6]),
                                        "response_count": int(chat[7]),
                                        "response_all": int(chat[8]),
                                        "voice_response_count": int(chat[9]),
                                        "voice_response_all": int(chat[10]),
                                        "image_response_count": int(chat[11]),
                                        "image_response_all": int(chat[12]),
                                        "gift": str(chat[13])}
        else:
            if message.chat.title is None:
                chat_name = (await bot.get_chat(message.from_user.id)).username
            else:
                chat_name = message.chat.title
            self.chats[str(chat_id)] = {"chat_name": chat_name,
                                        "user_count": int(await message.chat.get_members_count()),
                                        "character_elli": str(character_elli["default"]),
                                        "status": "False",
                                        "available_sub": "False",
                                        "given": "None",
                                        "response_count": 0,
                                        "response_all": 0,
                                        "voice_response_count": 0,
                                        "voice_response_all": 0,
                                        "image_response_count": 0,
                                        "image_response_all": 0,
                                        "gift": "True"}
            self.cur.execute("INSERT INTO chats VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                             (str(chat_id),
                              self.chats[str(chat_id)]["chat_name"],
                              self.chats[str(chat_id)]["user_count"],
                              self.chats[str(chat_id)]["character_elli"],
                              self.chats[str(chat_id)]["status"],
                              self.chats[str(chat_id)]["available_sub"],
                              self.chats[str(chat_id)]["given"],
                              self.chats[str(chat_id)]["response_count"],
                              self.chats[str(chat_id)]["response_all"],
                              self.chats[str(chat_id)]["voice_response_count"],
                              self.chats[str(chat_id)]["voice_response_all"],
                              self.chats[str(chat_id)]["image_response_count"],
                              self.chats[str(chat_id)]["image_response_all"],
                              self.chats[str(chat_id)]["gift"]))
            self.db.commit()

            await message.reply("Бот был полностью обновлён! Вырезана дуэльная часть, улучшена поддержка Элли.")

            await activityHandler(f"Добавлен новый чат: {self.chats[str(chat_id)]['chat_name']} ({chat_id})")

    def loadChatInfo(self, chat_id: int) -> bool:
        self.cur.execute(f"SELECT * FROM chats WHERE chat_id = '{str(chat_id)}'")
        chat = self.cur.fetchone()
        if chat is not None:
            self.chats[str(chat[0])] = {"chat_name": str(chat[1]),
                                        "user_count": int(chat[2]),
                                        "character_elli": str(chat[3]),
                                        "status": str(chat[4]),
                                        "available_sub": str(chat[5]),
                                        "given": str(chat[6]),
                                        "response_count": int(chat[7]),
                                        "response_all": int(chat[8]),
                                        "voice_response_count": int(chat[9]),
                                        "voice_response_all": int(chat[10]),
                                        "image_response_count": int(chat[11]),
                                        "image_response_all": int(chat[12]),
                                        "gift": str(chat[13])}
            return True

        return False

    def getChats(self) -> list:
        self.startLoadChatInfo()
        return list(self.chats.keys())

    def getChatsInfo(self) -> dict:
        self.startLoadChatInfo()
        user_count = 0
        response_count = 0

        chat_count = len(self.chats)
        for chat in self.chats:
            user_count += self.chats[chat]["user_count"] - 1
            response_count += self.chats[chat]["response_count"]
        return {"user_count": user_count,
                "response_count": response_count,
                "chat_count": chat_count}

    def clearChatInfo(self, chat_id: int) -> None:
        self.cur.execute(f"DELETE FROM chats WHERE chat_id = '{str(chat_id)}'")
        self.db.commit()

    def getChatInfo(self, chat_id: int) -> dict:
        self.loadChatInfo(chat_id)
        return self.chats[str(chat_id)]

    def addResponse(self, chat_id: int, rtype: str = None) -> None:
        self.loadChatInfo(chat_id)
        match rtype:
            case "voice":
                self.chats[str(chat_id)]["voice_response_count"] += 1
                self.chats[str(chat_id)]["voice_response_all"] += 1
            case "image":
                self.chats[str(chat_id)]["image_response_count"] += 1
                self.chats[str(chat_id)]["image_response_all"] += 1
            case _:
                self.chats[str(chat_id)]["response_count"] += 1
        self.chats[str(chat_id)]["response_all"] += 1
        self.saveChatInfo(chat_id)

    def clearResponse(self, chat_id=None) -> None:
        if chat_id is None:
            self.startLoadChatInfo()
            for chat in self.chats:
                self.chats[chat]["response_count"] = 0
                self.chats[chat]["voice_response_count"] = 0
                self.chats[chat]["image_response_count"] = 0
                self.saveChatInfo(int(chat))
        else:
            self.loadChatInfo(chat_id)
            self.chats[str(chat_id)]["response_count"] = 0
            self.chats[str(chat_id)]["voice_response_count"] = 0
            self.chats[str(chat_id)]["image_response_count"] = 0
            self.saveChatInfo(chat_id)

    def checkResponse(self, chat_id: int) -> bool:
        self.loadChatInfo(chat_id)
        status = self.getSubscribe(chat_id)
        if status["status"] == "Стандарт":
            return self.chats[str(chat_id)]["response_count"] < 50
        else:
            return self.chats[str(chat_id)]["response_count"] < 150

    def checkVoiceResponse(self, chat_id: int) -> bool:
        self.loadChatInfo(chat_id)
        status = self.getSubscribe(chat_id)
        if status["status"] == "Стандарт":
            return self.chats[str(chat_id)]["voice_response_count"] < 5
        else:
            return self.chats[str(chat_id)]["voice_response_count"] < 15

    def checkImageResponse(self, chat_id: int) -> bool:
        self.loadChatInfo(chat_id)
        status = self.getSubscribe(chat_id)
        if status["status"] == "Стандарт":
            return self.chats[str(chat_id)]["image_response_count"] < 5
        else:
            return self.chats[str(chat_id)]["image_response_count"] < 15

    def getResponseCount(self, chat_id: int) -> dict:
        self.loadChatInfo(chat_id)
        return {"balance": self.chats[str(chat_id)]["response_count"],
                "count": self.chats[str(chat_id)]["response_all"],
                "voice_balance": self.chats[str(chat_id)]["voice_response_count"],
                "voice_count": self.chats[str(chat_id)]["voice_response_all"],
                "image_balance": self.chats[str(chat_id)]["image_response_count"],
                "image_count": self.chats[str(chat_id)]["image_response_all"]}

    def changeCharacter(self, chat_id: int, character: str) -> None:
        self.chats[str(chat_id)]["character_elli"] = character
        self.saveChatInfo(chat_id)

    def getCharacter(self, chat_id: int) -> str:
        self.loadChatInfo(chat_id)

        return self.chats[str(chat_id)]["character_elli"]

    def setGift(self, chat_id: int) -> bool:
        self.loadChatInfo(chat_id)

        if self.chats[str(chat_id)]["gift"] == "True":
            self.setSubscribe(chat_id, 7)
            self.chats[str(chat_id)]["gift"] = "False"
            self.saveChatInfo(chat_id)

            return True
        else:
            return False

    def clearAllGift(self) -> None:
        self.startLoadChatInfo()
        for chat in self.chats:
            self.chats[chat]["gift"] = "False"
            self.saveChatInfo(int(chat))

    def setSubscribe(self, chat_id: int, days: int = None) -> None:
        """
        Метод, который устанавливает подписку на месяц.

        :param days: количество дней
        :param chat_id: уникальный идентификатор чата
        """
        self.loadChatInfo(chat_id)
        if self.chats[str(chat_id)]["status"] == "False":
            today = date.today()
        else:
            today = date.fromisoformat(self.chats[str(chat_id)]["status"])
        if not days:
            days = calendar.monthrange(today.year, today.month)[1]
        next_month_date = today + timedelta(days=days)
        self.chats[str(chat_id)]["status"] = str(next_month_date)
        self.chats[str(chat_id)]["available_sub"] = "True"
        self.saveChatInfo(chat_id)

    def setAllSubscribe(self) -> None:
        for chat in self.chats:
            self.setSubscribe(chat)

    def getSubscribe(self, chat_id: int) -> dict:
        """
        Метод, который проверяет, есть ли подписка у пользователя.

        :param chat_id: Уникальный идентификатор чата
        """
        self.loadChatInfo(chat_id)
        if self.chats[str(chat_id)]["status"] == "False":
            return {"status": "Стандарт",
                    "available": "False",
                    "date": "None",
                    "given": "None"}
        else:
            return {"status": "Подписка.",
                    "available": "True",
                    "date": self.chats[str(chat_id)]["status"],
                    "given": self.chats[str(chat_id)]["given"]}

    def checkSubscribe(self) -> None:
        self.startLoadChatInfo()
        for chat in self.chats:
            if not self.chats[chat]["status"] == "False":
                today = date.today()
                if today > datetime.strptime(self.chats[chat]["status"], "%Y-%m-%d").date():
                    self.chats[chat]["status"] = "False"
                    self.chats[chat]["available_sub"] = "False"
                    self.chats[chat]["given"] = "None"

    def swapSubscribe(self, user_id: int, chat_id: int) -> None:
        self.loadChatInfo(chat_id)
        self.loadChatInfo(user_id)
        if self.chats[str(chat_id)]["status"] == "False":
            self.chats[str(chat_id)]["status"] = self.chats[str(user_id)]["status"]
        else:
            today = date.today()
            days = calendar.monthrange(today.year, today.month)[1]
            self.chats[str(chat_id)]["status"] = \
                datetime.strptime(self.chats[str(chat_id)]["status"], "%Y-%m-%d").date() + timedelta(days=days)

        self.chats[str(user_id)]["given"], self.chats[str(chat_id)]["given"] \
            = self.chats[str(chat_id)]["chat_name"], self.chats[str(user_id)]["chat_name"]
        self.chats[str(user_id)]["available_sub"] = "False"
        self.saveChatInfo(user_id)
        self.saveChatInfo(chat_id)

    def timeUpdateSchedule(self) -> None:
        self.checkSubscribe()
        self.clearResponse()


elli_bot = ElliDataBase()


# Класс для работы и хранения сообщений в чате для контекста бота
class ElliMemory:

    def __init__(self):
        self.messages = dict()
        self.queue = list()

    def checkTokens(self, chat_id: int) -> None:
        context_size = 0
        if elli_bot.getSubscribe(chat_id)["status"] == "Стандарт":
            limit = 6500
        else:
            limit = 13000
        if str(chat_id) not in self.messages:
            self.toDefaultMessage(chat_id)
        for msg in self.messages[str(chat_id)]:
            if context_size > limit:
                context_size -= len(self.messages[chat_id][1])
                self.messages[str(chat_id)].pop(1)
            context_size += len(msg["content"])

    def addMessage(self, chat_id: int, role: str, message: str) -> None:
        if str(chat_id) not in self.messages:
            print(elli_bot.getCharacter(chat_id))
            self.changeCharacter(chat_id, elli_bot.getCharacter(chat_id))
        self.messages[str(chat_id)].append({"role": role,
                                            "content": message})
        self.checkTokens(chat_id)

    def getMessages(self, chat_id: int) -> list:
        if str(chat_id) not in self.messages:
            print(1)
            self.toDefaultMessage(chat_id)
        return self.messages[str(chat_id)]

    def clearMessages(self, chat_id: int) -> None:
        if str(chat_id) not in self.messages:
            self.toDefaultMessage(chat_id)
        del self.messages[str(chat_id)][1::]

    def toDefaultMessage(self, chat_id: int) -> None:
        self.messages[str(chat_id)] = []
        self.messages[str(chat_id)].append({"role": "system", "content": character_elli["default"]})

    def changeCharacter(self, chat_id: int, character: str) -> None:
        self.messages[str(chat_id)] = []
        self.messages[str(chat_id)].append({"role": "system", "content": character})
        elli_bot.changeCharacter(chat_id, character)

    async def addQueue(self, user_id: int) -> None:
        self.queue.append(user_id)

    async def delQueue(self) -> None:
        try:
            del self.queue[0]
        except:
            pass

    def getQueue(self) -> list:
        return self.queue


# Скопировал с Хабра: https://habr.com/ru/articles/694632/
class ElliSTT:

    default_init = {
        "model_path": "model/vosk",  # путь к папке с файлами STT модели Vosk
        "sample_rate": 16000,
        "ffmpeg_path": "ffmpeg"  # путь к ffmpeg
    }

    def __init__(self,
                 model_path=None,
                 sample_rate=None,
                 ffmpeg_path=None
                 ) -> None:
        """
        Настройка модели Vosk для распознавания аудио и
        преобразования его в текст.

        :arg model_path:  str путь до модели Vosk
        :arg sample_rate: int частота выборки, обычно 16000
        :arg ffmpeg_path: str путь к ffmpeg
        """
        self.model_path = model_path if model_path else ElliSTT.default_init["model_path"]
        self.sample_rate = sample_rate if sample_rate else ElliSTT.default_init["sample_rate"]
        self.ffmpeg_path = ffmpeg_path if ffmpeg_path else ElliSTT.default_init["ffmpeg_path"]

        model = Model(self.model_path)
        self.recognizer = KaldiRecognizer(model, self.sample_rate)
        self.recognizer.SetWords(True)

    def audio_to_text(self, audio_file_name=None) -> str:

        # Конвертация аудио в wav и результат в process.stdout
        process = subprocess.Popen(
            [self.ffmpeg_path,
             "-loglevel", "quiet",
             "-i", audio_file_name,
             "-ar", str(self.sample_rate),
             "-ac", "1",
             "-f", "s16le",
             "-"
             ],
            stdout=subprocess.PIPE
        )

        while True:
            data = process.stdout.read(4000)
            if len(data) == 0:
                break
            if self.recognizer.AcceptWaveform(data):
                pass

        result_json = self.recognizer.FinalResult()
        result_dict = json.loads(result_json)
        return result_dict["text"]
