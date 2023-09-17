import asyncio
import os

import openai
from aiogram.types import ChatActions
from googletrans import Translator

from data import ElliMemory, activityHandler, elli_bot
from default_data import bot

openai.api_key = os.environ["OPENAI_API_KEY"]

em = ElliMemory()
translator = Translator()


async def createResponse(chat_id, user_id, prompt, rtype="text"):

    if rtype == "image":
        return await getImageResponse({"chat_id": chat_id,
                                       "user_id": user_id,
                                       "prompt": prompt})
    em.checkTokens(chat_id)
    return await getResponse({"chat_id": chat_id,
                              "user_id": user_id,
                              "prompt": prompt})


async def getResponse(info: dict) -> str:

    try:
        if len(em.getQueue()) > 3:
            bot.send_message(info["chat_id"], "Высокая нагрузка на бота, ожидайте ответа...")
        while len(em.getQueue()) > 3:
            if em.getQueue()[0] == info["user_id"] or em.getQueue()[1] == info["chat_id"]:
                break
            await asyncio.sleep(2)
        else:
            await asyncio.sleep(5)
        await em.addQueue(info["user_id"])

        if not elli_bot.getCharacter(info["chat_id"]) == em.getMessages(info["chat_id"])[0]["content"]:
            em.changeCharacter(info["chat_id"], elli_bot.getCharacter(info["chat_id"]))

        await bot.send_chat_action(info["chat_id"], ChatActions.TYPING)

        em.addMessage(info["chat_id"], "user", info["prompt"])
        response = await openai.ChatCompletion.acreate(
            model="gpt-3.5-turbo-16k",
            messages=em.getMessages(info["chat_id"])
        )

        em.addMessage(info["chat_id"], "assistant", response['choices'][0]['message']['content'])

        await em.delQueue()

        return response['choices'][0]['message']['content']

    except (openai.error.APIError, openai.error.APIConnectionError) as e:

        await activityHandler(f"{info['chat_id']} | Error APIError: {e}")

        await em.delQueue()

        return "Произошла внутренняя ошибка, повторите запрос позже. Приносим извинения за неудобства."

    except openai.error.RateLimitError as e:

        await activityHandler(f"{info['chat_id']} | Error RateLimitError: {e}")
        await asyncio.sleep(20)

        await em.delQueue()

        return await getResponse(info)

    except Exception as e:

        await activityHandler(f"{info['chat_id']} | Unknown error: {e}")
        print(e)

        await asyncio.sleep(3)
        await em.delQueue()

        return "Произошла непредвиденная ошибка, повторите запрос позже. Приносим извинения за неудобства. \
               \nЕсли ошибка останется на продолжительное время - обратитесь к @akkuchan0."


async def getImageResponse(info: dict) -> str:

    try:

        prompt = translator.translate(info["prompt"], dest="en").text

        await bot.send_chat_action(info["chat_id"], ChatActions.TYPING)

        response = await openai.Image.acreate(
            prompt=prompt,
            n=1,
            size="512x512"
        )

        return response['data'][0]['url']

    except Exception as e:
        await activityHandler(f"{info['chat_id']} | Error: {e}")
        return "Ой-ой, кажется, я немного заглючила. Попробуйте ещё раз."


async def changeCharacterHandler(chat_id: int, character: str) -> None:
    em.changeCharacter(chat_id, character)

    await bot.send_message(chat_id, f"Изменение характера прошло успешно.\n\nТекущий характер:\n{character}")
    await activityHandler(f"{chat_id} | Change character: {character}")


async def clearChatHandler(chat_id: int) -> None:
    em.clearMessages(chat_id)
    await bot.send_message(chat_id, "Память успешно очищена.")
    await activityHandler(f"{chat_id} | Clear chat: {chat_id}")


async def defaultElliHandler(chat_id: int) -> None:
    em.toDefaultMessage(chat_id)
    await bot.send_message(chat_id, "Я сброшена к стандартным настройкам.")
