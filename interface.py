import os
import re
from datetime import datetime
from pathlib import Path

from aiogram import types
from aiogram.types import ChatActions
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram import exceptions

from elli import createResponse, changeCharacterHandler, em
from default_data import bot
from info import words, MESSAGES, WHITELIST, words_image
from data import elli_bot, activityHandler, ElliSTT, isSubscribed

elli_stt = ElliSTT()

PRICE = types.LabeledPrice(label="Подписка", amount=6900)


async def startHandler(message: types.Message) -> None:

    await elli_bot.concreteChatInfo(message)

    await message.reply(
        f"""Привет всем, я Элли, ваша новая собеседница в Telegram. Рада присоединиться к вашему чату.
Надеюсь, мы сможем найти общий язык и наслаждаться временем, проведённым вместе. *улыбается*

Если вы хотите узнать, что я умею, напишите <u>/help</u>""", parse_mode=types.ParseMode.HTML)


async def helpHandler(message: types.Message) -> None:

    await elli_bot.concreteChatInfo(message)

    await message.reply(
        f"""Я умею:

  <b>1. Разговаривать с вами.</b>
  <b>2. Помогать вам.</b>
  <b>3. Помогать другим.</b>
  <b>4. Запоминать наш диалог и использовать его для ответа.</b>
  <b>5. Рисовать по вашему запросу</b> (просто попроси. Ключевые слова: <i>нарисуй, portray</i>).
  <b>6. Отвечать на ваши голосовые сообщения (пока только в ЛС).</b>

Для вышеперечисленного просто отвечайте на мои сообщения или используйте ключевые слова: <i>Элли, Elli, БФТБот, BFTBot</i> (регистр не имеет значения).
В ЛС упоминание бота необязательно.

Также имеются дополнительные функции:

  <b>1. Могу поменять свой характер на желаемый вами</b>, для этого ответьте на сообщение, в котором написан мой новый характер, командой <u>/change</u>.
  <b>2. Могу забыть о всём</b>, о чём мы говорили, если это мешает диалогу, командой <u>/clear.</u>
  <b>3. Могу вернуться к заводским настройкам</b> в любое время командой <u>/default.</u>
  <b>4. Могу выдать вам информацию о чате</b> командой <u>/profile</u>
  <b>5. Могу выдать вам общую небольшую статистику</b> командой <u>/statistic</u>
  <b>6.</b> Ну и конечно же <b>могу продать вам свои повышенные лимиты за 69 рублей.</b> Команда <u>/buy</u> в ЛС. Подробности там же.""", parse_mode=types.ParseMode.HTML)


async def profileHandler(message: types.Message) -> None:
    chat_id = message.chat.id
    user_id = message.from_user.id

    await elli_bot.concreteChatInfo(message)

    if message.chat.title is None:
        chat_name = (await bot.get_chat(message.from_user.id)).username
    else:
        chat_name = message.chat.title

    response_count = elli_bot.getResponseCount(chat_id)
    status = elli_bot.getSubscribe(chat_id)
    if status["status"] == "Стандарт":
        response_count["balance"] = f"{50 - response_count['balance']}/50"
        response_count["image_balance"] = f"{5 - response_count['image_balance']}/5"
        if chat_id == user_id:
            response_count["voice_balance"] = str(5 - response_count["voice_balance"]) + "/5"
        else:
            response_count["voice_balance"] = "Только в ЛС."
            response_count["voice_count"] = "Только в ЛС."

        await message.reply(f"""Профиль чата: <b>{chat_name}</b>

Статус чата: <b>Стандарт.</b>

Осталось запросов в день: <b>{response_count["balance"]}</b>
Запросов за всё время: <b>{response_count["count"]}</b>

Осталось голосовых запросов в день: <b>{response_count["voice_balance"]}</b>
Голосовых запросов за всё время: <b>{response_count["voice_count"]}</b>

Осталось запросов на рисунок: <b>{response_count["image_balance"]}</b>
Запросов на рисунок за всё время: <b>{response_count["image_count"]}</b>
""", parse_mode=types.ParseMode.HTML)
    else:
        response_count["balance"] = f"{150 - response_count['balance']}/150"
        _temp = status["date"].split("-")
        _temp.reverse()
        _temp = '.'.join(_temp)
        response_count["image_balance"] = f"{15 - response_count['image_balance']}/15"

        if chat_id == user_id:
            response_count["voice_balance"] = str(15 - response_count["voice_balance"]) + "/15"
        else:
            response_count["voice_balance"] = "Только в ЛС."
            response_count["voice_count"] = "Только в ЛС."

        await message.reply(f"""Профиль чата: <b>{chat_name}</b>

Статус чата: <b>Подписка.</b>
Истекает: <b>{_temp}</b>
Подписка подарена: <b>{status["given"]}</b>

Осталось запросов в день: <b>{response_count["balance"]}</b>
Запросов за всё время: <b>{response_count["count"]}</b>

Осталось голосовых запросов в день: <b>{response_count["voice_balance"]}</b>
Голосовых запросов за всё время: <b>{response_count["voice_count"]}</b>

Осталось запросов на рисунок: <b>{response_count["image_balance"]}</b>
Запросов на рисунок за всё время: <b>{response_count["image_count"]}</b>
""", parse_mode=types.ParseMode.HTML)

        await activityHandler(f"{chat_id} | Вызван профиль.")


async def statisticHandler(message: types.Message) -> None:

    _temp = elli_bot.getChatsInfo()

    await message.reply(f"""Статистика:

Чатов: <b>{_temp["chat_count"]}</b>
Пользователей: <b>{_temp["user_count"]}</b>
Всего запросов: <b>{_temp["response_count"]}</b>""", parse_mode=types.ParseMode.HTML)


async def elliHandler(message: types.Message) -> None:
    chat_id = message.chat.id
    user_id = message.from_user.id
    username = (await bot.get_chat(user_id)).username
    full_name = (await bot.get_chat(user_id)).full_name

    await elli_bot.concreteChatInfo(message)

    parse = re.split(",| |/", message.text.lower().replace("?", " ").replace("!", " "))

    if message.text[0] == "/":
        return

    if user_id == bot.id or user_id == int(os.environ["OFFICIAL_CHANNEL"]):
        return

    if not words & set(parse) and not chat_id == user_id:
        if message.reply_to_message:
            if message.from_user.id == bot.id:
                return
            if not message.reply_to_message.from_user.id == bot.id:
                return
        else:
            return

    if message.reply_to_message:
        if message.from_user.id == bot.id:
            return

    if chat_id == user_id:
        if not await isSubscribed(message):
            button = InlineKeyboardButton(text="Подписаться", url="https://t.me/bftbot_news")
            url_ = InlineKeyboardMarkup(inline_keyboard=[[button]])
            await message.reply("Вижу, что вы не подписаны на наш официальный канал."
                                "\n\nПодпишитесь, чтобы знать о всех обновлениях!", reply_markup=url_)
            return

    if words_image & set(parse):
        await elliImageHandler(message)
        return

    status = elli_bot.getSubscribe(chat_id)
    if elli_bot.checkResponse(chat_id):
        elli_bot.addResponse(chat_id)
        if status["status"] == "Стандарт":
            if elli_bot.getResponseCount(chat_id)["balance"] == 45:
                await message.reply("<b>У вас осталось всего 5 запросов на этот день!</b>\
                                    \n\nУвеличьте свой лимит запросов до 150 всего за <b><u>69</u> </b><s>89</s> рублей в месяц.", parse_mode=types.ParseMode.HTML)
        else:
            if elli_bot.getResponseCount(chat_id)["balance"] == 145:
                await message.reply("<b>У вас осталось всего 5 запросов на этот день!</b>",
                                    parse_mode=types.ParseMode.HTML)
    else:
        if status["status"] == "Стандарт":
            await message.reply("Вы достигли лимита запроса в день.\
            \nЛимит: 50 запросов в день\
            \nПопробуйте завтра или купите подписку.")
        else:
            await message.reply("Вы достигли лимита запроса в день.\
            \nЛимит: 150 запросов в день\
            \nПопробуйте завтра.")
        return

    await bot.send_chat_action(chat_id, ChatActions.TYPING)

    response = await createResponse(chat_id, user_id, f"Сообщение от {full_name} ({username}) в {datetime.now()} UTC+0. chat_id для функций: {chat_id} :b:: {message.text}")

    await activityHandler(f"{chat_id} | Выполнен запрос к нейросети.")

    try:
        if len(response) > 4096:
            for x in range(0, len(response), 4096):
                await message.reply(response[x:x + 4096])
        else:
            await message.reply(response)
    except:
        await message.reply(response)


async def elliImageHandler(message: types.Message) -> None:
    chat_id = message.chat.id
    user_id = message.from_user.id

    await elli_bot.concreteChatInfo(message)

    status = elli_bot.getSubscribe(chat_id)
    if elli_bot.checkImageResponse(chat_id):
        elli_bot.addResponse(chat_id, rtype="image")
        if status["status"] == "Стандарт":
            if elli_bot.getResponseCount(chat_id)["image_balance"] == 3:
                await message.reply("<b>У вас осталось всего 2 запроса на этот день!</b>\
                                    \n\nУвеличьте свой лимит запросов до 15 всего за <b><u>69</u> </b><s>89</s> рублей в месяц.",
                                    parse_mode=types.ParseMode.HTML)
        else:
            if elli_bot.getResponseCount(chat_id)["image_balance"] == 13:
                await message.reply("<b>У вас осталось всего 2 запроса на этот день!</b>",
                                    parse_mode=types.ParseMode.HTML)
    else:
        if status["status"] == "Стандарт":
            await message.reply("Вы достигли лимита запроса в день.\
            \nЛимит: 5 запросов в день\
            \nПопробуйте завтра или купите подписку.")
        else:
            await message.reply("Вы достигли лимита запроса в день.\
            \nЛимит: 15 запросов в день\
            \nПопробуйте завтра.")
        return

    await bot.send_chat_action(chat_id, ChatActions.TYPING)

    parse = re.split(",| |/", message.text.lower().replace("?", " ").replace("!", " "))

    if parse[0] in words:
        del parse[0]

    response = await createResponse(chat_id, user_id, ' '.join(parse), rtype="image")

    await message.reply(response)

    await activityHandler(f"{chat_id} | Выполнен запрос на рисунок к нейросети.")


async def elliAudioHandler(message: types.Message):

    chat_id = message.chat.id
    user_id = message.from_user.id
    username = (await bot.get_chat(user_id)).username
    full_name = (await bot.get_chat(user_id)).full_name

    await elli_bot.concreteChatInfo(message)

    if not chat_id == user_id:
        return

    if not await isSubscribed(message):
        button = InlineKeyboardButton(text="Подписаться", url="https://t.me/bftbot_news")
        url_ = InlineKeyboardMarkup(inline_keyboard=[[button]])
        await message.reply("Вижу, что вы не подписаны на наш официальный канал."
                            "\n\nПодпишитесь, чтобы знать о всех обновлениях!", reply_markup=url_)
        return

    status = elli_bot.getSubscribe(chat_id)
    if elli_bot.checkVoiceResponse(chat_id):
        elli_bot.addResponse(chat_id, rtype="voice")
        if status["status"] == "Стандарт":
            if elli_bot.getResponseCount(chat_id)["voice_balance"] == 3:
                await message.reply("<b>У вас осталось всего 2 запросов на этот день!</b>\
                                    \n\nУвеличьте свой лимит запросов до 15 всего за <b><u>69</u> </b><s>89</s> рублей в месяц.", parse_mode=types.ParseMode.HTML)
        else:
            if elli_bot.getResponseCount(chat_id)["voice_balance"] == 13:
                await message.reply("<b>У вас осталось всего 2 запросов на этот день!</b>", parse_mode=types.ParseMode.HTML)
    else:
        if status["status"] == "Стандарт":
            await message.reply("Вы достигли лимита голосовых запроса в день.\
            \nЛимит: 5 запросов в день\
            \nПопробуйте завтра или купите подписку.")
        else:
            await message.reply("Вы достигли лимита голосовых запроса в день.\
            \nЛимит: 15 запросов в день\
            \nПопробуйте завтра.")
        return

    if message.content_type == types.ContentType.VOICE:
        file_id = message.voice.file_id
    elif message.content_type == types.ContentType.AUDIO:
        file_id = message.audio.file_id
    else:
        await message.reply("Прости, но формат не поддерживается.")
        return

    file = await bot.get_file(file_id)
    file_path = file.file_path
    file_on_disk = Path("", f"temp_voice/{file_id}.tmp")
    await bot.download_file(file_path, file_on_disk)

    result = elli_stt.audio_to_text(file_on_disk)

    os.remove(file_on_disk)

    if result:
        await message.reply(f"""Ваше голосовое сообщение:

{result}

<b><i>Ожидайте ответа...</i></b>""", parse_mode=types.ParseMode.HTML)

    else:
        await message.reply("Прости, но я не могу распознать твоё голосовое сообщение.")
        return

    response = await createResponse(chat_id, user_id, f"Сообщение от {full_name} ({username}) в {datetime.now()} UTC+0. chat_id для функций: {chat_id} :b:: {result}")

    await activityHandler(f"{chat_id} | Выполнен запрос к нейросети с помощью ГС.")

    try:
        if len(response) > 4096:
            for x in range(0, len(response), 4096):
                await message.reply(response[x:x + 4096])
        else:
            await message.reply(response)
    except:
        await message.reply(response)


async def elliChangeHandler(message: types.Message):

    chat_id = message.chat.id
    user_id = message.from_user.id

    await elli_bot.concreteChatInfo(message)

    if not message.reply_to_message or not message.reply_to_message.from_user.id == user_id:
        await message.reply("Опишите новый характер, которому будет стараться следовать нейросеть.\
        \nЧтобы установить новый характер, используйте команду <u>/change</u>, <b>ответив на своё сообщение с новым характером</b>.\
        \n\n<b>Пример характера:</b> Тебя зовут Анна, ты senior-разработчик C++.\
        \n<i>Но вы также можете экспериментировать и писать огромные данные.</i>\
        \n\nДля возвращения к начальному характеру используйте: <u>/default</u>", parse_mode=types.ParseMode.HTML)
        return

    await changeCharacterHandler(chat_id, message.reply_to_message.text)
    await message.reply(f"Характер успешно изменён: \n{message.reply_to_message.text}.")

    await activityHandler(f"{chat_id} | Изменён характер.")


async def elliClearHandler(message: types.Message):
    chat_id = message.chat.id

    await elli_bot.concreteChatInfo(message)

    em.clearMessages(chat_id)

    await message.reply("Память Элли была успешно отформатирована \
    \n\n<i>Теперь она вас не знает...</i>", parse_mode=types.ParseMode.HTML)

    await activityHandler(f"{chat_id} | Чат очищен.")


async def elliDefaultHandler(message: types.Message):
    chat_id = message.chat.id

    await elli_bot.concreteChatInfo(message)

    em.toDefaultMessage(chat_id)

    await message.reply("Характер возвращён к стандартным настройкам.\
    \n\n<i>Начните общение с самого начала.</i>", parse_mode=types.ParseMode.HTML)

    await activityHandler(f"{chat_id} | Характер установлен на стандартный.")


async def elliBuySubscribeHandler(message: types.Message):

    chat_id = message.chat.id
    user_id = message.from_user.id

    await elli_bot.concreteChatInfo(message)

    if not chat_id == user_id:
        await message.reply("Покупка подписки возможна только в ЛС Бота.\
            \n\nВ ЛС бота используйте команду /buy.")
        return

    if message.from_user.id not in WHITELIST:
        await message.reply("Покупка подписки временно недоступна.")
        return

    await message.reply("""Что даёт подписка:
<b>1. Увеличивает лимит текстовых запросов с 50 до 150;</b>
<b>2. Увеличивает лимит запросов на рисунок с 5 до 15;</b>
<b>3. Увеличивает лимит голосовых запросов с 5 до 15;</b>
<b>4. Увеличивает запоминаемую информацию с 6500 до 13000 символов;</b>
<b>5. Можно подарить подписку групповому чату;</b>
<b>6. Покупкой подписки вы помогаете поддерживать функционал бота;</b>""", parse_mode=types.ParseMode.HTML)
    await bot.send_invoice(
        chat_id,
        title=MESSAGES["tm_title"],
        description=MESSAGES['tm_desc'],
        provider_token=os.environ["PAYMENT_PROVIDER_TOKEN"],
        currency='rub',
        prices=[{"label": "Руб", "amount": 6900}],
        start_parameter='bftbot-subscribe',
        payload='month_sub'
    )

    await activityHandler(f"{chat_id} | Началась покупка подписки.")


async def elliProcessPaymentHandler(pre_checkout_query: types.PreCheckoutQuery):
    print(1)
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)


async def elliSuccessfulPaymentHandler(message: types.Message):
    chat_id = message.chat.id

    elli_bot.setSubscribe(chat_id)

    await message.reply(f"""<b>Подписка успешно приобретена.
Спасибо, что выбрали нашего бота!</b>

Подписка действительна до <b>{elli_bot.getSubscribe(chat_id)['date']}.</b>

Дополнительные плюшки получены.

Также вы можете подарить подписку любому групповому чату, где находится <b>Элли | BFTBot</b>, для этого просто используйте в \
нужном чате команду <b><u>/give.</u></b>""", parse_mode=types.ParseMode.HTML)

    await activityHandler(f"{chat_id} | Подписка успешно приобретена.")


async def elliGiveSubscribeHandler(message: types.Message):

    chat_id = message.chat.id
    user_id = message.from_user.id

    if not elli_bot.loadChatInfo(user_id):
        await message.reply("Не вижу вас в базе... Возможно, вы не писали мне в ЛС. \
                            \nДля выдачи подписки вам необходимо приобрести её у меня в ЛС.")
        return

    if elli_bot.getSubscribe(user_id)["status"] == "Стандарт":
        if chat_id == user_id:
            await message.reply("Вы не можете подарить подписку самому себе. Да и она отсутствует у вас. \
                                \nКупите подписку и используйте команду /give в канале, которому хотите подарить подписку.")
        else:
            await message.reply("Вижу, что мы связывались с вами, но... К сожалению, у вас отсутствует подписка.\
                                \nДля выдачи подписки вам необходимо приобрести её у меня в ЛС.")
        return

    if chat_id == user_id:
        await message.reply("Вы не можете подарить подписку самому себе. \
                            \nИспользуйте команду /give в канале, которому хотите подарить подписку.")
        return

    if not elli_bot.getSubscribe(user_id)["available"] == "False":
        await message.reply("Подписка у вас есть, однако вы уже подарили её. \
                            \nПродлите подписку на ещё один месяц и получите возможность подарить её вновь.")
        return

    elli_bot.swapSubscribe(user_id, chat_id)

    await message.reply("Вы успешно подарили подписку.")

    await activityHandler(f"{chat_id} | Подарена подписка пользователем {user_id}.")


"""
all : True/False ||| inline_url : url ||| inline_text : text ||| text : text
"""


async def botSendAllMessage(message: types.Message):

    if message.from_user.id not in WHITELIST:
        return

    if message.reply_to_message.photo:
        parse = message.reply_to_message.caption.split(" ||| ")
    else:
        parse = message.reply_to_message.text.split(" ||| ")

    info = {}

    _temp = parse[0].split(" : ")

    if _temp[0] == "all":
        match _temp[1]:
            case "True":
                info["all"] = True
            case "False":
                info["all"] = False
            case _:
                info["all"] = False

    url_ = None

    if len(parse) > 2:
        _temp = parse[1].split(" : ")

        if _temp[0] == "inline_url":
            info["inline_url"] = _temp[1]

            _temp = parse[2].split(" : ")

            if _temp[0] == "inline_text":
                info["inline_text"] = _temp[1]

            button = InlineKeyboardButton(text=info["inline_text"], url=info["inline_url"])
            url_ = InlineKeyboardMarkup(inline_keyboard=[[button]])

    if len(parse) > 2:
        _temp = parse[3].split(" : ")
    else:
        _temp = parse[1].split(" : ")

    if _temp[0] == "text":
        info["text"] = _temp[1]

    for chat in elli_bot.getChats():
        if not info["all"] and not str(chat)[0] == "-":
            continue
        try:
            if message.reply_to_message.photo:
                await bot.send_photo(chat, message.reply_to_message.photo[-1].file_id, info["text"], reply_markup=url_)
                await activityHandler(f"Доставлено в {chat}")
            else:
                await bot.send_message(chat, info["text"], reply_markup=url_)
                await activityHandler(f"Доставлено в {chat}")

        except exceptions.BotKicked as e:
            print(f"{chat} | Ошибка отправки сообщения. Происходит удаление из БД... Ошибка: {e}")
            elli_bot.clearChatInfo(chat)


async def botSendTestMessage(message: types.Message):

    if message.from_user.id not in WHITELIST:
        return

    if message.reply_to_message.photo:
        parse = message.reply_to_message.caption.split(" ||| ")
    else:
        parse = message.reply_to_message.text.split(" ||| ")

    info = {}

    _temp = parse[0].split(" : ")

    if _temp[0] == "all":
        match _temp[1]:
            case "True":
                info["all"] = True
            case "False":
                info["all"] = False
            case _:
                info["all"] = False

    _temp = parse[1].split(" : ")

    url_ = None

    if _temp[0] == "inline_url":
        info["inline_url"] = _temp[1]

        _temp = parse[2].split(" : ")

        if _temp[0] == "inline_text":
            info["inline_text"] = _temp[1]

        button = InlineKeyboardButton(text=info["inline_text"], url=info["inline_url"])
        url_ = InlineKeyboardMarkup(inline_keyboard=[[button]])

    _temp = parse[3].split(" : ")

    if _temp[0] == "text":
        info["text"] = _temp[1]

    if message.reply_to_message.photo:
        await bot.send_photo(os.environ["CONSOLE_CHAT"], message.reply_to_message.photo[-1].file_id, info["text"], reply_markup=url_)
    else:
        await bot.send_message(os.environ["CONSOLE_CHAT"], info["text"], reply_markup=url_)


async def botGiftHandler(message: types.Message) -> None:

    chat_id = message.chat.id

    await elli_bot.concreteChatInfo(message)

    if elli_bot.setGift(chat_id):
        await message.reply("Поздравляю, вы получили бесплатную недельную подписку!")
    else:
        await message.reply("К сожалению, вы уже использовали бесплатную недельную подписку.")

    await activityHandler(f"{chat_id} | Получена бесплатная недельная подписка.")


async def botClearGiftHandler(message: types.Message) -> None:

    if message.from_user.id not in WHITELIST:
        return

    elli_bot.clearAllGift()

    await message.reply("Теперь все могут получить недельную подписку бесплатно!")
